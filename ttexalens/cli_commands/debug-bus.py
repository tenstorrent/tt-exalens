# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  debug-bus list-names [-v] [-d <device>] [-l <loc>] [--search <pattern>] [--max <max-sigs>] [-s]
  debug-bus [<signals>] [-v] [-d <device>] [-l <loc>] [--l1-sampling] [--samples <num>] [--sampling-interval <cycles>]

Options:
    -s, --simple                        Print simple output.
    --search <pattern>                  Search for signals by pattern (in wildcard format).
    --max <max-sigs>                    Limit --search output (default: 10, use --max "all" to print all matches).
    --l1-sampling                       Enable sampling into L1 memory. Instead of a direct 32-bit register read,
                                        this triggers a 128-bit capture of the signal into the core's L1 memory at address 0.
    --samples <num>                     (L1-sampling only) Number of 128-bit samples to capture. [default: 1].
    --sampling-interval <cycles>        (L1-sampling only) When samples > 1, this sets the delay in clock cycles
                                        between each sample. Must be between 2 and 255. [default: 2].

Description:
  Commands for RISC-V debugging:
    - list-names:    List all predefined debug bus signal names.
        --search:
    - [<signals>]:   List of signals described by signal name or signal description.
        <signal-description>: {DaisyId,RDSel,SigSel,Mask}
            -DaisyId - daisy chain identifier
            -RDSel   - select 32bit data in 128bit register -> values [0-3]
            -SigSel  - select 128bit register
            -Mask    - 32bit number to show only significant bits (optional)

Examples:
  debug-bus list-names                        # List predefined debug bus signals
  debug-bus list-names --search *pc* --max 5  # List up to 5 signals whose names contain pc
  debug-bus trisc0_pc,trisc1_pc               # Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
  debug-bus {7,0,12,0x3ffffff},trisc2_pc      # Prints custom debug bus signal and trisc2_pc
  debug-bus trisc0_pc --l1-sampling --samples 5 --sampling-interval 10 # Read trisc0_pc using L1 sampling 5 times with 10 cycle interval
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
    pattern = r"\{([\dA-Fa-fx]+),([\dA-Fa-fx]+),([\dA-Fa-fx]+)(?:,([\dA-Fa-fx]+))?\}|([A-Za-z_][A-Za-z0-9_/#]*)"

    parsed_result = []

    for m in re.finditer(pattern, input_string):
        if m.group(1): 
            numbers = [int(m.group(i), 0) for i in range(1, 4)]  
            fourth_number = int(m.group(4), 0) if m.group(4) else 0xFFFFFFFF
            numbers.append(fourth_number)
            parsed_result.append(numbers)
        else:  
            parsed_result.append(m.group(5))

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


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    device: Device
    loc: OnChipCoordinate
    if dopt.args["list-names"]:
        # Fetch all signal names, optionally search by pattern, and pretty-print.
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

                # Read signal values and convert to list of tuples
                signal_data = []
                for name in names:
                    value = debug_bus_signal_store.read_signal(name)
                    signal_data.append((name, f"0x{value:08x}"))
                # And pretty-print.
                formatter.print_header(f"=== Device {device._id} - location {loc.to_str('logical')})", style="bold")
                formatter.display_grouped_data(
                    {"Signals": signal_data},
                    [("Name", ""), ("Value", "")],
                    [["Signals"]],
                    simple_print=dopt.args["--simple"],
                )

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
            for signal in signals:
                try:
                    read_signal_args = {"signal": signal}
                    if dopt.args["--l1-sampling"]:
                        read_signal_args["use_l1_sampling"] = True

                        samples = 1
                        if "--samples" in cmd_text:
                            samples = int(dopt.args["--samples"])
                            read_signal_args["samples"] = samples

                        if "--sampling-interval" in cmd_text:
                            sampling_interval = int(dopt.args["--sampling-interval"])
                            if samples > 1 and not (2 <= sampling_interval <= 255):
                                raise ValueError(
                                    f"When --samples > 1, --sampling-interval must be between 2 and 255, but got {sampling_interval}"
                                )
                            read_signal_args["sampling_interval"] = sampling_interval

                    value = debug_bus_signal_store.read_signal(**read_signal_args)

                    if isinstance(value, list):
                        # Multiple samples returned as list
                        for i, sample_value in enumerate(value):
                            if isinstance(signal, str):
                                print(f"{where} {signal} [sample {i}]: 0x{sample_value:x}")
                            else:
                                signal_description = f"Daisy:{signal.daisy_sel}; Rd Sel:{signal.rd_sel}; Sig Sel:{signal.sig_sel}; Mask:0x{signal.mask:x}"
                                print(f"{where} Debug Bus Config({signal_description}) [sample {i}] = 0x{sample_value:x}")
                    else:
                        # Single value
                        if isinstance(signal, str):
                            print(f"{where} {signal}: 0x{value:x}")
                        else:
                            signal_description = f"Daisy:{signal.daisy_sel}; Rd Sel:{signal.rd_sel}; Sig Sel:{signal.sig_sel}; Mask:0x{signal.mask:x}"
                            print(f"{where} Debug Bus Config({signal_description}) = 0x{value:x}")
                except ValueError as e:
                    util.ERROR(f"Error reading signal '{signal}': {e}")
                    continue

    return []
