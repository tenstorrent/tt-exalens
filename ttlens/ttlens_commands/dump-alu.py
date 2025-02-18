# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-alu [ -d <device> ] [ -l <loc> ]

Options:
  -d <device>   Device ID. Optional and repeatable. Default: current device
  -l <loc       Either X-Y or R,C location of a core

Description:
  Prints alu configuration register.

Examples:
  alu
  alu -d 0
  alu -l 0,0
  alu -d 0 -l 0,0
"""

command_metadata = {
    "short": "alu",
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
    data = []
    for key in keys:
        row = [key]
        for d in dicts:
            if key in d:
                row.append(d[key])
            else:
                row.append("/")
        data.append(row)
            
    if len(dicts) == 1:
        headers = [register_name] + ["VALUES"]
    else:
        headers = [register_name] + [f"REG_ID = {i+1}" for i in range(len(dicts))]

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
            alu_config_table = dict_list_to_table(alu_config, "ALU CONFIG")

            print(alu_config_table)
            
    return None
