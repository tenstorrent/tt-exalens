# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from abc import abstractmethod
from functools import cache, cached_property
from typing import TYPE_CHECKING

from ttexalens.context import NocId
from ttexalens.memory_map import MemoryMap

if TYPE_CHECKING:
    from ttexalens.device import Device
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.debug_bus_signal_store import DebugBusSignalStore
    from ttexalens.hardware.perf_counters import TensixPerfCounters
    from ttexalens.hardware.risc_debug import RiscDebug
    from ttexalens.register_store import RegisterStore
    from ttexalens.memory_map import MemoryMap


class NocBlock:
    def __init__(
        self,
        location: OnChipCoordinate,
        block_type: str,
        debug_bus: DebugBusSignalStore | None = None,
        perf_counters: TensixPerfCounters | None = None,
    ):
        self.location = location
        self.block_type = block_type
        self.debug_bus = debug_bus
        self.perf_counters = perf_counters
        self.noc_memory_map: MemoryMap = MemoryMap()

    @property
    def device(self) -> Device:
        return self.location.device

    @abstractmethod
    def get_register_store(self, noc_id: NocId | None = None, neo_id: int | None = None) -> RegisterStore:
        pass

    def get_debug_bus(self, neo_id: int | None = None) -> DebugBusSignalStore | None:
        if neo_id is None:
            return self.debug_bus
        return None

    def get_perf_counters(self, neo_id: int | None = None) -> TensixPerfCounters | None:
        return self.perf_counters

    @cached_property
    def has_risc_cores(self) -> bool:
        return len(self.debuggable_riscs) > 0

    @cached_property
    def debuggable_riscs(self) -> list[RiscDebug]:
        return [risc_debug for risc_debug in self.all_riscs if risc_debug.can_debug()]

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return []

    @property
    def neo_ids(self) -> list[int]:
        return []

    def get_riscs(self, neo_id: int | None = None) -> list[RiscDebug]:
        return [risc for risc in self.all_riscs if risc.risc_location.neo_id == neo_id]

    @cached_property
    def risc_names(self) -> list[str]:
        """
        Returns a list of RISC core names available in the NocBlock.
        This method should be overridden in subclasses to provide a specific implementation.
        """
        return [risc.risc_location.risc_name for risc in self.all_riscs]

    @cache
    def get_default_risc_debug(self, neo_id: int | None = None) -> RiscDebug:
        """
        Returns a default RiscDebug instance for the NocBlock. It is meant to be used by RegisterStore to read/write configuration regusters.
        If block has NEOs, the caller can specify which one it wants to use.
        This method should be overridden in subclasses to provide a specific implementation.
        """
        raise NotImplementedError(f"Noc block on location {self.location.to_user_str()} doesn't have RISC cores.")

    @cache
    def get_risc_debug(self, risc_name: str, neo_id: int | None = None) -> RiscDebug:
        """
        Returns a RiscDebug instance for the specified RISC core.
        This method should be overridden in subclasses to provide a specific implementation.
        """
        raise NotImplementedError(f"Noc block on location {self.location.to_user_str()} doesn't have RISC cores.")


def str_to_neo_id(value: str, noc_block: NocBlock) -> int | None:
    stripped = value.strip().lower()
    if stripped == "none":
        return None
    try:
        neo_id = int(stripped, 0)
    except ValueError:
        raise ValueError(f"Invalid NEO '{value}'. Expected None or one of {noc_block.neo_ids}.") from None
    return neo_id


def to_neo_id(value: str | int, noc_block: NocBlock) -> int | None:
    if isinstance(value, str):
        neo_id = str_to_neo_id(value, noc_block)
    else:
        neo_id = value

    if neo_id is not None and neo_id not in noc_block.neo_ids:
        where = f"{noc_block.block_type} block at {noc_block.location.to_user_str()}"
        raise ValueError(f"Invalid NEO {neo_id} for the {where}.")
    return neo_id


def neo_id_to_str(neo_id: int | None) -> str:
    return "None" if neo_id is None else str(neo_id)
