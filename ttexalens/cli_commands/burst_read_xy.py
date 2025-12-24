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

import time
from docopt import docopt

from ttexalens.memory_map import MemoryMap
from ttexalens.uistate import UIState

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import read_words_from_device, read_word_from_device
from ttexalens.object import DataArray
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, CommonCommandOptions, tt_docopt

command_metadata = CommandMetadata(
    short_name="brxy",
    long_name="burst-read-xy",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device],
)


def run(cmd_text, context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    location_str = args["<core-loc>"]
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
        location = OnChipCoordinate.create(location_str, device=context.devices[device_id])

        addr, size_bytes = addr_arg, size_bytes_arg

        size_words = ((size_bytes + 3) // 4) if size_bytes else 1

        for offset in offsets:
            addr += offset

        print_a_burst_read(
            device_id,
            location,
            addr,
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
def print_a_read(header, addr, val, comment=""):
    print(f"{header} 0x{addr:08x} ({addr}) => 0x{val:08x} ({val:d}) {comment}")


def print_memory_block(header: str, start_addr: int, data: list[int], bytes_per_entry: int, is_hex: bool):
    da = DataArray(f"{header} : 0x{start_addr:08x} ({len(data) * 4} bytes)", 4)
    da.data = data
    if bytes_per_entry != 4:
        da.to_bytes_per_entry(bytes_per_entry)
    print(f"{da._id}\n{util.dump_memory(start_addr, da.data, bytes_per_entry, 16, is_hex)}")


def print_a_burst_read(device_id, location, addr, word_count=1, sample=1, print_format="hex32", context=None):
    is_hex = util.PRINT_FORMATS[print_format]["is_hex"]
    bytes_per_entry = util.PRINT_FORMATS[print_format]["bytes"]

    device = context.devices[device_id]
    noc_block = device.get_block(location)
    memory_map: MemoryMap = noc_block.get_noc_memory_map()

    if sample == 0:  # No sampling, just a single read
        # Read all data at once for efficiency
        data = read_words_from_device(location, addr, device_id, word_count, context)

        # Print overall header
        print(f"{location.to_user_str()} : 0x{addr:08x} ({word_count * 4} total bytes)")

        i = 0
        while i < word_count:
            word_addr = addr + i * 4
            memory_block_name = memory_map.get_block_name_by_noc_address(word_addr)

            if memory_block_name is not None:
                # Get block info and calculate how many words fit in this known region
                memory_block = memory_map.get_block_by_name(memory_block_name)
                assert memory_block is not None, f"Memory block '{memory_block_name}' not found in map but expected"
                assert (
                    memory_block.address.noc_address is not None
                ), f"Memory block '{memory_block_name}' has no NOC address"
                memory_block_start = memory_block.address.noc_address
                memory_block_end = memory_block_start + memory_block.size
                remaining_words_in_block = max(
                    (memory_block_end - word_addr) // 4, 1
                )  # If not aligned and have less than 4 bytes until end, read at least 1 word
                words_to_read = min(remaining_words_in_block, word_count - i)
            else:
                # Unknown block - find how many consecutive unknown words
                memory_block_name = "?"
                remaining_words_in_block = word_count - i
                words_to_read = remaining_words_in_block
                for offset in range(remaining_words_in_block):
                    check_addr = word_addr + offset * 4
                    if memory_map.get_block_name_by_noc_address(check_addr) is not None:
                        words_to_read = offset if offset > 0 else 1
                        break

            # Collect data for this block
            block_data = data[i : i + words_to_read]
            block_start_addr = word_addr

            # Print this block's data
            header = f"({memory_block_name})"
            print_memory_block(header, block_start_addr, block_data, bytes_per_entry, bool(is_hex))

            i += words_to_read
    else:
        # Sampling mode
        for i in range(word_count):
            word_addr = addr + 4 * i

            block_name = memory_map.get_block_name_by_noc_address(word_addr)
            if block_name is None:
                block_name = "?"

            block_header = f"{location.to_user_str()} ({block_name})"

            values = {}
            print(f"Sampling for {sample / word_count} second{'s' if sample != 1 else ''}...")
            t_end = time.time() + sample / word_count
            while time.time() < t_end:
                val = read_word_from_device(location, word_addr, device_id, context=context)
                if val not in values:
                    values[val] = 0
                values[val] += 1
            for val in values.keys():
                print_a_read(block_header, word_addr, val, f"- {values[val]} times")
