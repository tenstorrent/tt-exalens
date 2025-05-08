# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

"""
Script Name: check_noc_status.py
Description:
    This script checks if there are any mismatches between values of number of NOC transactions
    stored in global variables from risc firmware and NOC status registers. Script looks for
    these mismatches across all available devices and locations.

Arguments:
    <firmware_elf.elf> Path to risc firmware elf file

Usage:
    python3 check_noc_status.py <firwmare_elf.elf>
"""
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens.tt_exalens_lib import read_riscv_memory, read_tensix_register
from ttexalens import util
from elftools.elf.elffile import ELFFile
from ttexalens.parse_elf import decode_symbols
from ttexalens.context import Context

import sys
import os


def get_elf_path() -> str:
    """Gets elf path from command line"""
    # Number of given arguments
    arg_num = len(sys.argv) - 1
    # Check if number of given arguments is correct
    if arg_num == 1:
        return sys.argv[1]
    elif arg_num == 0:
        print("ERROR: No argument detected! Please provide firmware elf path.")
        return None
    else:
        print("ERROR: Too many arguements! Please just provide firmware elf path.")
        return None


def get_symbols_from_elf(elf_path: str, context: Context) -> dict[str, int]:
    """Gets symbols from symbol table from elf file"""
    # Open elf file from given path
    f = context.server_ifc.get_binary(elf_path)
    # Read elf file
    elf = ELFFile(f)
    # Get symbols from elf
    return decode_symbols(elf)


def main():
    # Dictionary of corresponding variables and registers to check
    VAR_TO_REG_MAP = {
        "noc_reads_num_issued": "NIU_MST_RD_RESP_RECEIVED",
        "noc_nonposted_writes_num_issued": "NIU_MST_NONPOSTED_WR_REQ_SENT",
        "noc_nonposted_writes_acked": "NIU_MST_WR_ACK_RECEIVED",
        "noc_nonposted_atomics_acked": "NIU_MST_ATOMIC_RESP_RECEIVED",
        "noc_posted_writes_num_issued": "NIU_MST_POSTED_WR_REQ_SENT",
    }

    elf_path = get_elf_path()
    if elf_path is None:
        return

    if not os.path.exists(elf_path):
        util.ERROR(f"File {elf_path} does not exist")
        return

    risc_id = 0  # For now only works on BRISC
    noc_id = 0  # For now we only use noc0

    context = init_ttexalens()
    # Get symbols in order to obtain variable addresses
    symbols = get_symbols_from_elf(elf_path, context)

    for device_id in context.device_ids:
        device = context.devices[device_id]
        locations = device.get_block_locations(block_type="functional_workers")
        for loc in locations:
            util.INFO(f"Device: {device.id()}, loc: {loc}", end=" ")
            passed = True
            error = False

            # Check if all variables match with corresponding register
            for var in VAR_TO_REG_MAP:
                reg = VAR_TO_REG_MAP[var]
                address = symbols[var]
                # If reading fails, write error message and skip to next core
                try:
                    reg_val = read_tensix_register(loc, reg, device.id(), context)
                    var_val = read_riscv_memory(loc, address, noc_id, risc_id, device.id(), context)
                except Exception as e:
                    util.WARN(e)
                    error = True
                    break

                if reg_val != var_val:
                    # If this is the first one to fail print failed
                    if passed:
                        print(f"{util.CLR_ERR}FAILED{util.CLR_END}")
                    passed = False
                    util.ERROR(f"\tMismatch between {reg} and {var} -> {reg_val} != {var_val}")

            if passed and not error:
                print(f"{util.CLR_GREEN}PASSED{util.CLR_END}")


if __name__ == "__main__":
    main()
