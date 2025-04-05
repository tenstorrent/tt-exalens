# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  tensix-reg <register> [--type <data-type>] [ --write <value> ] [ -d <device> ] [ -l <loc> ]
  tensix-reg --search <register_pattern> [ --max <max-regs> ] [ -d <device> ] [ -l <loc> ]

Arguments:
  <register>            Register to dump/write to. Format: <reg-type>(<reg-parameters>) or register name.
                        <reg-type> Register type. Options: [cfg, dbg].
                        <reg-parameters> Register parameters, comma separated integers. For cfg: index,mask,shift. For dbg: address.
  <register-pattern>    Register pattern used to print register names that match it. Format: wildcard.

Options:
  --type <data-type>  Data type of the register. This affects print format. Options: [INT_VALUE, ADDRESS, MASK, FLAGS, TENSIX_DATA_FORMAT]. Default: INT_VALUE.
  --write <value>     Value to write to the register. If not given, register is dumped instead.
  --max <max-regs>    Maximum number of register names to print when searching or all for everything. Default: 10.
  -d <device>         Device ID. Optional. Default: current device.
  -l <loc>            Core location in X-Y or R,C format. Default: current core.

Description:
  Prints/writes to the specified register, at the specified location and device.

Examples:
  reg cfg(1,0x1E000000,25)                            # Prints configuration register with index 1, mask 0x1E000000, shift 25
  reg dbg(0x54)                                       # Prints debug register with address 0x54
  reg --search PACK*                                  # Prints names of first 10 registers that start with PACK
  reg --search ALU* --max 5                           # Prints names of first 5 registers that start with ALU
  reg --search *format* --max all                     # Prints names of all reigsters that include word format
  reg UNPACK_CONFIG0_out_data_format                  # Prints register with name UNPACK_CONFIG0_out_data_format
  reg cfg(1,0x1E000000,25) --type TENSIX_DATA_FORMAT  # Prints configuration register with index 60, mask 0xf, shift 0 in tensix data format
  reg dbg(0x54) --type INT_VALUE                      # Prints debug register with address 0x54 in integer format
  reg dbg(0x54) --write 18                            # Writes 18 to debug register with address 0x54
  reg cfg(1,0x1E000000,25) --write 0x0                # Writes 0 to configuration register with index 1, mask 0x1E000000, shift 25
  reg dbg(0x54) -d 0 -l 0,0                           # Prints debug register with address 0x54 for device 0 and core at location 0,0
  reg dbg(0x54) -l 0,0                                # Prints debug register with address 0x54 for core at location 0,0
  reg dbg(0x54) -d 0                                  # Prints debug register with address 0x54 for device 0
"""

command_metadata = {
    "short": "reg",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "command_option_names": ["--device", "--loc"],
}

from ttexalens.uistate import UIState
from ttexalens.device import Device
from ttexalens.register_store import REGISTER_DATA_TYPE, format_register_value, parse_register_value
from ttexalens import command_parser
from ttexalens.util import INFO, WARN
from typing import List
from fnmatch import fnmatch

# Possible values
data_types = ["INT_VALUE", "ADDRESS", "MASK", "FLAGS", "TENSIX_DATA_FORMAT"]


# Print strings that match wildcard pattern. Maximum max_prints, negaitve values enable print all.
def print_matches(pattern: str, strings: List[str], max_prints: int) -> None:
    pattern = pattern.lower()
    for s in strings:
        if max_prints == 0:
            WARN("Hit printing limit. To see more results, increase the --max value.")
            break

        if fnmatch(s.lower(), pattern):
            print(s)
            max_prints -= 1


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    register_pattern = dopt.args["<register_pattern>"] if dopt.args["--search"] else None

    # Do this only if search is disabled
    if register_pattern == None:
        data_type = dopt.args["--type"] if dopt.args["--type"] else "INT_VALUE"
        if data_type not in data_types:
            raise ValueError(f"Invalid data type: {data_type}. Possible values: {data_types}")

        value_str = dopt.args["--write"]
        value = parse_register_value(value_str) if value_str else None

    device: Device
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            register_store = device.get_register_store(loc)

            # Do this only if search is enabled
            if register_pattern != None:
                register_names = register_store.get_register_names()
                max_regs = dopt.args["--max"] if dopt.args["--max"] else 10
                try:
                    if max_regs != "all":
                        max_regs = int(max_regs)
                        if max_regs <= 0:
                            raise ValueError(
                                f"Invalid value for max-regs. Expected positive integer, but got {max_regs}"
                            )
                    else:
                        max_regs = len(register_names)
                except:
                    raise ValueError(f"Invalid value for max-regs. Expected an integer, but got {max_regs}")

                INFO(f"Register names that match pattern on device {device.id()}")
                print_matches(register_pattern, register_names, max_regs)

                continue
            else:
                register = register_store.parse_register_description(dopt.args["<register>"])

            if value != None:
                register_store.write_register(register, value)
                INFO(f"Register {register} on device {device.id()} and location {loc} written with value {value_str}.")
            else:
                reg_value = register_store.read_register(register)

                # Overwritting data type of register if user specified it
                if dopt.args["--type"]:
                    data_type = REGISTER_DATA_TYPE[data_type]
                else:
                    data_type = register.data_type

                INFO(f"Value of register {register} on device {device.id()} and location {loc}:")
                print(format_register_value(reg_value, data_type, bin(register.mask).count("1")))
