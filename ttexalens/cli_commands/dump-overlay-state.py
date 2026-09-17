# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-overlay-state [--counters] [--cmdbuf] [--errors] [--wdt] [--debug] [--clint] [--plic] [--cores <cores>] [ -d <device> ] [ -l <loc> ] [ -v ]

Options:
  --counters        Dump LLK tile counters (DFB credits / flow control).
  --cmdbuf          Dump ROCC command-buffer descriptors (in-flight NOC transfers).
  --errors          Dump bus error units (latched fault cause / address).
  --wdt             Dump watchdog timers (hang detection).
  --debug           Dump RISC-V debug module state (halt / abstract / system bus).
  --clint           Dump CLINT (per-core software interrupt + timer compare).
  --plic            Dump PLIC (interrupt priorities / pending / enables).
  --cores <cores>   Comma-separated core indices for the per-core groups (e.g. 0,3,5). Default: all cores.

Description:
  Dumps Quasar overlay state at the given
  location and device, grouped by logical block. With no group flag, all
  groups are dumped; multiple group flags may be combined to dump a subset.

  The core selector (--cores) restricts the per-core groups (cmdbuf, errors, wdt,
  debug, clint, plic) to the given cores; the per-interface LLK tile-counter
  group is unaffected.

  Verbose (-v) widens each group: read-mirror/threshold counters, the full
  command-buffer descriptor, extra debug-module registers, and PLIC priorities.

Examples:
  dump-overlay-state                 # all groups, current device/core
  overlay                            # same (short name)
  overlay --cmdbuf                   # only ROCC command buffers
  overlay --errors --wdt             # bus errors + watchdogs together
  overlay --counters -v              # LLK counters incl. read-mirrors/thresholds
  overlay --cmdbuf --cores 0,3,5     # command buffers for cores 0, 3, 5 only
  overlay --debug -l 1,1             # debug module at location 1,1
