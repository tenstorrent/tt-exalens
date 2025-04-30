# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  noc-status <elf-file> [-n <noc>] [-d <device>] [-l <loc>]

Description:
    Cheks if noc status registers allign with variables from elf file.
    Should be only used for BRISC cores.

Arguments:
    <elf-file>       Path to the firmware elf file.

Options:
    -d <device>   Device ID. Default: current device
    -l <loc>      Core location in X-Y or R,C format. Default: current location
    -n <noc>      Noc ID (0 or 1). Default: 0

Examples:
  noc-status .../brisc.elf
"""

command_metadata = {
    "short": "ns",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
}

import os
from ttexalens.uistate import UIState
from ttexalens import command_parser
from ttexalens import util
from ttexalens.parse_elf import read_elf
from elftools.elf.elffile import ELFFile
import ttexalens.tt_exalens_lib as lib


VARS_TO_CHECK = {
    "noc_reads_num_issued": ["NIU_MST_RD_RESP_RECEIVED", None],
    "noc_nonposted_writes_num_issued": ["NIU_MST_NONPOSTED_WR_REQ_SENT", None],
    "noc_nonposted_writes_acked": ["NIU_MST_WR_ACK_RECEIVED", None],
    "noc_nonposted_atomics_acked": ["NIU_MST_ATOMIC_RESP_RECEIVED", None],
    "noc_posted_writes_num_issued": ["NIU_MST_POSTED_WR_REQ_SENT", None],
}


def get_symbol_from_elf(elf, symbol_name):
    # Iterate through sections to find the symbol table
    for section in elf.iter_sections():
        if section.header.sh_type == "SHT_SYMTAB":
            symbol_table = section
            for symbol in symbol_table.iter_symbols():
                # Match the variable name
                if symbol.name == symbol_name:
                    return symbol.entry.st_value  # + 4*noc_id


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    elf_path = dopt.args["<elf-file>"]
    risc_id = 0  # For now only works on BRISC
    noc_id = dopt.args["-n"] if dopt.args["-n"] else 0

    if not os.path.exists(elf_path):
        util.ERROR(f"File {elf_path} does not exist")
        return

    f = context.server_ifc.get_binary(elf_path)
    elf = ELFFile(f)
    for var in VARS_TO_CHECK:
        VARS_TO_CHECK[var][1] = get_symbol_from_elf(elf, var)

    dopt.args["-d"] = "all" if dopt.args["-d"] is None else dopt.args["-d"]
    dopt.args["-l"] = "all" if dopt.args["-l"] is None else dopt.args["-l"]

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            passed = True
            util.INFO(f"Device: {device.id()}, loc: {loc}", end=" ")

            for var in VARS_TO_CHECK:
                reg, address = VARS_TO_CHECK[var]
                reg_val = lib.read_tensix_register(loc, reg, device.id(), context)
                var_val = lib.read_riscv_memory(loc, address, noc_id, risc_id, device.id(), context)

                if reg_val != var_val:
                    if passed:
                        print(util.XMARK)
                    passed = False
                    util.ERROR(
                        f"\tMismatch between {reg} and {var} at device: {device.id()} at loc: {loc}: {reg_val} != {var_val}"
                    )

            if passed:
                print(util.CHECKMARK)

    return None
