"""Reads and prints BRISC and NCRISC status registers.

.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:1-1 rc:0,0 stream:8 > srs 0
        Reading status registers on device 0...
        NCRISC status summary:
        X-Y    Status    Status Description
        -----  --------  ---------------------------
        1-1    11111111  Main loop begin
        2-1    11111111  Main loop begin
        3-1    11111111  Main loop begin
        3-3    11111111  Main loop begin
        4-1    f2000000  Ready to write data to dram
        ...
"""

from tabulate import tabulate
import tt_util as util

command_metadata = {
    "short" : "srs",
    "long" : "status-register",
    "type" : "low-level",
    "expected_argument_count" : [ 1 ],
    "arguments" : "verbosity",
    "description" : "Prints BRISC and NCRISC status registers. Verbosity can be 0, 1 or 2."
}

def print_status_register_summary(verbosity, context):
    for device_id, device in context.devices.items():
        print (f"{util.CLR_INFO}Reading status registers on device {device_id}...{util.CLR_END}")

        print("NCRISC status summary:")
        status_descs_rows = device.status_register_summary(device.NCRISC_STATUS_REG_ADDR, verbosity)
        if status_descs_rows:
            print(tabulate(status_descs_rows, headers=["X-Y", "Status", "Status Description"]));
        else:
            print("- nothing unusual")

        print("BRISC status summary:")
        status_descs_rows = device.status_register_summary(device.BRISC_STATUS_REG_ADDR, verbosity)
        if status_descs_rows:
            print(tabulate(status_descs_rows, headers=["X-Y", "Status", "Status Description"]));
        else:
            print("- nothing unusual")

def run(args, context, ui_state = None):
    verbosity = int(args[1])

    navigation_suggestions = []
    print_status_register_summary (verbosity, context)

    return navigation_suggestions
