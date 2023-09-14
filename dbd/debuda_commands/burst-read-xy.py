"""
Usage:
  brxy <x> <y> <addr> <burst-type> [<format>]

Arguments:
  x           Noc0 location x-coordinate
  y           Noc0 location y-coordinate
  addr        Address to read from
  burst-type  Type of burst read:
              1 - read the same location for one second. Print the histogram of values.
              >1 - read an array of 'burst-type' words once
  format      Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: i32]

Description:
  Reads data from address 'addr' at noc0 location x-y of the chip associated with the currently selected graph.

Examples:
  brxy 1 1 0x0 1
  brxy 1 1 0x0 16
  brxy 1 1 0x0 32 i8
"""

command_metadata = {
    "long": "brxy",
    "short": "brxy",
    "type": "low-level",
    "description": __doc__
}

from docopt import docopt
import tt_util as util
from tt_object import DataArray
import tt_device
import time

def run(cmd_text, context, ui_state=None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    x = int(args['<x>'], 0)
    y = int(args['<y>'], 0)
    addr = int(args['<addr>'], 0)
    burst_type = int(args['<burst-type>'], 0)
    format = args['<format>'] if args['<format>'] else 'hex32'

    print_a_pci_burst_read (ui_state['current_device_id'], x, y, 0, addr, burst_type=burst_type, print_format=format)

    return None

# A helper function to parse print_format
def get_print_format(print_format):
    is_hex_bytes_per_entry_dict = {
        "i32"  :[False, 4],
        "i16"  :[False,2],
        "i8"   :[False,1],
        "hex32":[True, 4],
        "hex16":[True,2],
        "hex8" :[True,1]}
    return is_hex_bytes_per_entry_dict[print_format]

# A helper to print the result of a single PCI read
def print_a_pci_read (x, y, addr, val, comment=""):
    print(f"{x}-{y} 0x{addr:08x} => 0x{val:08x} ({val:d}) {comment}")

# Perform a burst of PCI reads and print results.
# If burst_type is 1, read the same location for a second and print a report
# If burst_type is 2, read an array of locations once and print a report
def print_a_pci_burst_read (device_id, x, y, noc_id, addr, burst_type = 1, print_format = "hex32"):
    if burst_type == 1:
        values = {}
        t_end = time.time() + 1
        print ("Sampling for 1 second...")
        while time.time() < t_end:
            val = tt_device.SERVER_IFC.pci_read_xy(device_id, x, y, noc_id, addr)
            if val not in values:
                values[val] = 0
            values[val] += 1
        for val in values.keys():
            print_a_pci_read(x, y, addr, val, f"- {values[val]} times")
    elif burst_type >= 2:
        num_words = burst_type
        da = DataArray(f"L1-0x{addr:08x}-{num_words * 4}", 4)
        for i in range (num_words):
            data = tt_device.SERVER_IFC.pci_read_xy(device_id, x, y, noc_id, addr + 4*i)
            da.data.append(data)
        is_hex, bytes_per_entry = get_print_format(print_format)
        if bytes_per_entry != 4:
            da.to_bytes_per_entry(bytes_per_entry)
        formated = f"{da._id}\n" + util.dump_memory(addr, da.data, bytes_per_entry, 16, is_hex)
        print(formated)
