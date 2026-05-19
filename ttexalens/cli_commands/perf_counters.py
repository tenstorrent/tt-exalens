# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  perf-counters list [-d <device>] [-l <loc>]
  perf-counters init [--block=<name>] [-d <device>] [-l <loc>]
  perf-counters start [--block=<name>] [-d <device>] [-l <loc>]
  perf-counters stop [--block=<name>] [-d <device>] [-l <loc>]
  perf-counters read [--snapshot] [--block=<name>] [--counter=<id>] [--active] [-d <device>] [-l <loc>]

Options:
  --block=<name>        Block to operate on (FPU, INSTRN_THREAD, TDMA_UNPACK, TDMA_PACK).
                        For init/start/stop/read: omit to operate on all blocks.
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
    list      Show every counter block and its counters available on the current core.
    init      Replicate the firmware init_perf_counters() sequence (REG0=0xFFFFFFFF;
              REG1=0; REG2=0; REG2=1).
    start     Start every block (or just --block) by writing each block's REG2[0].
    stop      Stop every block (or just --block) by writing each block's REG2[1].
    read      Read counters. Both --block and --counter are optional. With
              no args, reads every counter in every block. With --block=X,
              reads every counter in block X. With --block=X --counter=Y,
              reads just counter Y in block X. By default each counter is
              read once; pass --snapshot to take two samples and show the
              delta between them.

Examples:
  perf-counters list
  perf-counters init -l 0,0
  perf-counters start
  perf-counters read
  perf-counters read --snapshot --active
  perf-counters read --block=FPU
  perf-counters read --block=FPU --counter=fpu_or_sfpu_instrn
