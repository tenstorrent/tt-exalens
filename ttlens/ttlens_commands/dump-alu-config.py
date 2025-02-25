# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-alu-config [ -d <device> ] [ -l <loc> ]

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

from ttlens.uistate import UIState
from ttlens.debug_tensix import TensixDebug
from ttlens import commands
from ttlens.util import dict_list_to_table, INFO

import tabulate


def print_config_regs(config_regs: list[dict], debug_tensix: TensixDebug, table_name: str, column_names: list[str]):
    keys = config_regs[0]
    data = []
    for key in keys:
        row = [key]
        for config in config_regs:
            if key in config:
                row.append(debug_tensix.read_tensix_register(config[key]))
            else:
                row.append("/")
    data.append(row)

    headers = [table_name] + [column_names]

    return tabulate(data, headers=headers, tablefmt="simple_outline", colalign=("left",) * len(headers))


def run(cmd_text, context, ui_state: UIState = None):
    dopt = commands.tt_docopt(
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

            alu_config = device.get_alu_config()
            print_config_regs(alu_config, debug_tensix, "ALU_CONIFG", ["VALUES"])

    return None
