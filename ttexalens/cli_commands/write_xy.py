# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  wxy <addr> <data> [--repeat <repeat>] [-d <device>]
  wxy <core-loc> <addr> <data> [--repeat <repeat>] [-d <device>]

Description:
  Writes a data word to address <addr> at <core-loc>, or at the current location when <core-loc> is omitted.

Arguments:
  core-loc    Optional. X-Y or R,C location of a core, or dram channel (e.g. ch3). Defaults to the current UI location.
  addr        Address to write to
  data        Data to write

Options:
  --repeat <repeat>  Number of times to repeat the write. Default: 1

Examples:
  wxy 0x0 0x1234                               # Current device, current UI core location, address 0x0
  wxy 0,0 0x0 0x1234                           # Current device, explicit core location 0,0
  wxy 0,0 0x0 0x1234 -d 1                      # Device 1
  wxy 0,0 0x0 0x1234 --repeat 10
"""

from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.uistate import UIState
import ttexalens.util as util

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import write_words_to_device
from ttexalens.command_parser import CommandMetadata, CommonCommandOptions, tt_docopt

command_metadata = CommandMetadata(
    short_name="wxy",
    long_name="write-xy",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device],
)


# A helper to print the result of a single PCI read
def print_a_write(core_loc_str: str, addr: int, val: int):
    core_loc_str = f"{core_loc_str} (L1) :" if not core_loc_str.startswith("ch") else f"{core_loc_str} (DRAM): "
    print(f"{core_loc_str} 0x{addr:08x} ({addr}) <= 0x{val:08x} ({val:d})")


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    core_loc_str: str | None = args["<core-loc>"]
    base_addr = int(args["<addr>"], 0)
    data = int(args["<data>"], 0)
    repeat = int(args["--repeat"]) if args["--repeat"] else 1
    if repeat <= 0:
        util.WARN("Repeat count must be a positive integer, defaulting to 1")
        repeat = 1

    def do_writes(device: Device, core_loc: OnChipCoordinate):
        addr = base_addr
        for _ in range(repeat):
            write_words_to_device(core_loc, addr, data, device.id, context)
            print_a_write(core_loc.to_user_str(), addr, data)
            addr += 4

    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        util.INFO(f"Writing to device {device.id}")
        core_loc = (
            OnChipCoordinate.create(core_loc_str, device=device)
            if core_loc_str
            else ui_state.current_location.change_device(device)
        )
        do_writes(device, core_loc)

    return None
