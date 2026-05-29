# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  search <pattern>... [--start <start>] [--end <end>] [--width <width>] [--read-size <rs>] [--max-results <n>] [--unsafe] [-r <risc_name>] [-d <device>] [-l <loc>]

Arguments:
  pattern         One or more integer values forming the byte pattern to search for.

Options:
  --start=<start>    Start address for the search. Defaults to 0, or to the start of RISC private memory if -r is specified.
  --end=<end>        End address (exclusive) or 'all'. If omitted, searches only the block containing --start.
                     'all' searches all contiguous blocks from --start onwards.
  --width=<width>    Bytes per pattern element (any positive integer) or auto. [default: auto]
                     auto = minimum power-of-2 byte count needed to represent the largest element,
                     applied uniformly to all elements.
  --read-size=<rs>   Maximum bytes per device read. Defaults to 4 when -r is used (RISC debug hardware),
                     or 1MB otherwise.
  --max-results=<n>  Limit the number of matches displayed, or 'all' to show every match. [default: 1]
  -r <risc_name>     RISC core name to search in private memory instead of NOC memory.
  --unsafe           Expert mode, allow searching everywhere (bypass safety checks).

Description:
  Searches for a byte pattern in device memory. Pattern elements are encoded as
  little-endian integers. With --width=auto (default), the width is determined once
  as the minimum power-of-2 byte count needed to represent the largest element, and
  applied uniformly to all elements.

Examples:
  search 0xDEADBEEF                              # Search for pattern in the block containing address 0
  search 0xDEADBEEF --end all                    # Search all contiguous blocks from address 0
  search 0xDEADBEEF --start 0x10000 --end all    # Search all contiguous blocks from 0x10000 onwards
  search 0x1234 --start 0 --end 0xFFFF           # Search from address 0 to 0xFFFF
  search 0x1234 0x5678 --width 2                 # Search for two 2-byte LE values (0x34 0x12 0x78 0x56)
  search 0xDEADBEEF --read-size 64               # Search using 64-byte reads
  search 0xAB --unsafe                           # Search with safety checks bypassed
  search 0xBEEF -r brisc                         # Search brisc private memory
  search 0xBEEF -r brisc --read-size 256         # Search brisc private memory with 256-byte reads
"""

import math

from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.uistate import UIState
from ttexalens.coordinate import OnChipCoordinate
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions
from ttexalens.tt_exalens_lib import search_memory

command_metadata = CommandMetadata(
    short_name="search",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)


def _auto_pattern_width(values: list[int]) -> int:
    """Return minimum power-of-2 byte count needed to represent the largest element in values."""

    def _min_bytes(v: int) -> int:
        n = max(1, math.ceil(v.bit_length() / 8))
        return 1 << (n - 1).bit_length()

    return max(_min_bytes(v) for v in values)


def _build_pattern_bytes(values: list[int], width: int) -> bytes:
    """Convert pattern values to little-endian bytes with uniform width."""
    mask = (1 << (width * 8)) - 1
    result = b""
    for v in values:
        result += (v & mask).to_bytes(width, byteorder="little", signed=False)
    return result


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

    end_addr: int | str | None = None  # None → single block (default)
    if end_arg == "all":
        end_addr = "all"
    elif end_arg:
        end_addr = int(end_arg, 0)
        if end_addr <= start_addr:
            util.ERROR(f"End address 0x{end_addr:08x} must be greater than start address 0x{start_addr:08x}.")
            return

    unsafe: bool = args["--unsafe"]
    risc_name: str | None = args["-r"]

    # --- Parse --read-size ---
    read_size: int | None = None
    if args["--read-size"]:
        try:
            read_size = int(args["--read-size"], 0)
            if read_size < 1:
                raise ValueError
        except ValueError:
            util.ERROR(f"Invalid --read-size value: {args['--read-size']!r}. Must be a positive integer.")
            return

    # --- Parse --max-results ---
    max_results_arg: str = args["--max-results"] if args["--max-results"] else "1"
    max_results: int | None  # None means unlimited
    if max_results_arg == "all":
        max_results = None
    else:
        try:
            max_results = int(max_results_arg)
            if max_results < 1:
                raise ValueError
        except ValueError:
            util.ERROR(f"Invalid --max-results value: {max_results_arg!r}. Must be a positive integer or 'all'.")
            return

    # --- Display pattern summary ---
    pattern_hex = " ".join(f"0x{b:02x}" for b in pattern_bytes)
    util.INFO(f"Searching for pattern [{pattern_hex}] ({len(pattern_bytes)} byte(s))")

    safe_mode_arg = False if unsafe else None

    device: Device
    location: OnChipCoordinate
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        device_id_str = f"{device.id}"
        if device.unique_id is not None:
            device_id_str += f" [0x{device.unique_id:x}]"

        for location in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            location_str = location.to_user_str()

            try:
                all_matches: list = []
                current_start = start_addr
                while True:
                    matches, next_addr = search_memory(
                        location,
                        pattern_bytes,
                        risc_name=risc_name,
                        start_addr=current_start,
                        end_addr=end_addr,
                        device_id=device.id,
                        context=context,
                        chunk_size=read_size,
                        safe_mode=safe_mode_arg,
                    )
                    all_matches.extend(matches)
                    if next_addr is None or (max_results is not None and len(all_matches) >= max_results):
                        break
                    current_start = next_addr
            except util.TTException as e:
                util.ERROR(f"Device {device_id_str} | Location {location_str}: {e}")
                continue

            if max_results is not None:
                all_matches = all_matches[:max_results]

            header = f"Device {device_id_str} | Location {location_str}"
            if all_matches:
                util.INFO(f"{header}: {len(all_matches)} match(es) found:")
                for match_addr, block_name in all_matches:
                    print(f"  0x{match_addr:08x}  ({block_name})")
            else:
                util.INFO(f"{header}: pattern not found.")
