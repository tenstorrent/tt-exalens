# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  debug-bus list-names [-v] [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s] [--l1-address <addr> [--samples <num>] [--sampling-interval <cycles>]]
  debug-bus list-groups [-v] [--search <pattern>] [-s]
  debug-bus [<signals>] [-v] [-d <device>] [-l <loc>] [--l1-address <addr> [--samples <num>] [--sampling-interval <cycles>]] [--group <group-name>]

Options:
    -s, --simple                        Print simple output.
    --search <pattern>                  Search for signals by pattern (in wildcard format).
    --max <max-sigs>                    Limit --search output (default: 10, use --max "all" to print all matches).
    --group <group-names>               List signals in the specified group(s). Multiple groups can be separated by commas.
    --l1-address <addr>                 Byte address in L1 memory for L1 sampling mode. Must be 16-byte aligned.
                                        When specified, enables L1 sampling mode which triggers a 128-bit capture
                                        of the signal into the core's L1 memory instead of a direct 32-bit register read.
                                        Each sample occupies 16 bytes (128 bits) in L1 memory. All samples must fit within
                                        the first 1 MiB of L1 memory (0x0 - 0xFFFFF).
    --samples <num>                     (L1-sampling mode only) Number of 128-bit samples to capture. [default: 1].
    --sampling-interval <cycles>        (L1-sampling mode only) When samples > 1, this sets the delay in clock cycles
                                        between each sample. Must be between 2 and 256.

Description:
  Commands for RISC-V debugging:
    - list-names:    List all predefined debug bus signal names.
        --search:
    - list-groups:   List all debug bus signal groups or signals in a specific group.
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
  debug-bus list-names --l1-address 0x1000    # List all signals with L1 sampling (no composite signal warnings)
  debug-bus list-groups                       # List all debug bus signal groups
  debug-bus list-groups --search *brisc*      # List groups matching pattern
  debug-bus --group brisc_group_a             # List all signals in brisc_group_a
  debug-bus --group brisc_group_a --l1-address 0x1000 # List signals in group using L1 sampling
  debug-bus --group brisc_group_a,trisc0_group_a,trisc1_group_a # List signals from multiple groups
  debug-bus trisc0_pc,trisc1_pc               # Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
  debug-bus {7,0,12,0x3ffffff},trisc2_pc      # Prints custom debug bus signal and trisc2_pc
  debug-bus trisc0_pc --l1-address 0x1000 --samples 5 --sampling-interval 10 # Read trisc0_pc using L1 sampling 5 times with 10 cycle interval
  debug-bus trisc0_pc --l1-address 0x2000 --samples 3    # Read trisc0_pc using L1 sampling at address 0x2000
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
from ttexalens.util import search
from ttexalens.rich_formatters import formatter
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription
from ttexalens.uistate import UIState


def _format_signal_value(
    value, is_composite_signal=False, use_l1_sampling=False, show_all_samples=False, signal_desc=None
):
    """
    Format signal value for display:
    - 1-bit signals as True/False
    - others as 0x... (no leading zeros)
    """

    def is_single_bit(mask):
        return mask is not None and (mask & (mask - 1)) == 0

    if signal_desc is not None:
        mask = signal_desc.mask
        if is_single_bit(mask):
            # Always display 1-bit signals as True/False
            if isinstance(value, list):
                samples_str = (
                    ", ".join(["True" if v else "False" for v in value])
                    if show_all_samples and len(value) > 1
                    else ("True" if value[0] else "False")
                )
                return f"[{samples_str}]" if show_all_samples and len(value) > 1 else samples_str
            else:
                return "True" if value else "False"

    def hex_width(val):
        return f"0x{val:x}"

    if isinstance(value, list):
        samples_str = (
            ", ".join([hex_width(v) for v in value]) if show_all_samples and len(value) > 1 else hex_width(value[0])
        )
        return f"[{samples_str}]" if show_all_samples and len(value) > 1 else samples_str
    else:
        formatted = hex_width(value)
        if is_composite_signal and not use_l1_sampling:
            formatted += "**"
        return formatted


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
    print(args["<signals>"])
    if not (args["<signals>"]):
        raise ValueError("Missing debug bus signal parameter")

    result: list[str | DebugBusSignalDescription] = []

    signals = parse_string(args["<signals>"])

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

    group_names = [name.strip() for name in group_string.split(",")]
    # Remove empty strings
    return [name for name in group_names if name]


