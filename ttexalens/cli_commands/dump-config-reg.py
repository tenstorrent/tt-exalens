# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-config-reg [ <config-reg> ] [ -d <device> ] [ -l <loc> ] [ -v ] [ -t <thread-id> ]

Options:
  <config-reg>    Configuration register name to dump. Options: [all, alu, pack, unpack] Default: all
  -d <device>     Device ID. Optional. Default: current device
  -l <loc>        Core location in X-Y or R,C format. Default: current core
  -v              Verbose mode. Prints all general purpose registers.
  -t <thread-id>  Thread ID. Options: [0, 1, 2] Default: all
Description:
  Prints the configuration register of the given name, at the specified location and device.

Examples:
  cfg              # Prints all configuration registers for current device and core
  cfg -d 0         # Prints all configuration registers for device with id 0 and current core
  cfg -l 0,0       # Pirnts all configuration registers for current device and core at location 0,0
  cfg all          # Prints all configuration registers for current device and core
  cfg alu          # Prints alu configuration registers for current device and core
  cfg pack         # Prints packer's configuration registers for current device and core
  cfg unpack       # Prints unpacker's configuration registers for current device and core
  cfg gpr          # Prints general purpose registers for current device and core
  cfg gpr -v       # Prints all general purpose registers for current device and core
  cfg gpr -t 0,1    # Prints general purpose registers for threads 0 and 1 for current device and core
"""

command_metadata = {
    "short": "cfg",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "command_option_names": ["--device", "--loc"],
}

import copy

import tabulate
from ttexalens import util
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

possible_registers = ["all", "alu", "pack", "unpack", "gpr"]

# Creates list of column names for configuration register table
def create_column_names(num_of_columns):
    if num_of_columns == 1:
        return ["VALUES"]
    else:
        return [f"REG_ID = {i}" for i in range(1, num_of_columns + 1)]


# Converts list of configuration registers to table
def config_regs_to_table(config_regs: list[dict[str, str]], table_name: str, register_store: RegisterStore):
    config_reg_values: list[dict[str, int]] = []
    keys = list(config_regs[0].keys())

    for config in config_regs:
        config_reg_value: dict[str, int] = {}
        for key in keys:
            if key in config:
                if key.endswith("_hi"):
                    continue
                elif key.endswith("_lo"):
                    value = (register_store.read_register(config[key]) << 16) + register_store.read_register(
                        config[key[:-3] + "_hi"]
                    )
                    name = key[:-3]
                else:
                    value = register_store.read_register(config[key])
                    name = key
                reg_desc = register_store.get_register_description(config[key])
                config_reg_value[name] = format_register_value(value, reg_desc.data_type, reg_desc.mask.bit_count())
        config_reg_values.append(config_reg_value)

    return dict_list_to_table(config_reg_values, table_name, create_column_names(len(config_reg_values)))


def run(cmd_text, context, ui_state: UIState):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )
    cfg = dopt.args["<config-reg>"] if dopt.args["<config-reg>"] else "all"
    if cfg not in possible_registers:
        raise ValueError(f"Invalid configuration register: {cfg}. Possible values: {possible_registers}")

    device: Device
    for device in dopt.for_each("--device", context, ui_state):
        conf_reg_desc = device.get_tensix_configuration_registers_description()
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            INFO(f"Configuration registers for location {loc} on device {device.id()}")

            noc_block = device.get_block(loc)
            if not noc_block:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a NOC block.")
                continue
            if noc_block.block_type != "functional_workers":
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} is not a functional worker block.")
                continue
            register_store = noc_block.get_register_store()

            if cfg == "alu" or cfg == "all":
                print(f"{CLR_GREEN}ALU{CLR_END}")
                alu_config_table = config_regs_to_table(conf_reg_desc.alu_config, "ALU CONFIG", register_store)
                print(alu_config_table)
            if cfg == "unpack" or cfg == "all":
                print(f"{CLR_GREEN}UNPACKER{CLR_END}")
                tile_descriptor_table = config_regs_to_table(
                    conf_reg_desc.unpack_tile_descriptor, "TILE DESCRIPTOR", register_store
                )
                unpack_config_table = config_regs_to_table(conf_reg_desc.unpack_config, "UNPACK CONFIG", register_store)
                print(put_table_list_side_by_side([unpack_config_table, tile_descriptor_table]))
            if cfg == "pack" or cfg == "all":
                print(f"{CLR_GREEN}PACKER{CLR_END}")
                pack_config_table = config_regs_to_table(conf_reg_desc.pack_config, "PACK CONFIG", register_store)
                pack_counters_table = config_regs_to_table(conf_reg_desc.pack_counters, "COUNTERS", register_store)
                edge_offset_table = config_regs_to_table(conf_reg_desc.pack_edge_offset, "EDGE OFFSET", register_store)
                pack_strides_table = config_regs_to_table(conf_reg_desc.pack_strides, "STRIDES", register_store)
                if device.is_wormhole() or device.is_blackhole():
                    relu_config_table = config_regs_to_table(conf_reg_desc.relu_config, "RELU CONFIG", register_store)
                    dest_rd_ctrl_table = config_regs_to_table(
                        conf_reg_desc.pack_dest_rd_ctrl, "DEST RD CTRL", register_store
                    )
                    print(pack_counters_table)
                    print(pack_config_table)
                    print(put_table_list_side_by_side([edge_offset_table, pack_strides_table]))
                    print(put_table_list_side_by_side([relu_config_table, dest_rd_ctrl_table]))
                else:
                    print(pack_counters_table)
                    print(pack_config_table)
                    print(put_table_list_side_by_side([edge_offset_table, pack_strides_table]))
            if cfg == "gpr" or cfg == "all":
                verbose = dopt.args["-v"]
                thread_ids = (
                    [int(thread_id) for thread_id in dopt.args["-t"].split(",")] if dopt.args["-t"] else [0, 1, 2]
                )
                print(f"{CLR_GREEN}GPR{CLR_END}")
                tables: list[str] = []
                for thread_id in thread_ids:
                    gpr_mapping = conf_reg_desc.general_purpose_registers[thread_id]
                    rows: list[list[str]] = []
                    merged_registers: dict[str, int] = {}
                    for register_name in gpr_mapping:
                        if verbose or not register_name.startswith("ID"):
                            reg_desc = register_store.registers[gpr_mapping[register_name]]
                            if register_name.endswith("_lo"):
                                value = register_store.read_register(
                                    gpr_mapping[register_name[:-3] + "_hi"]
                                ) << 16 + register_store.read_register(gpr_mapping[register_name])
                                merged_registers[register_name[:-3]] = format_register_value(
                                    value, reg_desc.data_type, reg_desc.mask.bit_count()
                                )
                            value = register_store.read_register(gpr_mapping[register_name])
                            rows.append(
                                [
                                    register_name,
                                    format_register_value(value, reg_desc.data_type, reg_desc.mask.bit_count()),
                                ]
                            )
                    # Adding merged registers to the end of the table
                    for register_name in merged_registers:
                        rows.append([register_name, str(merged_registers[register_name])])
                    table = tabulate.tabulate(
                        rows,
                        headers=[f"Thread {thread_id}", "Values"],
                        tablefmt="simple_outline",
                    )
                    tables.append(table)
                print(put_table_list_side_by_side(tables))
