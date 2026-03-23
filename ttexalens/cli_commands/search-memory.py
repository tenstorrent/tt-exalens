# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  search <pattern>... [--start <start>] [--end <end>] [--width <width>] [--read-size <rs>] [--max-results <n>] [--unsafe] [-r <risc_name>] [-d <device>] [-l <loc>]

Arguments:
  pattern         One or more integer values forming the byte pattern to search for.

Options:
  --start=<start>   Start address for the search. Defaults to 0, or to the start of RISC private memory if -r is specified.
  --end=<end>       End address (exclusive) or 'all'. If omitted, searches only the block containing --start.
                    'all' searches all blocks from --start onwards.
  --width=<width>   Bytes per pattern element (any positive integer) or auto. [default: auto]
                    auto = minimum power-of-2 byte count needed to represent the largest element,
                    applied uniformly to all elements.
  --read-size=<rs>  Maximum bytes per device read. Defaults to 4 when -r is used (RISC debug hardware),
                    or 1MB otherwise.
  --max-results=<n> Maximum number of matches to return, or 'all'. [default: 1]
  -r <risc_name>    RISC core name to search in private memory instead of NOC memory.
  --unsafe          Expert mode, allow searching everywhere (bypass safety checks).

Description:
  Searches for a byte pattern in device memory. Pattern elements are encoded as
  little-endian integers. With --width=auto (default), the width is determined once
  as the minimum power-of-2 byte count needed to represent the largest element, and
  applied uniformly to all elements.

Examples:
  search 0xDEADBEEF                              # Search for pattern in the block containing address 0
  search 0xDEADBEEF --end all                    # Search all accessible blocks
  search 0xDEADBEEF --start 0x10000 --end all    # Search all blocks from 0x10000 onwards
  search 0x1234 --start 0 --end 0xFFFF           # Search from address 0 to 0xFFFF
  search 0x1234 0x5678 --width 2                 # Search for two 2-byte LE values (0x34 0x12 0x78 0x56)
  search 0xDEADBEEF --read-size 64               # Search using 64-byte reads
  search 0xAB --unsafe                           # Search with safety checks bypassed
  search 0xBEEF -r brisc                         # Search brisc private memory (4-byte reads by default)
  search 0xBEEF -r brisc --read-size 256         # Search brisc private memory with 256-byte reads