def collect_signal_data(debug_bus_signal_store, signal_names, use_l1_sampling, l1_address, samples, sampling_interval):
    """Helper to read and format all signals (simple and composite) for display."""
    composite_signals, simple_signals = debug_bus_signal_store.group_composite_signals(signal_names)
    signal_data = []

    # Simple signals
    for name in simple_signals:
        value = debug_bus_signal_store.read_signal(
            name,
            use_l1_sampling=use_l1_sampling,
            l1_address=l1_address,
            samples=samples,
            sampling_interval=sampling_interval,
        )
        formatted_value = _format_signal_value(
            value,
            is_composite_signal=False,
            use_l1_sampling=use_l1_sampling,
            show_all_samples=use_l1_sampling and samples > 1,
            signal_desc=debug_bus_signal_store.signals.get(name, None),
        )
        signal_data.append((name, formatted_value))

    # Composite signals
    for base_name, part_names in composite_signals.items():
        value = debug_bus_signal_store.read_signal(
            base_name,
            use_l1_sampling=use_l1_sampling,
            l1_address=l1_address,
            samples=samples,
            sampling_interval=sampling_interval,
        )
        formatted_value = _format_signal_value(
            value,
            is_composite_signal=True,
            use_l1_sampling=use_l1_sampling,
            show_all_samples=use_l1_sampling and samples > 1,
            signal_desc=debug_bus_signal_store.signals.get(base_name, None),
        )
        signal_data.append((base_name, formatted_value))

    signal_data.sort(key=lambda x: x[0])
    return signal_data, composite_signals


def handle_list_names_command(dopt, context, ui_state):
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
            if dopt.args["--search"]:
                max = dopt.args["--max"] if dopt.args["--max"] else 10
                names = search(list(names), dopt.args["--search"], max)
                if len(names) == 0:
                    print("No matches found.")
                    return []

            use_l1_sampling = dopt.args["--l1-address"] is not None
            l1_address = int(dopt.args["--l1-address"], 0) if use_l1_sampling else None
            samples = int(dopt.args["--samples"]) if dopt.args["--samples"] else 1
            sampling_interval = int(dopt.args["--sampling-interval"]) if dopt.args["--sampling-interval"] else 2

            signal_data, composite_signals = collect_signal_data(
                debug_bus_signal_store, names, use_l1_sampling, l1_address, samples, sampling_interval
            )

            formatter.print_header(f"=== Device {device._id} - location {loc.to_str('logical')})", style="bold")
            if not use_l1_sampling and composite_signals:
                formatter.print_header("** Composite signals marked with ** - use L1 sampling for consistent reads")

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
                group_names = parse_group_names(dopt.args["--group"])
                if not group_names:
                    util.ERROR("No valid group names provided.")
                    continue

                for group_name in group_names:
                    try:
                        signal_names = debug_bus_signal_store.get_signals_in_group(group_name)
                        use_l1_sampling = dopt.args["--l1-address"] is not None
                        l1_address = int(dopt.args["--l1-address"], 0) if use_l1_sampling else None
                        samples = int(dopt.args["--samples"]) if dopt.args["--samples"] else 1
                        sampling_interval = (
                            int(dopt.args["--sampling-interval"]) if dopt.args["--sampling-interval"] else 2
                        )

                        signal_data, composite_signals = collect_signal_data(
                            debug_bus_signal_store,
                            signal_names,
                            use_l1_sampling,
                            l1_address,
                            samples,
                            sampling_interval,
                        )

                        if len(group_names) == 1:
                            header = (
                                f"=== Device {device._id} - location {loc.to_str('logical')} - Group: {group_name} ==="
                            )
                        else:
                            header = f"=== Device {device._id} - location {loc.to_str('logical')} - Group: {group_name} ({group_names.index(group_name) + 1}/{len(group_names)}) ==="

                        formatter.print_header(header, style="bold")
                        if not use_l1_sampling and composite_signals:
                            formatter.print_header(
                                "** Composite signals marked with ** - use L1 sampling for consistent reads"
                            )

                        formatter.display_grouped_data(
                            {"Signals": signal_data},
                            [("Name", ""), ("Value", "")],
                            [["Signals"]],
                            simple_print=dopt.args["--simple"],
                        )

                        if len(group_names) > 1 and group_names.index(group_name) < len(group_names) - 1:
                            print()
                    except ValueError as e:
                        util.ERROR(f"Error processing group '{group_name}': {e}")
                        continue

            else:
                group_names = list(debug_bus_signal_store.get_group_names())
                if dopt.args["--search"]:
                    max_results = dopt.args["--max"] if dopt.args["--max"] else 10
                    group_names = search(group_names, dopt.args["--search"], max_results)
                    if len(group_names) == 0:
                        print("No groups found matching the pattern.")
                        return []

                group_data = [(group_name,) for group_name in group_names]

                formatter.print_header(
                    f"=== Device {device._id} - location {loc.to_str('logical')} - Signal Groups ===", style="bold"
                )
                formatter.display_grouped_data(
                    {"Groups": group_data},
                    [("Group Name", "")],
                    [["Groups"]],
                    simple_print=dopt.args["--simple"],
                )
    return []


