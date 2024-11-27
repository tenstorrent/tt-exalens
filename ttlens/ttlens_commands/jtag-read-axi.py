# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  jraxi <addr> [-d <D>...]

Arguments:
  addr        Address to read from

Options:
  -d <D>        Device ID. Optional and repeatable. Default: current device

Description:
  Reads data word from address 'addr' at AXI address of the current chip using jtag.

Examples:
  jraxi 0x0
  jraxi 0xffb20110 -d 0
"""

command_metadata = {
    "short": "jraxi",
    "type": "dev",
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt

from ttlens.tt_uistate import UIState

from ttlens.tt_coordinate import OnChipCoordinate


# A helper to print the result of a single JTAG axi read
def print_a_jtag_axi_read(device_id, addr, val, comment=""):
    print(f"device: {device_id} (AXI) 0x{addr:08x} ({addr}) = 0x{val:08x} ({val:d})")


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    addr = int(args["<addr>"], 0)

    current_device_id = ui_state.current_device_id
    device_ids = args["-d"] if args["-d"] else [f"{current_device_id}"]
    device_array = []
    for device_id in device_ids:
        device_array.append(int(device_id,0))

    for device_id in device_array:
      val = context.server_ifc.jtag_read32_axi(
          device_id, addr
      )
      print_a_jtag_axi_read(device_id, addr, val)

    return None
