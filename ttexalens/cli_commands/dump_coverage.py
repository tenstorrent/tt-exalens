# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

"""
Usage:
  dumpxy <core-loc> <start> <size> -f <file> [-d <D>...]

Arguments:
  core-loc     Either X-Y or R,C location of a core, or dram channel (e.g. ch3)
  start        Start address to read from (can be a symbol or numeric)
  size         Number of bytes to read (must be >= 1)

Options:
  -f <file>    Output file to dump raw memory into
  -d <D>       Device ID. Optional and repeatable. Default: current device

Description:
  Reads raw memory from <core-loc> starting at <start> address for <size> bytes and dumps it into a file.
"""

command_metadata = {
    "short": "dumpxy",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc", "--verbose"],
}

import os
from docopt import docopt

from ttexalens.uistate import UIState
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import read_words_from_device
from ttexalens.firmware import ELF
from ttexalens import command_parser, util


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

    # Parse start address
    try:
        addr = int(args["<start>"], 0)
    except ValueError:
        addr, _ = context.elf.parse_addr_size(args["<start>"], mem_reader)

    # Size in bytes
    size_bytes = int(args["<size>"])
    if size_bytes < 1:
        raise util.TTException("Size must be >= 1")

    # Output file
    output_file = args["-f"]
    if not output_file:
        raise util.TTException("You must specify an output file using -f")

    # Word alignment
    addr_aligned = addr & ~0x3
    end_addr = addr + size_bytes
    word_count = ((end_addr - addr_aligned + 3) // 4)

    devices = args["-d"]
    if not devices:
        devices = [str(current_device_id)]

    for device in devices:
        did = int(device, 0)
        util.INFO(f"Reading from device {did}")

        data = read_words_from_device(core_loc, addr_aligned, did, word_count, context)

        # Convert to bytes and trim to requested range
        raw_bytes = b''.join(word.to_bytes(4, byteorder="little") for word in data)
        offset = addr - addr_aligned
        trimmed = raw_bytes[offset:offset + size_bytes]

        # Write to file
        with open(output_file, "wb") as f:
            f.write(trimmed)
        util.INFO(f"Wrote {len(trimmed)} bytes to {output_file}")
