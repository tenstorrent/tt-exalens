# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  gpr   [ <reg-list> ] [ <elf-file> ] [ -v ] [ -d <device> ] [ -l <loc> ] [ -r <risc> ]

Options:
    <reg-list>                          List of registers to dump, comma-separated
    <elf-file>                          Name of the elf file to use to resolve the source code location

Description:
  Prints all RISC-V registers for BRISC, TRISC0, TRISC1, and TRISC2 on the current core.
  If the core cannot be halted, it prints nothing. If core is not active, an exception
  is thrown.

Examples:
  gpr
  gpr ra,sp,pc
"""
command_metadata = {
    "short": "gpr",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc", "--verbose", "--risc"],
}

import tabulate

from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.hardware.baby_risc_debug import get_register_index, get_register_name
from ttexalens.uistate import UIState

from ttexalens import command_parser
from ttexalens import util as util
from ttexalens.firmware import ELF


def reg_included(reg_index, regs_to_include):
    if regs_to_include:
        return reg_index in regs_to_include
    return True


def get_register_data(device: Device, context: Context, loc: OnChipCoordinate, args, riscs_to_include):
    regs_to_include = args["<reg-list>"].split(",") if args["<reg-list>"] else []
    regs_to_include = [get_register_index(reg) for reg in regs_to_include]
    elf_file = args["<elf-file>"] if args["<elf-file>"] else None
    elf = ELF(context.server_ifc, {"elf": elf_file}) if elf_file else None
    pc_map = elf.names["elf"].file_line if elf else None

    reg_value: dict[int, dict[int, int]] = {}

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
        halted_state[risc_name] = already_halted

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
            if pc_map and reg_id == 32:
                PC = reg_value[risc_id][reg_id]
                if PC in pc_map:
                    source_loc = pc_map[PC]
                    if source_loc:
                        src_location = f"- {source_loc[0].decode('utf-8')}:{source_loc[1]}"
            row.append(f"0x{reg_value[risc_id][reg_id]:08x}{src_location}" if reg_id in reg_value[risc_id] else "-")
        table.append(row)

    # Print soft reset status
    row = ["Soft reset"]
    for j in riscs_to_include:
        row.append(reset_state[j])
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


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            riscs_to_include = list(dopt.for_each("--risc", context, ui_state, device=device, location=loc))
            table = get_register_data(device, context, loc, dopt.args, riscs_to_include)
            if table:
                util.INFO(f"RISC-V registers for location {loc} on device {device.id()}")
                print(table)
            else:
                print(f"No data available for location {loc} on device {device.id()}")