"""

from typing import Any

from ttexalens import util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.register_store import RegisterStore
from ttexalens.uistate import UIState
from ttexalens.device import Device
from ttexalens.util import INFO, format_hex, format_dec, format_flag
from ttexalens.rich_formatters import formatter, console
from ttexalens.hardware.quasar.functional_overlay_registers_description import OverlayRegistersDescription
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="overlay",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location, CommonCommandOptions.Verbose],
)

GROUPS = ["counters", "cmdbuf", "errors", "wdt", "debug", "clint", "plic"]


def _parse_cores(cores_arg: str | None, num_cores: int) -> list[int]:
    if not cores_arg:
        return list(range(num_cores))
    try:
        cores = [int(c) for c in cores_arg.split(",")]
    except ValueError:
        raise ValueError(f"Invalid --cores value '{cores_arg}'. Expected comma-separated core indices.")
    for c in cores:
        if c < 0 or c >= num_cores:
            raise ValueError(f"Core index {c} is out of range. Valid cores: 0..{num_cores - 1}.")
    return cores


def dump_counters(
    register_store: RegisterStore, verbose: bool, cores: list[int], desc: OverlayRegistersDescription
) -> None:
    formatter.print_section_header("LLK TILE COUNTERS")
    headers = ["CNT", "POSTED", "ACKED", "OCC", "CAP", "FREE", "ERR"]
    if verbose:
        headers += ["R_POST", "R_ACK", "AVL_TH", "FREE_TH"]
    data: dict[str, list[tuple[Any, ...]]] = {}
    for iface, counters in enumerate(desc.tile_counters):
        rows: list[tuple[Any, ...]] = []
        for counter, regs in enumerate(counters):
            posted = register_store.read_register(regs["POSTED"])
            acked = register_store.read_register(regs["ACKED"])
            cap = register_store.read_register(regs["CAP"])
            err = register_store.read_register(regs["ERR"])
            occ = (posted - acked) & 0xFFFFFFFF
            free = cap - occ
            row = [
                counter,
                format_dec(posted),
                format_dec(acked),
                format_dec(occ),
                format_dec(cap),
                format_dec(free),
                format_flag(err),
            ]
            if verbose:
                row += [
                    format_dec(register_store.read_register(regs["R_POST"])),
                    format_dec(register_store.read_register(regs["R_ACK"])),
                    format_dec(register_store.read_register(regs["AVL_TH"])),
                    format_dec(register_store.read_register(regs["FREE_TH"])),
                ]
            rows.append(tuple(row))
        data[f"Interface {iface}"] = rows
    formatter.display_grouped_data_autoflow(data, columns=formatter.styled_columns(headers), sort_by_height_desc=False)


def dump_cmdbuf(
    register_store: RegisterStore, verbose: bool, cores: list[int], desc: OverlayRegistersDescription
) -> None:
    fields = list(desc.command_buffers[0].keys())
    rows: list[tuple[Any, ...]] = []
    for cpu in cores:
        regs = desc.command_buffers[cpu]
        vals = {field: register_store.read_register(regs[field]) for field in fields}
        outst = "YES" if vals["WR_SENT"] != vals["TR_ACK"] else ""
        rows.append((cpu, *(format_hex(vals[field]) for field in fields), outst))
    formatter.print_styled_table("ROCC COMMAND BUFFERS (cmd_buf_r)", ["CPU", *fields, "OUTST"], rows)

    if verbose:
        descriptor_fields = list(desc.command_buffer_descriptors[0].keys())
        drows: list[tuple[Any, ...]] = []
        for cpu in cores:
            regs = desc.command_buffer_descriptors[cpu]
            drows.append((cpu, *(format_hex(register_store.read_register(regs[field])) for field in descriptor_fields)))
        formatter.print_styled_table("ROCC COMMAND BUFFERS — descriptor", ["CPU", *descriptor_fields], drows)


def dump_errors(
    register_store: RegisterStore, verbose: bool, cores: list[int], desc: OverlayRegistersDescription
) -> None:
    fields = list(desc.bus_error_units[0].keys())
    rows: list[tuple[Any, ...]] = []
    for unit in cores:
        regs = desc.bus_error_units[unit]
        vals = {field: register_store.read_register(regs[field]) for field in fields}
        note = "FAULT" if vals["CAUSE"] != 0 else ""
        rows.append((unit, *(format_hex(vals[field]) for field in fields), note))
    formatter.print_styled_table("BUS ERROR UNITS", ["Unit", *fields, "NOTE"], rows)


def dump_wdt(register_store: RegisterStore, verbose: bool, cores: list[int], desc: OverlayRegistersDescription) -> None:
    fields = list(desc.watchdog_timers[0].keys())
    rows: list[tuple[Any, ...]] = []
    for core in cores:
        regs = desc.watchdog_timers[core]
        rows.append(
            (
                core,
                format_hex(register_store.read_register(regs["CTRL"])),
                format_dec(register_store.read_register(regs["COUNT"])),
                format_dec(register_store.read_register(regs["SCALED_COUNT"])),
                format_dec(register_store.read_register(regs["CMP"])),
            )
        )
    formatter.print_styled_table("WATCHDOG TIMERS", ["Core", *fields], rows)


def dump_debug(
    register_store: RegisterStore, verbose: bool, cores: list[int], desc: OverlayRegistersDescription
) -> None:
    regs = desc.debug_module_verbose if verbose else desc.debug_module
    rows: list[tuple[Any, ...]] = [(name, format_hex(register_store.read_register(rn))) for name, rn in regs.items()]
    formatter.print_styled_table("DEBUG MODULE", ["Register", "Value"], rows)
    hs = register_store.read_register(desc.debug_module["HALTSUMMARY0"])
    halted = [i for i in cores if hs & (1 << i)]
    console.print(f"  Halted harts (HALTSUMMARY0 bitmap): {halted if halted else 'none'}", markup=False)


def dump_clint(
    register_store: RegisterStore, verbose: bool, cores: list[int], desc: OverlayRegistersDescription
) -> None:
    fields = list(desc.clint[0].keys())
    rows: list[tuple[Any, ...]] = []
    for core in cores:
        regs = desc.clint[core]
        rows.append((core, *(format_hex(register_store.read_register(regs[field])) for field in fields)))
    formatter.print_styled_table("CLINT", ["Core", *fields], rows)
    console.print(f"  MTIME: {format_hex(register_store.read_register(desc.clint_mtime))}", markup=False)


def dump_plic(
    register_store: RegisterStore, verbose: bool, cores: list[int], desc: OverlayRegistersDescription
) -> None:
    fields = list(desc.plic_cores[0].keys())
    rows: list[tuple[Any, ...]] = []
    for core in cores:
        regs = desc.plic_cores[core]
        rows.append((core, *(format_hex(register_store.read_register(regs[field])) for field in fields)))
    formatter.print_styled_table("PLIC", ["Core", *fields], rows)
    pend = [register_store.read_register(rn) for rn in desc.plic_pending]
    console.print(
        "  PENDING: " + ", ".join(f"[{n}]={format_hex(v)}" for n, v in enumerate(pend)),
        markup=False,
    )
    if verbose:
        prows: list[tuple[Any, ...]] = [
            (source, format_hex(register_store.read_register(rn))) for source, rn in enumerate(desc.plic_priorities)
        ]
        formatter.print_styled_table("PLIC — source priorities", ["Source", "PRIORITY"], prows)


DISPATCH = {
    "counters": dump_counters,
    "cmdbuf": dump_cmdbuf,
    "errors": dump_errors,
    "wdt": dump_wdt,
    "debug": dump_debug,
    "clint": dump_clint,
    "plic": dump_plic,
}


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    verbose: bool = dopt.args["-v"]

    selected = [g for g in GROUPS if dopt.args[f"--{g}"]]
    if not selected:
        selected = list(GROUPS)

    device: Device
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        loc: OnChipCoordinate
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            noc_block = device.get_block(loc)
            if not noc_block:
                util.ERROR(f"Device {device.id} at location {loc.to_user_str()} does not have a NOC block.")
                continue
            overlay_block = getattr(noc_block, "overlay", None)
            if overlay_block is None:
                util.ERROR(f"Device {device.id} at location {loc.to_user_str()} does not have an overlay block.")
                continue
            desc = overlay_block.get_register_description()
            num_cores = len(overlay_block.all_riscs)
            register_store = noc_block.get_register_store()
            cores = _parse_cores(dopt.args["--cores"], num_cores)

            INFO(f"Overlay state for location {loc} on device {device.id}")
            for group in selected:
                DISPATCH[group](register_store, verbose, cores, desc)
