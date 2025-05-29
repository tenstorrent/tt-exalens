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
from ttexalens.debug_tensix import TensixDebug
from ttexalens.device import (
    Device,
    TensixRegisterDescription,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
)
from ttexalens import command_parser
from ttexalens.util import TTException, INFO, WARN, DATA_TYPE, convert_int_to_data_type, convert_data_type_to_int
from ttexalens.unpack_regfile import TensixDataFormat
import re
from fnmatch import fnmatch

# Possible values
reg_types = ["cfg", "dbg"]
data_types = ["INT_VALUE", "ADDRESS", "MASK", "FLAGS", "TENSIX_DATA_FORMAT"]


def convert_str_to_int(param: str) -> int:
    try:
        if param.startswith("0x"):
            return int(param, 16)
        else:
            return int(param)
    except ValueError:
        raise ValueError(f"Invalid parameter {param}. Expected a hexadecimal or decimal integer.")


# Convert register parameters to integers
def convert_reg_params(reg_params: str) -> list[int]:
    params = []
    for param in reg_params.split(","):
        params.append(convert_str_to_int(param))

    return params


# Create register description object given parameters
def create_register_description(reg_type: str, reg_params: list[int], data_type: str) -> TensixRegisterDescription:
    if reg_type == "cfg":
        if len(reg_params) != 3:
            raise TTException(
                "Invalid number of parameters for configuration register since it requires 3 parameters (index, mask, shift)."
            )
        return ConfigurationRegisterDescription(
            index=reg_params[0], mask=reg_params[1], shift=reg_params[2], data_type=DATA_TYPE[data_type]
        )
    elif reg_type == "dbg":
        if len(reg_params) != 1:
            raise TTException(
                "Invalid number of parameters for debug register since it requires 1 parameter (address)."
            )
        return DebugRegisterDescription(address=reg_params[0], data_type=DATA_TYPE[data_type])
    else:
        raise ValueError(f"Unknown register type: {reg_type}. Possible values: {reg_types}")


def parse_register_argument(register: str):
    match = re.match(r"(\w+)\((.*?)\)", register)
    if match:
        reg_type = match.group(1)
        reg_params = convert_reg_params(match.group(2))
        return reg_type, reg_params
    else:
        return register


# Print strings that match wildcard pattern. Maximum max_prints, negaitve values enable print all.
def print_matches(pattern: str, strings: list[str], max_prints: int) -> None:
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
        register_ref = parse_register_argument(dopt.args["<register>"])

        data_type = dopt.args["--type"] if dopt.args["--type"] else "INT_VALUE"
        if data_type not in data_types:
            raise ValueError(f"Invalid data type: {data_type}. Possible values: {data_types}")

        value = convert_data_type_to_int(dopt.args["--write"]) if dopt.args["--write"] else None
        value_str = dopt.args["--write"]

        if isinstance(register_ref, tuple):
            reg_type, reg_params = register_ref
            register = create_register_description(reg_type, reg_params, data_type)

    for device in dopt.for_each("--device", context, ui_state):

        # Do this only if search is enabled
        if register_pattern != None:
            register_names = device._get_tensix_register_map_keys()
            max_regs = dopt.args["--max"] if dopt.args["--max"] else 10
            try:
                if max_regs != "all":
                    max_regs = int(max_regs)
                    if max_regs <= 0:
                        raise ValueError(f"Invalid value for max-regs. Expected positive integer, but got {max_regs}")
                else:
                    max_regs = len(register_names)
            except:
                raise ValueError(f"Invalid value for max-regs. Expected an integer, but got {max_regs}")

            INFO(f"Register names that match pattern on device {device.id()}")
            print_matches(register_pattern, register_names, max_regs)

            continue

        for loc in dopt.for_each("--loc", context, ui_state, device=device):

            debug_tensix = TensixDebug(loc, device.id(), context)

            if isinstance(register_ref, str):
                register = device.get_tensix_register_description(register_ref)
                if register == None:
                    raise ValueError(
                        f"Referencing register by {register_ref} is invalid. Please use valid register name or <reg-type>(<reg-parameters>) format."
                    )

            if value != None:
                debug_tensix.write_tensix_register(register, value)
                INFO(f"Register {register} on device {device.id()} and location {loc} written with value {value_str}.")
            else:
                reg_value = debug_tensix.read_tensix_register(register)

                # Overwritting data type of register if user specified it
                if dopt.args["--type"]:
                    data_type = DATA_TYPE[data_type]
                else:
                    data_type = register.data_type

                INFO(f"Value of register {register} on device {device.id()} and location {loc}:")
                print(convert_int_to_data_type(reg_value, data_type, register.mask.bit_count()))
