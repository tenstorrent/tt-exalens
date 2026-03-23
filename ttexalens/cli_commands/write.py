# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  write <address> <data>... [ --width=<width> ] [ --repeat=<repeat> ] [ --unsafe ] [ -r <risc_name> ] [ -d <device> ] [ -l <loc> ]

Arguments:
  address         Address to write to
  data            One or more data values to write

Options:
  --width=<width>   Number of bytes per data value, or 'auto' to use the minimum power-of-2 width
                    that fits all values. [default: auto]
  --repeat=<repeat> Number of times to repeat the write, advancing the address each time. [default: 1]
  -r <risc_name>    RISC core name if you want to write memory that is not exposed on NOC.
  --unsafe          Experts mode, allow writing everything (bypass safety checks).

Description:
  Writes a block of data to address 'address'.

Examples:
  write 0x0 0xdeadbeef                        # Write 1 word (4 bytes) to address 0
  write 0x0 0x1 0x2 0x3                       # Write 3 bytes to address 0
  write 0x0 0x12 0x34 --width 2               # Write 4 bytes to address 0
  write 0x0 0xdeadbeef --repeat 4             # Write the same word to 4 consecutive addresses
  write 0xFFB0000 0xdeadbeef -r brisc         # Write 1 word to brisc private data memory
"""

from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.uistate import UIState

from ttexalens.coordinate import OnChipCoordinate
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="w",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)


def _auto_width(values: list[int]) -> int:
    """Return the minimum power-of-2 byte width that fits all values."""
    max_val = max((abs(v) for v in values), default=0)
    min_bytes = max(1, (max_val.bit_length() + 7) // 8)
    width = 1
    while width < min_bytes:
        width *= 2
    return width


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    address = int(args["<address>"], 0)
    data_values = [int(v, 0) for v in args["<data>"]]
    width_arg = args["--width"]
    if width_arg and width_arg != "auto":
        bytes_per_entry = int(width_arg)
        if bytes_per_entry < 1:
            util.ERROR(f"Invalid width '{bytes_per_entry}'. Width must be a positive integer.")
            return
    else:
        bytes_per_entry = _auto_width(data_values)
    repeat = int(args["--repeat"]) if args["--repeat"] else 1
    if repeat <= 0:
        util.WARN("Repeat count must be a positive integer, defaulting to 1")
        repeat = 1
    unsafe = args["--unsafe"]
    risc_name = args["-r"]

    # Convert data arguments to bytes using little-endian packing
    mask = (1 << (bytes_per_entry * 8)) - 1
    write_data = bytearray()
    for val in data_values:
        write_data.extend((val & mask).to_bytes(bytes_per_entry, byteorder="little"))
    write_data *= repeat

    total_bytes = len(write_data)

    device: Device
    location: OnChipCoordinate
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        device_id_str = f"{device.id}"
        if device.unique_id is not None:
            device_id_str += f" [0x{device.unique_id:x}]"
        for location in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            location_str = location.to_user_str()
            write_address = address
            written_bytes = 0
            data_offset = 0
            while written_bytes < total_bytes:
                chunk = bytes(write_data[data_offset : data_offset + (total_bytes - written_bytes)])
                if unsafe:
                    chunk_written, memory_block_name = execute_unsafe_write(location, write_address, chunk, risc_name)
                else:
                    chunk_written, memory_block_name = execute_safe_write(location, write_address, chunk, risc_name)
                util.INFO(
                    f"Device {device_id_str} | Location {location_str} | Block {memory_block_name} : 0x{write_address:08x} ({chunk_written} bytes written)"
                )
                write_address += chunk_written
                written_bytes += chunk_written
                data_offset += chunk_written


def execute_safe_write(location: OnChipCoordinate, address: int, data: bytes, risc_name: str | None) -> tuple[int, str]:
    if risc_name is None:
        memory_block_info = location.noc_block.noc_memory_map.find_by_noc_address(address)
        if not memory_block_info:
            raise util.TTException(f"Address 0x{address:08X} is not in a known memory block for location {location}")
        if memory_block_info.memory_block.address.noc_address is None:
            raise util.TTException(f"Memory block '{memory_block_info.name}' does not have a NOC address")
        memory_block_end = memory_block_info.memory_block.address.noc_address + memory_block_info.memory_block.size
        write_size = min(len(data), memory_block_end - address)
        location.noc_write(address, data[:write_size])
        return write_size, memory_block_info.name
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
        write_size = min(len(data), memory_block_end - address)
        if memory_block_info.memory_block.address.noc_address is not None:
            # Prefer writing over NOC if possible
            noc_address = memory_block_info.memory_block.address.noc_address + (
                address - memory_block_info.memory_block.address.private_address
            )
            location.noc_write(noc_address, data[:write_size])
        else:
            risc_debug.write_memory_bytes(address, data[:write_size])
        return write_size, memory_block_info.name


def execute_unsafe_write(
    location: OnChipCoordinate, address: int, data: bytes, risc_name: str | None
) -> tuple[int, str]:
    if risc_name is None:
        risc_debug = None
        memory_block_info = location.noc_block.noc_memory_map.find_by_noc_address(address)
        if memory_block_info is not None and memory_block_info.memory_block.address.noc_address is not None:
            memory_block_end = memory_block_info.memory_block.address.noc_address + memory_block_info.memory_block.size
            write_size = min(len(data), memory_block_end - address)
            location.noc_write(address, data[:write_size], safe_mode=False)
            return write_size, memory_block_info.name
    else:
        risc_debug = location.noc_block.get_risc_debug(risc_name)
        memory_block_info = risc_debug.risc_info.memory_map.find_by_private_address(address)
        if memory_block_info is not None and memory_block_info.memory_block.address.private_address is not None:
            memory_block_end = (
                memory_block_info.memory_block.address.private_address + memory_block_info.memory_block.size
            )
            write_size = min(len(data), memory_block_end - address)
            if memory_block_info.memory_block.address.noc_address is not None:
                # Prefer writing over NOC if possible
                noc_address = memory_block_info.memory_block.address.noc_address + (
                    address - memory_block_info.memory_block.address.private_address
                )
                location.noc_write(noc_address, data[:write_size], safe_mode=False)
            else:
                risc_debug.write_memory_bytes(address, data[:write_size], safe_mode=False)
            return write_size, memory_block_info.name

    # Find end address of unknown block and limit write size to that
    if risc_debug is None:
        next_block_info = location.noc_block.noc_memory_map.find_next_by_noc_address(address)
        if next_block_info is not None and next_block_info.memory_block.address.noc_address is not None:
            next_block_start = next_block_info.memory_block.address.noc_address
            data = data[: min(len(data), next_block_start - address)]
    else:
        next_block_info = risc_debug.risc_info.memory_map.find_next_by_private_address(address)
        if next_block_info is not None and next_block_info.memory_block.address.private_address is not None:
            next_block_start = next_block_info.memory_block.address.private_address
            data = data[: min(len(data), next_block_start - address)]

    # Not found in known memory blocks, do direct write
    if risc_debug:
        with risc_debug.ensure_private_memory_access():
            risc_debug.write_memory_bytes(address, data, safe_mode=False)
    else:
        location.noc_write(address, data, safe_mode=False)
    return len(data), "???"
