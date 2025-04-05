# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from typing import Union
from ttexalens.hw.tensix.blackhole.noc_registers import noc_registers_offset_map
from ttexalens.register_store import (
    REGISTER_DATA_TYPE,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
    NocStatusRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


def get_register_noc_base_address_noc0(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, ConfigurationRegisterDescription):
        return None
    return get_register_internal_base_address_noc0(register_description)


def get_register_internal_base_address_noc0(register_description: RegisterDescription) -> int:
    if isinstance(register_description, ConfigurationRegisterDescription):
        return 0xFFEF0000
    elif isinstance(register_description, DebugRegisterDescription):
        return 0xFFB12000
    elif isinstance(register_description, NocControlRegisterDescription):
        return 0xFFB20000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0xFFB20100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0xFFB20200
    else:
        return None


def get_register_noc_base_address_noc1(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, ConfigurationRegisterDescription):
        return None
    return get_register_internal_base_address_noc1(register_description)


def get_register_internal_base_address_noc1(register_description: RegisterDescription) -> int:
    if isinstance(register_description, ConfigurationRegisterDescription):
        return 0xFFEF0000
    elif isinstance(register_description, DebugRegisterDescription):
        return 0xFFB12000
    elif isinstance(register_description, NocControlRegisterDescription):
        return 0xFFB30000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0xFFB30100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0xFFB30200
    else:
        return None


register_offset_map = {
    # UNPACK TILE DESCRIPTOR SEC0
    "UNPACK_TILE_DESCRIPTOR0_in_data_format": ConfigurationRegisterDescription(
        index=64, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "UNPACK_TILE_DESCRIPTOR0_uncompressed": ConfigurationRegisterDescription(
        index=64, mask=0x10, shift=4, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_TILE_DESCRIPTOR0_reserved_0": ConfigurationRegisterDescription(
        index=64, mask=0xE0, shift=5, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane": ConfigurationRegisterDescription(
        index=64, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_reserved_1": ConfigurationRegisterDescription(
        index=64, mask=0xF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_x_dim": ConfigurationRegisterDescription(
        index=64, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_y_dim": ConfigurationRegisterDescription(
        index=65, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_z_dim": ConfigurationRegisterDescription(
        index=65, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_w_dim": ConfigurationRegisterDescription(
        index=66, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo": ConfigurationRegisterDescription(
        index=66, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi": ConfigurationRegisterDescription(
        index=67, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_digest_type": ConfigurationRegisterDescription(
        index=67, mask=0xFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_digest_size": ConfigurationRegisterDescription(
        index=67, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # UNPACK TILE DESCRIPTOR SEC1
    "UNPACK_TILE_DESCRIPTOR1_in_data_format": ConfigurationRegisterDescription(
        index=112, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "UNPACK_TILE_DESCRIPTOR1_uncompressed": ConfigurationRegisterDescription(
        index=112, mask=0x10, shift=4, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_TILE_DESCRIPTOR1_reserved_0": ConfigurationRegisterDescription(
        index=112, mask=0xE0, shift=5, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane": ConfigurationRegisterDescription(
        index=112, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_reserved_1": ConfigurationRegisterDescription(
        index=112, mask=0xF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_x_dim": ConfigurationRegisterDescription(
        index=112, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_y_dim": ConfigurationRegisterDescription(
        index=113, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_z_dim": ConfigurationRegisterDescription(
        index=113, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_w_dim": ConfigurationRegisterDescription(
        index=114, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo": ConfigurationRegisterDescription(
        index=114, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi": ConfigurationRegisterDescription(
        index=115, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_digest_type": ConfigurationRegisterDescription(
        index=115, mask=0xFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_digest_size": ConfigurationRegisterDescription(
        index=115, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # UNPACK CONFIG SEC 0
    "UNPACK_CONFIG0_out_data_format": ConfigurationRegisterDescription(
        index=72, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "UNPACK_CONFIG0_throttle_mode": ConfigurationRegisterDescription(
        index=72, mask=0x30, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_context_count": ConfigurationRegisterDescription(
        index=72, mask=0xC0, shift=6, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_haloize_mode": ConfigurationRegisterDescription(
        index=72, mask=0x100, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_tileize_mode": ConfigurationRegisterDescription(
        index=72, mask=0x200, shift=9, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_unpack_src_reg_set_upd": ConfigurationRegisterDescription(
        index=72, mask=0x400, shift=10, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG0_unpack_if_sel": ConfigurationRegisterDescription(
        index=72, mask=0x800, shift=11, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG0_upsample_rate": ConfigurationRegisterDescription(
        index=72, mask=0x3000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_reserved_1": ConfigurationRegisterDescription(
        index=72, mask=0x4000, shift=14, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_upsample_and_interleave": ConfigurationRegisterDescription(
        index=72, mask=0x8000, shift=15, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG0_shift_amount": ConfigurationRegisterDescription(
        index=72, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_uncompress_cntx0_3": ConfigurationRegisterDescription(
        index=73, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(
        index=73, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_force_shared_exp": ConfigurationRegisterDescription(
        index=73, mask=0x100, shift=8, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG0_reserved_2": ConfigurationRegisterDescription(
        index=73, mask=0xFE00, shift=9, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_uncompress_cntx4_7": ConfigurationRegisterDescription(
        index=73, mask=0xF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(
        index=73, mask=0xF00000, shift=20, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_reserved_3": ConfigurationRegisterDescription(
        index=73, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_limit_addr": ConfigurationRegisterDescription(
        index=74, mask=0x1FFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "UNPACK_CONFIG0_reserved_4": ConfigurationRegisterDescription(
        index=74, mask=0xFFFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_fifo_size": ConfigurationRegisterDescription(
        index=75, mask=0x1FFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_reserved_5": ConfigurationRegisterDescription(
        index=75, mask=0xFFFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # UNPACK CONFIG SEC 1
    "UNPACK_CONFIG1_out_data_format": ConfigurationRegisterDescription(
        index=120, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "UNPACK_CONFIG1_throttle_mode": ConfigurationRegisterDescription(
        index=120, mask=0x30, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_context_count": ConfigurationRegisterDescription(
        index=120, mask=0xC0, shift=6, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_haloize_mode": ConfigurationRegisterDescription(
        index=120, mask=0x100, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_tileize_mode": ConfigurationRegisterDescription(
        index=120, mask=0x200, shift=9, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_unpack_src_reg_set_upd": ConfigurationRegisterDescription(
        index=120, mask=0x400, shift=10, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG1_unpack_if_sel": ConfigurationRegisterDescription(
        index=120, mask=0x800, shift=11, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG1_upsample_rate": ConfigurationRegisterDescription(
        index=120, mask=0x3000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_reserved_1": ConfigurationRegisterDescription(
        index=120, mask=0x4000, shift=14, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_upsample_and_interleave": ConfigurationRegisterDescription(
        index=120, mask=0x8000, shift=15, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG1_shift_amount": ConfigurationRegisterDescription(
        index=120, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_uncompress_cntx0_3": ConfigurationRegisterDescription(
        index=121, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(
        index=121, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_force_shared_exp": ConfigurationRegisterDescription(
        index=121, mask=0x100, shift=8, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG1_reserved_2": ConfigurationRegisterDescription(
        index=121, mask=0xFE00, shift=9, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_uncompress_cntx4_7": ConfigurationRegisterDescription(
        index=121, mask=0xF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(
        index=121, mask=0xF00000, shift=20, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_reserved_3": ConfigurationRegisterDescription(
        index=121, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_limit_addr": ConfigurationRegisterDescription(
        index=122, mask=0x1FFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "UNPACK_CONFIG1_reserved_4": ConfigurationRegisterDescription(
        index=122, mask=0xFFFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_fifo_size": ConfigurationRegisterDescription(
        index=123, mask=0x1FFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_reserved_5": ConfigurationRegisterDescription(
        index=123, mask=0xFFFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # ALU CONFIG
    "ALU_ROUNDING_MODE_Fpu_srnd_en": ConfigurationRegisterDescription(
        index=1, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_ROUNDING_MODE_Gasket_srnd_en": ConfigurationRegisterDescription(
        index=1, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_ROUNDING_MODE_Packer_srnd_en": ConfigurationRegisterDescription(
        index=1, mask=0x4, shift=2, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_ROUNDING_MODE_Padding": ConfigurationRegisterDescription(
        index=1, mask=0x1FF8, shift=3, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "ALU_ROUNDING_MODE_GS_LF": ConfigurationRegisterDescription(
        index=1, mask=0x2000, shift=13, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_ROUNDING_MODE_Bfp8_HF": ConfigurationRegisterDescription(
        index=1, mask=0x4000, shift=14, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_FORMAT_SPEC_REG0_SrcAUnsigned": ConfigurationRegisterDescription(
        index=1, mask=0x8000, shift=15, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_FORMAT_SPEC_REG0_SrcBUnsigned": ConfigurationRegisterDescription(
        index=1, mask=0x10000, shift=16, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_FORMAT_SPEC_REG0_SrcA": ConfigurationRegisterDescription(
        index=1, mask=0x1E0000, shift=17, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "ALU_FORMAT_SPEC_REG1_SrcB": ConfigurationRegisterDescription(
        index=1, mask=0x1E00000, shift=21, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "ALU_FORMAT_SPEC_REG2_Dstacc": ConfigurationRegisterDescription(
        index=1, mask=0x1E000000, shift=25, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "ALU_ACC_CTRL_Fp32_enabled": ConfigurationRegisterDescription(
        index=1, mask=0x20000000, shift=29, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_ACC_CTRL_SFPU_Fp32_enabled": ConfigurationRegisterDescription(
        index=1, mask=0x40000000, shift=30, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_ACC_CTRL_INT8_math_enabled": ConfigurationRegisterDescription(
        index=1, mask=0x80000000, shift=31, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    # PACK CONFIG SEC 0 REG 1
    "PACK_CONFIG01_row_ptr_section_size": ConfigurationRegisterDescription(
        index=68, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_exp_section_size": ConfigurationRegisterDescription(
        index=68, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_l1_dest_addr": ConfigurationRegisterDescription(
        index=69, mask=0xFFFFFFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG01_uncompress": ConfigurationRegisterDescription(
        index=70, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
        index=70, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_disable_pack_zero_flag": ConfigurationRegisterDescription(
        index=70, mask=0x4, shift=2, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_reserved_0": ConfigurationRegisterDescription(
        index=70, mask=0x8, shift=3, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_out_data_format": ConfigurationRegisterDescription(
        index=70, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG01_in_data_format": ConfigurationRegisterDescription(
        index=70, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG01_dis_shared_exp_assembler": ConfigurationRegisterDescription(
        index=70, mask=0x1000, shift=12, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_auto_set_last_pacr_intf_sel": ConfigurationRegisterDescription(
        index=70, mask=0x2000, shift=13, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_enable_out_fifo": ConfigurationRegisterDescription(
        index=70, mask=0x4000, shift=14, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_sub_l1_tile_header_size": ConfigurationRegisterDescription(
        index=70, mask=0x8000, shift=15, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_src_if_sel": ConfigurationRegisterDescription(
        index=70, mask=0x10000, shift=16, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_pack_start_intf_pos": ConfigurationRegisterDescription(
        index=70, mask=0x1E0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_all_pack_disable_zero_compress_ovrd": ConfigurationRegisterDescription(
        index=70, mask=0x200000, shift=21, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_add_tile_header_size": ConfigurationRegisterDescription(
        index=70, mask=0x400000, shift=22, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_pack_dis_y_pos_start_offset": ConfigurationRegisterDescription(
        index=70, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_l1_src_addr": ConfigurationRegisterDescription(
        index=70, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    # RELU CONFIG
    "ALU_ACC_CTRL_Zero_Flag_disabled_src": ConfigurationRegisterDescription(
        index=2, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "ALU_ACC_CTRL_Zero_Flag_disabled_dst": ConfigurationRegisterDescription(
        index=2, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "STACC_RELU_ApplyRelu": ConfigurationRegisterDescription(
        index=2, mask=0x3C, shift=2, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "STACC_RELU_ReluThreshold": ConfigurationRegisterDescription(
        index=2, mask=0x3FFFC0, shift=6, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "DISABLE_RISC_BP_Disable_main": ConfigurationRegisterDescription(
        index=2, mask=0x400000, shift=22, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "DISABLE_RISC_BP_Disable_trisc": ConfigurationRegisterDescription(
        index=2, mask=0x3800000, shift=23, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "DISABLE_RISC_BP_Disable_ncrisc": ConfigurationRegisterDescription(
        index=2, mask=0x4000000, shift=26, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "DISABLE_RISC_BP_Disable_bmp_clear_main": ConfigurationRegisterDescription(
        index=2, mask=0x8000000, shift=27, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "DISABLE_RISC_BP_Disable_bmp_clear_trisc": ConfigurationRegisterDescription(
        index=2, mask=0x70000000, shift=28, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "DISABLE_RISC_BP_Disable_bmp_clear_ncrisc": ConfigurationRegisterDescription(index=2, mask=0x80000000, shift=31),
    # DEST RD CTRL
    "PACK_DEST_RD_CTRL_Read_32b_data": ConfigurationRegisterDescription(
        index=18, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_DEST_RD_CTRL_Read_unsigned": ConfigurationRegisterDescription(
        index=18, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_DEST_RD_CTRL_Read_int8": ConfigurationRegisterDescription(
        index=18, mask=0x4, shift=2, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_DEST_RD_CTRL_Round_10b_mant": ConfigurationRegisterDescription(
        index=18, mask=0x8, shift=3, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_DEST_RD_CTRL_Reserved": ConfigurationRegisterDescription(
        index=18, mask=0xFFFFFFF0, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # EDGE OFFSET SEC 0
    "PACK_EDGE_OFFSET0_mask": ConfigurationRegisterDescription(
        index=24, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    "PACK_EDGE_OFFSET0_mode": ConfigurationRegisterDescription(
        index=24, mask=0x10000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_tile_row_set_select_pack0": ConfigurationRegisterDescription(
        index=24, mask=0x60000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_tile_row_set_select_pack1": ConfigurationRegisterDescription(
        index=24, mask=0x180000, shift=19, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_tile_row_set_select_pack2": ConfigurationRegisterDescription(
        index=24, mask=0x600000, shift=21, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_tile_row_set_select_pack3": ConfigurationRegisterDescription(
        index=24, mask=0x1800000, shift=23, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_reserved": ConfigurationRegisterDescription(
        index=24, mask=0xFE000000, shift=25, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK COUNTERS SEC 0
    "PACK_COUNTERS0_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=28, mask=0xFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS0_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
        index=28, mask=0xFF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS0_pack_xys_per_til": ConfigurationRegisterDescription(
        index=28, mask=0x7F0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS0_pack_yz_transposed": ConfigurationRegisterDescription(
        index=28, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_COUNTERS0_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
        index=28, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK STRIDES REG 0
    "PACK_STRIDES0_x_stride": ConfigurationRegisterDescription(
        index=12, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES0_y_stride": ConfigurationRegisterDescription(
        index=12, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES0_z_stride": ConfigurationRegisterDescription(
        index=13, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES0_w_stride": ConfigurationRegisterDescription(
        index=13, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK STRIDES REG 1
    "PACK_STRIDES1_x_stride": ConfigurationRegisterDescription(
        index=14, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES1_y_stride": ConfigurationRegisterDescription(
        index=14, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES1_z_stride": ConfigurationRegisterDescription(
        index=15, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES1_w_stride": ConfigurationRegisterDescription(
        index=15, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # REST
    "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=185, mask=0x1F),
    "RISCV_DEBUG_REG_DBG_BUS_CNTL_REG": DebugRegisterDescription(address=0x54),
    "RISCV_DEBUG_REG_CFGREG_RD_CNTL": DebugRegisterDescription(address=0x58),
    "RISCV_DEBUG_REG_DBG_RD_DATA": DebugRegisterDescription(address=0x5C),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_EN": DebugRegisterDescription(address=0x60),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD": DebugRegisterDescription(address=0x64),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA": DebugRegisterDescription(address=0x6C),
    "RISCV_DEBUG_REG_CFGREG_RDDATA": DebugRegisterDescription(address=0x78),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": DebugRegisterDescription(address=0x80),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": DebugRegisterDescription(address=0x84),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": DebugRegisterDescription(address=0x88),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": DebugRegisterDescription(address=0x8C),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0": DebugRegisterDescription(address=0xA0),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL1": DebugRegisterDescription(address=0xA4),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS": DebugRegisterDescription(address=0xA8),
    "RISCV_DEBUG_REG_SOFT_RESET_0": DebugRegisterDescription(address=0x1B0),
    "TRISC_RESET_PC_SEC0_PC": DebugRegisterDescription(address=0x228),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC0_RESET_PC": DebugRegisterDescription(address=0x228),  # New name
    "TRISC_RESET_PC_SEC1_PC": DebugRegisterDescription(address=0x22C),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC1_RESET_PC": DebugRegisterDescription(address=0x22C),  # New name
    "TRISC_RESET_PC_SEC2_PC": DebugRegisterDescription(address=0x230),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC2_RESET_PC": DebugRegisterDescription(address=0x230),  # New name
    "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": DebugRegisterDescription(
        address=0x234, mask=0x7
    ),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE": DebugRegisterDescription(address=0x234, mask=0x7),  # New name
    "NCRISC_RESET_PC_PC": DebugRegisterDescription(address=0x238),  # Old name from configuration register
    "RISCV_DEBUG_REG_NCRISC_RESET_PC": DebugRegisterDescription(address=0x238),  # New name
    "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": DebugRegisterDescription(
        address=0x23C, mask=0x1
    ),  # Old name from configuration register
    "RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE": DebugRegisterDescription(address=0x23C, mask=0x1),  # New name
}

register_map_noc0 = RegisterStore.initialize_register_map(
    [register_offset_map, noc_registers_offset_map],
    get_register_internal_base_address_noc0,
    get_register_noc_base_address_noc0,
)
register_map_noc1 = RegisterStore.initialize_register_map(
    [register_offset_map, noc_registers_offset_map],
    get_register_internal_base_address_noc1,
    get_register_noc_base_address_noc1,
)