"""

import math

from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.uistate import UIState
from ttexalens.coordinate import OnChipCoordinate
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions
from ttexalens.cli_commands.read import execute_safe_read, execute_unsafe_read

command_metadata = CommandMetadata(
    short_name="search",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)

_DEFAULT_READ_SIZE = 0x100000  # 1MB default for NOC reads
_DEFAULT_READ_SIZE_RISC = 4  # 4 bytes default for RISC debug hardware reads


def _auto_pattern_width(values: list[int]) -> int:
    """Return minimum power-of-2 byte count needed to represent the largest element in values."""

    def _min_bytes(v: int) -> int:
        n = max(1, math.ceil(v.bit_length() / 8))
        # Round up to the next power of 2
        return 1 << (n - 1).bit_length()

    return max(_min_bytes(v) for v in values)


def _build_pattern_bytes(values: list[int], width: int) -> bytes:
    """Convert pattern values to a byte string using little-endian encoding with a uniform width.

    Negative values are masked to the given width (two's-complement), so -1 at width 4
    produces the same bytes as 0xFFFFFFFF.
    """
    mask = (1 << (width * 8)) - 1
    result = b""
    for v in values:
        result += (v & mask).to_bytes(width, byteorder="little", signed=False)
    return result


def _find_in_data(data: bytes, pattern: bytes, base_addr: int, max_results: int | None = None) -> list[int]:
    """Return absolute addresses of occurrences of pattern in data, up to max_results (None = unlimited)."""
    matches = []
    start = 0
    while True:
        idx = data.find(pattern, start)
        if idx == -1:
            break
        matches.append(base_addr + idx)
        if max_results is not None and len(matches) >= max_results:
            break
        start = idx + 1
    return matches


def _get_noc_search_ranges(
    location: OnChipCoordinate, start_addr: int, end_addr: int | None, unsafe: bool
) -> list[tuple[int, int, str]]:
    """Return list of (range_start, range_end, block_name) for consecutive NOC blocks from start_addr.

    With unsafe=True and an explicit end_addr the block map is skipped entirely and a single
    raw range is returned.  Raises TTException if start_addr is not inside any known block.
    """
    if unsafe and end_addr is not None:
        return [(start_addr, end_addr, "???")]

    memory_map = location.noc_block.noc_memory_map
    ranges: list[tuple[int, int, str]] = []
    current = start_addr

    while end_addr is None or current < end_addr:
        block_info = memory_map.find_by_noc_address(current)
        if block_info is None:
            if not ranges:
                raise util.TTException(f"Address 0x{current:08x} is not in a known NOC memory block")
            break  # Gap after the last found block — stop here

        assert block_info.memory_block.address.noc_address is not None
        block_end = block_info.memory_block.address.noc_address + block_info.memory_block.size
        eff_end = block_end if end_addr is None else min(block_end, end_addr)
        ranges.append((current, eff_end, block_info.name))
        current = block_end

    return ranges


def _get_risc_search_ranges(
    location: OnChipCoordinate, risc_name: str, start_addr: int, end_addr: int | None, unsafe: bool
) -> list[tuple[int, int, str]]:
    """Return list of (range_start, range_end, block_name) for consecutive RISC private blocks from start_addr.

    With unsafe=True and an explicit end_addr the block map is skipped entirely and a single
    raw range is returned.  Raises TTException if start_addr is not inside any known block.
    """
    if unsafe and end_addr is not None:
        return [(start_addr, end_addr, "???")]

    risc_debug = location.noc_block.get_risc_debug(risc_name)
    memory_map = risc_debug.risc_info.memory_map
    ranges: list[tuple[int, int, str]] = []
    current = start_addr

    while end_addr is None or current < end_addr:
        block_info = memory_map.find_by_private_address(current)
        if block_info is None:
            if not ranges:
                raise util.TTException(f"Address 0x{current:08x} is not in a known {risc_name} private memory block")
            break  # Gap after the last found block — stop here

        assert block_info.memory_block.address.private_address is not None
        block_end = block_info.memory_block.address.private_address + block_info.memory_block.size
        eff_end = block_end if end_addr is None else min(block_end, end_addr)
        ranges.append((current, eff_end, block_info.name))
        current = block_end

    return ranges


def _search_in_range(
    location: OnChipCoordinate,
    range_start: int,
    range_end: int,
    block_name: str,
    pattern_bytes: bytes,
    unsafe: bool,
    risc_name: str | None,
    read_size: int,
    max_results: int | None,
) -> list[tuple[int, str]]:
    """
    Read memory in [range_start, range_end) in chunks and search for pattern_bytes.

    Returns list of (match_address, block_name) pairs. Handles patterns that span
    chunk boundaries by keeping a (len(pattern)-1) byte overlap between chunks.
    Stops early once max_results matches are collected (None means no limit).
    """
    matches: list[tuple[int, str]] = []
    overlap = len(pattern_bytes) - 1
    current_addr = range_start
    prev_tail = b""

    while current_addr < range_end:
        chunk_size = min(read_size, range_end - current_addr)
        try:
            if unsafe:
                data, _ = execute_unsafe_read(location, current_addr, chunk_size, risc_name)
            else:
                data, _ = execute_safe_read(location, current_addr, chunk_size, risc_name)
        except util.TTException as e:
            util.DEBUG(f"search: skipping 0x{current_addr:08x}: {e}")
            break

        if not data:
            break

        # Prepend tail of previous chunk so patterns spanning the boundary are found.
        # The base address of search_data = current_addr - len(prev_tail).
        search_data = prev_tail + data
        base = current_addr - len(prev_tail)

        # All positions in search_data correspond to unique, not-yet-reported addresses
        # (the math ensures no duplicates between iterations).
        remaining = None if max_results is None else max_results - len(matches)
        for match_addr in _find_in_data(search_data, pattern_bytes, base, remaining):
            matches.append((match_addr, block_name))
        if max_results is not None and len(matches) >= max_results:
            return matches

        prev_tail = search_data[-overlap:] if overlap > 0 else b""
        current_addr += len(data)

    return matches


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    # --- Parse pattern values ---
    pattern_strs: list[str] = args["<pattern>"]
    try:
        pattern_values = [int(v, 0) for v in pattern_strs]
    except ValueError as e:
        util.ERROR(f"Invalid pattern value: {e}")
        return

    # --- Parse --width ---
    width_str: str = args["--width"] if args["--width"] else "auto"
    if width_str == "auto":
        width = _auto_pattern_width(pattern_values)
    else:
        try:
            width = int(width_str)
        except ValueError:
            util.ERROR(f"Invalid --width value: {width_str!r}. Must be a positive integer or 'auto'.")
            return
        if width < 1:
            util.ERROR(f"--width must be at least 1, got {width_str!r}.")
            return

    try:
        pattern_bytes = _build_pattern_bytes(pattern_values, width)
    except (OverflowError, ValueError) as e:
        util.ERROR(f"Pattern value does not fit in the specified width: {e}")
        return

    if not pattern_bytes:
        util.ERROR("Pattern is empty.")
        return

    # --- Parse address range ---
    start_addr = int(args["--start"], 0) if args["--start"] else 0
    end_arg: str | None = args["--end"]

    end_all = end_arg == "all"
    end_addr: int | None = None
    if end_arg and not end_all:
        end_addr = int(end_arg, 0)
        if end_addr <= start_addr:
            util.ERROR(f"End address 0x{end_addr:08x} must be greater than start address 0x{start_addr:08x}.")
            return

    unsafe: bool = args["--unsafe"]
    risc_name: str | None = args["-r"]

    # --- Parse --read-size ---
    if args["--read-size"]:
        try:
            read_size = int(args["--read-size"], 0)
        except ValueError:
            util.ERROR(f"Invalid --read-size value: {args['--read-size']!r}. Must be a positive integer.")
            return
        if read_size < 1:
            util.ERROR(f"--read-size must be at least 1, got {read_size}.")
            return
    else:
        read_size = _DEFAULT_READ_SIZE_RISC if risc_name else _DEFAULT_READ_SIZE

    # --- Parse --max-results ---
    max_results_arg: str = args["--max-results"] if args["--max-results"] else "1"
    if max_results_arg == "all":
        max_results: int | None = None
    else:
        try:
            max_results = int(max_results_arg)
        except ValueError:
            util.ERROR(f"Invalid --max-results value: {max_results_arg!r}. Must be a positive integer or 'all'.")
            return
        if max_results < 1:
            util.ERROR(f"--max-results must be at least 1, got {max_results_arg!r}.")
            return

    # --- Display pattern summary ---
    pattern_hex = " ".join(f"0x{b:02x}" for b in pattern_bytes)
    util.INFO(f"Searching for pattern [{pattern_hex}] ({len(pattern_bytes)} byte(s))")

    device: Device
    location: OnChipCoordinate
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        device_id_str = f"{device.id}"
        if device.unique_id is not None:
            device_id_str += f" [0x{device.unique_id:x}]"

        for location in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            location_str = location.to_user_str()

            try:
                if risc_name:
                    ranges = _get_risc_search_ranges(location, risc_name, start_addr, end_addr, unsafe)
                else:
                    ranges = _get_noc_search_ranges(location, start_addr, end_addr, unsafe)
            except util.TTException as e:
                util.ERROR(f"Device {device_id_str} | Location {location_str}: {e}")
                continue

            if not ranges:
                util.INFO(f"Device {device_id_str} | Location {location_str}: no accessible memory in search range.")
                continue

            all_matches: list[tuple[int, str]] = []
            for r_start, r_end, block_name in ranges:
                remaining = None if max_results is None else max_results - len(all_matches)
                block_matches = _search_in_range(
                    location, r_start, r_end, block_name, pattern_bytes, unsafe, risc_name, read_size, remaining
                )
                all_matches.extend(block_matches)
                if max_results is not None and len(all_matches) >= max_results:
                    break

            header = f"Device {device_id_str} | Location {location_str}"
            if all_matches:
                util.INFO(f"{header}: {len(all_matches)} match(es) found:")
                for match_addr, block_name in all_matches:
                    print(f"  0x{match_addr:08x}  ({block_name})")
            else:
                util.INFO(f"{header}: pattern not found.")
