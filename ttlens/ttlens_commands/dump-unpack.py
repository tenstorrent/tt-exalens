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

import tabulate


def dict_list_to_table(dicts: list[dict], register_name: str) -> str:
    keys = dicts[0].keys()
    data = [[key] + [d[key] for d in dicts] for key in keys]
    if len(dicts) == 1:
        headers = [register_name] + ["VALUES"]
    else:
        headers = [register_name] + [f"REG_ID={i+1}" for i in range(len(dicts))]

    return tabulate.tabulate(data, headers=headers, tablefmt="grid")


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

            print(dict_list_to_table(alu_config, "ALU CONFIG"))
            print(dict_list_to_table(tile_descriptor, "TILE DESCRIPTOR"))
            print(dict_list_to_table(unpack_config, "UNPACK CONFIG"))

    return None
