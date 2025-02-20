# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-pack [ -d <device> ] [ -l <loc> ]

Options:
  -d <device>   Device ID. Optional and repeatable. Default: current device
  -l <loc>      Either X-Y or R,C location of a core

Description:
  Prints packer's configuration register.

Examples:
  pack
  pack -d 0
  pack -l 0,0
  pack -d 0 -l 0,0
"""

command_metadata = {
    "short": "pack",
    "type": "dev",
    "description": __doc__,
    "context": ["limited"],
}

from ttlens.tt_uistate import UIState
from ttlens.tt_debug_tensix import TensixDebug, DataFormat
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


def join_tables_side_by_side(tables: list[str]) -> str:
    # Split each table into rows by lines
    split_tables = [table.split("\n") for table in tables]

    # Find the maximum number of rows across all tables
    max_rows = max(len(table) for table in split_tables)

    # Pad each table with empty lines to ensure equal row count
    padded_tables = [table + [" " * len(table[0])] * (max_rows - len(table)) for table in split_tables]

    # Combine the rows of all tables side by side
    side_by_side = ["   ".join(row) for row in zip(*padded_tables)]

    # Join all rows into a single string
    return "\n".join(side_by_side)


def run(cmd_text, context, ui_state: UIState = None):
    dopt = tt_commands.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            debug_tensix = TensixDebug(loc, device.id(), context)
            device = debug_tensix.context.devices[debug_tensix.device_id]

            pack_config = device.get_pack_config(debug_tensix)
            edge_offset = device.get_pack_edge_offset(debug_tensix)
            pack_counters = device.get_pack_counters(debug_tensix)
            pack_strides = device.get_pack_strides(debug_tensix)

            pack_config_table = dict_list_to_table(pack_config, "PACK CONFIG")
            edge_offset_table = dict_list_to_table(edge_offset, "EDGE OFFSET")
            pack_counters_table = dict_list_to_table(pack_counters, "PACK COUNTERS")
            pack_strides_table = dict_list_to_table(pack_strides, "PACK STRIDES")

            if device._arch == "wormhole_b0" or device._arch == "blackhole":
                relu_config = device.get_relu_config(debug_tensix)
                dest_rd_ctrl = device.get_pack_dest_rd_ctrl(debug_tensix)

                relu_config_table = dict_list_to_table(relu_config, "RELU CONFIG")
                dest_rd_ctrl_table = dict_list_to_table(dest_rd_ctrl, "DEST RD CTRL")

                print(join_tables_side_by_side([edge_offset_table, pack_counters_table, dest_rd_ctrl_table]))
                print(join_tables_side_by_side([pack_config_table, relu_config_table, pack_strides_table]))
            
            else:
                print(join_tables_side_by_side([pack_config_table, pack_counters_table]))
                print(join_tables_side_by_side([edge_offset_table, pack_strides_table]))

    return None
