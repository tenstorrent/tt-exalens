# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Tensix performance-counter access (architecture-agnostic).

Each Tensix functional worker exposes a debug-perf-counter block at
``0xFFB12000`` containing several "counter blocks" (FPU, INSTRN_THREAD,
TDMA_UNPACK, TDMA_PACK, ...). Each counter block follows the same
3-register pattern:

  - ``REG0``: counter-select mask (firmware writes 0xFFFFFFFF to enable all)
  - ``REG1``: mode + event select. Bits ``[15:8]`` pick which sub-counter
    is routed onto OUT_H. Bit ``[16]`` toggles the req-vs-grant view of the
    same counter; we encode the grant view as counter ids 256..511.
  - ``REG2``: control. Bit 0 = start (rising edge), bit 1 = stop.

Outputs are 64-bit, split across:
  - ``OUT_L``: free-running 32-bit reference cycle counter (denominator).
  - ``OUT_H``: 32-bit value of whatever counter is currently selected by REG1.

Per-architecture register names and counter-id maps live alongside this
module under ``ttexalens/hardware/<arch>/perf_counters.py``. The protocol
itself is identical across Wormhole and Blackhole; Quasar uses a different
layout and currently raises NotImplementedError.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

from ttexalens._lib_helpers import trace_api
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.util import TTException

if TYPE_CHECKING:
    from ttexalens.hardware.noc_block import NocBlock
    from ttexalens.register_store import RegisterStore


# Counter ids occupy 9 bits in REG1: 8-bit bank index in [15:8] plus the
# grant-view selector in [16]. We flatten that into a single id space of
# [0, 512) where ids >= 256 are the grant view of bank (id - 256).
_COUNTER_ID_LIMIT = 512


@dataclass(frozen=True)
class PerfCounterBlockDescription:
    """Describes one counter block (e.g. FPU, INSTRN_THREAD).

    Register names are looked up in the noc-block's register store at read
    time; the same description can be reused across architectures whose
    register stores share these names (Wormhole and Blackhole do).

    The ``counters`` mapping is wrapped in ``MappingProxyType`` after
    construction so callers cannot mutate the per-arch HW spec at runtime.
    """

    name: str
    reg0: str  # counter-select mask (X0)
    reg1: str  # mode + counter select (X1)
    reg2: str  # control: bit0=start, bit1=stop (X2)
    out_l: str  # reference cycle counter (free-running)
    out_h: str  # selected event counter (depends on REG1)
    counters: Mapping[int, str]  # counter_id -> human name; ids >= 256 are grant-mode

    def __post_init__(self) -> None:
        for cid in self.counters:
            if not 0 <= cid < _COUNTER_ID_LIMIT:
                raise ValueError(f"counter id {cid} in block {self.name!r} out of range [0, {_COUNTER_ID_LIMIT})")
        # Freeze the counters mapping. Use object.__setattr__ because the
        # dataclass is frozen.
        if not isinstance(self.counters, MappingProxyType):
            object.__setattr__(self, "counters", MappingProxyType(dict(self.counters)))


@dataclass(frozen=True)
class TensixPerfCountersInitialization:
    """Module-level immutable spec; one per arch.

    Mirrors the ``DebugBusSignalStore.create_initialization`` /
    ``RegisterStore.create_initialization`` two-phase pattern: build this
    once per architecture at module load, then bind it cheaply per noc
    block instance. The ``blocks`` mapping is wrapped in ``MappingProxyType``
    in ``__post_init__`` so the per-arch spec is genuinely immutable.
    """

    blocks: Mapping[str, PerfCounterBlockDescription]

    def __post_init__(self) -> None:
        if not isinstance(self.blocks, MappingProxyType):
            object.__setattr__(self, "blocks", MappingProxyType(dict(self.blocks)))


