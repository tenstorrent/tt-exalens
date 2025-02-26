# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-config-reg [<config-reg>] [ -d <device> ] [ -l <loc> ]

Options:
  -d <device>   Device ID. Optional and repeatable. Default: current device
  -l <loc>      Either X-Y or R,C location of a core
  <config-reg>  Configuration register name to dump. Options: [all, alu, pack, unpack] Default: all

Description:
  Prints the configuration register of the given name, at the specified location and device.

Examples:
  cfg
  cfg -d 0
  cfg -l 0,0
  cfg all
  cfg alu
  cfg pack
  cfg unpack
"""

command_metadata = {
    "short": "cfg",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "command_option_names": ["--device", "--loc"],
}

from ttlens.uistate import UIState
from ttlens.debug_tensix import TensixDebug
from ttlens.device import Device
from ttlens import commands
from ttlens.util import convert_value, put_table_list_side_by_side, INFO, CLR_GREEN, CLR_END

from tabulate import tabulate

# Creates list of column names for configuration register table
def create_column_names(num_of_columns):
    if num_of_columns == 1:
        return ["VALUES"]
    else:
        return [f"REG_ID = {i}" for i in range(1, num_of_columns + 1)]


# Converts list of configuration registers to table
def config_regs_to_table(
    config_regs: list[dict], table_name: str, column_names: list[str], debug_tensix: TensixDebug, device: Device
):
    keys = config_regs[0]
    data = []
    for key in keys:
        if key == "blobs_y_start_lo":
            continue
        elif key == "blobs_y_start_hi":
            row = ["blobs_y_start"]
        else:
            row = [key]
        for config in config_regs:
            if key == "blobs_y_start_hi":
                row.append(
                    (debug_tensix.read_tensix_register(config["blobs_y_start_hi"]) << 16)
                    + debug_tensix.read_tensix_register(config["blobs_y_start_lo"])
                )
                continue
            if key == "blobs_y_start_low":
                continue
            if key in config:
                value = debug_tensix.read_tensix_register(config[key])
                row.append(convert_value(value, device.get_tensix_register_description(config[key]).data_type))
            else:
                row.append("/")
        data.append(row)

    headers = [table_name] + column_names

    return tabulate(data, headers=headers, tablefmt="simple_outline", colalign=("left",) * len(headers))


def run(cmd_text, context, ui_state: UIState = None):
    dopt = commands.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            INFO(f"Configuration registers for location {loc} on device {device.id()}")

            debug_tensix = TensixDebug(loc, device.id(), context)
            device = debug_tensix.context.devices[debug_tensix.device_id]

            cfg = dopt.args["<config-reg>"] if dopt.args["<config-reg>"] else "all"

            if cfg == "alu" or cfg == "all":
                print(f"{CLR_GREEN}ALU{CLR_END}")

                if device._arch == "grayskull":
                    print("Not supported on grayskull")
                else:
                    alu_config = device.get_alu_config()
                    alu_config_table = config_regs_to_table(
                        alu_config, "ALU CONFIG", create_column_names(len(alu_config)), debug_tensix, device
                    )
                    print(alu_config_table)

            if cfg == "unpack" or cfg == "all":
                print(f"{CLR_GREEN}UNPACKER{CLR_END}")

                tile_descriptor = device.get_unpack_tile_descriptor()
                unpack_config = device.get_unpack_config()

                tile_descriptor_table = config_regs_to_table(
                    tile_descriptor, "TILE DESCRIPTOR", create_column_names(len(tile_descriptor)), debug_tensix, device
                )
                unpack_config_table = config_regs_to_table(
                    unpack_config, "UNPACK CONFIG", create_column_names(len(unpack_config)), debug_tensix, device
                )

                print(put_table_list_side_by_side([unpack_config_table, tile_descriptor_table]))

            if cfg == "pack" or cfg == "all":
                print(f"{CLR_GREEN}PACKER{CLR_END}")

                pack_config = device.get_pack_config()
                pack_counters = device.get_pack_counters()
                edge_offset = device.get_pack_edge_offset()
                pack_strides = device.get_pack_strides()

                pack_config_table = config_regs_to_table(
                    pack_config, "PACK CONFIG", create_column_names(len(pack_config)), debug_tensix, device
                )
                pack_counters_table = config_regs_to_table(
                    pack_counters, "COUNTERS", create_column_names(len(pack_counters)), debug_tensix, device
                )
                edge_offset_table = config_regs_to_table(
                    edge_offset, "EDGE OFFSET", create_column_names(len(edge_offset)), debug_tensix, device
                )
                pack_strides_table = config_regs_to_table(
                    pack_strides, "STRIDES", create_column_names(len(pack_strides)), debug_tensix, device
                )

                if device._arch == "wormhole_b0" or device._arch == "blackhole":
                    relu_config = device.get_relu_config()
                    dest_rd_ctrl = device.get_pack_dest_rd_ctrl()

                    relu_config_table = config_regs_to_table(
                        relu_config, "RELU CONFIG", create_column_names(len(relu_config)), debug_tensix, device
                    )
                    dest_rd_ctrl_table = config_regs_to_table(
                        dest_rd_ctrl, "DEST RD CTRL", create_column_names(len(dest_rd_ctrl)), debug_tensix, device
                    )

                    print(put_table_list_side_by_side([edge_offset_table, pack_counters_table, dest_rd_ctrl_table]))
                    print(put_table_list_side_by_side([pack_config_table, relu_config_table, pack_strides_table]))

                else:
                    print(put_table_list_side_by_side([pack_config_table, pack_counters_table]))
                    print(put_table_list_side_by_side([edge_offset_table, pack_strides_table]))
