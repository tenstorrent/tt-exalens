# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  debug-bus list-names [-v] [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s]
  debug-bus list-groups [-v] [-d <device>] [-l <loc>] [--search <pattern>] [--group <group-name>] [-s]
  debug-bus [<signals>] [-v] [-d <device>] [-l <loc>] [--l1-sampling --l1-address <addr> [--samples <num>] [--sampling-interval <cycles>]]

Options:
    -s, --simple                        Print simple output.
    --search <pattern>                  Search for signals by pattern (in wildcard format).
    --max <max-sigs>                    Limit --search output (default: 10, use --max "all" to print all matches).
    --group <group-names>               (list-groups only) List signals in the specified group(s). Multiple groups can be separated by commas.
    --l1-sampling                       Enable sampling into L1 memory. Instead of a direct 32-bit register read,
                                        this triggers a 128-bit capture of the signal into the core's L1 memory.
    --l1-address <addr>                 (L1-sampling only) Byte address in L1 memory for sampling. Must be 16-byte aligned. 
                                        Each sample occupies 16 bytes (128 bits) in L1 memory. All samples must fit within 
                                        the first 1 MiB of L1 memory (0x0 - 0xFFFFF). Required when using --l1-sampling.
    --samples <num>                     (L1-sampling only) Number of 128-bit samples to capture. [default: 1].
    --sampling-interval <cycles>        (L1-sampling only) When samples > 1, this sets the delay in clock cycles
                                        between each sample. Must be between 2 and 256. [default: 2].

Description:
  Commands for RISC-V debugging:
    - list-names:    List all predefined debug bus signal names.
        --search:
    - list-groups:   List all debug bus signal groups or signals in a specific group.
        --group:     Show signals in a specific group
        --search:    Search for groups by pattern (in wildcard format)
    - [<signals>]:   List of signals described by signal name or signal description.
        <signal-description>: {DaisyId,RDSel,SigSel,Mask}
            -DaisyId - daisy chain identifier
            -RDSel   - select 32bit data in 128bit register -> values [0-3]
            -SigSel  - select 128bit register
            -Mask    - 32bit number to show only significant bits (optional)

Examples:
  debug-bus list-names                        # List predefined debug bus signals
  debug-bus list-names --search *pc* --max 5  # List up to 5 signals whose names contain pc
  debug-bus list-groups                       # List all debug bus signal groups
  debug-bus list-groups --search *brisc*      # List groups matching pattern
  debug-bus list-groups --group brisc_group_a # List all signals in brisc_group_a
  debug-bus list-groups --group brisc_group_a,trisc0_group_a,trisc1_group_a # List signals from multiple groups
  debug-bus trisc0_pc,trisc1_pc               # Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
  debug-bus {7,0,12,0x3ffffff},trisc2_pc      # Prints custom debug bus signal and trisc2_pc
  debug-bus trisc0_pc --l1-sampling --l1-address 0x1000 --samples 5 --sampling-interval 10 # Read trisc0_pc using L1 sampling 5 times with 10 cycle interval
  debug-bus trisc0_pc --l1-sampling --l1-address 0x2000 --samples 3    # Read trisc0_pc using L1 sampling at address 0x2000
"""

command_metadata = {
    "short": "dbus",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc", "--verbose"],
}

import re

from ttexalens import command_parser
from ttexalens import util as util
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.util import search
from ttexalens.rich_formatters import formatter
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription
from ttexalens.device import Device
from ttexalens.uistate import UIState


def parse_string(input_string):
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
        ValueError: If a signal list has an invalid format that prevents the creation of
                    a `DebugBusSignalDescription` object.
    """
    if not (args.get("<signals>")):
        raise ValueError("Missing debug bus signal parameter")

    result: list[str | DebugBusSignalDescription] = []

    signals = parse_string(args.get("<signals>"))

    for item in signals:
        if isinstance(item, str):  # It's a string
            result.append(item)
        elif isinstance(item, list):  # It's a list of numbers
            try:
                signal_description = DebugBusSignalDescription(item[1], item[0], item[2], item[3])
                result.append(signal_description)
            except ValueError as e:
                raise ValueError(f"Invalid signal description format: {e}")

    return result


