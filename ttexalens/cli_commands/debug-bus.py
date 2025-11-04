# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  debug-bus list-signals [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s]
  debug-bus list-groups [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s]
  debug-bus group <group-name> <l1-address> [--samples <num>] [--sampling-interval <cycles>] [--search <pattern>] [-d <device>] [-l <loc>] [-s]
  debug-bus <signals> [-d <device>] [-l <loc>] [-s]

Options:
    -s, --simple                        Print simple output.
    --search <pattern>                  Search for signals by pattern (in wildcard format).
    --max <max-sigs>                    Limit --search output (default: 10, use --max "all" to print all matches). [default: 10].
    --samples <num>                     (L1 sampling only) Number of 128-bit samples to capture. [default: 1]
    --sampling-interval <cycles>        (L1 sampling only, if --samples > 1) Delay in clock cycles between samples. Must be 2-256.[ default: 2]

Description:
  Commands for RISC-V debugging:
    - list-signals:    List all predefined debug bus signal names.
        --search:    Search for signals by pattern (wildcard format)
        --max:       Limit number of results
    - list-groups:   List all debug bus signal groups.
        --search:    Search for groups by pattern (wildcard format)
        --max:       Limit number of results
    - group <group-name> <l1-address>:   List all signals in group using L1 sampling
        --search:    Search for signals by pattern (wildcard format)
        --samples:   Number of samples
        --sampling-interval: Delay between samples
        <l1-address>:      Byte address in L1 memory for L1 sampling mode (must be 16-byte aligned).
                                Enables L1 sampling: signal(s) are captured as 128-bit words to L1 memory at the given address
                                instead of direct 32-bit register read. Each sample uses 16 bytes. All samples must fit in the first 1 MiB (0x0 - 0xFFFFF).

    - [<signals>]:   List of signals described by signal name or signal description.
        <signal-description>: {DaisyId,RDSel,SigSel,Mask}
            - DaisyId   - daisy chain identifier
            - RDSel     - select 32bit data in 128bit register (values 0-3)
            - SigSel    - select 128bit register
            - Mask      - 32bit mask for significant bits (optional)

Examples:
  debug-bus list-signals                                        # List up to 10 predefined debug bus signals (default max)
  debug-bus list-signals --max all                              # List all predefined debug bus signals
  debug-bus list-signals --search *pc* --max 5                  # List up to 5 signals whose names contain 'pc'
  debug-bus list-groups                                         # List all debug bus signal groups
  debug-bus list-groups --search *brisc*                        # List groups whose names match pattern 'brisc'
  debug-bus group brisc_group_a 0x1000 --samples 4 --sampling-interval 10 # List all signals in group 'brisc_group_a' using L1 sampling, 4 samples, 10 cycles interval
  debug-bus group brisc_group_a 0x1000 --search *pc             # List all signals in group 'brisc_group_a' that ends with 'pc' using L1 sampling
  debug-bus trisc0_pc,trisc1_pc                                 # Print values for trisc0_pc and trisc1_pc
  debug-bus {7,0,12,0x3ffffff},trisc2_pc                        # Print value for a custom signal and trisc2_pc
