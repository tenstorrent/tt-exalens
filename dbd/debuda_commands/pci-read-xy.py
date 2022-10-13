"""Documentation for testtest
"""
command_metadata = {
    "short" : "rxy",
    "type" : "low-level",
    "expected_argument_count" : [ 3 ],
    "arguments" : "x y addr",
    "description" : "Reads data word from address 'addr' at noc0 location x-y of the current chip."
}

import tt_util as util
import tt_device

# A helper to print the result of a single PCI read
def print_a_pci_read (x, y, addr, val, comment=""):
    print(f"{util.noc_loc_str((x, y))} 0x{addr:08x} => 0x{val:08x} ({val:d}) {comment}")

def run(args, context, ui_state = None):
    """Run command
    """
    navigation_suggestions = []

    x = int(args[1],0)
    y = int(args[2],0)
    addr = int(args[3],0)
    data = tt_device.SERVER_IFC.pci_read_xy (ui_state['current_device_id'], x, y, 0, addr)
    print_a_pci_read (x, y, addr, data)

    return navigation_suggestions
