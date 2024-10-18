# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  jwxy <core-loc> <addr> <data>

Description:
  Writes data word 'data' to address 'addr' at noc0 location x-y of the current chip using jtag.

Arguments:
  core-loc    Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
  addr        Address to write to
  data        Data to write

Examples:
  jwxy 18-18 0x0 0
"""

command_metadata = {
    "short": "jwxy",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "buda", "metal"],
}

from docopt import docopt

from debuda import UIState

from dbd import tt_device
from dbd.tt_coordinate import OnChipCoordinate


# A helper to print the result of a single JTAG write
def print_a_jtag_write(core_loc_str, addr, val, comment=""):
    print(f"{core_loc_str} 0x{addr:08x} ({addr}) <= 0x{val:08x} ({val:d})")


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    core_loc_str = args["<core-loc>"]
    addr = int(args["<addr>"], 0)
    data = int(args["<data>"], 0)

    current_device_id = ui_state.current_device_id
    current_device = context.devices[current_device_id]
    core_loc = OnChipCoordinate.create(core_loc_str, device=current_device)

    val = tt_device.SERVER_IFC.jtag_write32(
        ui_state.current_device_id, *core_loc.to("nocVirt"), addr, data
    )
    core_loc_str = f"{core_loc_str} (L1) :" if not core_loc_str.startswith("ch") else f"{core_loc_str} (DRAM): "
    print_a_jtag_write(core_loc_str, addr, val)

    return None
