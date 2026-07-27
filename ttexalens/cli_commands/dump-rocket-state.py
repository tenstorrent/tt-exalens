# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-rocket-state [--counters] [--cmdbuf] [--errors] [--wdt] [--debug] [--clint] [--plic] [--cores <cores>] [ -d <device> ] [ -l <loc> ] [ -v ]

Options:
  --counters        Dump LLK tile counters (DFB credits / flow control).
  --cmdbuf          Dump ROCC command-buffer descriptors (in-flight NOC transfers).
  --errors          Dump bus error units (latched fault cause / address).
  --wdt             Dump watchdog timers (hang detection).
  --debug           Dump RISC-V debug module state (halt / abstract / system bus).
  --clint           Dump CLINT (per-core software interrupt + timer compare).
  --plic            Dump PLIC (interrupt priorities / pending / enables).
  --cores <cores>   Comma-separated Rocket core indices for the per-core groups (e.g. 0,3,5). Default: all cores.

Description:
  Dumps Quasar overlay ("Rocket" data-movement cluster) state at the given
  location and device, grouped by logical block. With no group flag, all
  groups are dumped; multiple group flags may be combined to dump a subset.

  The core selector (--cores) restricts the per-core groups (cmdbuf, errors, wdt,
  debug, clint, plic) to the given Rocket cores; the per-interface LLK tile-counter
  group is unaffected.

  Verbose (-v) widens each group: read-mirror/threshold counters, the full
  command-buffer descriptor, extra debug-module registers, and PLIC priorities.

Examples:
  dump-rocket-state                 # all groups, current device/core
  rocket                            # same (short name)
  rocket --cmdbuf                   # only ROCC command buffers
  rocket --errors --wdt             # bus errors + watchdogs together
  rocket --counters -v              # LLK counters incl. read-mirrors/thresholds
  rocket --cmdbuf --cores 0,3,5     # command buffers for cores 0, 3, 5 only
  rocket --debug -l 1,1             # debug module at location 1,1
