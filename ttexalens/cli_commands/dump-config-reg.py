# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-config-reg list-names <group-name>
  dump-config-reg <group-name> [ <reg-name> ] [ -d <device> ] [ -l <loc> ]

Arguments:
  <group-name>  Configuration register group name to dump. Options: [alu, pack, unpack, all]

Options:
  <reg-name>    Configuration register name to dump.
  -d <device>   Device ID. Optional. Default: current device
  -l <loc>      Core location in X-Y or R,C format

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

from ttexalens.uistate import UIState
from ttexalens.debug_tensix import TensixDebug
from ttexalens.device import Device
from ttexalens import command_parser
from ttexalens.util import (
    convert_value,
    put_table_list_side_by_side,
    INFO,
    ERROR,
    CLR_GREEN,
    CLR_END,
    dict_list_to_table,
)
from typing import List
from tabulate import tabulate

possible_groups = ["alu", "pack", "unpack", "all"]

# Creates list of column names for configuration register table
def create_column_names(num_of_columns):
    if num_of_columns == 1:
        return ["VALUES"]
    else:
        return [f"REG_ID = {i}" for i in range(1, num_of_columns + 1)]


# Converts list of configuration registers to table
def config_regs_to_table(config_regs: List[dict], table_name: str, debug_tensix: TensixDebug, device: Device):
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
                config[key] = convert_value(value, reg_desc.data_type, (reg_desc.mask).bit_count())

    return dict_list_to_table(config_regs, table_name, create_column_names(len(config_regs)))


def print_keys(dict: dict):
    for key in dict.keys():
        print(key)


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    cfg = dopt.args["<group-name>"]
    if cfg not in possible_groups:
        ERROR(f"Invalid register group name. Options: {possible_groups}")
        return
    reg = dopt.args["<reg-name>"] if dopt.args["<reg-name>"] else None

    for device in dopt.for_each("--device", context, ui_state):

        if dopt.args["list-names"]:

            if cfg == "alu" or cfg == "all":
                alu_config = device.get_alu_config()
                print(f"{CLR_GREEN}ALU{CLR_END}")
                print_keys(alu_config[0])
            if cfg == "unpack" or cfg == "all":
                tile_descriptor = device.get_unpack_tile_descriptor()
                unpack_config = device.get_unpack_config()
                print(f"{CLR_GREEN}UNPACK{CLR_END}")
                print_keys(tile_descriptor[0])
                print_keys(unpack_config[0])
            if cfg == "pack" or cfg == "all":
                pack_config = device.get_pack_config()
                pack_counters = device.get_pack_counters()
                edge_offset = device.get_pack_edge_offset()
                pack_strides = device.get_pack_strides()
                relu_config = device.get_relu_config()
                dest_rd_ctrl = device.get_pack_dest_rd_ctrl()
                print(f"{CLR_GREEN}PACK{CLR_END}")
                print_keys(pack_config[0])
                print_keys(pack_counters[0])
                print_keys(edge_offset[0])
                print_keys(pack_strides[0])
                print_keys(relu_config[0])
                print_keys(dest_rd_ctrl[0])

            return

        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            INFO(f"Configuration registers for location {loc} on device {device.id()}")

            debug_tensix = TensixDebug(loc, device.id(), context)
            device = debug_tensix.context.devices[debug_tensix.device_id]

            if cfg == "alu" or cfg == "all":
                print(f"{CLR_GREEN}ALU{CLR_END}")

                if device._arch == "grayskull":
                    print("Not supported on grayskull")
                else:
                    alu_config = device.get_alu_config()
                    if reg:
                        if reg in alu_config[0]:
                            for config in alu_config:
                                reg_desc = device.get_tensix_register_description(config[reg])
                                print(
                                    f"{reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                                )
                        else:
                            ERROR(f"{reg} not found in ALU")
                    else:
                        alu_config_table = config_regs_to_table(alu_config, "ALU CONFIG", debug_tensix, device)
                        print(alu_config_table)

            if cfg == "unpack" or cfg == "all":
                print(f"{CLR_GREEN}UNPACKER{CLR_END}")

                tile_descriptor = device.get_unpack_tile_descriptor()
                unpack_config = device.get_unpack_config()

                if reg:
                    if reg in tile_descriptor[0]:
                        for config in tile_descriptor:
                            reg_desc = device.get_tensix_register_description(config[reg])
                            print(
                                f"{reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                            )
                    elif reg in unpack_config[0]:
                        for config in unpack_config:
                            reg_desc = device.get_tensix_register_description(config[reg])
                            print(
                                f"{reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                            )
                    else:
                        ERROR(f"{reg} not found in UNPACK")
                else:
                    tile_descriptor_table = config_regs_to_table(
                        tile_descriptor, "TILE DESCRIPTOR", debug_tensix, device
                    )
                    unpack_config_table = config_regs_to_table(unpack_config, "UNPACK CONFIG", debug_tensix, device)

                    print(put_table_list_side_by_side([unpack_config_table, tile_descriptor_table]))

            if cfg == "pack" or cfg == "all":
                print(f"{CLR_GREEN}PACKER{CLR_END}")

                pack_config = device.get_pack_config()
                pack_counters = device.get_pack_counters()
                edge_offset = device.get_pack_edge_offset()
                pack_strides = device.get_pack_strides()
                if device._arch == "wormhole_b0" or device._arch == "blackhole":
                    relu_config = device.get_relu_config()
                    dest_rd_ctrl = device.get_pack_dest_rd_ctrl()

                if reg:
                    if reg in pack_config[0]:
                        for i, config in enumerate(pack_config):
                            reg_desc = device.get_tensix_register_description(config[reg])
                            print(
                                f"({i+1}) {reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                            )
                    elif reg in pack_counters[0]:
                        for config in pack_counters:
                            reg_desc = device.get_tensix_register_description(config[reg])
                            print(
                                f"{reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                            )
                    elif reg in edge_offset[0]:
                        for config in edge_offset:
                            reg_desc = device.get_tensix_register_description(config[reg])
                            print(
                                f"{reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                            )
                    elif reg in pack_strides[0]:
                        for config in pack_strides:
                            reg_desc = device.get_tensix_register_description(config[reg])
                            print(
                                f"{reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                            )
                    elif device._arch == "wormhole_b0" or device._arch == "blackhole":
                        if reg in relu_config[0]:
                            for config in relu_config:
                                reg_desc = device.get_tensix_register_description(config[reg])
                                print(
                                    f"{reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                                )
                        elif reg in dest_rd_ctrl[0]:
                            for config in dest_rd_ctrl:
                                reg_desc = device.get_tensix_register_description(config[reg])
                                print(
                                    f"{reg} = {convert_value(debug_tensix.read_tensix_register(config[reg]), reg_desc.data_type, bin(reg_desc.mask).count('1'))}"
                                )
                    else:
                        ERROR(f"{reg} not found in PACK")
                else:
                    pack_config_table = config_regs_to_table(pack_config, "PACK CONFIG", debug_tensix, device)
                    pack_counters_table = config_regs_to_table(pack_counters, "COUNTERS", debug_tensix, device)
                    edge_offset_table = config_regs_to_table(edge_offset, "EDGE OFFSET", debug_tensix, device)
                    pack_strides_table = config_regs_to_table(pack_strides, "STRIDES", debug_tensix, device)

                    if device._arch == "wormhole_b0" or device._arch == "blackhole":
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
