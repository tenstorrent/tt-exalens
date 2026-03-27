# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  brxy [ <core-loc> ] [ <addr> ] [ <word-count> ] [ --format=hex32 ] [--sample <N>] [-o <O>...] [-d <device>]

Arguments:
  Docopt stores up to three positionals in order in the brackets above. Semantics (not the bracket names) are:
  core-loc      Optional. X-Y or R,C, or dram channel (e.g. ch3). Defaults to the current UI location when omitted.
  addr          Required. Address to read from (omit zero positionals to get a clear error).
  word-count    Optional. Number of words to read. Default: 1

Options:
  --sample=<N>  Number of seconds to sample for. [default: 0] (single read)
  --format=<F>  Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex32]
  -o <O>        Address offset. Optional and repeatable.

Description:
  Reads a block of data at <addr> on <core-loc>, or at the current UI core when <core-loc> is omitted.

Examples:
  brxy 0x0                                      # 1 word at 0x0, current UI core
  brxy 0x0 16                                   # 16 words at 0x0, current UI core
  brxy 0,0 0x0                                  # 1 word at 0x0, core 0,0
  brxy 0,0 0x0 16                               # 16 words at 0x0, core 0,0
  brxy 0,0 0x0 32 --format i8                   # 32 words, i8 format
  brxy 0,0 0x0 32 --format i8 --sample 5        # Sample for 5 seconds
  brxy ch0 0x0 16                               # 16 words at 0x0, dram channel 0
"""

import time

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


def _brxy_docopt_ordered_slots(args: dict) -> list[str]:
    """Left-filled docopt slots; map to t0,t1,t2 by length, not by key name."""
    slots: list[str] = []
    for key in ("<core-loc>", "<addr>", "<word-count>"):
        v = args.get(key)
        if not v:
            break
        slots.append(v)
    return slots


def _resolve_brxy_positionals(slots: list[str]) -> tuple[str | None, str, int]:
    """
    Interpret t0,t1,t2 from docopt's left-filled optional positionals.
    0 → error (addr required). 1 → addr only. 2 → (core, addr) if t0 is a core location or dram channel, else (addr, word-count).
    3 → core, addr, word-count (strict order).
    """
    match len(slots):
        # No positional arguments -> error
        case 0:
            raise util.TTException("brxy: address omitted; give at least one positional argument (the address).")
        # One positional argument -> addr only
        case 1:
            return None, slots[0], 1
        # Two positional arguments -> core, addr or addr, word-count
        case 2:
            t0, t1 = slots[0], slots[1]
            if any(x in t0 for x in ["-", ",", "ch"]):
                return t0, t1, 1
            else:
                try:
                    return None, t0, int(t1, 0)
                except ValueError:
                    raise util.TTException(f"brxy: second argument must be an integer word count; got {t1!r}.")
        # Three positional arguments -> core, addr, word-count
        case 3:
            t0, t1, t2 = slots[0], slots[1], slots[2]
            if any(x in t0 for x in ["-", ",", "ch"]):
                try:
                    return t0, t1, int(t2, 0)
                except ValueError:
                    raise util.TTException(f"brxy: third argument must be an integer word count; got {t2!r}.")
            raise util.TTException(f"brxy: first argument must be a valid core location or dram channel; got {t0!r}.")
        case _:
            raise util.TTException(
                f"brxy: at most three positional arguments (core, address, word-count); got {len(slots)}: {' '.join(slots)}."
            )


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    slots = _brxy_docopt_ordered_slots(args)
    core_loc_str, addr_str, word_count = _resolve_brxy_positionals(slots)
    offsets = args["-o"]
    sample = float(args["--sample"]) if args["--sample"] else 0
    format = args["--format"] if args["--format"] else "hex32"
    if format not in util.PRINT_FORMATS:
        raise util.TTException(f"Invalid print format '{format}'. Valid formats: {list(util.PRINT_FORMATS)}")
    try:
        # If we can parse the address as a number, do it. Otherwise, it's a variable name.
        addr_arg = int(addr_str, 0)
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
        util.INFO(f"Reading from device {device.id}")
        core_loc = (
            OnChipCoordinate.create(core_loc_str, device=device)
            if core_loc_str
            else ui_state.current_location.change_device(device)
        )
        do_burst_read(device, core_loc)


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