def parse_group_names(group_string):
    """Parse comma-separated group names from input string."""
    if not group_string:
        return []
    
    # Simple split for group names (no complex {num,num,num} format needed)
    group_names = [name.strip() for name in group_string.split(',')]
    # Remove empty strings
    return [name for name in group_names if name]


def handle_list_names_command(dopt, context, ui_state):
    """Handle the list-names command - list all signal names with optional search."""
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            noc_block = device.get_block(loc)
            if not noc_block:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a NOC block.")
                continue
            debug_bus_signal_store = noc_block.debug_bus
            if not debug_bus_signal_store:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a debug bus.")
                continue
            
            names = debug_bus_signal_store.get_signal_names()

            # Apply search filter if provided
            if dopt.args["--search"]:
                max = dopt.args["--max"] if dopt.args["--max"] else 10
                names = search(list(names), dopt.args["--search"], max)
                if len(names) == 0:
                    print("No matches found.")
                    return []

            # Read signal values and convert to list of tuples
            signal_data = []
            for name in names:
                value = debug_bus_signal_store.read_signal(name)
                signal_data.append((name, f"0x{value:08x}"))
            
            # Display results in formatted table
            formatter.print_header(f"=== Device {device._id} - location {loc.to_str('logical')})", style="bold")
            formatter.display_grouped_data(
                {"Signals": signal_data},
                [("Name", ""), ("Value", "")],
                [["Signals"]],
                simple_print=dopt.args["--simple"],
            )
    return []


def handle_list_groups_command(dopt, context, ui_state):
    """Handle the list-groups command - list all groups or signals in a specific group."""
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            noc_block = device.get_block(loc)
            if not noc_block:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a NOC block.")
                continue
            debug_bus_signal_store = noc_block.debug_bus
            if not debug_bus_signal_store:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a debug bus.")
                continue

            if dopt.args["--group"]:
                # Show signals in specified group(s)
                group_names = parse_group_names(dopt.args["--group"])
                if not group_names:
                    util.ERROR("No valid group names provided.")
                    continue
                
                # Process each group
                for group_name in group_names:
                    try:
                        signal_names = debug_bus_signal_store.get_signals_in_group(group_name)
                        
                        # Read signal values and convert to list of tuples
                        signal_data = []
                        for name in signal_names:
                            value = debug_bus_signal_store.read_signal(name)
                            signal_data.append((name, f"0x{value:08x}"))
                        
                        # Display group signals in formatted table
                        if len(group_names) == 1:
                            header = f"=== Device {device._id} - location {loc.to_str('logical')} - Group: {group_name} ==="
                        else:
                            header = f"=== Device {device._id} - location {loc.to_str('logical')} - Group: {group_name} ({group_names.index(group_name) + 1}/{len(group_names)}) ==="
                        
                        formatter.print_header(header, style="bold")
                        formatter.display_grouped_data(
                            {"Signals": signal_data},
                            [("Name", ""), ("Value", "")],
                            [["Signals"]],
                            simple_print=dopt.args["--simple"],
                        )
                        
                        # Add spacing between groups if multiple groups
                        if len(group_names) > 1 and group_names.index(group_name) < len(group_names) - 1:
                            print()  
                            
                    except ValueError as e:
                        util.ERROR(f"Error processing group '{group_name}': {e}")
                        continue
                    
            else:
                # List all groups with their signal counts
                group_names = list(debug_bus_signal_store.get_group_names())
                
                # Apply search filter if provided
                if dopt.args["--search"]:
                    max = dopt.args["--max"] if dopt.args["--max"] else 10
                    group_names = search(group_names, dopt.args["--search"], max)
                    if len(group_names) == 0:
                        print("No groups found matching the pattern.")
                        return []
                
                # Create group data with signal counts
                group_data = []
                for group_name in group_names:
                    signal_count = len(debug_bus_signal_store.get_signals_in_group(group_name))
                    group_data.append((group_name, str(signal_count)))
                
                # Display groups in formatted table
                formatter.print_header(f"=== Device {device._id} - location {loc.to_str('logical')} - Signal Groups ===", style="bold")
                formatter.display_grouped_data(
                    {"Groups": group_data},
                    [("Group Name", ""), ("Signal Count", "")],
                    [["Groups"]],
                    simple_print=dopt.args["--simple"],
                )
    return []


