# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  debug-bus list-names [-v] [-d <device>] [-l <loc>]
  debug-bus name [<signal-name>] [-v] [-d <device>] [-l <loc>]
  debug-bus signal [<signal-description>] [-v] [-d <device>] [-l <loc>]

Description:
  Commands for RISC-V debugging:
    - list-names:    List all predefined debug bus signal names.
    - name [<signal-name>]: Prints value of debug bus signal for predefined signal name.
    - signal [<signal-description>]: Print value of debug bus signal with provided description.
        <signal-description>: DaisyId,RDSel,SigSel,Mask
            -DaisyId - daisy chain identifier
            -RDSel   - select 32bit data in 128bit register -> values [0-3]
            -SigSel  - select 128bit register
            -Mask    - 32bit number to show only significant bits
Examples:
  debug-bus list-names                       # List predefined debug bus signals
  debug-bus name trisc0_pc                   # Prints trisc0_pc, program counter for trisc0
  debug-bus signal 7,0,12,0x3ffffff          # Prints custom debug bus signal
"""

command_metadata = {
    "short": "dbus",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc", "--verbose"],
}

from ttlens.uistate import UIState

from ttlens import commands
from ttlens import util as util
from ttlens.device import DebugBusSignalDescription


def run_debug_bus_command(context, device, loc, args):
    """
    Given a command trough args, run the corresponding RISC-V command
    """
    where = f"device:{device._id} loc:{loc.to_str('logical')} "

    if args["list-names"]:
        print(device.get_debug_bus_signal_names())
        return

    if args["name"]:
        if args["<signal-name>"] is None:
            util.ERROR("Signal name is required")
        else:
            signal_name = args.get("<signal-name>", "")
            value = device.read_debug_bus_signal(loc, signal_name)
            print(f"{where} {signal_name}: 0x{value:x}")
    elif args["signal"]:
        if args["<signal-description>"] is None:
            util.ERROR("Debug Bus signal description is required")
            return
        else:
            configuration = args.get("<signal-description>", "")
            params = [int(n, 0) for n in configuration.split(",")]
            if len(params) < 4:
                util.ERROR("Debug Bus configuration values are not formatted correctly")

            signal = DebugBusSignalDescription(params[1], params[0], params[2], params[3])
            value = device.read_debug_bus_signal_from_description(loc, signal)

            signal_description = f"Diasy:{params[0]}; Rd Sel:{params[1]}; Sig Sel:{params[2]}; Mask:0x{params[3]:x}"
            print(f"{where} Debug Bus Config({signal_description}) = 0x{value:x}")
    else:
        raise ValueError(f"Unknown input parameters")


def run(cmd_text, context, ui_state: UIState = None):
    dopt = commands.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            run_debug_bus_command(context, device, loc, dopt.args)
    return None
