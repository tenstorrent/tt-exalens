# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  run-elf <elf-file> [ -v ] [ -d <device> ] [ -r <risc> ] [ -l <loc> ]

Description:
  Loads an elf file into a brisc and runs it.

Options:
  -r <risc>           RiscV name (brisc, triscs0, triscs1, triscs2, ncrisc, erisc). [default: first risc]

Examples:
  run-elf build/riscv-src/wormhole/sample.brisc.elf
"""

from ttexalens import util as util
from ttexalens import command_parser
from ttexalens.device import Device
from ttexalens.tt_exalens_lib import run_elf
from ttexalens.uistate import UIState

command_metadata = {
    "short": "re",
    "long": "run-elf",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited"],
    "common_option_names": ["--device", "--loc", "--verbose"],
}

# TODO: Do we need this function?
def print_PC_and_source(PC, elf):
    # Find the location in source code given the PC
    pc_map = elf.names["brisc"]["file-line"]
    if PC in pc_map:
        source_loc = pc_map[PC]
        if source_loc:
            util.INFO(f"PC: 0x{PC:x} is at {str(source_loc[0])}:{source_loc[1]}")
        else:
            util.INFO(f"PC: 0x{PC:x} is not in the source code.")
    else:
        print(f"PC 0x{PC:x} not found in the ELF file.")


# TODO:
# - Test disable watchpoint
# - Test memory access watchpoints
# - Run on all riscs


def run(cmd_text, context, ui_state: UIState):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )
    risc = dopt.args["-r"]
    device: Device
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            if not risc or risc == "first risc":
                noc_block = device.get_block(loc)
                riscs = noc_block.all_riscs
                if len(riscs) > 0:
                    risc_name = riscs[0].risc_location.risc_name
                else:
                    util.ERROR(f"No RISC-V cores found at location {loc}")
                    return
            else:
                risc_name = risc
            run_elf(dopt.args["<elf-file>"], loc, risc_name, None, device.id(), context)