"""

import time

from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, CommonCommandOptions, tt_docopt
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.perf_counters import (
    TensixPerfCounters,
    list_perf_counters,
    read_perf_counters,
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


def _resolve_perf(location: OnChipCoordinate) -> TensixPerfCounters | None:
    return location.noc_block.get_perf_counters()


def _parse_counter(arg: str) -> int | str:
    arg = arg.strip()
    try:
        return int(arg, 0)
    except ValueError:
        return arg


def _print_list(device_id: int, location: OnChipCoordinate) -> None:
    """`pc list` for one core via the public discovery API."""
    listing = list_perf_counters(location, device_id=device_id)
    data: dict[str, list[tuple[str, str]]] = {}
    for (_did, _coord, block_name), counters in listing.items():
        if not counters:
            continue
        data[block_name] = [(str(cid), cname) for cid, cname in counters]
    if not data:
        print("  (no readable counter blocks)")
        return
    formatter.display_grouped_data_autoflow(
        data,
        columns=[("ID", "cyan"), ("Counter", "green")],
        sort_by_height_desc=False,
    )


def _resolve_read_filters(
    args: dict, context: Context, ui_state: UIState
) -> tuple[int | None, str | OnChipCoordinate | None]:
    """Translate ``-d`` / ``-l`` argv into ``read_perf_counters`` filters.

    Default behavior preserves the REPL's notion of "current device + current
    location" so a bare ``pc read`` reads one core. ``-d all`` and ``-l all``
    delegate fan-out to the lib (``device_id=None`` / ``location=None``).
    Slash-separated ``-l a/b`` is rejected — the lib reads either a single
    location or all locations on the selected device(s).
    """
    d_arg = args.get("-d")
    l_arg = args.get("-l")

    if d_arg is None:
        device_id: int | None = ui_state.current_device.id
    elif d_arg == "all":
        device_id = None
    else:
        device_id = int(d_arg, 0)

    location: str | OnChipCoordinate | None
    if l_arg is None:
        if device_id is None:
            location = None
        else:
            device = context.find_device_by_id(device_id)
            location = ui_state.current_location.change_device(device)
    elif l_arg == "all":
        location = None
    elif "/" in l_arg:
        raise util.TTException(
            "slash-separated -l is not supported by `pc read`; "
            "use `-l all`, a single location, or call `pc read` per location."
        )
    else:
        location = l_arg

    return device_id, location


def _build_render_data(
    snap: dict[tuple[int, OnChipCoordinate, str, int, str], tuple[int, int]],
    snap_prev: dict[tuple[int, OnChipCoordinate, str, int, str], tuple[int, int]] | None,
    active_only: bool,
    consolidated: bool,
) -> dict[str, list[tuple[str, ...]]]:
    """Group counter rows by block. If ``consolidated`` prepend a Loc column.

    ``snap`` is the most recent read; each value is a ``(counter_value,
    ref_cnt)`` tuple. ``snap_prev`` is the earlier read for delta mode
    (``--snapshot``); ``None`` means single-read mode — no Δ column, and
    ref_cnt shows just the absolute value.
    """
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
            # Single-read mode: no delta, ref_cnt is just the absolute value.
            ref_str = str(r1)
            if consolidated:
                loc_str = f"d{did} {coord.to_user_str()}"
                row = (loc_str, str(cid), cname, value_str, ref_str)
            else:
                row = (str(cid), cname, value_str, ref_str)
        data.setdefault(block_name, []).append(row)
    return data


def _render_per_core(
    snap: dict[tuple[int, OnChipCoordinate, str, int, str], tuple[int, int]],
    snap_prev: dict[tuple[int, OnChipCoordinate, str, int, str], tuple[int, int]] | None,
    active_only: bool,
) -> None:
    """Caller has already verified snap has exactly one (device, coord)."""
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
    snap: dict[tuple[int, OnChipCoordinate, str, int, str], tuple[int, int]],
    snap_prev: dict[tuple[int, OnChipCoordinate, str, int, str], tuple[int, int]] | None,
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


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args
    block_name = args["--block"]

    # ---- Read paths: delegate fan-out to read_perf_counters ----
    if args["read"]:
        device_id, location = _resolve_read_filters(args, context, ui_state)

        if args["--counter"] is None:
            # Multi-counter read. Default = single sample; ``--snapshot`` =
            # two samples ``_SNAPSHOT_INTERVAL_S`` apart with a Δ column.
            snapshot_mode = args["--snapshot"]
            active_only = args["--active"]
            if active_only and not snapshot_mode:
                util.WARN("--active requires --snapshot (nothing to compare against without a second sample)")
                active_only = False

            snap = read_perf_counters(location, block_name=block_name, device_id=device_id)
            if not snap:
                util.WARN("no perf-counter targets in scope")
                return

            snap_prev = None
            if snapshot_mode:
                # The most-recent reading goes in ``snap``; the earlier one in
                # ``snap_prev``. Swap names accordingly: the first call above
                # becomes ``snap_prev``, then we re-read into ``snap``.
                snap_prev = snap
                time.sleep(_SNAPSHOT_INTERVAL_S)
                snap = read_perf_counters(location, block_name=block_name, device_id=device_id)

            unique_locs = {(did, coord) for did, coord, _b, _i, _n in snap.keys()}
            if len(unique_locs) > 1:
                _render_consolidated(snap, snap_prev, active_only)
            else:
                _render_per_core(snap, snap_prev, active_only)
            return

        # Single-counter path: same fan-out, then filter to the one counter.
        if block_name is None:
            util.WARN("--counter requires --block (counter ids are not unique across blocks)")
            return
        counter_arg = _parse_counter(args["--counter"])
        snap = read_perf_counters(location, block_name=block_name, device_id=device_id)
        if not snap:
            util.WARN("no perf-counter targets in scope")
            return
        matched = False
        for (_did, _coord, _bname, cid, cname), (value, _ref) in snap.items():
            if (isinstance(counter_arg, int) and cid == counter_arg) or (
                isinstance(counter_arg, str) and cname == counter_arg
            ):
                print(value)
                matched = True
        if not matched:
            util.WARN(f"counter {counter_arg!r} not found in block {block_name}")
        return

    # ---- list / init / start / stop: per-(device, location) loop ----
    device: Device
    location_iter: OnChipCoordinate
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        for location_iter in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            perf = _resolve_perf(location_iter)
            header = f"chip={device.id} core={location_iter.to_user_str()}"
            if perf is None:
                util.WARN(
                    f"{header}: performance counters are not available on "
                    f"block_type={location_iter.noc_block.block_type}"
                )
                continue

            if args["list"]:
                print(f"\n=== Perf Counter Blocks: {header} ===\n")
                _print_list(device.id, location_iter)
                continue

            if args["init"]:
                print(f"\n=== Init Perf Counters: {header} ===\n")
                if block_name is None:
                    perf.init_all()
                    print(f"  Initialized all blocks: {perf.block_names}")
                else:
                    perf.init_block(block_name)
                    print(f"  Initialized {block_name}")
                continue

            if args["start"]:
                if block_name is None:
                    perf.start_all()
                    util.INFO(f"{header}: started all blocks: {perf.block_names}")
                else:
                    perf.start_block(block_name)
                    util.INFO(f"{header}: started {block_name}")
                continue

            if args["stop"]:
                if block_name is None:
                    perf.stop_all()
                    util.INFO(f"{header}: stopped all blocks: {perf.block_names}")
                else:
                    perf.stop_block(block_name)
                    util.INFO(f"{header}: stopped {block_name}")
                continue
