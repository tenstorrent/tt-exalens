# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-unpack [ -d <device> ] [ -l <loc> ]

Options:
  -d <device>   Device ID. Optional and repeatable. Default: current device
  -l <loc       Either X-Y or R,C location of a core

Description:
  Prints unpacker's configuration register.

Examples:
  unpack
  unpack -d 0
  unpack -l 0,0
  unpack -d 0 -l 0,0
"""

command_metadata = {
    "short": "unpack",
    "type": "dev",
    "description": __doc__,
    "context": ["limited"],
}

from ttlens.tt_uistate import UIState
from ttlens.tt_debug_tensix import TensixDebug

from ttlens import tt_commands


def print_dict_list(dicts: list[dict]):
    for id, dict in enumerate(dicts):
        if len(dicts) > 1:
            print(f"  REG_ID = {id + 1}:")
        for key, value in dict.items():
            print(f"    {key}: {value}")


def run(cmd_text, context, ui_state: UIState = None):
    dopt = tt_commands.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            debug_tensix = TensixDebug(loc, device.id(), context)
            device = debug_tensix.context.devices[debug_tensix.device_id]

            alu_config = device.get_alu_config(debug_tensix)
            tile_descriptor = device.get_unpack_tile_descriptor(debug_tensix)
            unpack_config = device.get_unpack_config(debug_tensix)

            print("ALU CONFIG:")
            print_dict_list(alu_config)
            print("TILE DESC:")
            print_dict_list(tile_descriptor)
            print("UNPACK_CONFIG")
            print_dict_list(unpack_config)

    return None
