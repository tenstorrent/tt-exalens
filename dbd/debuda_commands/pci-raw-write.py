"""Documentation for testtest
"""
command_metadata = {
    "short" : "pciw",
    "type" : "low-level",
    "expected_argument_count" : 2,
    "arguments_description" : "addr data: write 'data' to PCI bar at address 'addr"
}

import tt_device

def run(args, context, ui_state = None):
    """Run command
    """
    navigation_suggestions = []

    addr = int(args[1],0)
    data = int(args[2],0)
    print ("PCI WR [0x%x] <- 0x%x" % (addr, tt_device.SERVER_IFC.pci_raw_write (ui_state['current_device_id'], addr, data)))

    return navigation_suggestions
