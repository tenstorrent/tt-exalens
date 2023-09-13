"""
Usage:
  wxy <x> <y> <addr> <data>

Description:
  Writes data word to address 'addr' at noc0 location x-y of the current chip.

Arguments:
  x           Noc0 location x-coordinate
  y           Noc0 location y-coordinate
  addr        Address to read from
  data        Data to write

Examples:
  wxy 1 1 0x0
"""
command_metadata = {
    "short" : "wxy",
    "type" : "low-level",
    "description" : __doc__
}
import tt_device
from docopt import docopt

def run(cmd_text, context, ui_state = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    x = int(args['<x>'], 0)
    y = int(args['<y>'], 0)
    addr = int(args['<addr>'], 0)
    data = int(args['<data>'], 0)
    tt_device.SERVER_IFC.pci_write_xy (ui_state['current_device_id'], x, y, 0, addr, data = data)

    return None
