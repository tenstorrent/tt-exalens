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
from ttlens.tt_debug_tensix import TensixDebug
from ttlens import tt_commands
from ttlens.tt_util import dict_list_to_table, put_table_list_side_by_side

import tabulate


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

                print(put_table_list_side_by_side([edge_offset_table, pack_counters_table, dest_rd_ctrl_table]))
                print(put_table_list_side_by_side([pack_config_table, relu_config_table, pack_strides_table]))

            else:
                print(put_table_list_side_by_side([pack_config_table, pack_counters_table]))
                print(put_table_list_side_by_side([edge_offset_table, pack_strides_table]))

    return None
