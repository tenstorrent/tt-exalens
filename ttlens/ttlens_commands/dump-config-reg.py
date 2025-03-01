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
from ttlens.util import convert_value, put_table_list_side_by_side, INFO, CLR_GREEN, CLR_END, dict_list_to_table

from tabulate import tabulate

# Creates list of column names for configuration register table
def create_column_names(num_of_columns):
    if num_of_columns == 1:
        return ["VALUES"]
    else:
        return [f"REG_ID = {i}" for i in range(1, num_of_columns + 1)]


# Converts list of configuration registers to table
def config_regs_to_table(config_regs: list[dict], table_name: str, debug_tensix: TensixDebug, device: Device):
    keys = list(config_regs[0].keys())

    if "blobs_y_start_lo" in keys and "blobs_y_start_hi" in keys:
        for config in config_regs:
            config["blobs_y_start"] = (
                debug_tensix.read_tensix_register(config["blobs_y_start_hi"]) << 16
            ) + debug_tensix.read_tensix_register(config["blobs_y_start_hi"])
            del config["blobs_y_start_lo"]
            del config["blobs_y_start_hi"]

        keys.remove("blobs_y_start_lo")
        keys.remove("blobs_y_start_hi")

    for config in config_regs:
        for key in keys:
            if key in config:
                value = debug_tensix.read_tensix_register(config[key])
                reg_desc = device.get_tensix_register_description(config[key])
                config[key] = convert_value(value, reg_desc.data_type, bin(reg_desc.mask).count("1"))

    return dict_list_to_table(config_regs, table_name, create_column_names(len(config_regs)))


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
                    alu_config_table = config_regs_to_table(alu_config, "ALU CONFIG", debug_tensix, device)
                    print(alu_config_table)

            if cfg == "unpack" or cfg == "all":
                print(f"{CLR_GREEN}UNPACKER{CLR_END}")

                tile_descriptor = device.get_unpack_tile_descriptor()
                unpack_config = device.get_unpack_config()

                tile_descriptor_table = config_regs_to_table(tile_descriptor, "TILE DESCRIPTOR", debug_tensix, device)
                unpack_config_table = config_regs_to_table(unpack_config, "UNPACK CONFIG", debug_tensix, device)

                print(put_table_list_side_by_side([unpack_config_table, tile_descriptor_table]))

            if cfg == "pack" or cfg == "all":
                print(f"{CLR_GREEN}PACKER{CLR_END}")

                pack_config = device.get_pack_config()
                pack_counters = device.get_pack_counters()
                edge_offset = device.get_pack_edge_offset()
                pack_strides = device.get_pack_strides()

                pack_config_table = config_regs_to_table(pack_config, "PACK CONFIG", debug_tensix, device)
                pack_counters_table = config_regs_to_table(pack_counters, "COUNTERS", debug_tensix, device)
                edge_offset_table = config_regs_to_table(edge_offset, "EDGE OFFSET", debug_tensix, device)
                pack_strides_table = config_regs_to_table(pack_strides, "STRIDES", debug_tensix, device)

                if device._arch == "wormhole_b0" or device._arch == "blackhole":
                    relu_config = device.get_relu_config()
                    dest_rd_ctrl = device.get_pack_dest_rd_ctrl()

                    relu_config_table = config_regs_to_table(relu_config, "RELU CONFIG", debug_tensix, device)
                    dest_rd_ctrl_table = config_regs_to_table(dest_rd_ctrl, "DEST RD CTRL", debug_tensix, device)

                    print(pack_counters_table)
                    print(pack_config_table)
                    print(put_table_list_side_by_side([edge_offset_table, pack_strides_table]))
                    print(put_table_list_side_by_side([relu_config_table, dest_rd_ctrl_table]))

                else:
                    print(pack_counters_table)
                    print(pack_config_table)
                    print(put_table_list_side_by_side([edge_offset_table, pack_strides_table]))
