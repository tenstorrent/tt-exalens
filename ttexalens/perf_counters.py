# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Public library API for Tensix performance counters.

Each function operates on exactly one core (one ``OnChipCoordinate``) and
raises if perf counters are not wired there. Callers that want to fan
out across many cores iterate themselves.
"""

from ttexalens import _lib_helpers
from ttexalens.context import NocId
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.perf_counters import (
    PerfCounterBlockDescription,
    TensixPerfCounters,
)
from ttexalens.exceptions import TTException

__all__ = [
    "PerfCounterBlockDescription",
    "TensixPerfCounters",
    "list_perf_counters",
    "read_perf_counters",
    "reset_perf_counters",
    "start_perf_counters",
    "stop_perf_counters",
]


def _check_and_get_perf_counters(
    location: OnChipCoordinate,
    neo_id: int | None,
) -> TensixPerfCounters:
    perf = location.noc_block.get_perf_counters(neo_id=neo_id)
    if perf is None:
        raise TTException(
            f"Performance counters are not available on {location.to_user_str()} "
            f"(block_type={location.noc_block.block_type})."
        )
    return perf


@_lib_helpers.trace_api
def reset_perf_counters(
    location: OnChipCoordinate,
    block_name: str | None = None,
    *,
    noc_id: NocId | int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> None:
    """Reset Tensix perf counters on this core. Raises if perf counters are not wired here."""
    perf = _check_and_get_perf_counters(location, neo_id)
    noc_id = _lib_helpers.check_noc_id(noc_id, location.context)
    if block_name is None:
        for block_name in perf.block_names:
            perf.reset_block(block_name, noc_id=noc_id, neo_id=neo_id, safe_mode=safe_mode)
    else:
        perf.reset_block(block_name, noc_id=noc_id, neo_id=neo_id, safe_mode=safe_mode)


@_lib_helpers.trace_api
def start_perf_counters(
    location: OnChipCoordinate,
    block_name: str | None = None,
    *,
    noc_id: NocId | int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> None:
    """Start Tensix perf counters on this core. Raises if perf counters are not wired here."""
    perf = _check_and_get_perf_counters(location, neo_id)
    noc_id = _lib_helpers.check_noc_id(noc_id, location.context)
    if block_name is None:
        for block_name in perf.block_names:
            perf.start_block(block_name, noc_id=noc_id, neo_id=neo_id, safe_mode=safe_mode)
    else:
        perf.start_block(block_name, noc_id=noc_id, neo_id=neo_id, safe_mode=safe_mode)


@_lib_helpers.trace_api
def stop_perf_counters(
    location: OnChipCoordinate,
    block_name: str | None = None,
    *,
    noc_id: NocId | int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> None:
    """Stop Tensix perf counters on this core. Raises if perf counters are not wired here."""
    perf = _check_and_get_perf_counters(location, neo_id)
    noc_id = _lib_helpers.check_noc_id(noc_id, location.context)
    if block_name is None:
        for block_name in perf.block_names:
            perf.stop_block(block_name, noc_id=noc_id, neo_id=neo_id, safe_mode=safe_mode)
    else:
        perf.stop_block(block_name, noc_id=noc_id, neo_id=neo_id, safe_mode=safe_mode)


@_lib_helpers.trace_api
def read_perf_counters(
    location: OnChipCoordinate,
    block_name: str | None = None,
    *,
    noc_id: NocId | int | None = None,
    neo_id: int | None = None,
    safe_mode: bool | None = None,
) -> dict[tuple[str, int, str], tuple[int, int]]:
    """Read every named counter on this core (or only those in ``block_name``).
    Returns a dict keyed by ``(block_name, counter_id, counter_name)`` with
    values ``(value, ref_cnt)``. Counter values are unsigned 32-bit; mask
    deltas with ``& 0xFFFFFFFF``. Raises ``TTException`` if perf counters
    are not wired here.
    """
    perf = location.noc_block.get_perf_counters(neo_id=neo_id)
    if perf is None:
        raise TTException(
            f"Performance counters are not available on {location.to_user_str()} "
            f"(block_type={location.noc_block.block_type})."
        )
    resolved_noc = _lib_helpers.check_noc_id(noc_id, location.context)
    out: dict[tuple[str, int, str], tuple[int, int]] = {}
    block_names = [block_name] if block_name is not None else perf.block_names
    for bname in block_names:
        block = perf.get_block(bname)
        for cid, cname in block.counters.items():
            value = perf.read_counter(bname, cid, noc_id=resolved_noc, safe_mode=safe_mode)
            ref = perf.read_ref_cnt(bname, noc_id=resolved_noc, safe_mode=safe_mode)
            out[(bname, cid, cname)] = (value, ref)
    return out


@_lib_helpers.trace_api
def list_perf_counters(location: OnChipCoordinate) -> dict[str, list[tuple[int, str]]]:
    """Return the perf-counter schema at this core as
    ``{block_name: [(counter_id, counter_name), ...]}``, sorted by counter
    id. Empty-counter blocks are omitted. Returns ``{}`` if perf counters
    are not wired here.
    """
    perf = location.noc_block.get_perf_counters()
    if perf is None:
        return {}
    out: dict[str, list[tuple[int, str]]] = {}
    for bname in perf.block_names:
        block = perf.get_block(bname)
        if block.counters:
            out[bname] = sorted(block.counters.items())
    return out
