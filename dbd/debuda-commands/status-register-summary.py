# Traverses all streams and detects the blocked one. It then prints the results.
# It prioritizes the streams that are genuinely blocked, to the ones that are waiting on genuinely 
# blocked cores.
from tabulate import tabulate
import tt_util as util

command_metadata = {
        "short" : "srs",
        "expected_argument_count" : 1,
        "arguments_description" : "verbosity [0-2] : prints brisc and ncrisc status registers."
    }

def print_status_register_summary(verbosity, context):
    for device_id, device in enumerate (context.devices):
        print (f"{util.CLR_INFO}Reading status registers on device %d...{util.CLR_END}" % device_id)

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
