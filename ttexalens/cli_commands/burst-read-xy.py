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
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc", "--verbose"],
}

import time
from docopt import docopt

from ttexalens.uistate import UIState

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import read_words_from_device, read_from_device
from ttexalens.firmware import ELF
from ttexalens.object import DataArray
from ttexalens import command_parser, util as util


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )
    args = dopt.args

    core_loc_str = args["<core-loc>"]
    current_device_id = ui_state.current_device_id
    current_device = context.devices[current_device_id]
    core_loc = OnChipCoordinate.create(core_loc_str, device=current_device)
    mem_reader = ELF.get_mem_reader(context, current_device_id, core_loc)

    # If we can parse the address as a number, do it. Otherwise, it's a variable name.
    try:
        addr, size_bytes = int(args["<addr>"], 0), 4
    except ValueError:
        addr, size_bytes = context.elf.parse_addr_size(args["<addr>"], mem_reader)

    size_words = ((size_bytes + 3) // 4) if size_bytes else 1

    sample = float(args["--sample"]) if args["--sample"] else 0
    word_count = int(args["<word-count>"]) if args["<word-count>"] else size_words
    format = args["--format"] if args["--format"] else "hex32"
    if format not in util.PRINT_FORMATS:
        raise util.TTException(f"Invalid print format '{format}'. Valid formats: {list(util.PRINT_FORMATS)}")

    offsets = args["-o"]
    for offset in offsets:
        offset_addr, _ = context.elf.parse_addr_size(offset, mem_reader)
        addr += offset_addr

    devices = args["-d"]
    if devices:
        for device in devices:
            did = int(device, 0)
            util.INFO(f"Reading from device {did}")
            print_a_pci_burst_read(
                did,
                core_loc,
                addr,
                core_loc_str,
                word_count=word_count,
                sample=sample,
                print_format=format,
                context=context,
            )
    else:
        print_a_pci_burst_read(
            ui_state.current_device_id,
            core_loc,
            addr,
            core_loc_str,
            word_count=word_count,
            sample=sample,
            print_format=format,
            context=context,
        )


# A helper to print the result of a single PCI read
def print_a_pci_read(core_loc_str, addr, val, comment=""):
    print(f"{core_loc_str} 0x{addr:08x} ({addr}) => 0x{val:08x} ({val:d}) {comment}")


def print_a_pci_burst_read(
    device_id, core_loc, addr, core_loc_str, word_count=1, sample=1, print_format="hex32", context=None
):
    is_hex = util.PRINT_FORMATS[print_format]["is_hex"]
    bytes_per_entry = util.PRINT_FORMATS[print_format]["bytes"]
    core_loc_str = (
        f"{core_loc_str} (L1) :" if not core_loc_str.lower().startswith("ch") else f"{core_loc_str.lower()} (DRAM) :"
    )

    if sample == 0:  # No sampling, just a single read
        da = DataArray(f"{core_loc_str} 0x{addr:08x} ({word_count * 4} bytes)", 4)
        data = read_words_from_device(core_loc, addr, device_id, word_count, context)
        da.data = data
        if bytes_per_entry != 4:
            da.to_bytes_per_entry(bytes_per_entry)
        formated = f"{da._id}\n" + util.dump_memory(addr, da.data, bytes_per_entry, 16, is_hex)
        print(formated)
    else:
        for i in range(word_count):
            values = {}
            print(f"Sampling for {sample / word_count} second{'s' if sample != 1 else ''}...")
            t_end = time.time() + sample / word_count
            while time.time() < t_end:
                val = read_from_device(core_loc, addr, device_id, context=context)
                val = int.from_bytes(val, byteorder="little")
                if val not in values:
                    values[val] = 0
                values[val] += 1
            for val in values.keys():
                print_a_pci_read(core_loc_str, addr + 4 * i, val, f"- {values[val]} times")
