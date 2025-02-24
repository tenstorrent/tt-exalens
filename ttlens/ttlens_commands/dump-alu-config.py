# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-alu [ -d <device> ] [ -l <loc> ]

Options:
  -d <device>   Device ID. Optional and repeatable. Default: current device
  -l <loc>      Either X-Y or R,C location of a core

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
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "command_option_names": ["--device", "--loc"],
}

from ttlens.tt_uistate import UIState
from ttlens.tt_debug_tensix import TensixDebug
from ttlens import tt_commands
from ttlens.tt_util import dict_list_to_table, INFO

import tabulate


def run(cmd_text, context, ui_state: UIState = None):
    dopt = tt_commands.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    for device in dopt.for_each("--device", context, ui_state):

        if device._arch == "grayskull":
            print("Not supported on grayskull")
            continue

        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            INFO(f"Alu configuration register for location {loc} on device {device.id()}")

            debug_tensix = TensixDebug(loc, device.id(), context)
            device = debug_tensix.context.devices[debug_tensix.device_id]

            alu_config = device.get_alu_config(debug_tensix)

            alu_config_table = dict_list_to_table(alu_config, "ALU CONFIG")

            print(alu_config_table)

    return None
