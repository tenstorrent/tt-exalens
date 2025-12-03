# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  brxy <core-loc> <addr> [ <word-count> ] [ --format=hex32 ] [--sample <N>] [-o <O>...] [-d <D>...]

Arguments:
  core-loc      Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
  addr          Address to read from
  word-count    Number of words to read. Default: 1

Options:
  --sample=<N>  Number of seconds to sample for. [default: 0] (single read)
  --format=<F>  Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex32]
  -o <O>        Address offset. Optional and repeatable.
  -d <D>        Device ID. Optional and repeatable. Default: current device

Description:
  Reads and prints a block of data from address 'addr' at core <core-loc>.

Examples:
  brxy 0,0 0x0 1                          # Read 1 word from address 0
  brxy 0,0 0x0 16                         # Read 16 words from address 0
  brxy 0,0 0x0 32 --format i8             # Prints 32 bytes in i8 format
  brxy 0,0 0x0 32 --format i8 --sample 5  # Sample for 5 seconds
  brxy ch0 0x0 16                         # Read 16 words from dram channel 0
"""

command_metadata = {
    "short": "brxy",
    "long": "burst-read-xy",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc", "--verbose"],
}

import time
from docopt import docopt

from ttexalens.uistate import UIState

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import read_words_from_device, read_word_from_device
from ttexalens.object import DataArray
from ttexalens import command_parser, util as util


def run(cmd_text, context, ui_state: UIState):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )
    args = dopt.args

    core_loc_str = args["<core-loc>"]
    offsets = args["-o"]
    sample = float(args["--sample"]) if args["--sample"] else 0
    word_count = int(args["<word-count>"]) if args["<word-count>"] else 0
    format = args["--format"] if args["--format"] else "hex32"
    if format not in util.PRINT_FORMATS:
        raise util.TTException(f"Invalid print format '{format}'. Valid formats: {list(util.PRINT_FORMATS)}")
    addr_arg = args["<addr>"]
    size_bytes_arg = 4
    try:
        # If we can parse the address as a number, do it. Otherwise, it's a variable name.
        addr_arg = int(addr_arg, 0)
    except ValueError:
        pass

    def process_device(device_id):
        core_loc = OnChipCoordinate.create(core_loc_str, device=context.devices[device_id])

        addr, size_bytes = addr_arg, size_bytes_arg

        size_words = ((size_bytes + 3) // 4) if size_bytes else 1

        for offset in offsets:
            addr += offset

        print_a_burst_read(
            device_id,
            core_loc,
            addr,
            core_loc_str,
            word_count=word_count if word_count > 0 else size_words,
            sample=sample,
            print_format=format,
            context=context,
        )

    devices = args["-d"]
    if devices:
        for device in devices:
            did = int(device, 0)
            util.INFO(f"Reading from device {did}")
            process_device(did)
    else:
        process_device(ui_state.current_device_id)


# A helper to print the result of a single PCI read
def print_a_read(core_loc_str, addr, val, comment=""):
    print(f"{core_loc_str} 0x{addr:08x} ({addr}) => 0x{val:08x} ({val:d}) {comment}")


def print_a_burst_read(
    device_id, core_loc, addr, core_loc_str, word_count=1, sample=1, print_format="hex32", context=None
):
    is_hex = util.PRINT_FORMATS[print_format]["is_hex"]
    bytes_per_entry = util.PRINT_FORMATS[print_format]["bytes"]

    memory_map = None
    try:
        device = context.devices[device_id]
        noc_block = device.get_block(core_loc)
        memory_map = noc_block.get_noc_memory_map()
    except Exception:
        # If we can't get the memory map, fall back to simple header
        pass

    if sample == 0:  # No sampling, just a single read
        # Read all data at once for efficiency
        data = read_words_from_device(core_loc, addr, device_id, word_count, context)

        # Print overall header
        print(f"{core_loc_str} : 0x{addr:08x} ({word_count * 4} total bytes)")

        if memory_map is not None:
            i = 0
            while i < word_count:
                word_addr = addr + i * 4
                region_name = memory_map.get_region_by_noc_address(word_addr)

                if region_name:
                    # Get region info and calculate how many words fit
                    region = memory_map.get_region_by_name(region_name)
                    region_start = region["noc_address"]
                    region_end = region_start + region["size"]
                    remaining_in_region = (region_end - word_addr) // 4
                    words_to_read = min(remaining_in_region, word_count - i)
                else:
                    # Unknown region, just take one word
                    region_name = "unknown"
                    words_to_read = 1

                # Collect data for this region
                block_data = data[i : i + words_to_read]
                block_start_addr = word_addr

                # Print this region's data
                block_header = f"({region_name})"
                da = DataArray(f"{block_header} : 0x{block_start_addr:08x} ({len(block_data) * 4} bytes)", 4)
                da.data = block_data
                if bytes_per_entry != 4:
                    da.to_bytes_per_entry(bytes_per_entry)
                print(f"{da._id}\n{util.dump_memory(block_start_addr, da.data, bytes_per_entry, 16, is_hex)}")

                i += words_to_read
        else:
            # No memory map, just print the data
            da = DataArray(f"{core_loc_str} : 0x{addr:08x} ({word_count * 4} bytes)", 4)
            da.data = data
            if bytes_per_entry != 4:
                da.to_bytes_per_entry(bytes_per_entry)
            print(util.dump_memory(addr, da.data, bytes_per_entry, 16, is_hex))
    else:
        # Sampling mode
        if memory_map is not None:
            # Track region for each sampled word
            for i in range(word_count):
                word_addr = addr + 4 * i
                region_name = memory_map.get_region_by_noc_address(word_addr)
                if not region_name:
                    region_name = "unknown"
                block_header = f"{core_loc_str} ({region_name})"

                values = {}
                print(f"Sampling for {sample / word_count} second{'s' if sample != 1 else ''}...")
                t_end = time.time() + sample / word_count
                while time.time() < t_end:
                    val = read_word_from_device(core_loc, word_addr, device_id, context=context)
                    if val not in values:
                        values[val] = 0
                    values[val] += 1
                for val in values.keys():
                    print_a_read(block_header, word_addr, val, f"- {values[val]} times")
        else:
            # No memory map, original behavior
            for i in range(word_count):
                values = {}
                print(f"Sampling for {sample / word_count} second{'s' if sample != 1 else ''}...")
                t_end = time.time() + sample / word_count
                while time.time() < t_end:
                    val = read_word_from_device(core_loc, addr + 4 * i, device_id, context=context)
                    if val not in values:
                        values[val] = 0
                    values[val] += 1
                for val in values.keys():
                    print_a_read(core_loc_str, addr + 4 * i, val, f"- {values[val]} times")
