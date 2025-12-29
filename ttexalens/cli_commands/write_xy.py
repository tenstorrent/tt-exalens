# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  wxy <core-loc> <addr> <data> [--repeat <repeat>]

Description:
  Writes data word to address 'addr' at noc0 location x-y of the current chip.

Arguments:
  core-loc    Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
  addr        Address to write to
  data        Data to write

Options:
  --repeat <repeat>  Number of times to repeat the write. Default: 1

Examples:
  wxy 0,0 0x0 0x1234
  wxy 0,0 0x0 0x1234 --repeat 10
"""

from ttexalens.uistate import UIState
import ttexalens.util as util

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import write_words_to_device
from ttexalens.command_parser import CommandMetadata, tt_docopt

command_metadata = CommandMetadata(
    short_name="wxy",
    long_name="write-xy",
    type="low-level",
    description=__doc__,
)


# A helper to print the result of a single PCI read
def print_a_write(core_loc_str, addr, val, comment=""):
    core_loc_str = f"{core_loc_str} (L1) :" if not core_loc_str.startswith("ch") else f"{core_loc_str} (DRAM): "
    print(f"{core_loc_str} 0x{addr:08x} ({addr}) <= 0x{val:08x} ({val:d})")


def run(cmd_text, context, ui_state: UIState):
    args = tt_docopt(command_metadata, cmd_text).args

    core_loc_str = args["<core-loc>"]
    addr = int(args["<addr>"], 0)
    data = int(args["<data>"], 0)
    repeat = int(args["--repeat"]) if args["--repeat"] else 1
    if repeat <= 0:
        util.WARN("Repeat count must be a positive integer, defaulting to 1")
        repeat = 1

    current_device_id = ui_state.current_device_id
    current_device = context.devices[current_device_id]
    core_loc = OnChipCoordinate.create(core_loc_str, device=current_device)

    for _ in range(repeat):
        write_words_to_device(core_loc, addr, data, ui_state.current_device_id, context)

        print_a_write(core_loc_str, addr, data)
        addr += 4

    return None
