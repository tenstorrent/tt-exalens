from cgi import print_form
from dbd.tt_object import DataArray
import tt_device
import tt_util as util

command_metadata = {
          "long" : "dump-debug-buffer",
          "short" : "ddb",
          "expected_argument_count" : [2,3],
          "arguments_description" : "id, num_words, print_format: id - trisc 0|1|2 at current x-y.\nnum_words - number of words to dump.\nPrint formats are i8, i16, i32, hex8, hex16, hex32.\n"
        }

def run(args, context, ui_state = None):
    #This is defined in src/firmware/riscv/grayskull/l1_address_map.h
    TRISC_DEBUG_BASE=[71680, 83968, 108544]

    trisc_id = int(args[1])
    num_words = int(args[2])
    print_format = "hex32"
    if (len(args) > 3):
        print_format = args[3]

    addr = TRISC_DEBUG_BASE[trisc_id]
    da = DataArray(f"L1-0x{addr:08x}-{num_words * 4}", 4)
    for i in range (num_words):
        data = tt_device.SERVER_IFC.pci_read_xy(ui_state['current_device_id'], ui_state['current_x'], ui_state['current_y'], 0, addr + 4*i)
        da.data.append(data)

    is_hex = util.PRINT_FORMATS[print_format]["is_hex"]
    bytes_per_entry = util.PRINT_FORMATS[print_format]["bytes"]

    if bytes_per_entry != 4:
        da.to_bytes_per_entry(bytes_per_entry)
    formated = f"{da._id}\n" + util.dump_memory(addr, da.data, bytes_per_entry, 16, is_hex)
    print(formated)