class TensixPerfCounters:
    """Per-core wrapper over the Tensix perf-counter registers.

    Obtain via ``noc_block.get_perf_counters()`` (or the higher-level
    library helpers in :mod:`ttexalens.perf_counters`) — do not construct
    directly. The noc block's ``__init__`` wires this up so NOC routing
    and (for Quasar) per-NEO register-store selection are inherited.

    Concurrency note: ``read_counter`` writes REG1 to select the counter
    being read. This is racy with anything else that writes REG1 — most
    notably with firmware that may itself reconfigure the perf-counter
    block on every kernel launch (``init_perf_counters()`` in trisc.cc).
    Callers must serialize against firmware writes, e.g. by halting the
    relevant cores or running between kernel launches.
    """

    # REG1 encoding: counter index in bits [15:8], grant-bit in [16].
    _GRANT_BIT = 1 << 16

    # REG2 bit layout.
    _CTRL_START = 1
    _CTRL_STOP = 2

    def __init__(
        self,
        initialization: TensixPerfCountersInitialization,
        noc_block: NocBlock,
        neo_id: int | None = None,
    ):
        self._blocks = initialization.blocks
        self._noc_block = noc_block
        self._neo_id = neo_id

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @cached_property
    def block_names(self) -> list[str]:
        return list(self._blocks.keys())

    def get_block(self, block_name: str) -> PerfCounterBlockDescription:
        if block_name not in self._blocks:
            raise ValueError(f"Unknown perf-counter block '{block_name}'. Available: {sorted(self._blocks)}")
        return self._blocks[block_name]

    # ------------------------------------------------------------------
    # Control
    # ------------------------------------------------------------------

    def init_block(
        self,
        block_name: str,
        *,
        noc_id: int | None = None,
        safe_mode: bool | None = None,
    ) -> None:
        """Replicate the firmware init sequence for one block.

        Mirrors ``init_perf_counters()`` in ``trisc.cc`` on tt-1xx::

            REG0 = 0xFFFFFFFF  (counter-select mask: enable all)
            REG1 = 0           (clear mode + counter select)
            REG2 = 0           (clear control)
            REG2 = 1           (rising-edge start)
        """
        block = self.get_block(block_name)
        store = self._register_store(noc_id)
        store.write_register(block.reg0, 0xFFFFFFFF, safe_mode=safe_mode)
        store.write_register(block.reg1, 0, safe_mode=safe_mode)
        store.write_register(block.reg2, 0, safe_mode=safe_mode)
        store.write_register(block.reg2, self._CTRL_START, safe_mode=safe_mode)

    def init_all(self, *, noc_id: int | None = None, safe_mode: bool | None = None) -> None:
        """Init every known block. Equivalent to firmware init on tt-1xx."""
        for name in self._blocks:
            self.init_block(name, noc_id=noc_id, safe_mode=safe_mode)

    def start_block(
        self,
        block_name: str,
        *,
        noc_id: int | None = None,
        safe_mode: bool | None = None,
    ) -> None:
        """Start one block (rising edge on REG2[0])."""
        block = self.get_block(block_name)
        store = self._register_store(noc_id)
        store.write_register(block.reg2, 0, safe_mode=safe_mode)
        store.write_register(block.reg2, self._CTRL_START, safe_mode=safe_mode)

    def stop_block(
        self,
        block_name: str,
        *,
        noc_id: int | None = None,
        safe_mode: bool | None = None,
    ) -> None:
        """Stop one block (rising edge on REG2[1])."""
        block = self.get_block(block_name)
        store = self._register_store(noc_id)
        store.write_register(block.reg2, 0, safe_mode=safe_mode)
        store.write_register(block.reg2, self._CTRL_STOP, safe_mode=safe_mode)

    def start_all(self, *, noc_id: int | None = None, safe_mode: bool | None = None) -> None:
        """Start every known block.

        Iterates per-block.
        """
        for name in self._blocks:
            self.start_block(name, noc_id=noc_id, safe_mode=safe_mode)

    def stop_all(self, *, noc_id: int | None = None, safe_mode: bool | None = None) -> None:
        """Stop every known block (per-block; see ``start_all`` for rationale)."""
        for name in self._blocks:
            self.stop_block(name, noc_id=noc_id, safe_mode=safe_mode)

    # ------------------------------------------------------------------
    # Readback
    # ------------------------------------------------------------------

    def read_ref_cnt(
        self,
        block_name: str,
        *,
        noc_id: int | None = None,
        safe_mode: bool | None = None,
    ) -> int:
        """Read the block's free-running cycle counter (the denominator)."""
        block = self.get_block(block_name)
        return self._register_store(noc_id).read_register(block.out_l, safe_mode=safe_mode)

    def read_counter(
        self,
        block_name: str,
        counter: int | str,
        *,
        noc_id: int | None = None,
        safe_mode: bool | None = None,
    ) -> int:
        """Select ``counter`` in REG1 and return the OUT_H readback.

        ``counter`` is either the numeric id (0..511; >=256 means grant view)
        or the human name listed in the block description's counter map.
        """
        block = self.get_block(block_name)
        counter_id = self._resolve_counter(block, counter)
        return self._read_counter_id(block, counter_id, noc_id, safe_mode)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _register_store(self, noc_id: int | None) -> RegisterStore:
        if noc_id is None:
            # Pick up the active NOC from the device's TTExaLens context so
            # callers reaching directly through ``noc_block.perf_counters``
            # don't have to re-resolve it themselves.
            noc_id = 1 if self._noc_block.location.context.use_noc1 else 0
        return self._noc_block.get_register_store(noc_id=noc_id, neo_id=self._neo_id)

    def _resolve_counter(self, block: PerfCounterBlockDescription, counter: int | str) -> int:
        if isinstance(counter, int):
            if not 0 <= counter < _COUNTER_ID_LIMIT:
                raise ValueError(f"counter id {counter} out of range [0, {_COUNTER_ID_LIMIT})")
            return counter
        for cid, name in block.counters.items():
            if name == counter:
                return cid
        raise ValueError(
            f"Unknown counter {counter!r} in block {block.name!r}. Available: {sorted(block.counters.values())}"
        )

    def _read_counter_id(
        self,
        block: PerfCounterBlockDescription,
        counter_id: int,
        noc_id: int | None,
        safe_mode: bool | None,
    ) -> int:
        if counter_id >= 256:
            mode_value = ((counter_id - 256) << 8) | self._GRANT_BIT
        else:
            mode_value = counter_id << 8
        store = self._register_store(noc_id)
        store.write_register(block.reg1, mode_value, safe_mode=safe_mode)
        # Two dummy reads to let the MUX and output registers settle. Matches
        # the production tt-metal reference in tools/triage/check_perf_counters.py.
        store.read_register(block.out_l, safe_mode=safe_mode)
        store.read_register(block.out_h, safe_mode=safe_mode)
        return store.read_register(block.out_h, safe_mode=safe_mode)

    @staticmethod
    def create_initialization(
        blocks: list[PerfCounterBlockDescription],
    ) -> TensixPerfCountersInitialization:
        """Create the immutable per-arch initialization spec.

        Counter-id range is validated by ``PerfCounterBlockDescription.__post_init__``
        when each block is constructed; this factory just bundles the blocks
        by name.
        """
        return TensixPerfCountersInitialization(
            blocks={b.name: b for b in blocks},
        )
