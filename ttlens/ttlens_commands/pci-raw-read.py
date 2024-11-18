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

from docopt import docopt

from ttlens.tt_uistate import UIState

command_metadata = {
    "short": "pcir", 
    "type": "dev", 
    "description": __doc__,
    "context": ["limited", "metal"],
}


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])
    addr = int(args["<addr>"], 0)
    pci_read_result = context.server_ifc.pci_read32_raw(
        ui_state.current_device_id, addr
    )
    print(f"PCI RD [0x{addr:x}]: 0x{pci_read_result:x}")
    return None
