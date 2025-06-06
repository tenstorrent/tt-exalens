# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  debug-bus list-names [-v] [-d <device>] [-l <loc>]
  debug-bus [<signals>] [-v] [-d <device>] [-l <loc>]

Description:
  Commands for RISC-V debugging:
    - list-names:    List all predefined debug bus signal names.
    - [<signals>]:   List of signals described by signal name or signal description.
        <signal-description>: {DaisyId,RDSel,SigSel,Mask}
            -DaisyId - daisy chain identifier
            -RDSel   - select 32bit data in 128bit register -> values [0-3]
            -SigSel  - select 128bit register
            -Mask    - 32bit number to show only significant bits (optional)

Examples:
  debug-bus list-names                       # List predefined debug bus signals
  debug-bus trisc0_pc,trisc1_pc              # Prints trisc0_pc and trisc1_pc program counter for trisc0 and trisc1
  debug-bus {7,0,12,0x3ffffff},trisc2_pc     # Prints custom debug bus signal and trisc2_pc
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
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription
from ttexalens.device import Device
from ttexalens.uistate import UIState


def parse_string(input_string):
    pattern = r"(\{([\dA-Fa-fx]+),([\dA-Fa-fx]+),([\dA-Fa-fx]+)(?:,([\dA-Fa-fx]+))?\}|[^,\{\}]+)"

    matches = re.findall(pattern, input_string)
    parsed_result = []

    for match in matches:
        if match[0].startswith("{"):  # Case when A is in bracket format
            numbers = [int(match[i], 0) for i in range(1, 4)]  # First 3 numbers (mandatory)
            fourth_number = int(match[4], 0) if match[4] else 0xFFFFFFFF  # Replace missing with 0xFFFFFFFF
            numbers.append(fourth_number)
            parsed_result.append(numbers)
        else:  # Case of plain string
            parsed_result.append(match[0])

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
                print(debug_bus_signal_store.get_signal_names())
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
                    if isinstance(signal, str):
                        value = debug_bus_signal_store.read_signal(signal)
                        print(f"{where} {signal}: 0x{value:x}")
                    else:
                        value = debug_bus_signal_store.read_signal(signal)
                        signal_description = f"Daisy:{signal.daisy_sel}; Rd Sel:{signal.rd_sel}; Sig Sel:{signal.sig_sel}; Mask:0x{signal.mask:x}"
                        print(f"{where} Debug Bus Config({signal_description}) = 0x{value:x}")
                except ValueError as e:
                    util.ERROR(f"Error reading signal '{signal}': {e}")
                    continue

    return []
