# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  wxy <addr> <data> [--repeat <repeat>] [-d <device>]
  wxy <noc-loc> <addr> <data> [--repeat <repeat>] [-d <device>]

Description:
  Writes a data word to address <addr> at <noc-loc>, or at the current location when <noc-loc> is omitted.

Arguments:
  noc-loc     Optional. X-Y or R,C noc location, or dram channel (e.g. ch3). Defaults to the current location.
  addr        Address to write to
  data        Data to write

Options:
  --repeat <repeat>  Number of times to repeat the write. Default: 1

Examples:
  wxy 0x0 0x1234                               # Current device, current location, address 0x0
  wxy 0,0 0x0 0x1234                           # Current device, explicit noc location 0,0
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
def print_a_write(noc_loc_str: str, addr: int, val: int):
    noc_loc_str = f"{noc_loc_str} (L1) :" if not noc_loc_str.startswith("ch") else f"{noc_loc_str} (DRAM): "
    print(f"{noc_loc_str} 0x{addr:08x} ({addr}) <= 0x{val:08x} ({val:d})")


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    noc_loc_str: str | None = args["<noc-loc>"]
    base_addr = int(args["<addr>"], 0)
    data = int(args["<data>"], 0)
    repeat = int(args["--repeat"]) if args["--repeat"] else 1
    if repeat <= 0:
        util.WARN("Repeat count must be a positive integer, defaulting to 1")
        repeat = 1

    def do_writes(device: Device, noc_loc: OnChipCoordinate):
        addr = base_addr
        for _ in range(repeat):
            write_words_to_device(noc_loc, addr, data, device.id, context)
            print_a_write(noc_loc.to_user_str(), addr, data)
            addr += 4

    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        util.INFO(f"Writing to device {device.id}")
        noc_loc = (
            OnChipCoordinate.create(noc_loc_str, device=device)
            if noc_loc_str
            else ui_state.current_location.change_device(device)
        )
        do_writes(device, noc_loc)

    return None