"""

command_metadata = {
    "short": "dbus",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc", "--verbose"],
}

import re
from typing import Any

from ttexalens.command_parser import tt_docopt
from ttexalens import util as util
from ttexalens.util import search
from ttexalens.rich_formatters import formatter
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.uistate import UIState
from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.coordinate import OnChipCoordinate


def _format_signal_value(value, show_all_samples=False, signal_desc=None):
    """
    Format signal value for display:
    - 1-bit signals as True/False
    - multi-bit signals as hexadecimal (0x...)
    - can display a single value or a list of samples
    """

    def is_single_bit(mask):
        return mask is not None and (mask & (mask - 1)) == 0

    def fmt(v):
        """
        Format a single sample value `v`:
        - If the signal has a mask and it's a single bit, return "True" or "False"
        - Otherwise, return the value in hexadecimal (without leading zeros)
        """
        mask_value = getattr(signal_desc, "mask", None)
        if is_single_bit(mask_value):
            return "True" if v else "False"
        return f"0x{v:x}"

    if isinstance(value, list):
        formatted = [fmt(v) for v in value]
        return f"[{', '.join(formatted)}]" if show_all_samples else formatted[0]
    return fmt(value)


def parse_string(input_string: str) -> list[list[int] | str]:
    """Parse input string to extract signal descriptions and signal names."""
    # Regex pattern with groups:
    # group(0): entire match
    # group(1): first number in {num,num,num,num} format
    # group(2): second number
    # group(3): third number
    # group(4): fourth number (optional, may be None)
    # group(5): signal name (when not in {} format)
    pattern = r"\{([\dA-Fa-fx]+),([\dA-Fa-fx]+),([\dA-Fa-fx]+)(?:,([\dA-Fa-fx]+))?\}|([A-Za-z_][A-Za-z0-9_/#]*)"

    parsed_result: list[list[int] | str] = []

    for match in re.finditer(pattern, input_string):
        if match.group(1):
            # Matched {num,num,num,num} format - extract numbers from groups 1-4
            numbers = [int(match.group(i), 0) for i in range(1, 4)]
            fourth_number = int(match.group(4), 0) if match.group(4) else 0xFFFFFFFF
            numbers.append(fourth_number)
            parsed_result.append(numbers)
        else:
            # Matched signal name format - group(5) contains the signal name
            parsed_result.append(match.group(5))

    return parsed_result


def parse_command_arguments(args):
    """
    Processes a list of signals provided in `args` and returns a list containing either
    string signals or `DebugBusSignalDescription` objects.

    Parameters:
        args (dict): A dictionary containing a key "signals" which maps to a list of items.
                     Each item can be:
                     - A string (which is added to the result as is).
                     - A list of four elements, expected to represent:
                       {index, name, width, offset}, used to create a `DebugBusSignalDescription` object.

    Returns:
        list: A list containing either strings or `DebugBusSignalDescription` objects.

    Raises:
        ValueError: If a signal list has an invalid format that prevents the creation of a `DebugBusSignalDescription` object.
    """
    if args["<signals>"] is None:
        raise ValueError("Missing debug bus signal parameter")

    result: list[str | DebugBusSignalDescription] = []
    signals = parse_string(args["<signals>"])

    for item in signals:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, list):
            try:
                signal_description = DebugBusSignalDescription(item[1], item[0], item[2], item[3])
                result.append(signal_description)
            except ValueError as e:
                raise ValueError(f"Invalid signal description format: {e}")

    return result


def _get_group_for_signal(signal_store: DebugBusSignalStore, signal: str) -> str:
    """Get the group name for a given signal name."""
    for group_name, group_dict in signal_store.signal_groups.items():
        if signal_store.get_base_signal_name(signal) in group_dict:
            return group_name

    return ""


def _get_signal_part_names(debug_bus_signal_store: DebugBusSignalStore, base_name: str) -> list[str]:
    """Get all part names for a combined signal based on its base name. Does not guarantee order."""
    if not debug_bus_signal_store.is_combined_signal(base_name):
        return [base_name]

    part_names: list[str] = []
    for signal_name in debug_bus_signal_store.signal_names:
        if signal_name.startswith(f"{base_name}/"):
            part_names.append(signal_name)

    return part_names


def _get_debug_bus_signal_store(device: Device, loc: OnChipCoordinate) -> DebugBusSignalStore | None:
    """Return debug bus signal store for given device and location, or None if unavailable."""
    noc_block = device.get_block(loc)
    if not noc_block:
        util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a NOC block.")
        return None

    debug_bus_signal_store = noc_block.debug_bus
    if debug_bus_signal_store is None:
        util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a debug bus.")
        return None

    return debug_bus_signal_store


def handle_list_signals_command(device: Device, loc: OnChipCoordinate, params: dict[str, Any]) -> None:
    """Handle the list-signals command: list all debug bus signals for the device/location."""
    debug_bus_signal_store = _get_debug_bus_signal_store(device, loc)
    if debug_bus_signal_store is None:
        return

    # Get all signal names
    names: list[str] = list(debug_bus_signal_store.signal_names)
    max_arg: str = "all"
    if params["max"] is not None:
        max_arg = params["max"]

    # Filter signal names by search pattern
    if params["search"] is not None:
        search_arg: str = params["search"]
        names = search(names, search_arg, max_arg)
        if len(names) == 0:
            print("No matches found.")
            return

    signal_data: list[tuple[str, str, str]] = []
    # Read and format each signal value
    for name in names:
        value = debug_bus_signal_store.read_signal(name)
        formatted_value = _format_signal_value(
            value,
            show_all_samples=False,
            signal_desc=debug_bus_signal_store.signals.get(name, None),
        )
        group_name = _get_group_for_signal(debug_bus_signal_store, name)
        signal_data.append((group_name, name, formatted_value))

    # Sort by group and signal name
    signal_data.sort(key=lambda x: (x[0], x[1]))

    # Limit number of displayed signals
    if max_arg is not None and str(max_arg).lower() != "all":
        try:
            max_count = int(max_arg)
            signal_data = signal_data[:max_count]
        except Exception:
            pass

    # Display results
    formatter.print_header(f"=== Device {device._id} - location {loc.to_str('logical')})", style="bold")
    formatter.display_grouped_data(
        {"Signals": signal_data},
        [("Group", ""), ("Name", ""), ("Value", "")],
        [["Signals"]],
        simple_print=params["simple"],
    )


def handle_list_groups_command(device: Device, loc: OnChipCoordinate, params: dict[str, Any]) -> None:
    """Handle the list-groups command - list all groups or signals in a specific group."""
    debug_bus_signal_store = _get_debug_bus_signal_store(device, loc)
    if debug_bus_signal_store is None:
        return

    names: list[str] = list(debug_bus_signal_store.group_names)
    max_arg: str = "all"
    if params["max"] is not None:
        max_arg = params["max"]

    # Filter group names by search pattern
    if params["search"] is not None:
        search_arg: str = params["search"]
        names = search(names, search_arg, max_arg)
        if len(names) == 0:
            print("No matches found.")
            return
    elif max_arg is not None and str(max_arg).lower() != "all":
        names = names[: int(max_arg)]

    # Handle case of no groups
    if len(names) == 0:
        formatter.print_header(
            f"=== Device {device._id} - location {loc.to_str('logical')} - Signal Groups ===", style="bold"
        )
        print("No signal groups available.")
        return

    # Display results
    formatter.print_header(
        f"=== Device {device._id} - location {loc.to_str('logical')} - Signal Groups ===", style="bold"
    )
    formatter.display_grouped_data(
        {"Groups": [(name,) for name in names]},
        [("Group Name", "")],
        [["Groups"]],
        simple_print=params["simple"],
    )


def handle_group_reading_command(device: Device, loc: OnChipCoordinate, params: dict[str, Any]) -> None:
    """Handle the 'dbus group' command: read all signals in specified group using L1 sampling."""
    debug_bus_signal_store = _get_debug_bus_signal_store(device, loc)
    if debug_bus_signal_store is None:
        return

    group_name: str = params["group-name"]
    l1_address: int = params["l1-address"]
    samples: int = params["samples"] or 1
    sampling_interval: int = params["sampling-interval"] or 2

    if samples == 1 and params.get("sampling-interval") is not None:
        util.WARN("Sampling interval is ignored when --samples=1.")

    # Read all signals in the group using L1 sampling
    signal_group_sample = debug_bus_signal_store.sample_signal_group(
        group_name,
        l1_address,
        samples=samples,
        sampling_interval=sampling_interval,
    )

    if not signal_group_sample:
        print("No signals read from group.")
        return

    # Get all signal names from the first sample
    signal_names = list(signal_group_sample[0].keys())
    if params.get("search"):
        signal_names = search(signal_names, params["search"])
        if not signal_names:
            print("No matches found.")
            return

    # Format all signals, showing all samples
    formatted_data = []
    for signal_name in signal_names:
        # Collect all samples for this signal
        signal_values = [sample[signal_name] for sample in signal_group_sample]
        formatted_value = _format_signal_value(
            signal_values,
            show_all_samples=samples > 1,
            signal_desc=debug_bus_signal_store.signals.get(signal_name),
        )
        formatted_data.append((signal_name, formatted_value))

    # Display results
    header = f"=== Device {device._id} - location {loc.to_str('logical')} - Group: {group_name} ==="
    formatter.print_header(header, style="bold")
    formatter.display_grouped_data(
        {group_name: formatted_data},
        [("Name", ""), ("Value", "")],
        [[group_name]],
        simple_print=params["simple"],
    )


def handle_signal_reading_command(device: Device, loc: OnChipCoordinate, params: dict[str, Any]) -> None:
    """Handle signal reading commands - read specific signals with optional L1 sampling."""
    debug_bus_signal_store = _get_debug_bus_signal_store(device, loc)
    if debug_bus_signal_store is None:
        return

    where = f"device:{device._id} loc:{loc.to_user_str()} "
    for signal in params["signals"]:
        try:
            if isinstance(signal, str) and debug_bus_signal_store.is_combined_signal(signal):
                util.WARN(
                    f"Signal '{signal}' is a combined signal. For consistent reading, use L1 sampling mode. "
                    "Only parts can be read in this mode, and their values may be inconsistent due to hardware implementation.\n"
                    "The parts are listed below:"
                )
                for s in _get_signal_part_names(debug_bus_signal_store, signal):
                    print(s)
                return

            value = debug_bus_signal_store.read_signal(signal)
            _display_signal_value(where, signal, value)

        except ValueError as e:
            util.ERROR(f"Error reading signal '{signal}': {e}")
            return


def _display_signal_value(where: str, signal: str | DebugBusSignalDescription, value):
    """Display signal value(s) in a simple format."""

    def signal_desc_str(sig):
        return (
            f"Daisy:{sig.daisy_sel}; Rd Sel:{sig.rd_sel}; Sig Sel:{sig.sig_sel}; Mask:0x{sig.mask:x}"
            if isinstance(sig, DebugBusSignalDescription)
            else str(sig)
        )

    if isinstance(value, list):
        for i, v in enumerate(value):
            print(f"{where} {signal_desc_str(signal)} [sample {i}]: 0x{v:x}")
    else:
        print(f"{where} {signal_desc_str(signal)}: 0x{value:x}")


def run(cmd_text: str, context: Context, ui_state: UIState):
    """Main entry point for debug-bus command."""
    dopt = tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    # Route to appropriate handler based on command
    if dopt.args["list-signals"]:
        command_handler = handle_list_signals_command
    elif dopt.args["list-groups"]:
        command_handler = handle_list_groups_command
    elif dopt.args["group"] and dopt.args["<group-name>"] and dopt.args["<l1-address>"]:
        command_handler = handle_group_reading_command
    else:
        command_handler = handle_signal_reading_command

    # Collect parameters for the command
    params: dict[str, Any] = {
        "search": dopt.args.get("--search") or None,
        "max": dopt.args.get("--max") or None,
        "samples": int(dopt.args["--samples"]) if dopt.args.get("--samples") is not None else None,
        "sampling-interval": int(dopt.args["--sampling-interval"])
        if dopt.args.get("--sampling-interval") is not None
        else None,
        "group-name": dopt.args.get("<group-name>") if dopt.args["<group-name>"] is not None else None,
        "l1-address": int(dopt.args["<l1-address>"], 0) if dopt.args["<l1-address>"] is not None else None,
        "signals": parse_command_arguments(dopt.args) if dopt.args["<signals>"] is not None else None,
        "simple": dopt.args["--simple"] or None,
    }

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            command_handler(device, loc, params)
