# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  brxy <addr> [ <core-loc> ] [ <word-count> ] [ --format=hex32 ] [--sample <N>] [-o <O>...] [-d <device>]

Arguments:
  addr          Address to read from
  core-loc      Either X-Y or R,C location of a core, or dram channel (e.g. ch3).
                Optional; defaults to the current location from the UI. If you pass
                both <core-loc> and <word-count>, they may be given in either order.
  word-count    Number of words to read. Default: 1

Options:
  --sample=<N>  Number of seconds to sample for. [default: 0] (single read)
  --format=<F>  Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex32]
  -o <O>        Address offset. Optional and repeatable.

Description:
  Reads and prints a block of data from address 'addr' at core <core-loc>, or at the current UI location when <core-loc> is omitted.

Examples:
  brxy 0x0                                      # Read 1 word from address 0, current UI core
  brxy 0x0 0,0                                  # Read 1 word from address 0, core 0,0
  brxy 0x0 16                                   # Read 16 words from address 0, current UI core
  brxy 0x0 0,0 16                               # Read 16 words from address 0, core 0,0
  brxy 0x0 16 0,0                               # Same (word-count and core-loc may be swapped)
  brxy 0x0 0,0 32 --format i8                   # Read 32 words in i8 format from address 0, core 0,0
  brxy 0x0 0,0 32 --format i8 --sample 5        # Sample for 5 seconds
  brxy 0x0 ch0 16                               # Read 16 words from address 0, dram channel 0
"""

import time
from docopt import docopt

from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.memory_map import MemoryMap
from ttexalens.uistate import UIState

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import read_words_from_device, read_word_from_device
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, CommonCommandOptions, tt_docopt

command_metadata = CommandMetadata(
    short_name="brxy",
    long_name="burst-read-xy",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device],
)


def _brxy_token_is_core_loc(token: str, device) -> bool:
    try:
        OnChipCoordinate.create(token, device=device)
        return True
    except (util.TTException, ValueError):
        return False


def _brxy_token_is_word_count(token: str) -> bool:
    try:
        int(token, 0)
        return True
    except ValueError:
        return False


def _resolve_one_brxy_optional_token(token: str, device) -> tuple[str | None, int]:
    """Single optional token after <addr> (docopt usually stores it in <core-loc>)."""
    if _brxy_token_is_core_loc(token, device):
        return token, 1
    if _brxy_token_is_word_count(token):
        return None, int(token, 0)
    # Not a valid core string; int() raises ValueError (same as unparseable word count).
    return None, int(token, 0)


def _resolve_brxy_core_loc_and_word_count(
    raw_core_loc: str | bool | None,
    raw_word_count: str | bool | None,
    context: Context,
    ui_state: UIState,
) -> tuple[str | None, int]:
    """
    Docopt fills [ <core-loc> ] then [ <word-count> ], so <word-count> is never set without
    <core-loc>. If only one token is given after <addr>, it lands in <core-loc>; classify it
    with the same predicates as the two-token case. If both tokens are present, accept either
    order (core then count, or count then core).
    """
    first = str(raw_core_loc) if raw_core_loc else None
    second = str(raw_word_count) if raw_word_count else None
    device = context.find_device_by_id(ui_state.current_device_id)

    if first is not None and second is not None:
        swapped_order = _brxy_token_is_core_loc(second, device) and _brxy_token_is_word_count(first)
        if swapped_order:
            return second, int(first, 0)
        return first, int(second, 0)

    if first is not None:
        return _resolve_one_brxy_optional_token(first, device)

    return None, 1


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    location_str, word_count = _resolve_brxy_core_loc_and_word_count(
        args["<core-loc>"], args["<word-count>"], context, ui_state
    )
    offsets = args["-o"]
    sample = float(args["--sample"]) if args["--sample"] else 0
    format = args["--format"] if args["--format"] else "hex32"
    if format not in util.PRINT_FORMATS:
        raise util.TTException(f"Invalid print format '{format}'. Valid formats: {list(util.PRINT_FORMATS)}")
    addr_arg = args["<addr>"]
    try:
        # If we can parse the address as a number, do it. Otherwise, it's a variable name.
        addr_arg = int(addr_arg, 0)
    except ValueError:
        pass

    def do_burst_read(device: Device, location: OnChipCoordinate):
        addr = addr_arg

        for offset in offsets:
            addr += offset

        print_a_burst_read(
            location,
            addr,
            word_count=word_count,
            sample=sample,
            print_format=format,
            context=context,
        )

    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        if args["-d"]:
            util.INFO(f"Reading from device {device.id}")
        if location_str:
            do_burst_read(device, OnChipCoordinate.create(location_str, device=device))
        else:
            do_burst_read(device, ui_state.current_location.change_device(device))


# A helper to print the result of a single PCI read
def print_a_read(header, addr, val, comment=""):
    print(f"{header} 0x{addr:08x} ({addr}) => 0x{val:08x} ({val:d}) {comment}")


def print_memory_block(header: str, start_addr: int, data: list[int], bytes_per_entry: int, is_hex: bool):
    da = util.DataArray(f"{header} : 0x{start_addr:08x} ({len(data) * 4} bytes)", 4)
    da.data = data
    if bytes_per_entry != 4:
        da.to_bytes_per_entry(bytes_per_entry)
    print(f"{da.id}\n{util.dump_memory(start_addr, da.data, bytes_per_entry, 16, is_hex)}")


def print_a_burst_read(
    location: OnChipCoordinate,
    addr: int,
    word_count: int,
    sample: float,
    print_format: str,
    context: Context,
):
    is_hex = util.PRINT_FORMATS[print_format]["is_hex"]
    bytes_per_entry = util.PRINT_FORMATS[print_format]["bytes"]

    memory_map: MemoryMap = location.noc_block.noc_memory_map

    if sample == 0:  # No sampling, just a single read
        # Read all data at once for efficiency
        data = read_words_from_device(location, addr, word_count=word_count)

        # Print overall header
        print(f"{location.to_user_str()} : 0x{addr:08x} ({word_count * 4} total bytes)")

        i = 0
        while i < word_count:
            word_addr = addr + i * 4
            memory_block_info = memory_map.find_by_noc_address(word_addr)
            if memory_block_info is not None:
                # Get block info and calculate how many words fit in this known region
                memory_block_name = memory_block_info.name
                memory_block = memory_block_info.memory_block
                assert (
                    memory_block.address.noc_address is not None
                ), f"Memory block '{memory_block_info.name}' has no NOC address"
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
                    if memory_map.find_by_noc_address(check_addr) is not None:
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

            block_info = memory_map.find_by_noc_address(word_addr)
            block_name = block_info.name if block_info is not None else "?"
            block_header = f"{location.to_user_str()} ({block_name})"

            values = {}
            print(f"Sampling for {sample / word_count} second{'s' if sample != 1 else ''}...")
            t_end = time.time() + sample / word_count
            while time.time() < t_end:
                val = read_word_from_device(location, word_addr)
                if val not in values:
                    values[val] = 0
                values[val] += 1
            for val in values.keys():
                print_a_read(block_header, word_addr, val, f"- {values[val]} times")
