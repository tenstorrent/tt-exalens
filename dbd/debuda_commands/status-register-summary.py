"""
Usage:
  srs [ <verbosity> ]

Arguments:
  verbosity    Verbosity level (0, 1 or 2) [default: 0]

Description:
  Prints BRISC and NCRISC status registers

Examples:
  srs 1
"""

from tabulate import tabulate
import tt_util as util
from docopt import docopt

command_metadata = {
    "short" : "srs",
    "long" : "status-register",
    "type" : "low-level",
    "description" : __doc__
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

def run(cmd_text, context, ui_state = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])
    if args['<verbosity>'] == None:
        verbosity = 0
    else:
        verbosity = int(args['<verbosity>'], 0)
    print_status_register_summary (verbosity, context)
    return None
