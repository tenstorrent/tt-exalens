# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  pciw <addr> <data>

Arguments:
  addr        Address in PCI BAR to read from.
  data        Data to write to PCI BAR.

Description:
  Writes data to PCI BAR at address 'addr'. The mapping between the addresses and the on-chip data is stored within the Tensix TLBs.

Examples:
  pciw 0x0 0x0
"""

from ttexalens.context import Context
from ttexalens.uistate import UIState
from ttexalens.command_parser import CommandMetadata, tt_docopt

command_metadata = CommandMetadata(
    short_name="pciw",
    long_name="pci-raw-write",
    type="dev",
    description=__doc__,
)


def run(cmd_text: str, context: Context, ui_state: UIState):
    args = tt_docopt(command_metadata, cmd_text).args
    addr = int(args["<addr>"], 0)
    data = int(args["<data>"], 0)
    device = context.devices[ui_state.current_device_id]
    device.bar0_write32(addr, data)
    print(f"PCI WR [0x{addr:x}] <- 0x{data:x}")
    return None
