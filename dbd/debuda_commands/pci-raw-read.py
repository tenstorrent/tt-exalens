"""Reads from the device's PCI memory space at a given offset. The mapping between the addresses and the on-chip data is
stored within the Tensix TLBs.

.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:1-1 rc:0,0 stream:8 > pcir 0
        PCI RD [0x0]: 0x17c0006f

"""
command_metadata = {
    "short" : "pcir",
    "type" : "low-level",
    "expected_argument_count" : [ 1 ],
    "arguments" : "addr",
    "description" : "Reads data from PCI BAR at address 'addr'"
}

import tt_device

def run(args, context, ui_state = None):
    """Run command
    """
    navigation_suggestions = []

    addr = int(args[1],0)
    print ("PCI RD [0x%x]: 0x%x" % (addr, tt_device.SERVER_IFC.pci_raw_read (ui_state['current_device_id'], addr)))

    return navigation_suggestions
