# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  gpr   [ <reg-list> ] [ -d <device> ] [ -l <loc> ] [ -r <risc> ]

Options:
    <reg-list>                          List of registers to dump, comma-separated

Description:
  Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
  If the core cannot be halted, it prints nothing. If core is not active, an exception
  is thrown.

Examples:
  gpr
  gpr ra,sp,pc
"""
import tabulate

from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
import ttexalens.tt_exalens_lib as lib
from ttexalens.hardware.baby_risc_debug import get_register_index, get_register_name
from ttexalens.hardware.risc_debug import CallstackEntry, RiscLocation
from ttexalens.uistate import UIState

from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="gpr",
    long_name="dump-gpr",
    type="low-level",
    description=__doc__,
    common_option_names=[
        CommonCommandOptions.Device,
        CommonCommandOptions.Location,
        CommonCommandOptions.Risc,
    ],
)


def reg_included(reg_index, regs_to_include):
    if regs_to_include:
        return reg_index in regs_to_include
    return True


def get_register_data(device: Device, context: Context, loc: OnChipCoordinate, args, riscs_to_include):
    regs_to_include = args["<reg-list>"].split(",") if args["<reg-list>"] else []
    regs_to_include = [get_register_index(reg) for reg in regs_to_include]

    reg_value: dict[str, dict[int, int]] = {}
    callstack_value: dict[str, list[CallstackEntry]] = {}
    halted_state = {}
    reset_state = {}

    # Read the registers
    noc_block = device.get_block(loc)
    for risc_name in riscs_to_include:
        risc = noc_block.get_risc_debug(risc_name)
        reset_state[risc_name] = risc.is_in_reset()
        if reset_state[risc_name]:
            continue  # We cannot read registers from a core in reset
        if not risc.can_debug():
            halted_state[risc_name] = "?"
            continue  # We cannot read registers from a core that doesn't have debug hardware

        already_halted = risc.is_halted()
        halted_state[risc_name] = str(already_halted)

        if not already_halted:
            risc.halt()  # We must halt the core to read the registers

        if risc.is_halted():
            reg_value[risc_name] = {}
            for reg_id in range(0, 33):
                if regs_to_include and reg_id not in regs_to_include:
                    continue
                reg_val = risc.read_gpr(reg_id)
                reg_value[risc_name][reg_id] = reg_val
            if not already_halted:
                risc.cont()  # Resume the core if it was not found halted
            try:
                elf_path = context.get_risc_elf_path(RiscLocation(loc, neo_id=None, risc_name=risc_name))
                if elf_path is not None:
                    elf = lib.parse_elf(elf_path, context)
                    callstack_value[risc_name] = lib.top_callstack(risc.get_pc(), elf, None, context)
            except:
                # Unable to load ELF file for this RISC
                pass
        else:
            util.ERROR(f"Core {risc_name} cannot be halted.")

    # Construct the table to print
    table = []
    for reg_id in range(0, 33):
        if regs_to_include and reg_id not in regs_to_include:
            continue

        row = [f"{reg_id} - {get_register_name(reg_id)}"]
        for risc_id in riscs_to_include:
            if risc_id not in reg_value:
                row.append("")
                continue
            src_location = ""
            if reg_id == 32:  # PC register
                top_callstack = callstack_value.get(risc_id, None)
                if top_callstack is not None and len(top_callstack) > 0:
                    src_location = f"- {top_callstack[0].file}:{top_callstack[0].line}"
            row.append(f"0x{reg_value[risc_id][reg_id]:08x}{src_location}" if reg_id in reg_value[risc_id] else "-")
        table.append(row)

    # Print soft reset status
    row = ["Soft reset"]
    for j in riscs_to_include:
        row.append(str(reset_state[j]))
    table.append(row)

    # Print halted status
    row = ["Halted"]
    for j in riscs_to_include:
        row.append(halted_state[j] if not reset_state[j] else "-")
    table.append(row)

    # Print the table
    if len(table) > 0:
        headers = ["Register"]
        for risc_name in riscs_to_include:
            headers.append(risc_name)
        return tabulate.tabulate(table, headers=headers, disable_numparse=True)
    return None


def run(cmd_text, context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    device: Device
    loc: OnChipCoordinate
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            riscs_to_include = list(
                dopt.for_each(CommonCommandOptions.Risc, context, ui_state, device=device, location=loc)
            )
            table = get_register_data(device, context, loc, dopt.args, riscs_to_include)
            if table:
                util.INFO(f"RISC-V registers for location {loc} on device {device.id}")
                print(table)
            else:
                print(f"No data available for location {loc} on device {device.id}")