def handle_signal_reading_command(dopt, context, ui_state):
    """Handle signal reading commands - read specific signals with optional L1 sampling."""
    signals = parse_command_arguments(dopt.args)

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            noc_block = device.get_block(loc)
            if not noc_block:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a NOC block.")
                continue
            debug_bus_signal_store = noc_block.debug_bus
            if not debug_bus_signal_store:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a debug bus.")
                continue
            
            where = f"device:{device._id} loc:{loc.to_user_str()} "
            
            # Process each signal
            for signal in signals:
                try:
                    if dopt.args["--l1-sampling"]:
                        value = _read_signal_with_l1_sampling(dopt, debug_bus_signal_store, signal)
                    else:
                        # Direct register read mode
                        value = debug_bus_signal_store.read_signal(signal=signal)

                    _display_signal_value(where, signal, value)
                        
                except ValueError as e:
                    util.ERROR(f"Error reading signal '{signal}': {e}")
                    continue
    return []


def _read_signal_with_l1_sampling(dopt, debug_bus_signal_store, signal):
    """Read signal using L1 sampling with parameter validation."""
    samples = int(dopt.args["--samples"]) if dopt.args["--samples"] else 1
    sampling_interval = int(dopt.args["--sampling-interval"]) if dopt.args["--sampling-interval"] else 2
    
    if not dopt.args["--l1-address"]:
        raise ValueError("--l1-address is required when using --l1-sampling")
    
    l1_address = int(dopt.args["--l1-address"], 0)

    # Validate L1 sampling parameters
    if l1_address % 16 != 0:
        raise ValueError(f"L1 address must be 16-byte aligned, got 0x{l1_address:x}")

    if dopt.args["--sampling-interval"] and samples == 1:
        util.WARN(f"--sampling-interval parameter is meaningless when --samples=1, ignoring interval value {sampling_interval}")
    elif samples > 1 and not (2 <= sampling_interval <= 256):
        raise ValueError(
            f"When --samples > 1, --sampling-interval must be between 2 and 256, but got {sampling_interval}"
        )

    return debug_bus_signal_store.read_signal(
        signal=signal,
        use_l1_sampling=True,
        l1_address=l1_address,
        samples=samples,
        sampling_interval=sampling_interval
    )


def _display_signal_value(where, signal, value):
    """Display signal value(s) in appropriate format."""
    if isinstance(value, list):
        # Multiple samples returned as list
        for i, sample_value in enumerate(value):
            if isinstance(signal, str):
                print(f"{where} {signal} [sample {i}]: 0x{sample_value:x}")
            else:
                signal_description = f"Daisy:{signal.daisy_sel}; Rd Sel:{signal.rd_sel}; Sig Sel:{signal.sig_sel}; Mask:0x{signal.mask:x}"
                print(f"{where} Debug Bus Config({signal_description}) [sample {i}] = 0x{sample_value:x}")
                
    elif isinstance(signal, str):
        # Single value with string signal name
        print(f"{where} {signal}: 0x{value:x}")
    else:
        # Single value with signal description object
        signal_description = f"Daisy:{signal.daisy_sel}; Rd Sel:{signal.rd_sel}; Sig Sel:{signal.sig_sel}; Mask:0x{signal.mask:x}"
        print(f"{where} Debug Bus Config({signal_description}) = 0x{value:x}")


def run(cmd_text, context, ui_state: UIState = None):
    """Main entry point for debug-bus command."""
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    # Route to appropriate handler based on command
    if dopt.args["list-names"]:
        return handle_list_names_command(dopt, context, ui_state)
    elif dopt.args["list-groups"]:
        return handle_list_groups_command(dopt, context, ui_state)
    else:
        return handle_signal_reading_command(dopt, context, ui_state)
