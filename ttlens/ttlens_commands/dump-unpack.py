# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-unpack <core-loc> [-d <D>...]

Arguments:
  <core-loc>     Either X-Y or R,C location of a core

Options:
  -d <D>            Device ID. Optional and repeatable. Default: current device

Description:
  Prints configuration register.

Examples:
  unpack 0,0
"""

command_metadata = {
    "short": "unpack",
    "type": "dev",
    "description": __doc__,
    "context": ["limited"],
}

from docopt import docopt

from ttlens.tt_uistate import UIState
from ttlens.tt_coordinate import OnChipCoordinate
from ttlens.tt_debug_tensix import TensixDebug


def print_config_field(debug_tensix: TensixDebug, name: str):
    print(f" {name}: {debug_tensix.read_tensix_register(name)}")


def print_alu_config(debug_tensix: TensixDebug):
    print("ALU CONFIG:")
    print_config_field(debug_tensix, "ALU_ROUNDING_MODE_Fpu_srnd_en")
    print_config_field(debug_tensix, "ALU_ROUNDING_MODE_Gasket_srnd_en")
    print_config_field(debug_tensix, "ALU_ROUNDING_MODE_Packer_srnd_en")
    print_config_field(debug_tensix, "ALU_ROUNDING_MODE_Padding")
    print_config_field(debug_tensix, "ALU_ROUNDING_MODE_GS_LF")
    print_config_field(debug_tensix, "ALU_ROUNDING_MODE_Bfp8_HF")
    print_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG0_SrcAUnsigned")
    print_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG0_SrcBUnsigned")
    print_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG0_SrcA")
    print_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG1_SrcB")
    print_config_field(debug_tensix, "ALU_FORMAT_SPEC_REG2_Dstacc")
    print_config_field(debug_tensix, "ALU_ACC_CTRL_Fp32_enabled")
    print_config_field(debug_tensix, "ALU_ACC_CTRL_SFPU_Fp32_enabled")
    print_config_field(debug_tensix, "ALU_ACC_CTRL_INT8_math_enabled")


def print_unpack_tile_descriptor(debug_tensix: TensixDebug):
    print("TILE DESC0:")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_in_data_format")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_uncompressed")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_reserved_0")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_reserved_1")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_x_dim")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_y_dim")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_z_dim")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_w_dim")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_digest_type")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR0_digest_size")
    print("TILE DESC1:")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_in_data_format")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_uncompressed")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_reserved_0")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_reserved_1")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_x_dim")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_y_dim")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_z_dim")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_w_dim")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_digest_type")
    print_config_field(debug_tensix, "UNPACK_TILE_DESCRIPTOR1_digest_size")


def print_unpack_config(debug_tensix: TensixDebug):
    print("CONFIG0:")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_out_data_format")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_throttle_mode")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_context_count")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_haloize_mode")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_tileize_mode")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_unpack_src_reg_set_upd")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_unpack_if_sel")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_upsample_rate")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_reserved_1")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_upsample_and_interleave")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_shift_amount")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_uncompress_cntx0_3")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_unpack_if_sel_cntx0_3")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_force_shared_exp")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_reserved_2")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_uncompress_cntx4_7")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_unpack_if_sel_cntx4_7")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_reserved_3")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_limit_addr")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_reserved_4")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_fifo_size")
    print_config_field(debug_tensix, "UNPACK_CONFIG0_reserved_5")
    print("CONFIG1:")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_out_data_format")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_throttle_mode")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_context_count")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_haloize_mode")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_tileize_mode")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_unpack_src_reg_set_upd")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_unpack_if_sel")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_upsample_rate")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_reserved_1")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_upsample_and_interleave")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_shift_amount")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_uncompress_cntx0_3")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_unpack_if_sel_cntx0_3")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_force_shared_exp")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_reserved_2")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_uncompress_cntx4_7")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_unpack_if_sel_cntx4_7")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_reserved_3")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_limit_addr")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_reserved_4")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_fifo_size")
    print_config_field(debug_tensix, "UNPACK_CONFIG1_reserved_5")


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
        print_unpack_tile_descriptor(debug_tensix)
        print_unpack_config(debug_tensix)
        print_alu_config(debug_tensix)

    return None
