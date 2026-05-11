# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  perf-counters list
  perf-counters reset [--block=<name>] [-d <device>] [-l <loc>]
  perf-counters start [--block=<name>] [-d <device>] [-l <loc>]
  perf-counters stop [--block=<name>] [-d <device>] [-l <loc>]
  perf-counters read [--snapshot] [--block=<name>] [--counter=<id>] [--active] [-d <device>] [-l <loc>]

Options:
  --block=<name>        Block to operate on (FPU, INSTRN_THREAD, TDMA_UNPACK, TDMA_PACK).
                        For reset/start/stop/read: omit to operate on all blocks.
  --counter=<id>        Counter id (0..511) or human name from the block's counter map.
                        For read: omit to read every counter in the selected block(s).
  --snapshot            Take two snapshots over a short interval and report the delta
                        between them. Without --snapshot, ``read`` does a single
                        read and omits the Δ column.
  --active              Only show counters whose value changed during the snapshot
                        window. Requires --snapshot.

Description:
  Read and control Tensix hardware performance counters on a functional worker core.

  Subcommands:
    list      Show every counter block and its counters defined for Tensix
              functional-worker cores.
    reset     Reset performance counters.
    start     Start every block (or just --block).
    stop      Stop every block (or just --block).
    read      Read counters. Both --block and --counter are optional. With
              no args, reads every counter in every block. With --block=X,
              reads every counter in block X. With --block=X --counter=Y,
              reads just counter Y in block X. By default each counter is
              read once; pass --snapshot to take two samples and show the
              delta between them.

Examples:
  perf-counters list
  perf-counters reset -l 0,0
  perf-counters start
  perf-counters read
  perf-counters read --snapshot --active
  perf-counters read --block=FPU
  perf-counters read --block=FPU --counter=fpu_or_sfpu_instrn
