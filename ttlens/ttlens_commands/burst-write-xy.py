# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  bwxy <core-loc> <addr> [ <word-count> ] [ --format=hex32 ] [--sample <N>] [-o <O>...] [-d <D>...] [ --fill <N> ] [ --nooutput ]

Arguments:
  core-loc      Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
  addr          Address to read from
  word-count    Number of words to read. Default: 1

Options:
  --format=<F>  Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex32]
  -o <O>        Address offset. Optional and repeatable.
  -d <D>        Device ID. Optional and repeatable. Default: current device
  --fill=<N>    Write fill. Optional and repeatable. Default: 0
  --nooutput    Does not output the result 

Description:
  Writes the specified value from address 'addr' in the next 'word-count' addresses, and prints the result at core <core-loc>.

Examples:
  bwxy 18-18 0x0 1                          # Writes value 0 to address 0
  bwxy 18-18 0x0 1 --fill A5                # Writes value A5 to address 0
  bwxy 18-18 0x0 16 --fill A5               # Writes 16 words with value A5 from address 0
  bwxy 18-18 0x0 32 --format i8             # Prints 32 bytes in i8 format
  bwxy 0,0 @brisc.EPOCH_INFO_PTR.epoch_id   # Writes values 0 on the epoch_id from the EPOCH_INFO_PTR # Needs Buda context / output of a Buda run
  bwxy ch0 0x0 16                           # Writes value 0 to 16 words at address 0 from dram channel 0
"""

command_metadata = {
    "short": "bwxy",
    "type": "low-level", 
    "description": __doc__,
    "context": ["limited", "buda", "metal"],
}

import time
from docopt import docopt

from debuda import UIState

from ttlens.tt_coordinate import OnChipCoordinate
from ttlens.tt_lens_lib import write_words_to_device, read_from_device
from ttlens.tt_firmware import ELF
from ttlens.tt_object import DataArray
from ttlens import tt_util as util

def generate_fill_with_addresses(start_address,count):
    data = []
    for i in range(count):
        address = start_address + (i * 4)
        data.append(address)
    return data;

def hex_array_to_bytes(hex_array):
    bytes_array = []
    for hex_value in hex_array:
        for i in range(0, 4, 1):
            byte = (hex_value >> (i * 8)) & 0xFF
            bytes_array.append(byte)
    return bytes_array

def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(command_metadata["description"], argv=cmd_text.split()[1:])

    core_loc_str = args["<core-loc>"]
    current_device_id = ui_state.current_device_id
    current_device = context.devices[current_device_id]
    core_loc = OnChipCoordinate.create(core_loc_str, device=current_device)
    mem_reader = ELF.get_mem_reader(current_device_id, core_loc)

    # If we can parse the address as a number, do it. Otherwise, it's a variable name.
    try:
        addr, size_bytes = int(args["<addr>"], 0), 4
    except ValueError:
        addr, size_bytes = context.elf.parse_addr_size(args["<addr>"], mem_reader)

    size_words = ((size_bytes + 3) // 4) if size_bytes else 1

    word_count = int(args["<word-count>"]) if args["<word-count>"] else size_words
    format = args["--format"] if args["--format"] else "hex32"
    if format not in util.PRINT_FORMATS:
        raise util.TTException(
            f"Invalid print format '{format}'. Valid formats: {list(util.PRINT_FORMATS)}"
        )

    offsets = args["-o"]
    for offset in offsets:
        offset_addr, _ = context.elf.parse_addr_size(offset, mem_reader)
        addr += offset_addr

    fill_str = args["--fill"]
    if fill_str == "address":
        write_data = generate_fill_with_addresses(addr,word_count)
    else:
        fill = int(args["--fill"],0) if args["--fill"] else 0
        if not isinstance(fill, int):
            raise util.TTException(
                f"Invalid fill '{fill}'. Fill should 'address' or a number"
            )
        write_data = [fill]*word_count

    nooutput = True if args["--nooutput"] else False

    devices = args["-d"]
    if devices:
        for device in devices:
            did = int(device, 0)
            util.INFO(f"Writing to device {did}")
            pci_burst_write(
                did,
                core_loc,
                addr,
                core_loc_str,
                write_data,
                word_count=word_count,
                print_format=format,
                context=context,
                nooutput=nooutput
            )
    else:
        pci_burst_write(
            ui_state.current_device_id,
            core_loc,
            addr,
            core_loc_str,
            write_data,
            word_count=word_count,
            print_format=format,
            context=context,
            nooutput=nooutput
        )

def pci_burst_write(
    device_id, core_loc, addr, core_loc_str,write_data, word_count=1, print_format="hex32", context=None,nooutput=False
):
    # Write data to device requires data to be separated into bytes
    byte_write_data = hex_array_to_bytes(write_data)

    is_hex = util.PRINT_FORMATS[print_format]["is_hex"]
    bytes_per_entry = util.PRINT_FORMATS[print_format]["bytes"]
    core_loc_str =  f"{core_loc_str} (L1) :" if not core_loc_str.lower().startswith("ch") else f"{core_loc_str.lower()} (DRAM) :"

    da = DataArray(f"{core_loc_str} 0x{addr:08x} ({word_count * 4} bytes)", 4)
    bytes_written = write_to_device(core_loc, addr, byte_write_data, device_id, context)

    if not nooutput:
        da.data = write_data
        if bytes_per_entry != 4:
            da.to_bytes_per_entry(bytes_per_entry)
        formated = f"{da._id}\n" + util.dump_memory(
            addr, da.data, bytes_per_entry, 16, is_hex
        )
        print(formated)
    else:
        print("Wrote successfully")
