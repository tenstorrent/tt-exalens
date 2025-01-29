# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-cfg-reg <core-loc> [-d <D>...]

Arguments:
  <core-loc>     Either X-Y or R,C location of a core

Options:
  -d <D>            Device ID. Optional and repeatable. Default: current device

Description:
  Prints configuration register.

Examples:
  cfg
  cfg 0,0
"""

command_metadata = {
    "short": "cfg",
    "type": "dev",
    "description": __doc__,
    "context": ["limited"],
}

from docopt import docopt

from ttlens.tt_uistate import UIState
from ttlens.tt_coordinate import OnChipCoordinate
from ttlens.tt_debug_tensix import TensixDebug


def print_alu_config_field(debug_tensix: TensixDebug, name: str):
    print(f"{name}: 0x{debug_tensix.read_tensix_register(name)}")


def print_alu_config(debug_tensix: TensixDebug):
    print_alu_config_field(debug_tensix, "ALU_ROUNDING_MODE_Fpu_srnd_en")
    print_alu_config_field(debug_tensix, "ALU_ROUNDING_MODE_Gasket_srnd_en")
    print_alu_config_field(debug_tensix, "ALU_ROUNDING_MODE_Packer_srnd_en")
    print_alu_config_field(debug_tensix, "ALU_ROUNDING_MODE_Padding")
    print_alu_config_field(debug_tensix, "ALU_ROUNDING_MODE_GS_LF")
    print_alu_config_field(debug_tensix, "ALU_ROUNDING_MODE_Bfp8_HF")
    print_alu_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG0_SrcAUnsigned")
    print_alu_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG0_SrcBUnsigned")
    print_alu_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG0_SrcA")
    print_alu_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG1_SrcB")
    print_alu_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG2_Dstacc")
    print_alu_config_field(debug_tensix, "ALU_ACC_CTRL_Fp32_enabled")
    print_alu_config_field(debug_tensix, "ALU_ACC_CTRL_SFPU_Fp32_enabled")
    print_alu_config_field(debug_tensix, "ALU_ACC_CTRL_INT8_math_enabled")


def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    current_device_id = ui_state.current_device_id
    current_location = ui_state.current_location

    core_loc_str = args["<core-loc>"] if args["<core-loc>"] else [f"{current_location}"]
    device_ids = args["-d"] if args["-d"] else [f"{current_device_id}"]
    device_array = []
    for device_id in device_ids:
        device_array.append(int(device_id, 0))

    for device_id in device_array:
        current_device = context.devices[device_id]
        core_loc = OnChipCoordinate.create(core_loc_str, device=current_device)

        debug_tensix = TensixDebug(core_loc, device_id, context)
        print_alu_config(debug_tensix)

    return None
