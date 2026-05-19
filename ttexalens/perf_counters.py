# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Public library API for Tensix performance counters.

End-user entry point. The hardware-level class lives in
:mod:`ttexalens.hardware.perf_counters`; this module wraps it with helpers
that handle context resolution, coordinate conversion, and multi-device /
multi-core iteration.
"""
from ttexalens import _lib_helpers
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.perf_counters import (
    PerfCounterBlockDescription,
    TensixPerfCounters,
)
from ttexalens.util import TTException

__all__ = [
    "init_perf_counters",
    "start_perf_counters",
    "stop_perf_counters",
    "read_perf_counters",
    "list_perf_counters",
    "PerfCounterBlockDescription",
    "TensixPerfCounters",
]


def _resolve_perf_counters(
    location: str | OnChipCoordinate,
    *,
    device_id: int = 0,
    context: Context | None = None,
    neo_id: int | None = None,
) -> tuple[OnChipCoordinate, TensixPerfCounters]:
    coordinate = _lib_helpers.convert_coordinate(location, device_id, context)
    perf = coordinate.noc_block.get_perf_counters(neo_id=neo_id)
    if perf is None:
        raise TTException(
            f"Performance counters are not available on {coordinate.to_user_str()} "
            f"(block_type={coordinate.noc_block.block_type})."
        )
    return coordinate, perf


def _resolve_perf_targets(
    location: str | OnChipCoordinate | None,
    *,
    device_id: int | None,
    context: Context | None,
    neo_id: int | None,
) -> list[tuple[int, OnChipCoordinate, TensixPerfCounters]]:
    """Resolve filters into the list of (device_id, coord, perf) triples.

    Behavior:
      - ``location`` given: single explicit core. Raises ``TTException`` if
        the core has no perf counters (mirrors ``_resolve_perf_counters``).
      - ``location`` is None: walk every functional-worker location on each
        selected device, silently skipping any that don't expose perf
        counters (e.g. harvested rows). This is the bulk-read default and
        should never raise on missing perf-counter providers.
      - ``device_id`` given: only that device.
      - ``device_id`` is None: every device the context knows about.
    """
    ctx = _lib_helpers.check_context(context)

    if location is not None:
        coord, perf = _resolve_perf_counters(
            location,
            device_id=device_id if device_id is not None else 0,
            context=ctx,
            neo_id=neo_id,
        )
        return [(coord.device.id, coord, perf)]

    device_ids = [device_id] if device_id is not None else list(ctx.device_ids)
    targets: list[tuple[int, OnChipCoordinate, TensixPerfCounters]] = []
    for did in device_ids:
        device = ctx.find_device_by_id(did)
        for coord in device.get_block_locations(block_type="functional_workers"):
            maybe_perf = coord.noc_block.get_perf_counters(neo_id=neo_id)
            if maybe_perf is None:
                continue
            targets.append((did, coord, maybe_perf))
    return targets


@_lib_helpers.trace_api
def init_perf_counters(
    location: str | OnChipCoordinate,
    block_name: str | None = None,
    *,
    device_id: int = 0,
    context: Context | None = None,
    noc_id: int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> None:
    """Initialize Tensix performance counters on a Tensix functional worker.

    Replicates the firmware ``init_perf_counters()`` sequence (REG0=0xFFFFFFFF,
    REG1=0, REG2=0, REG2=1) from ``trisc.cc`` so callers can baseline the
    counters from the host side. Useful in post-mortem flows or when firmware
    has not run.

    Args:
        location: Tensix core coordinate.
        block_name: If specified, only initialize that block (e.g. "FPU").
            If None, initializes all blocks (matching firmware behavior).
        device_id: Device id (default 0).
        context: TTExaLens context (default: global).
        noc_id: NOC id; defaults to context's active NOC.
        neo_id: NEO id (Quasar only); defaults to None.
        safe_mode: If specified, override the context's safe_mode for the
            register writes. Default: honor context.
    """
    coordinate, perf = _resolve_perf_counters(location, device_id=device_id, context=context, neo_id=neo_id)
    noc_id = _lib_helpers.check_noc_id(noc_id, coordinate.context)
    if block_name is None:
        perf.init_all(noc_id=noc_id, safe_mode=safe_mode)
    else:
        perf.init_block(block_name, noc_id=noc_id, safe_mode=safe_mode)


@_lib_helpers.trace_api
def start_perf_counters(
    location: str | OnChipCoordinate,
    block_name: str | None = None,
    *,
    device_id: int = 0,
    context: Context | None = None,
    noc_id: int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> None:
    """Start Tensix performance counters.

    Args:
        block_name: If None, starts every block. Otherwise starts the
            named block individually.
        safe_mode: If specified, override the context's safe_mode for the
            register writes. Default: honor context.
    """
    coordinate, perf = _resolve_perf_counters(location, device_id=device_id, context=context, neo_id=neo_id)
    noc_id = _lib_helpers.check_noc_id(noc_id, coordinate.context)
    if block_name is None:
        perf.start_all(noc_id=noc_id, safe_mode=safe_mode)
    else:
        perf.start_block(block_name, noc_id=noc_id, safe_mode=safe_mode)


@_lib_helpers.trace_api
def stop_perf_counters(
    location: str | OnChipCoordinate,
    block_name: str | None = None,
    *,
    device_id: int = 0,
    context: Context | None = None,
    noc_id: int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> None:
    """Stop Tensix performance counters.

    Args:
        block_name: If None, stops every block.
            Otherwise stops the named block individually.
        safe_mode: If specified, override the context's safe_mode for the
            register writes. Default: honor context.
    """
    coordinate, perf = _resolve_perf_counters(location, device_id=device_id, context=context, neo_id=neo_id)
    noc_id = _lib_helpers.check_noc_id(noc_id, coordinate.context)
    if block_name is None:
        perf.stop_all(noc_id=noc_id, safe_mode=safe_mode)
    else:
        perf.stop_block(block_name, noc_id=noc_id, safe_mode=safe_mode)


@_lib_helpers.trace_api
def read_perf_counters(
    location: str | OnChipCoordinate | None = None,
    block_name: str | None = None,
    *,
    device_id: int | None = None,
    context: Context | None = None,
    noc_id: int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> dict[tuple[int, OnChipCoordinate, str, int, str], tuple[int, int]]:
    """Read every named counter in the selected scope.

    Defaults walk all devices, all functional-worker locations on those
    devices, and all blocks. Pass ``location`` and/or ``block_name`` to
    narrow. Pass ``device_id`` to restrict to a single device.

    Returns a flat dict keyed by
    ``(device_id, coord, block_name, counter_id, counter_name)``. Each value
    is a ``(counter_value, ref_cnt)`` tuple. ``ref_cnt`` is the block's
    free-running cycle counter (OUT_L) sampled alongside the counter read —
    so each entry carries its own denominator for utilization ratios::

        snap0 = read_perf_counters()
        time.sleep(0.1)
        snap1 = read_perf_counters()
        for key in snap0:
            v0, r0 = snap0[key]
            v1, r1 = snap1[key]
            counter_delta = (v1 - v0) & 0xFFFFFFFF
            ref_delta     = (r1 - r0) & 0xFFFFFFFF
            utilization   = counter_delta / ref_delta if ref_delta else 0

    Notes:
      - Counter values are unsigned 32-bit. Subtraction wraps; mask with
        ``& 0xFFFFFFFF`` when computing deltas.
      - Each (location, counter) entry does a REG1 write + three OUT_L/OUT_H
        reads (the read_counter protocol) plus one extra OUT_L read for the
        paired ``ref_cnt``.
      - ``noc_id``/``safe_mode`` apply uniformly across the whole sweep.

    Raises:
        TTException: if ``location`` is given and that location has no
            perf-counter provider. With ``location=None`` non-tensix
            functional-workers (e.g. harvested rows) are silently skipped.
    """
    targets = _resolve_perf_targets(location, device_id=device_id, context=context, neo_id=neo_id)
    if not targets:
        return {}

    resolved_noc = _lib_helpers.check_noc_id(noc_id, targets[0][1].context)
    out: dict[tuple[int, OnChipCoordinate, str, int, str], tuple[int, int]] = {}
    for did, coord, perf in targets:
        block_names = [block_name] if block_name is not None else perf.block_names
        for bname in block_names:
            block = perf.get_block(bname)
            for cid, cname in block.counters.items():
                value = perf.read_counter(bname, cid, noc_id=resolved_noc, safe_mode=safe_mode)
                # Sample ref_cnt right after the counter value so the pair is
                # captured close together in time. OUT_L is independent of
                # REG1 — the just-completed read_counter doesn't disturb it.
                ref = perf.read_ref_cnt(bname, noc_id=resolved_noc, safe_mode=safe_mode)
                out[(did, coord, bname, cid, cname)] = (value, ref)
    return out


@_lib_helpers.trace_api
def list_perf_counters(
    location: str | OnChipCoordinate | None = None,
    *,
    device_id: int | None = None,
    context: Context | None = None,
    neo_id: int | None = None,
) -> dict[tuple[int, OnChipCoordinate, str], list[tuple[int, str]]]:
    """Discover which blocks/counters exist at the selected scope.

    Defaults walk all devices and all functional-worker locations. Same
    filter semantics as :func:`read_perf_counters`. Pure introspection —
    no register I/O, no ``noc_id`` / ``safe_mode`` parameters.

    Returns ``{(device_id, coord, block_name): [(counter_id, counter_name), ...]}``,
    sorted by counter id, with empty-counter blocks excluded.
    """
    targets = _resolve_perf_targets(location, device_id=device_id, context=context, neo_id=neo_id)
    out: dict[tuple[int, OnChipCoordinate, str], list[tuple[int, str]]] = {}
    for did, coord, perf in targets:
        for bname in perf.block_names:
            block = perf.get_block(bname)
            if not block.counters:
                continue
            out[(did, coord, bname)] = sorted(block.counters.items())
    return out
