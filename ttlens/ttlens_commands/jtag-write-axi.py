# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  jwaxi <addr> <data> [-d <D>...]

Arguments:
  addr        Address to write to
  data        Data to write

Options:
  -d <D>        Device ID. Optional and repeatable. Default: current device

Description:
  Writes data word 'data' to address 'addr' at AXI address of the current chip using jtag.

Examples:
  jwaxi 0x0 0 -d1
"""

command_metadata = {
    "short": "jwaxi",
    "type": "dev",
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt

from ttlens.tt_uistate import UIState

from ttlens.tt_coordinate import OnChipCoordinate


# A helper to print the result of a single JTAG AXI write
def print_a_jtag_axi_write(device_id, addr, val, comment=""):
    print(f"device {device_id} (AXI) 0x{addr:08x} ({addr}) <= 0x{val:08x} ({val:d})")


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    addr = int(args["<addr>"], 0)
    data = int(args["<data>"], 0)

    current_device_id = ui_state.current_device_id
    device_ids = args["-d"] if args["-d"] else [f"{current_device_id}"]
    device_array = []
    for device_id in device_ids:
        device_array.append(int(device_id,0))

    for device_id in device_array:
      context.server_ifc.jtag_write32_axi(
          device_id, addr, data
      )
      print_a_jtag_axi_write(device_id, addr, data)

    return None
