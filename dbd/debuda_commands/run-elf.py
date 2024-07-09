# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  run-elf <elf-file> [ -v ] [ -d <device> ] [ -r <risc> ] [ -l <loc> ]

Description:
  Loads an elf file into a brisc and runs it.

Options:
  -r <risc>           RiscV ID (0: brisc, 1-3 triscs). [default: 0]

Examples:
  run-elf brisc.elf
"""

import tt_util as util
import tt_commands
from tt_debug_risc import RiscLoader, get_risc_name
from tt_firmware import ELF
import tt_device
from tt_object import DataArray

from tt_debuda_lib import run_elf

command_metadata = {
    "short": "re",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited"], 
}

# TODO: Do we need this function?
def print_PC_and_source (PC, elf):
    # Find the location in source code given the PC
    pc_map = elf.names["brisc"]["file-line"]
    if PC in pc_map:
        source_loc = pc_map[PC]
        if source_loc:
            util.INFO (f"PC: 0x{PC:x} is at {str(source_loc[0])}:{source_loc[1]}")
        else:
            util.INFO (f"PC: 0x{PC:x} is not in the source code.")
    else:
        print (f"PC 0x{PC:x} not found in the ELF file.")

# TODO:
# - Test disable watchpoint
# - Test memory access watchpoints
# - Run on all riscs

def run(cmd_text, context, ui_state=None):
    dopt = tt_commands.tt_docopt(command_metadata["description"], argv=cmd_text.split()[1:],
                                common_option_names=[ "--device", "--loc", "--verbose", "--test" ]
                                )
    risc_id = int(dopt.args["-r"])

    if not dopt.args['-l']:
        loc = ui_state.current_location
    else:
        loc = dopt.args['-l']

    for device in dopt.for_each("--device", context, ui_state):
        run_elf(dopt.args['<elf-file>'], loc, risc_id, device.id(), context)
