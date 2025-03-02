# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  jwxy <core-loc> <addr> <data> [-d <D>...]

Arguments:
  core-loc    Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
  addr        Address to write to
  data        Data to write

Options:
  -d <D>        Device ID. Optional and repeatable. Default: current device

Description:
  Writes data word 'data' to address 'addr' at noc0 location x-y of the current chip using jtag.

Examples:
  jwxy 0,0 0x0 0
  jwxy 0,0 0x0 0 -d1
"""

command_metadata = {
    "short": "jwxy",
    "type": "dev",
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt

from ttexalens.uistate import UIState

from ttexalens.coordinate import OnChipCoordinate


# A helper to print the result of a single JTAG write
def print_a_jtag_write(device_id, core_loc_str, addr, val, comment=""):
    print(f"device: {device_id} loc: {core_loc_str} 0x{addr:08x} ({addr}) <= 0x{val:08x} ({val:d})")


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    core_loc_str = args["<core-loc>"]
    addr = int(args["<addr>"], 0)
    data = int(args["<data>"], 0)

    current_device_id = ui_state.current_device_id
    device_ids = args["-d"] if args["-d"] else [f"{current_device_id}"]
    device_array = []
    for device_id in device_ids:
        device_array.append(int(device_id, 0))

    for device_id in device_array:
        current_device = context.devices[device_id]
        core_loc = OnChipCoordinate.create(core_loc_str, device=current_device)

        context.server_ifc.jtag_write32(device_id, *core_loc.to("noc0"), addr, data)
        core_loc_str_print = (
            f"{core_loc_str} (L1) :" if not core_loc_str.startswith("ch") else f"{core_loc_str} (DRAM): "
        )
        print_a_jtag_write(device_id, core_loc_str_print, addr, data)

    return None
