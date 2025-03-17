# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-reg <reg-type> <reg_parameters> [ -d <device> ] [ -l <loc> ]

Arguments:
  <reg-type>    Register type to dump. Options: [cfg, dbg]
  <reg_parameters>  Register parameters. For cfg: index, mask, shift. For dbg: address

Options:
  -d <device>   Device ID. Optional. Default: current device
  -l <loc>      Core location in X-Y or R,C format. Default: current core

Description:
  Prints the specified register, at the specified location and device.

Examples:
    dreg cfg 60,0xf,0
    dreg dbg 0x54
    dreg dbg 0x54 -d 0 -l 0,0
    dreg dbg 0x54 -l 0,0
    dreg dbg 0x54 -d 0
"""

command_metadata = {
    "short": "dreg",
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

reg_types = ["cfg", "dbg"]


def parse_reg_params(reg_params):
    params = []
    for param in reg_params.split(","):
        try:
            if param.startswith("0x"):
                params.append(int(param, 16))
            else:
                params.append(int(param))
        except ValueError:
            raise ValueError("Invalid register parameter. Use integers separated by commas.")

    return params


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

    reg_type = dopt.args["<reg-type>"]
    reg_params = parse_reg_params(dopt.args["<reg_parameters>"])

    register = create_register_description(reg_type, reg_params)

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            print(TensixDebug(loc, device.id(), context).read_tensix_register(register))