"""

import tabulate

from ttexalens import util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.register_store import RegisterStore
from ttexalens.uistate import UIState
from ttexalens.device import Device
from ttexalens.util import INFO, CLR_GREEN, CLR_END
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="rocket",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location, CommonCommandOptions.Verbose],
)

GROUPS = ["counters", "cmdbuf", "errors", "wdt", "debug", "clint", "plic"]


def _hex(v: int | None) -> str:
    return "-" if v is None else f"0x{v:x}"


def _dec(v: int | None) -> str:
    return "-" if v is None else str(v)


def _flag(v: int | None) -> str:
    if v is None:
        return "-"
    return "False" if v == 0 else "True"


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


_LLK_IFACE_PREFIX = {
    0: "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_",
    1: "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_",
    2: "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_",
    3: "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_",
}

NUM_OF_TILE_COUNTERS = 16
NUM_OF_PLIC_PENDING_WORDS = 3
NUM_OF_PLIC_PRIORITY_SOURCES = 80


def dump_counters(register_store: RegisterStore, verbose: bool, cores: list[int]) -> None:
    print(f"{CLR_GREEN}LLK TILE COUNTERS{CLR_END}")
    headers = ["CNT", "POSTED", "ACKED", "OCC", "CAP", "FREE", "ERR"]
    if verbose:
        headers += ["R_POST", "R_ACK", "AVL_TH", "FREE_TH"]
    for iface in range(len(_LLK_IFACE_PREFIX)):
        prefix = _LLK_IFACE_PREFIX[iface]
        rows = []
        for c in range(NUM_OF_TILE_COUNTERS):
            base = f"{prefix}{c}__"
            posted = register_store.read_register(base + "POSTED")
            acked = register_store.read_register(base + "ACKED")
            cap = register_store.read_register(base + "BUFFER_CAPACITY")
            err = register_store.read_register(base + "ERROR_STATUS")
            occ = ((posted - acked) & 0xFFFFFFFF) if posted is not None and acked is not None else None
            free = (cap - occ) if cap is not None and occ is not None else None
            row = [c, _dec(posted), _dec(acked), _dec(occ), _dec(cap), _dec(free), _flag(err)]
            if verbose:
                row += [
                    _dec(register_store.read_register(base + "READ_POSTED")),
                    _dec(register_store.read_register(base + "READ_ACKED")),
                    _dec(register_store.read_register(base + "TILES_AVAIL_THRESHOLD")),
                    _dec(register_store.read_register(base + "TILES_FREE_THRESHOLD")),
                ]
            rows.append(row)
        print(f"Interface {iface}")
        print(tabulate.tabulate(rows, headers=headers, tablefmt="simple_outline"))


def dump_cmdbuf(register_store: RegisterStore, verbose: bool, cores: list[int]) -> None:
    print(f"{CLR_GREEN}ROCC COMMAND BUFFERS (cmd_buf_r){CLR_END}")
    rows = []
    for cpu in cores:
        b = f"TT_ROCC_ACCEL_TT_ROCC_CPU{cpu}_CMD_BUF_R_"
        ip = register_store.read_register(b + "IP")
        wr = register_store.read_register(b + "WR_SENT_TR_ID")
        ack = register_store.read_register(b + "TR_ACK_TR_ID")
        ip0 = register_store.read_register(b + "PER_TR_ID_IP_0")
        ip1 = register_store.read_register(b + "PER_TR_ID_IP_1")
        ip2 = register_store.read_register(b + "PER_TR_ID_IP_2")
        outst = "YES" if wr is not None and ack is not None and wr != ack else ""
        rows.append([cpu, _hex(ip), _hex(wr), _hex(ack), outst, _hex(ip0), _hex(ip1), _hex(ip2)])
    print(
        tabulate.tabulate(
            rows, headers=["CPU", "IP", "WR_SENT", "TR_ACK", "OUTST", "IP_0", "IP_1", "IP_2"], tablefmt="simple_outline"
        )
    )

    if verbose:
        desc = ["SRC_ADDR", "SRC_COORD", "DEST_ADDR", "DEST_COORD", "LEN_BYTES", "REQ_VC", "RESP_VC", "TR_ID", "MISC"]
        rows = []
        for cpu in cores:
            b = f"TT_ROCC_ACCEL_TT_ROCC_CPU{cpu}_CMD_BUF_R_"
            rows.append([cpu] + [_hex(register_store.read_register(b + r)) for r in desc])
        print("Descriptor")
        print(tabulate.tabulate(rows, headers=["CPU"] + desc, tablefmt="simple_outline"))


def dump_errors(register_store: RegisterStore, verbose: bool, cores: list[int]) -> None:
    print(f"{CLR_GREEN}BUS ERROR UNITS{CLR_END}")
    rows = []
    for u in cores:
        b = f"BUS_ERROR_UNIT_{u}_"
        cause = register_store.read_register(b + "CAUSE")
        pa = register_store.read_register(b + "PHYS_ADDR")
        acc = register_store.read_register(b + "ACCRUED")
        en = register_store.read_register(b + "ENABLE")
        plic_en = register_store.read_register(b + "PLIC_ENABLE")
        local_en = register_store.read_register(b + "LOCAL_ENABLE")
        note = "<-- FAULT" if cause not in (None, 0) else ""
        rows.append([u, _hex(cause), _hex(pa), _hex(acc), _hex(en), _hex(plic_en), _hex(local_en), note])
    print(
        tabulate.tabulate(
            rows,
            headers=["Unit", "CAUSE", "PHYS_ADDR", "ACCRUED", "EN", "PLIC_EN", "LOCAL_EN", ""],
            tablefmt="simple_outline",
        )
    )


def dump_wdt(register_store: RegisterStore, verbose: bool, cores: list[int]) -> None:
    print(f"{CLR_GREEN}WATCHDOG TIMERS{CLR_END}")
    rows = []
    for c in cores:
        b = f"TT_CLUSTER_CORE{c}_WDT_"
        rows.append(
            [
                c,
                _hex(register_store.read_register(b + "CTRL")),
                _dec(register_store.read_register(b + "COUNT")),
                _dec(register_store.read_register(b + "SCALED_COUNT")),
                _dec(register_store.read_register(b + "CMP")),
            ]
        )
    print(tabulate.tabulate(rows, headers=["Core", "CTRL", "COUNT", "SCALED_COUNT", "CMP"], tablefmt="simple_outline"))


def dump_debug(register_store: RegisterStore, verbose: bool, cores: list[int]) -> None:
    print(f"{CLR_GREEN}DEBUG MODULE{CLR_END}")
    names = ["DMSTATUS", "DMCONTROL", "HALTSUMMARY0", "HALTSUMMARY1", "ABSTRACTCS", "STATUS2", "SBCS", "HARTINFO"]
    if verbose:
        names += [
            "DATA0",
            "DATA1",
            "COMMAND",
            "ABSTRACTAUTO",
            "PROGBUF0",
            "PROGBUF1",
            "SBADDR0",
            "SBADDR1",
            "SBDATA0",
            "SBDATA1",
        ]
    rows = [[n, _hex(register_store.read_register(f"TT_DEBUG_MODULE_APB_{n}"))] for n in names]
    print(tabulate.tabulate(rows, headers=["Register", "Value"], tablefmt="simple_outline"))
    hs = register_store.read_register("TT_DEBUG_MODULE_APB_HALTSUMMARY0")
    if hs is not None:
        halted = [i for i in cores if hs & (1 << i)]
        print(f"  Halted harts (HALTSUMMARY0 bitmap): {halted if halted else 'none'}")


def dump_clint(register_store: RegisterStore, verbose: bool, cores: list[int]) -> None:
    print(f"{CLR_GREEN}CLINT{CLR_END}")
    rows = []
    for c in cores:
        rows.append(
            [
                c,
                _hex(register_store.read_register(f"TT_CLUSTER_CLINT_MSIP_{c}_")),
                _hex(register_store.read_register(f"TT_CLUSTER_CLINT_MTIMECMP_{c}_")),
            ]
        )
    print(tabulate.tabulate(rows, headers=["Core", "MSIP", "MTIMECMP"], tablefmt="simple_outline"))
    print(f"  MTIME: {_hex(register_store.read_register('TT_CLUSTER_CLINT_MTIME'))}")


def dump_plic(register_store: RegisterStore, verbose: bool, cores: list[int]) -> None:
    print(f"{CLR_GREEN}PLIC{CLR_END}")
    pend = [register_store.read_register(f"TT_CLUSTER_PLIC_PENDING_{n}_") for n in range(NUM_OF_PLIC_PENDING_WORDS)]
    print("  PENDING: " + ", ".join(f"[{n}]={_hex(pend[n])}" for n in range(NUM_OF_PLIC_PENDING_WORDS)))
    rows = []
    for c in cores:
        b = f"TT_CLUSTER_PLIC_CORE{c}_"
        rows.append(
            [
                c,
                _hex(register_store.read_register(b + "THRESHOLD")),
                _hex(register_store.read_register(b + "CLAIM_COMPLETE")),
                _hex(register_store.read_register(b + "IE_0_")),
                _hex(register_store.read_register(b + "IE_1_")),
                _hex(register_store.read_register(b + "IE_2_")),
            ]
        )
    print(
        tabulate.tabulate(
            rows, headers=["Core", "THRESHOLD", "CLAIM_COMP", "IE_0", "IE_1", "IE_2"], tablefmt="simple_outline"
        )
    )
    if verbose:
        rows = [
            [n, _hex(register_store.read_register(f"TT_CLUSTER_PLIC_PRIORITY_{n}_"))]
            for n in range(NUM_OF_PLIC_PRIORITY_SOURCES)
        ]
        print("Source priorities")
        print(tabulate.tabulate(rows, headers=["Source", "PRIORITY"], tablefmt="simple_outline"))


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
                util.ERROR(f"Device {device.id} at location {loc.to_user_str()} does not have a Rocket overlay.")
                continue
            num_cores = len(overlay_block.all_riscs)
            register_store = noc_block.get_register_store()
            cores = _parse_cores(dopt.args["--cores"], num_cores)

            INFO(f"Rocket state for location {loc} on device {device.id}")
            for group in selected:
                DISPATCH[group](register_store, verbose, cores)
