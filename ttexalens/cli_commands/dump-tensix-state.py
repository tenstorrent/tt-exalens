# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-tensix-state [ <group> ] [ -d <device> ] [ -l <loc> ] [ -v ] [ -t <thread-id> ] [ -a <l1-address> ]

Options:
  <group>         Tensix group to dump. Options: [all, alu, pack, unpack, gpr, rwc, adc] Default: all
  -t <thread-id>  Thread ID. Options: [0, 1, 2] Default: all (only for gpr group)
  -a <l1-address> L1 address to save group data.
Description:
  Prints the tensix group of the given name, at the specified location and device.

Examples:
  tensix              # Prints tensix state for current device and core (excludes RWC and ADC groups)
  tensix -a 0x0       # Prints tensix state for current device and core using L1 address 0x0
  tensix -d 0         # Prints tensix state for device with id 0 and current core
  tensix -l 0,0       # Prints tensix state for current device and core at location 0,0
  tensix all          # Prints tensix state for current device and core
  tensix alu          # Prints alu configuration registers for current device and core
  tensix pack         # Prints packer's configuration registers for current device and core
  tensix unpack       # Prints unpacker's configuration registers for current device and core
  tensix gpr          # Prints general purpose registers for current device and core
  tensix gpr -v       # Prints all general purpose registers for current device and core
  tensix gpr -t 0,1   # Prints general purpose registers for threads 0 and 1 for current device and core
  tensix rwc -a 0x0   # Prints RWC registers for current device and core using L1 address 0x0
  tensix adc -a 0x0   # Prints ADC registers for current device and core using L1 address 0x0
"""

import tabulate

from ttexalens import util
from ttexalens.register_store import RegisterStore, format_register_value
from ttexalens.uistate import UIState
from ttexalens.device import Device
from ttexalens.util import (
    put_table_list_side_by_side,
    INFO,
    CLR_GREEN,
    CLR_END,
    dict_list_to_table,
)
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="tensix",
    type="low-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)

possible_groups = ["all", "alu", "pack", "unpack", "gpr", "rwc", "adc"]

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
                    # Merging split registers into one
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


def print_3_tables_side_by_side(tables: list[str]):
    tables = sorted(tables, key=lambda table: len(table))
    for i in range(0, len(tables), 3):
        end = i + 3 if i + 3 < len(tables) else len(tables)
        print(put_table_list_side_by_side(tables[i:end][::-1]))
        if end == len(tables):
            break


def run(cmd_text, context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    group = dopt.args["<group>"] if dopt.args["<group>"] else "all"
    l1_address = int(dopt.args["-a"], 0) if dopt.args["-a"] else None

    if group not in possible_groups:
        raise ValueError(f"Invalid tensix group name: {group}. Possible values: {possible_groups}")

    device: Device
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        conf_reg_desc = device.get_tensix_registers_description()
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            INFO(f"Tensix registers for location {loc} on device {device.id()}")

            noc_block = device.get_block(loc)
            if not noc_block:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a NOC block.")
                continue
            if noc_block.block_type != "functional_workers":
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} is not a functional worker block.")
                continue
            register_store = noc_block.get_register_store()
            debug_bus = noc_block.debug_bus
            if debug_bus is None:
                util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a debug bus.")
                continue

            if group == "alu" or group == "all":
                print(f"{CLR_GREEN}ALU{CLR_END}")
                alu_config_table = config_regs_to_table(conf_reg_desc.alu_config, "ALU CONFIG", register_store)
                print(alu_config_table)
            if group == "unpack" or group == "all":
                print(f"{CLR_GREEN}UNPACKER{CLR_END}")
                tile_descriptor_table = config_regs_to_table(
                    conf_reg_desc.unpack_tile_descriptor, "TILE DESCRIPTOR", register_store
                )
                unpack_config_table = config_regs_to_table(conf_reg_desc.unpack_config, "UNPACK CONFIG", register_store)
                print(put_table_list_side_by_side([unpack_config_table, tile_descriptor_table]))
            if group == "pack" or group == "all":
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
            if group == "gpr" or group == "all":
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
                                # Merging split registers into one
                                value = (
                                    register_store.read_register(gpr_mapping[register_name[:-3] + "_hi"]) << 16
                                ) + register_store.read_register(gpr_mapping[register_name])
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
                    tables.append(
                        tabulate.tabulate(
                            rows,
                            headers=[f"Thread {thread_id}", "Values"],
                            tablefmt="simple_outline",
                        )
                    )
                print(put_table_list_side_by_side(tables))

            if group == "rwc" or group == "all":

                if device.is_blackhole():
                    util.WARN(
                        "Skipping RWC group since they are currently not supported on Blackhole devices. Issue: #729"
                    )
                elif l1_address is None:
                    util.WARN("No L1 address provided. Skipping RWC group. Use -a option to specify L1 address.")
                else:
                    print(f"{CLR_GREEN}RWCs{CLR_END}")
                    rwc_signal_groups = [
                        group_name for group_name in debug_bus.group_names if group_name.startswith("rwc")
                    ]
                    tables_rwc: list[str] = []
                    for signal_group in rwc_signal_groups:
                        signal_dict_rwc: dict[str, str] = {}
                        group_data = debug_bus.read_signal_group(signal_group, l1_address)
                        for signal_name, signal_value in group_data.items():
                            if signal_name.startswith("rwc_"):
                                signal_name = signal_name[4:]
                            signal_dict_rwc[signal_name] = hex(signal_value)

                        tables_rwc.append(dict_list_to_table([signal_dict_rwc], signal_group[4:].upper(), ["Values"]))

                    print_3_tables_side_by_side(tables_rwc)

            if group == "adc" or group == "all":

                if l1_address is None:
                    util.WARN("No L1 address provided. Skipping ADC group. Use -a option to specify L1 address.")
                else:
                    print(f"{CLR_GREEN}ADCs{CLR_END}")
                    adc_signal_groups = [
                        group_name for group_name in debug_bus.group_names if group_name.startswith("adc")
                    ]
                    tables_adc: list[str] = []
                    for signal_group in adc_signal_groups:
                        signal_dict_adc: dict[str, str] = {}
                        group_data = debug_bus.read_signal_group(signal_group, l1_address)
                        for signal_name, signal_value in group_data.items():
                            if signal_name.startswith(signal_group + "_"):
                                signal_name = signal_name[len(signal_group) + 1 :]
                            signal_dict_adc[signal_name] = hex(signal_value)

                        tables_adc.append(dict_list_to_table([signal_dict_adc], signal_group.upper(), ["Values"]))

                    print_3_tables_side_by_side(tables_adc)
