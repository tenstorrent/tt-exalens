# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  read <address> [ <word-count> ] [ --format=hex8 ] [ --unsafe ] [ -r <risc_name> ] [ -d <device> ] [ -l <loc> ]

Arguments:
  address         Address to read from
  word-count      Number of words to read. [Default: 1]

Options:
  --format=<F>    Data format. Options: i8, i16, i32, hex8, hex16, hex32 [default: hex8]
  -r <risc_name>  RISC core name if you want to read memory that is not exposed on NOC.
  --unsafe        Experts mode, allow reading everything (bypass safety checks).

Description:
  Reads and prints a block of data from address 'address'.

Examples:
  read 0x0 1                          # Read 1 word from address 0
  read 0x0 16                         # Read 16 words from address 0
  read 0x0 32 --format i8             # Prints 32 bytes in i8 format
  read 0xFFB0000 -r brisc 16          # Read 16 words from brisc private data memory
"""

from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.uistate import UIState

from ttexalens.coordinate import OnChipCoordinate
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="r",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    address = int(args["<address>"], 0)
    word_count = int(args["<word-count>"], 0) if args["<word-count>"] else 1
    if word_count < 1:
        util.ERROR(f"Number of words to read must be at least 1, but specified {word_count}")
        return
    unsafe = args["--unsafe"]
    risc_name = args["-r"]
    format = args["--format"] if args["--format"] else "hex8"
    if format not in util.PRINT_FORMATS:
        util.ERROR(f"Invalid print format '{format}'. Valid formats: {list(util.PRINT_FORMATS)}")
        return
    is_hex = util.PRINT_FORMATS[format]["is_hex"]
    bytes_per_entry = util.PRINT_FORMATS[format]["bytes"]
    bytes_to_read = word_count * bytes_per_entry
    device: Device
    location: OnChipCoordinate
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        device_id_str = f"{device.id}"
        if device.unique_id is not None:
            device_id_str += f" [0x{device.unique_id:x}]"
        for location in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            location_str = location.to_user_str()
            read_bytes = 0
            read_address = address
            while read_bytes < bytes_to_read:
                if unsafe:
                    bytes, memory_block_name = execute_unsafe_read(
                        location, read_address, bytes_to_read - read_bytes, risc_name
                    )
                else:
                    bytes, memory_block_name = execute_safe_read(
                        location, read_address, bytes_to_read - read_bytes, risc_name
                    )
                header = f"Device {device_id_str} | Location {location_str} | Block {memory_block_name} : 0x{read_address:08x} ({len(bytes)} bytes)"
                da = util.DataArray(header, bytes_per_entry)
                da.from_bytes(bytes)
                util.INFO(header)
                print(f"{util.dump_memory(read_address, da.data, bytes_per_entry, 16, is_hex)}")
                read_address += len(bytes)
                read_bytes += len(bytes)


def execute_safe_read(
    location: OnChipCoordinate, address: int, bytes_to_read: int, risc_name: str | None
) -> tuple[bytes, str]:
    # Check if we are reading using RISC debugging hardware or directly over NOC
    if risc_name is None:
        # Find memory block containing the address
        memory_block_info = location.noc_block.noc_memory_map.find_by_noc_address(address)
        if not memory_block_info:
            raise util.TTException(f"Address 0x{address:08X} is not in a known memory block for location {location}")
        if memory_block_info.memory_block.address.noc_address is None:
            raise util.TTException(f"Memory block '{memory_block_info.name}' does not have a NOC address")
        memory_block_end = memory_block_info.memory_block.address.noc_address + memory_block_info.memory_block.size
        read_size = min(bytes_to_read, memory_block_end - address)
        bytes = location.noc_read(address, read_size)
        return bytes, memory_block_info.name
    else:
        risc_debug = location.noc_block.get_risc_debug(risc_name)
        memory_block_info = risc_debug.risc_info.memory_map.find_by_private_address(address)
        if not memory_block_info:
            raise util.TTException(
                f"Address 0x{address:08X} is not in a known memory block for {risc_name} at location {location}"
            )
        if memory_block_info.memory_block.address.private_address is None:
            raise util.TTException(f"Memory block '{memory_block_info.name}' does not have a private address")
        memory_block_end = memory_block_info.memory_block.address.private_address + memory_block_info.memory_block.size
        read_size = min(bytes_to_read, memory_block_end - address)
        if memory_block_info.memory_block.address.noc_address is not None:
            # Prefer reading over NOC if possible
            noc_address = memory_block_info.memory_block.address.noc_address + (
                address - memory_block_info.memory_block.address.private_address
            )
            bytes = location.noc_read(noc_address, read_size)
        else:
            bytes = risc_debug.read_memory_bytes(address, read_size)
        return bytes, memory_block_info.name


def execute_unsafe_read(
    location: OnChipCoordinate, address: int, bytes_to_read: int, risc_name: str | None
) -> tuple[bytes, str]:
    if risc_name is None:
        risc_debug = None
        memory_block_info = location.noc_block.noc_memory_map.find_by_noc_address(address)
        if memory_block_info is not None and memory_block_info.memory_block.address.noc_address is not None:
            memory_block_end = memory_block_info.memory_block.address.noc_address + memory_block_info.memory_block.size
            read_size = min(bytes_to_read, memory_block_end - address)
            bytes = location.noc_read(address, read_size)
            return bytes, memory_block_info.name
    else:
        risc_debug = location.noc_block.get_risc_debug(risc_name)
        memory_block_info = risc_debug.risc_info.memory_map.find_by_private_address(address)
        if memory_block_info is not None and memory_block_info.memory_block.address.private_address is not None:
            memory_block_end = (
                memory_block_info.memory_block.address.private_address + memory_block_info.memory_block.size
            )
            read_size = min(bytes_to_read, memory_block_end - address)
            if memory_block_info.memory_block.address.noc_address is not None:
                # Prefer reading over NOC if possible
                noc_address = memory_block_info.memory_block.address.noc_address + (
                    address - memory_block_info.memory_block.address.private_address
                )
                bytes = location.noc_read(noc_address, read_size)
            else:
                bytes = risc_debug.read_memory_bytes(address, read_size)
            return bytes, memory_block_info.name

    # Find end address of unknown block and limit read size to that
    if risc_debug is None:
        next_block_info = location.noc_block.noc_memory_map.find_next_by_noc_address(address)
        if next_block_info is not None and next_block_info.memory_block.address.noc_address is not None:
            next_block_start = next_block_info.memory_block.address.noc_address
            bytes_to_read = min(bytes_to_read, next_block_start - address)
    else:
        next_block_info = risc_debug.risc_info.memory_map.find_next_by_private_address(address)
        if next_block_info is not None and next_block_info.memory_block.address.private_address is not None:
            next_block_start = next_block_info.memory_block.address.private_address
            bytes_to_read = min(bytes_to_read, next_block_start - address)

    # Not found in known memory blocks, do direct read
    if risc_debug:
        with risc_debug.ensure_private_memory_access():
            bytes = risc_debug.read_memory_bytes(address, bytes_to_read)
    else:
        bytes = location.noc_read(address, bytes_to_read)
    return bytes, "???"
