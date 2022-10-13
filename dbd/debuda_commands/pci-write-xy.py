"""Documentation for testtest
"""
command_metadata = {
    "short" : "wxy",
    "type" : "low-level",
    "expected_argument_count" : [ 4 ],
    "arguments" : "x y addr value",
    "description" : "Writes word 'value' to address 'addr' at noc0 location x-y of the current chip."
}

import tt_device

def run(args, context, ui_state = None):
    """Run command
    """
    navigation_suggestions = []

    x = int(args[1],0)
    y = int(args[2],0)
    addr = int(args[3],0)
    tt_device.SERVER_IFC.pci_write_xy (ui_state['current_device_id'], x, y, 0, addr, data = int(args[4],0))

    return navigation_suggestions
