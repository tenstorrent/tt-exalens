"""Prints a debug buffer at x-y location. 

.. code-block::
   :caption: Example

    Current epoch:0(test_op) device:0 core:1-1 rc:0,0 stream:8 > ddb 0 16 hex16
    L1-0x00011800-64
    -----------  ----  ----  ----  ----  ----  ----  ----  ----
    0x00011800:  d746  bcec  951e  45ee  5fce  37ba  3758  ec52
    0x00011810:  afa5  3fd2  4cbf  e653  56cd  caf6  d617  2647
    0x00011820:  f642  9d4c  6fbe  c6dc  6626  4257  4c46  8c5a
    0x00011830:  712d  277f  ea94  c6ab  57d7  c2ce  eb56  36ce
    -----------  ----  ----  ----  ----  ----  ----  ----  ----
"""
from cgi import print_form
from dbd.tt_object import DataArray
import tt_device
import tt_util as util

command_metadata = {
    "short" : "ddb",
    "type" : "low-level",
    "expected_argument_count" : [2,6],
    "arguments" : "id, num_words, format, x, y, c",
    "description" : "Prints a debug buffer. 'id' - trisc 0|1|2 at current x-y if not selcted. 'num_words' - number of words to dump. 'format' - i8, i16, i32, hex8, hex16, hex32. optional noc0 location x-y. optional c - chip_id"
}

def run(args, context, ui_state = None):
    #This is defined in src/firmware/riscv/grayskull/l1_address_map.h
    TRISC_DEBUG_BASE=[71680, 83968, 108544]

    trisc_id = int(args[1])
    num_words = int(args[2])
    print_format = "hex32"
    x = ui_state['current_x']
    y = ui_state['current_y']
    chip_id = ui_state['current_device_id']

    if (len(args) > 3):
        print_format = args[3]

    if (len(args) > 5):
        x = int(args[4])
        y = int(args[5])

    if (len(args) > 6):
        chip_id = int(args[6])

    addr = TRISC_DEBUG_BASE[trisc_id]
    da = DataArray(f"L1-0x{addr:08x}-{num_words * 4}", 4)
    for i in range (num_words):
        data = tt_device.SERVER_IFC.pci_read_xy(chip_id, x, y, 0, addr + 4*i)
        da.data.append(data)

    is_hex = util.PRINT_FORMATS[print_format]["is_hex"]
    bytes_per_entry = util.PRINT_FORMATS[print_format]["bytes"]

    if bytes_per_entry != 4:
        da.to_bytes_per_entry(bytes_per_entry)
    formated = f"{da._id}\n" + util.dump_memory(addr, da.data, bytes_per_entry, 16, is_hex)
    print(formated)