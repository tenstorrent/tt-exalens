# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  tensix-reg <register> [--type <data-type>] [ --write <value> ] [ -d <device> ] [ -l <loc> ]

Arguments:
  <register>    Register to dump/write to. Format: <reg-type>(<reg-parameters>) or register name.
                <reg-type> Register type. Options: [cfg, dbg]
                <reg-parameters> Register parameters, comma separated integers. For cfg: index,mask,shift. For dbg: address

Options:
  --type <data-type>  Data type of the register. This affects print format. Options: [INT_VALUE, ADDRESS, MASK, FLAGS, TENSIX_DATA_FORMAT]. Default: INT_VALUE
  --write <value>     Value to write to the register. If not given, register is dumped instead.
  -d <device>         Device ID. Optional. Default: current device
  -l <loc>            Core location in X-Y or R,C format. Default: current core

Description:
  Prints/writes to the specified register, at the specified location and device.

Examples:
  reg cfg(1,0x1E000000,25)                            # Prints configuration register with index 1, mask 0x1E000000, shift 25
  reg dbg(0x54)                                       # Prints debug register with address 0x54
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
from ttexalens.util import TTException, INFO, DATA_TYPE, convert_value
from ttexalens.unpack_regfile import TensixDataFormat
import re

reg_types = ["cfg", "dbg"]
data_types = ["INT_VALUE", "ADDRESS", "MASK", "FLAGS", "TENSIX_DATA_FORMAT"]


def convert_to_int(param: str) -> int:
    try:
        if param.startswith("0x"):
            return int(param, 16)
        else:
            return int(param)
    except ValueError:
        raise ValueError(f"Invalid parameter {param}. Expected a hexadecimal or decimal integer.")


def convert_reg_params(reg_params: str) -> list[int]:
    params = []
    for param in reg_params.split(","):
        params.append(convert_to_int(param))

    return params


def convert_write_value(value: str) -> int:
    if re.match(r"^0x[0-9a-fA-F]+$", value):
        return int(value, 16)
    elif re.match(r"^[0-9]+$", value):
        return int(value)
    elif re.match(r"^(True|False)(,(True|False))*$", value):
        return int("".join(["1" if v == "True" else "0" for v in value.split(",")]), 2)
    elif value in TensixDataFormat.__members__:
        return TensixDataFormat[value].value
    else:
        raise ValueError(
            f"Invalid value {value}. Expected a hexadecimal or decimal integer, boolean list or TensixDataFormat."
        )


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


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    register_ref = parse_register_argument(dopt.args["<register>"])

    data_type = dopt.args["--type"] if dopt.args["--type"] else "INT_VALUE"
    if data_type not in data_types:
        raise ValueError(f"Invalid data type: {data_type}. Possible values: {data_types}")

    value = convert_write_value(dopt.args["--write"]) if dopt.args["--write"] else None
    value_str = dopt.args["--write"]

    if isinstance(register_ref, tuple):
        reg_type, reg_params = register_ref
        register = create_register_description(reg_type, reg_params, data_type)

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):

            debug_tensix = TensixDebug(loc, device.id(), context)

            if isinstance(register_ref, str):
                device = debug_tensix.context.devices[debug_tensix.device_id]
                register = device._get_tensix_register_description(register_ref)
                if register == None:
                    raise ValueError(
                        f"Referencing register by {register_ref} is invalid. Please use valid register name or <reg-type>(<reg-parameters>) format."
                    )

                # Overwritting data type of register if user specified it
                # Do we need/want this???
                if dopt.args["--type"]:
                    register.data_type = data_type

            if value is not None:
                debug_tensix.write_tensix_register(register, value)
                INFO(f"Register {register} written with value {value_str}.")
            else:
                value = debug_tensix.read_tensix_register(register)
                print(convert_value(value, register.data_type, bin(register.mask).count("1")))
