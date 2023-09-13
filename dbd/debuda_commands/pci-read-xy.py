"""
Usage:
  rxy <x> <y> <addr>

Description:
  Reads data word from address 'addr' at noc0 location x-y of the current chip.

Arguments:
  x           Noc0 location x-coordinate
  y           Noc0 location y-coordinate
  addr        Address to read from

Examples:
  rxy 1 1 0x0
"""
command_metadata = {
    "short" : "rxy",
    "type" : "low-level",
    "description" : __doc__
}

import tt_device
from docopt import docopt

# A helper to print the result of a single PCI read
def print_a_pci_read (x, y, addr, val, comment=""):
    print(f"{x}-{y} 0x{addr:08x} => 0x{val:08x} ({val:d}) {comment}")

def run(cmd_text, context, ui_state = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    x = int(args['<x>'], 0)
    y = int(args['<y>'], 0)
    addr = int(args['<addr>'], 0)
    data = tt_device.SERVER_IFC.pci_read_xy (ui_state['current_device_id'], x, y, 0, addr)
    print_a_pci_read (x, y, addr, data)

    return None
