# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  pcir <addr>

Arguments:
  addr        Address in PCI BAR to read from.

Description:
  Reads data from PCI BAR at address 'addr'. The mapping between the addresses and the on-chip data is stored within the Tensix TLBs.

Examples:
  pcir 0x0
"""

from ttexalens.context import Context
from ttexalens.uistate import UIState
from ttexalens.command_parser import CommandMetadata, tt_docopt

command_metadata = CommandMetadata(
    short_name="pcir",
    long_name="pci-raw-read",
    type="dev",
    description=__doc__,
)


def run(cmd_text: str, context: Context, ui_state: UIState):
    args = tt_docopt(command_metadata, cmd_text).args
    addr = int(args["<addr>"], 0)
    device = context.devices[ui_state.current_device_id]
    pci_read_result = device.bar0_read32(addr)
    print(f"PCI RD [0x{addr:x}]: 0x{pci_read_result:x}")
    return None