"""

import time
from typing import Iterator

from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, CommonCommandOptions, tt_docopt
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.perf_counters import (
    list_perf_counters,
    read_perf_counters,
    reset_perf_counters,
    start_perf_counters,
    stop_perf_counters,
)
from ttexalens.rich_formatters import formatter
from ttexalens.uistate import UIState


command_metadata = CommandMetadata(
    short_name="pc",
    long_name="perf-counters",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)


_SNAPSHOT_INTERVAL_S = 0.1

# (device_id, coord, block_name, counter_id, counter_name) — the CLI fans out
# read_perf_counters() across multiple cores and prepends (device_id, coord)
# to the lib's per-core key so rows from different cores stay distinguishable.
FlatKey = tuple[int, OnChipCoordinate, str, int, str]
# Snapshot of every counter on every core in scope: FlatKey -> (value, ref_cnt).
# Two snapshots can be compared key-by-key to compute deltas in --snapshot mode.
FlatSnap = dict[FlatKey, tuple[int, int]]


def _parse_counter(arg: str) -> int | str:
    arg = arg.strip()
    try:
        return int(arg, 0)
    except ValueError:
        return arg


def _print_list(listing: dict[str, list[tuple[int, str]]]) -> None:
    if not listing:
        print("  (no readable counter blocks)")
        return
    data = {bname: [(str(cid), cname) for cid, cname in counters] for bname, counters in listing.items()}
    formatter.display_grouped_data_autoflow(
        data,
        columns=[("ID", "cyan"), ("Counter", "green")],
        sort_by_height_desc=False,
    )


def _iter_perf_targets(
    dopt: tt_docopt, context: Context, ui_state: UIState
) -> Iterator[tuple[Device, OnChipCoordinate]]:
    """Yield (device, location) pairs that have perf counters wired.
    Warns and skips targets without perf counters.
    """
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            if loc.noc_block.get_perf_counters() is None:
                util.WARN(
                    f"chip={device.id} core={loc.to_user_str()}: "
                    f"performance counters are not available on block_type={loc.noc_block.block_type}"
                )
                continue
            yield device, loc


def _build_render_data(
    snap: FlatSnap,
    snap_prev: FlatSnap | None,
    active_only: bool,
    consolidated: bool,
) -> dict[str, list[tuple[str, ...]]]:
    """Group counter rows by block. If ``consolidated`` prepend a Loc column."""
    data: dict[str, list[tuple[str, ...]]] = {}

    for key, (v1, r1) in snap.items():
        did, coord, block_name, cid, cname = key
        value_str = f"{v1} (0x{v1:08x})"

        if snap_prev is not None:
            v0, r0 = snap_prev[key]
            delta = (v1 - v0) & 0xFFFFFFFF
            if active_only and delta == 0:
                continue
            delta_str = f"+{delta}" if delta else "0"
            ref_delta = (r1 - r0) & 0xFFFFFFFF
            ref_str = f"{r1} (+{ref_delta})" if ref_delta else f"{r1} (0)"
            if consolidated:
                loc_str = f"d{did} {coord.to_user_str()}"
                row: tuple[str, ...] = (loc_str, str(cid), cname, value_str, delta_str, ref_str)
            else:
                row = (str(cid), cname, value_str, delta_str, ref_str)
        else:
            ref_str = str(r1)
            if consolidated:
                loc_str = f"d{did} {coord.to_user_str()}"
                row = (loc_str, str(cid), cname, value_str, ref_str)
            else:
                row = (str(cid), cname, value_str, ref_str)
        data.setdefault(block_name, []).append(row)
    return data


def _render_per_core(
    snap: FlatSnap,
    snap_prev: FlatSnap | None,
    active_only: bool,
) -> None:
    sample_key = next(iter(snap))
    did, coord = sample_key[0], sample_key[1]
    print(f"\n=== Perf Counter Read: chip={did} core={coord.to_user_str()} ===\n")
    data = _build_render_data(snap, snap_prev, active_only, consolidated=False)
    if not data:
        print("  (no counters changed)")
        return
    base_cols: list[tuple[str, str]] = [
        ("ID", "cyan"),
        ("Counter", "green"),
        ("Value", "yellow"),
    ]
    if snap_prev is not None:
        base_cols.append(("Δ", "magenta"))
    base_cols.append(("ref_cnt", "white"))
    formatter.display_grouped_data_autoflow(data, columns=base_cols, sort_by_height_desc=False)


def _render_consolidated(
    snap: FlatSnap,
    snap_prev: FlatSnap | None,
    active_only: bool,
) -> None:
    print("\n=== Perf Counter Read: multiple cores ===\n")
    data = _build_render_data(snap, snap_prev, active_only, consolidated=True)
    if not data:
        print("  (no counters changed)")
        return
    base_cols: list[tuple[str, str]] = [
        ("Loc", "blue"),
        ("ID", "cyan"),
        ("Counter", "green"),
        ("Value", "yellow"),
    ]
    if snap_prev is not None:
        base_cols.append(("Δ", "magenta"))
    base_cols.append(("ref_cnt", "white"))
    formatter.display_grouped_data_autoflow(data, columns=base_cols, sort_by_height_desc=False)


def _run_list(context: Context) -> None:
    listing: dict[str, list[tuple[int, str]]] = {}
    for device in context.devices.values():
        for coord in device.get_block_locations("functional_workers"):
            listing = list_perf_counters(coord)
            if listing:
                break
        if listing:
            break
    print("\n=== Perf Counter Blocks (Tensix functional workers) ===\n")
    _print_list(listing)


def _run_read(
    dopt: tt_docopt,
    args: dict,
    context: Context,
    ui_state: UIState,
    block_name: str | None,
) -> None:
    targets = list(_iter_perf_targets(dopt, context, ui_state))
    if not targets:
        util.WARN("no perf-counter targets in scope")
        return

    if args["--counter"] is not None:
        if block_name is None:
            util.WARN("--counter requires --block (counter ids are not unique across blocks)")
            return
        counter_arg = _parse_counter(args["--counter"])
        matched = False
        for _device, loc in targets:
            per_core = read_perf_counters(loc, block_name=block_name)
            for (_bname, cid, cname), (value, _ref) in per_core.items():
                if (isinstance(counter_arg, int) and cid == counter_arg) or (
                    isinstance(counter_arg, str) and cname == counter_arg
                ):
                    print(value)
                    matched = True
        if not matched:
            util.WARN(f"counter {counter_arg!r} not found in block {block_name}")
        return

    snapshot_mode = args["--snapshot"]
    active_only = args["--active"]
    if active_only and not snapshot_mode:
        util.WARN("--active requires --snapshot (nothing to compare against without a second sample)")
        active_only = False

    def take_snapshot() -> FlatSnap:
        snap: FlatSnap = {}
        for device, loc in targets:
            for (bname, cid, cname), (value, ref) in read_perf_counters(loc, block_name=block_name).items():
                snap[(device.id, loc, bname, cid, cname)] = (value, ref)
        return snap

    snap = take_snapshot()
    snap_prev: FlatSnap | None = None
    if snapshot_mode:
        snap_prev = snap
        time.sleep(_SNAPSHOT_INTERVAL_S)
        snap = take_snapshot()

    unique_locs = {(did, coord) for did, coord, *_ in snap.keys()}
    if len(unique_locs) > 1:
        _render_consolidated(snap, snap_prev, active_only)
    else:
        _render_per_core(snap, snap_prev, active_only)


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args
    block_name = args["--block"]

    if args["list"]:
        _run_list(context)
        return

    if args["read"]:
        _run_read(dopt, args, context, ui_state, block_name)
        return

    op_fn = {"reset": reset_perf_counters, "start": start_perf_counters, "stop": stop_perf_counters}
    for op_name, fn in op_fn.items():
        if not args[op_name]:
            continue
        for device, loc in _iter_perf_targets(dopt, context, ui_state):
            fn(loc, block_name)
            util.INFO(f"chip={device.id} core={loc.to_user_str()}: {op_name} {block_name or 'all blocks'}")
        return
