# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  noc-status <elf-file> [-n <noc>] [-d <device>] [-l <loc>]

Description:
    Cheks if noc status registers allign with variables from elf file.
    Should be only used for BRISC cores.

Arguments:
    <elf-file>    Path to the risc's firmware elf file.

Options:
    -d <device>   Device ID. Default: all
    -l <loc>      Core location in X-Y or R,C format. Default: all
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
from ttexalens.parse_elf import read_elf, decode_symbols
from elftools.elf.elffile import ELFFile
import ttexalens.tt_exalens_lib as lib


# Dictionary of corresponding variables and registers to check
VAR_TO_REG_MAP = {
    "noc_reads_num_issued": "NIU_MST_RD_RESP_RECEIVED",
    "noc_nonposted_writes_num_issued": "NIU_MST_NONPOSTED_WR_REQ_SENT",
    "noc_nonposted_writes_acked": "NIU_MST_WR_ACK_RECEIVED",
    "noc_nonposted_atomics_acked": "NIU_MST_ATOMIC_RESP_RECEIVED",
    "noc_posted_writes_num_issued": "NIU_MST_POSTED_WR_REQ_SENT",
}


# TODO: Move this to parse_elf.py or use one if exists
def get_symbol_address_from_elf(elf: ELFFile, symbol_name: str, noc_id: int = 0) -> int:
    # Iterate through sections to find the symbol table
    for section in elf.iter_sections():
        if section.name == ".symtab":
            symbol_table = section
            for symbol in symbol_table.iter_symbols():
                # Match the variable name
                if symbol.name == symbol_name:
                    return symbol.entry.st_value + 4 * noc_id

    return None


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

    # Open elf file from given path
    f = context.server_ifc.get_binary(elf_path)
    # Read elf
    elf = ELFFile(f)
    # Extract symbols from elf
    symbols = decode_symbols(elf)

    # Set default to all for devices and locations
    dopt.args["-d"] = "all" if dopt.args["-d"] is None else dopt.args["-d"]
    dopt.args["-l"] = "all" if dopt.args["-l"] is None else dopt.args["-l"]

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            util.INFO(f"Device: {device.id()}, loc: {loc}", end=" ")
            passed = True

            for var in VAR_TO_REG_MAP:
                reg = VAR_TO_REG_MAP[var]
                address = symbols[var]
                reg_val = lib.read_tensix_register(loc, reg, device.id(), context)
                var_val = lib.read_riscv_memory(loc, address, noc_id, risc_id, device.id(), context)

                if reg_val != var_val:
                    # If this is the first one to fail print xmark
                    if passed:
                        print(util.XMARK)
                    passed = False
                    util.ERROR(
                        f"\tMismatch between {reg} and {var} at device: {device.id()} at loc: {loc}: {reg_val} != {var_val}"
                    )

            if passed:
                print(util.CHECKMARK)

    return None
