# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ]

Options:
  <config-reg>  Configuration register name to dump. Options: [all, alu, pack, unpack] Default: all
  -d <device>   Device ID. Optional. Default: current device
  -l <loc>      Core location in X-Y or R,C format. Default: current core

Description:
  Prints the configuration register of the given name, at the specified location and device.

Examples:
  cfg              # Prints all configuration registers for current device and core
  cfg -d 0         # Prints all configuration reigsters for device with id 0 and current core
  cfg -l 0,0       # Pirnts all configuration registers for current device and core at location 0,0
  cfg all          # Prints all configuration registers for current device and core
  cfg alu          # Prints alu configuration registers for current device and core
  cfg pack         # Prints packer's configuration registers for current device and core
  cfg unpack       # Prints unpacker's configuration registers for current device and core
"""

command_metadata = {
    "short": "cfg",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "command_option_names": ["--device", "--loc"],
}

from ttexalens.register_store import RegisterStore, format_register_value
from ttexalens.uistate import UIState
from ttexalens.device import Device
from ttexalens import command_parser
from ttexalens.util import (
    put_table_list_side_by_side,
    INFO,
    CLR_GREEN,
    CLR_END,
    dict_list_to_table,
)
from typing import List
from tabulate import tabulate

possible_registers = ["all", "alu", "pack", "unpack"]

# Creates list of column names for configuration register table
def create_column_names(num_of_columns):
    if num_of_columns == 1:
        return ["VALUES"]
    else:
        return [f"REG_ID = {i}" for i in range(1, num_of_columns + 1)]


# Converts list of configuration registers to table
def config_regs_to_table(config_regs: List[dict], table_name: str, register_store: RegisterStore):
    keys = list(config_regs[0].keys())

    if "blobs_y_start_lo" in keys and "blobs_y_start_hi" in keys:
        for config in config_regs:
            config["blobs_y_start"] = (
                register_store.read_register(config["blobs_y_start_hi"]) << 16
            ) + register_store.read_register(config["blobs_y_start_hi"])
            del config["blobs_y_start_lo"]
            del config["blobs_y_start_hi"]

        keys.remove("blobs_y_start_lo")
        keys.remove("blobs_y_start_hi")

    for config in config_regs:
        for key in keys:
            if key in config:
                reg_desc = register_store.get_register_description(config[key])
                value = register_store.read_register(reg_desc)
                config[key] = format_register_value(value, reg_desc.data_type, bin(reg_desc.mask).count("1"))

    return dict_list_to_table(config_regs, table_name, create_column_names(len(config_regs)))


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    cfg = dopt.args["<config-reg>"] if dopt.args["<config-reg>"] else "all"
    if cfg not in possible_registers:
        raise ValueError(f"Invalid configuration register: {cfg}. Possible values: {possible_registers}")

    device: Device
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            INFO(f"Configuration registers for location {loc} on device {device.id()}")

            register_store = device.get_register_store(loc)
            if cfg == "alu" or cfg == "all":
                print(f"{CLR_GREEN}ALU{CLR_END}")

                alu_config = device.get_alu_config()
                alu_config_table = config_regs_to_table(alu_config, "ALU CONFIG", register_store)
                print(alu_config_table)

            if cfg == "unpack" or cfg == "all":
                print(f"{CLR_GREEN}UNPACKER{CLR_END}")

                tile_descriptor = device.get_unpack_tile_descriptor()
                unpack_config = device.get_unpack_config()

                tile_descriptor_table = config_regs_to_table(tile_descriptor, "TILE DESCRIPTOR", register_store)
                unpack_config_table = config_regs_to_table(unpack_config, "UNPACK CONFIG", register_store)

                print(put_table_list_side_by_side([unpack_config_table, tile_descriptor_table]))

            if cfg == "pack" or cfg == "all":
                print(f"{CLR_GREEN}PACKER{CLR_END}")

                pack_config = device.get_pack_config()
                pack_counters = device.get_pack_counters()
                edge_offset = device.get_pack_edge_offset()
                pack_strides = device.get_pack_strides()

                pack_config_table = config_regs_to_table(pack_config, "PACK CONFIG", register_store)
                pack_counters_table = config_regs_to_table(pack_counters, "COUNTERS", register_store)
                edge_offset_table = config_regs_to_table(edge_offset, "EDGE OFFSET", register_store)
                pack_strides_table = config_regs_to_table(pack_strides, "STRIDES", register_store)

                if device._arch == "wormhole_b0" or device._arch == "blackhole":
                    relu_config = device.get_relu_config()
                    dest_rd_ctrl = device.get_pack_dest_rd_ctrl()

                    relu_config_table = config_regs_to_table(relu_config, "RELU CONFIG", register_store)
                    dest_rd_ctrl_table = config_regs_to_table(dest_rd_ctrl, "DEST RD CTRL", register_store)

                    print(pack_counters_table)
                    print(pack_config_table)
                    print(put_table_list_side_by_side([edge_offset_table, pack_strides_table]))
                    print(put_table_list_side_by_side([relu_config_table, dest_rd_ctrl_table]))

                else:
                    print(pack_counters_table)
                    print(pack_config_table)
                    print(put_table_list_side_by_side([edge_offset_table, pack_strides_table]))