def handle_signal_reading_command(dopt, context, ui_state):
    """Handle signal reading commands - read specific signals with optional L1 sampling."""
    if not dopt.args["<signals>"] and dopt.args["--group"]:
        group_names = parse_group_names(dopt.args["--group"])
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
                for group_name in group_names:
                    try:
                        signal_names = debug_bus_signal_store.get_signals_in_group(group_name)
                        use_l1_sampling = dopt.args["--l1-address"] is not None
                        l1_address = int(dopt.args["--l1-address"], 0) if use_l1_sampling else None
                        samples = int(dopt.args["--samples"]) if dopt.args["--samples"] else 1
                        sampling_interval = (
                            int(dopt.args["--sampling-interval"]) if dopt.args["--sampling-interval"] else 2
                        )

                        signal_data, composite_signals = collect_signal_data(
                            debug_bus_signal_store,
                            signal_names,
                            use_l1_sampling,
                            l1_address,
                            samples,
                            sampling_interval,
                        )

                        header = f"=== Device {device._id} - location {loc.to_str('logical')} - Group: {group_name} ==="
                        formatter.print_header(header, style="bold")
                        if not use_l1_sampling and composite_signals:
                            formatter.print_header(
                                "** Composite signals marked with ** - use L1 sampling for consistent reads"
                            )
                        formatter.display_grouped_data(
                            {"Signals": signal_data},
                            [("Name", ""), ("Value", "")],
                            [["Signals"]],
                            simple_print=dopt.args["--simple"],
                        )
                        if len(group_names) > 1 and group_names.index(group_name) < len(group_names) - 1:
                            print()
                    except ValueError as e:
                        util.ERROR(f"Error processing group '{group_name}': {e}")
                        continue
        return []

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
            composite_signals, _ = debug_bus_signal_store.group_composite_signals(
                debug_bus_signal_store.get_signal_names()
            )

            for signal in signals:
                try:
                    if isinstance(signal, str) and signal in composite_signals and not dopt.args["--l1-address"]:
                        util.WARN(
                            f"Signal '{signal}' is a composite signal. For consistent reading, use L1 sampling mode (--l1-address)."
                        )

                    if dopt.args["--l1-address"]:
                        value = _read_signal_with_l1_sampling(dopt, debug_bus_signal_store, signal)
                    else:
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

    l1_address = int(dopt.args["--l1-address"], 0)

    if dopt.args["--sampling-interval"] is not None and samples == 1:
        util.WARN(
            f"--sampling-interval parameter is meaningless when --samples=1, ignoring interval value {sampling_interval}"
        )

    return debug_bus_signal_store.read_signal(
        signal=signal, use_l1_sampling=True, l1_address=l1_address, samples=samples, sampling_interval=sampling_interval
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
        signal_description = (
            f"Daisy:{signal.daisy_sel}; Rd Sel:{signal.rd_sel}; Sig Sel:{signal.sig_sel}; Mask:0x{signal.mask:x}"
        )
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
