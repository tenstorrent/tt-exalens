# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  jwaxi <addr> <data>

Description:
  Writes data word 'data' to address 'addr' at AXI address of the current chip using jtag.

Arguments:
  addr        Address to read from
  data        Data to write

Examples:
  jwaxi 0x0 0
"""

command_metadata = {
    "short": "jwaxi",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "buda", "metal"],
}

from docopt import docopt

from debuda import UIState

from dbd import tt_device
from dbd.tt_coordinate import OnChipCoordinate


# A helper to print the result of a single JTAG AXI write
def print_a_jtag_axi_write(addr, val, comment=""):
    print(f"AXI 0x{addr:08x} ({addr}) <= 0x{val:08x} ({val:d})")


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    addr = int(args["<addr>"], 0)
    data = int(args["<data>"], 0)

    current_device_id = ui_state.current_device_id
    current_device = context.devices[current_device_id]

    val = tt_device.SERVER_IFC.jtag_wraxi(
        ui_state.current_device_id, addr, data
    )
    print_a_jtag_axi_write(addr, val)

    return None
