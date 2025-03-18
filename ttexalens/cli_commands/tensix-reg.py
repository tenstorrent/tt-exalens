# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  tensix-reg <register> [ --write <value> ] [ -d <device> ] [ -l <loc> ]

Arguments:
  <register>    Register to dump/write to. Format: <reg-type>(<reg-parameters>)
                <reg-type> Register type. Options: [cfg, dbg]
                <reg-parameters> Register parameters, comma separated integers. For cfg: index,mask,shift. For dbg: address

Options:
  --write <value>  Value to write to the register. If not given, register is dumped instead.
  -d <device>      Device ID. Optional. Default: current device
  -l <loc>         Core location in X-Y or R,C format. Default: current core

Description:
  Prints/writes to the specified register, at the specified location and device.

Examples:
  reg cfg(60,0xf,0)               # Prints configuration register with index 60, mask 0xf, shift 0
  reg dbg(0x54)                   # Prints debug register with address 0x54
  reg dbg(0x54) --write 18        # Writes 18 to debug register with address 0x54
  reg cfg(60,0xf,0) --write 0x0   # Writes 0 to configuration register with index 60, mask 0xf, shift 0
  reg dbg(0x54) -d 0 -l 0,0       # Prints debug register with address 0x54 for device 0 and core at location 0,0
  reg dbg(0x54) -l 0,0            # Prints debug register with address 0x54 for core at location 0,0
  reg dbg(0x54) -d 0              # Prints debug register with address 0x54 for device 0
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
from ttexalens.util import TTException, INFO
import re

reg_types = ["cfg", "dbg"]


def convert_to_int(param: str) -> int:
    try:
        if param.startswith("0x"):
            return int(param, 16)
        else:
            return int(param)
    except ValueError:
        raise ValueError("Invalid parameter. Expected an integer.")


def convert_reg_params(reg_params: str) -> list[int]:
    params = []
    for param in reg_params.split(","):
        params.append(convert_to_int(param))

    return params


def parse_register(register: str) -> tuple:
    match = re.match(r"(\w+)\((.*?)\)", register)
    if not match:
        raise TTException("Invalid register format. Use <reg-type>(<reg-parameters>).")
    return match.groups()


def create_register_description(reg_type: str, reg_params: list[int]) -> TensixRegisterDescription:
    if reg_type == "cfg":
        if len(reg_params) != 3:
            raise TTException(
                "Invalid number of parameters for configuration register since it requires 3 parameters (index, mask, shift)."
            )
        return ConfigurationRegisterDescription(index=reg_params[0], mask=reg_params[1], shift=reg_params[2])
    elif reg_type == "dbg":
        if len(reg_params) != 1:
            raise TTException(
                "Invalid number of parameters for debug register since it requires 1 parameter (address)."
            )
        return DebugRegisterDescription(address=reg_params[0])
    else:
        raise ValueError(f"Unknown register type: {reg_type}. Possible values: {reg_types}")


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    reg_type, reg_params = parse_register(dopt.args["<register>"])
    reg_params = convert_reg_params(reg_params)
    value = convert_to_int(dopt.args["<value>"]) if dopt.args["<value>"] else None
    value_str = dopt.args["<value>"]

    register = create_register_description(reg_type, reg_params)

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            if value:
                TensixDebug(loc, device.id(), context).write_tensix_register(register, value)
                INFO(f"Register {register} written with value {value_str}.")
            else:
                print(TensixDebug(loc, device.id(), context).read_tensix_register(register))
