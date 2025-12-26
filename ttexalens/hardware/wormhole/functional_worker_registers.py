# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.tensix_registers_description import TensixRegisterDescription
from ttexalens.register_store import (
    REGISTER_DATA_TYPE,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    TensixGeneralPurposeRegisterDescription,
    RegisterDescription,
)


register_map: dict[str, RegisterDescription] = {
    # UNPACK TILE DESCRIPTOR SEC 0
    "UNPACK_TILE_DESCRIPTOR0_in_data_format": ConfigurationRegisterDescription(
        index=52, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "UNPACK_TILE_DESCRIPTOR0_uncompressed": ConfigurationRegisterDescription(
        index=52, mask=0x10, shift=4, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_TILE_DESCRIPTOR0_reserved_0": ConfigurationRegisterDescription(
        index=52, mask=0xE0, shift=5, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane": ConfigurationRegisterDescription(
        index=52, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_reserved_1": ConfigurationRegisterDescription(
        index=52, mask=0xF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_x_dim": ConfigurationRegisterDescription(
        index=52, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_y_dim": ConfigurationRegisterDescription(
        index=53, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_z_dim": ConfigurationRegisterDescription(
        index=53, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_w_dim": ConfigurationRegisterDescription(
        index=54, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo": ConfigurationRegisterDescription(
        index=54, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi": ConfigurationRegisterDescription(
        index=55, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_digest_type": ConfigurationRegisterDescription(
        index=55, mask=0xFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR0_digest_size": ConfigurationRegisterDescription(
        index=55, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # UNPACK TILE DESCRIPTOR SEC 1
    "UNPACK_TILE_DESCRIPTOR1_in_data_format": ConfigurationRegisterDescription(
        index=92, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "UNPACK_TILE_DESCRIPTOR1_uncompressed": ConfigurationRegisterDescription(
        index=92, mask=0x10, shift=4, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_TILE_DESCRIPTOR1_reserved_0": ConfigurationRegisterDescription(
        index=92, mask=0xE0, shift=5, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane": ConfigurationRegisterDescription(
        index=92, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_reserved_1": ConfigurationRegisterDescription(
        index=92, mask=0xF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_x_dim": ConfigurationRegisterDescription(
        index=92, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_y_dim": ConfigurationRegisterDescription(
        index=93, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_z_dim": ConfigurationRegisterDescription(
        index=93, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_w_dim": ConfigurationRegisterDescription(
        index=94, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo": ConfigurationRegisterDescription(
        index=94, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi": ConfigurationRegisterDescription(
        index=95, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_digest_type": ConfigurationRegisterDescription(
        index=95, mask=0xFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_TILE_DESCRIPTOR1_digest_size": ConfigurationRegisterDescription(
        index=95, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # UNPACK CONFIG SEC 0
    "UNPACK_CONFIG0_out_data_format": ConfigurationRegisterDescription(
        index=60, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "UNPACK_CONFIG0_throttle_mode": ConfigurationRegisterDescription(
        index=60, mask=0x30, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_context_count": ConfigurationRegisterDescription(
        index=60, mask=0xC0, shift=6, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_haloize_mode": ConfigurationRegisterDescription(
        index=60, mask=0x100, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_tileize_mode": ConfigurationRegisterDescription(
        index=60, mask=0x200, shift=9, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_unpack_src_reg_set_upd": ConfigurationRegisterDescription(
        index=60, mask=0x400, shift=10, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG0_unpack_if_sel": ConfigurationRegisterDescription(
        index=60, mask=0x800, shift=11, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG0_upsample_rate": ConfigurationRegisterDescription(
        index=60, mask=0x3000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_reserved_1": ConfigurationRegisterDescription(
        index=60, mask=0x4000, shift=14, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_upsample_and_interleave": ConfigurationRegisterDescription(
        index=60, mask=0x8000, shift=15, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG0_shift_amount": ConfigurationRegisterDescription(
        index=60, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_uncompress_cntx0_3": ConfigurationRegisterDescription(
        index=61, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(
        index=61, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_force_shared_exp": ConfigurationRegisterDescription(
        index=61, mask=0x100, shift=8, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG0_reserved_2": ConfigurationRegisterDescription(
        index=61, mask=0xFE00, shift=9, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_uncompress_cntx4_7": ConfigurationRegisterDescription(
        index=61, mask=0xF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(
        index=61, mask=0xF00000, shift=20, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_reserved_3": ConfigurationRegisterDescription(
        index=61, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_limit_addr": ConfigurationRegisterDescription(
        index=62, mask=0x1FFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "UNPACK_CONFIG0_reserved_4": ConfigurationRegisterDescription(
        index=62, mask=0xFFFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_fifo_size": ConfigurationRegisterDescription(
        index=63, mask=0x1FFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG0_reserved_5": ConfigurationRegisterDescription(
        index=63, mask=0xFFFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # UNPACK CONFIG SEC 1
    "UNPACK_CONFIG1_out_data_format": ConfigurationRegisterDescription(
        index=100, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "UNPACK_CONFIG1_throttle_mode": ConfigurationRegisterDescription(
        index=100, mask=0x30, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_context_count": ConfigurationRegisterDescription(
        index=100, mask=0xC0, shift=6, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_haloize_mode": ConfigurationRegisterDescription(
        index=100, mask=0x100, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_tileize_mode": ConfigurationRegisterDescription(
        index=100, mask=0x200, shift=9, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_unpack_src_reg_set_upd": ConfigurationRegisterDescription(
        index=100, mask=0x400, shift=10, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG1_unpack_if_sel": ConfigurationRegisterDescription(
        index=100, mask=0x800, shift=11, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG1_upsample_rate": ConfigurationRegisterDescription(
        index=100, mask=0x3000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_reserved_1": ConfigurationRegisterDescription(
        index=100, mask=0x4000, shift=14, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_upsample_and_interleave": ConfigurationRegisterDescription(
        index=100, mask=0x8000, shift=15, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG1_shift_amount": ConfigurationRegisterDescription(
        index=100, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_uncompress_cntx0_3": ConfigurationRegisterDescription(
        index=101, mask=0xF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(
        index=101, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_force_shared_exp": ConfigurationRegisterDescription(
        index=101, mask=0x100, shift=8, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "UNPACK_CONFIG1_reserved_2": ConfigurationRegisterDescription(
        index=101, mask=0xFE00, shift=9, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_uncompress_cntx4_7": ConfigurationRegisterDescription(
        index=101, mask=0xF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(
        index=101, mask=0xF00000, shift=20, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_reserved_3": ConfigurationRegisterDescription(
        index=101, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_limit_addr": ConfigurationRegisterDescription(
        index=102, mask=0x1FFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "UNPACK_CONFIG1_reserved_4": ConfigurationRegisterDescription(
        index=102, mask=0xFFFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_fifo_size": ConfigurationRegisterDescription(
        index=103, mask=0x1FFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "UNPACK_CONFIG1_reserved_5": ConfigurationRegisterDescription(
        index=103, mask=0xFFFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
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
        index=56, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_exp_section_size": ConfigurationRegisterDescription(
        index=56, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_l1_dest_addr": ConfigurationRegisterDescription(
        index=57, mask=0xFFFFFFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG01_uncompress": ConfigurationRegisterDescription(
        index=58, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
        index=58, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_reserved_0": ConfigurationRegisterDescription(
        index=58, mask=0xC, shift=2, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_out_data_format": ConfigurationRegisterDescription(
        index=58, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG01_in_data_format": ConfigurationRegisterDescription(
        index=58, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG01_reserved_1": ConfigurationRegisterDescription(
        index=58, mask=0xF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_src_if_sel": ConfigurationRegisterDescription(
        index=58, mask=0x10000, shift=16, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=58, mask=0xFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_l1_src_addr": ConfigurationRegisterDescription(
        index=58, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG01_downsample_mask": ConfigurationRegisterDescription(
        index=59, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    "PACK_CONFIG01_downsample_shift_count": ConfigurationRegisterDescription(
        index=59, mask=0x70000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_read_mode": ConfigurationRegisterDescription(
        index=59, mask=0x80000, shift=19, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_exp_threshold_en": ConfigurationRegisterDescription(
        index=59, mask=0x100000, shift=20, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
        index=59, mask=0x600000, shift=21, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG01_reserved_2": ConfigurationRegisterDescription(
        index=59, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG01_exp_threshold": ConfigurationRegisterDescription(
        index=59, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK CONFIG SEC 0 REG 8
    "PACK_CONFIG08_row_ptr_section_size": ConfigurationRegisterDescription(
        index=84, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG08_exp_section_size": ConfigurationRegisterDescription(
        index=84, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG08_l1_dest_addr": ConfigurationRegisterDescription(
        index=85, mask=0xFFFFFFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG08_uncompress": ConfigurationRegisterDescription(
        index=86, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG08_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
        index=86, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG08_reserved_0": ConfigurationRegisterDescription(
        index=86, mask=0xC, shift=2, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG08_out_data_format": ConfigurationRegisterDescription(
        index=86, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG08_in_data_format": ConfigurationRegisterDescription(
        index=86, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG08_reserved_1": ConfigurationRegisterDescription(
        index=86, mask=0xF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG08_src_if_sel": ConfigurationRegisterDescription(
        index=86, mask=0x10000, shift=16, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG08_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=86, mask=0xFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG08_l1_src_addr": ConfigurationRegisterDescription(
        index=86, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG08_downsample_mask": ConfigurationRegisterDescription(
        index=87, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    "PACK_CONFIG08_downsample_shift_count": ConfigurationRegisterDescription(
        index=87, mask=0x70000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG08_read_mode": ConfigurationRegisterDescription(
        index=87, mask=0x80000, shift=19, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG08_exp_threshold_en": ConfigurationRegisterDescription(
        index=87, mask=0x100000, shift=20, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG08_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
        index=87, mask=0x600000, shift=21, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG08_reserved_2": ConfigurationRegisterDescription(
        index=87, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG08_exp_threshold": ConfigurationRegisterDescription(
        index=87, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK CONFIG SEC 1 REG 1
    "PACK_CONFIG11_row_ptr_section_size": ConfigurationRegisterDescription(
        index=96, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG11_exp_section_size": ConfigurationRegisterDescription(
        index=96, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG11_l1_dest_addr": ConfigurationRegisterDescription(
        index=97, mask=0xFFFFFFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG11_uncompress": ConfigurationRegisterDescription(
        index=98, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG11_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
        index=98, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG11_reserved_0": ConfigurationRegisterDescription(
        index=98, mask=0xC, shift=2, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG11_out_data_format": ConfigurationRegisterDescription(
        index=98, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG11_in_data_format": ConfigurationRegisterDescription(
        index=98, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG11_reserved_1": ConfigurationRegisterDescription(
        index=98, mask=0xF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG11_src_if_sel": ConfigurationRegisterDescription(
        index=98, mask=0x10000, shift=16, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG11_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=98, mask=0xFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG11_l1_src_addr": ConfigurationRegisterDescription(
        index=98, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG11_downsample_mask": ConfigurationRegisterDescription(
        index=99, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    "PACK_CONFIG11_downsample_shift_count": ConfigurationRegisterDescription(
        index=99, mask=0x70000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG11_read_mode": ConfigurationRegisterDescription(
        index=99, mask=0x80000, shift=19, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG11_exp_threshold_en": ConfigurationRegisterDescription(
        index=99, mask=0x100000, shift=20, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG11_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
        index=99, mask=0x600000, shift=21, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG11_reserved_2": ConfigurationRegisterDescription(
        index=99, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG11_exp_threshold": ConfigurationRegisterDescription(
        index=99, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK CONFIG SEC 1 REG 8
    "PACK_CONFIG18_row_ptr_section_size": ConfigurationRegisterDescription(
        index=124, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG18_exp_section_size": ConfigurationRegisterDescription(
        index=124, mask=0xFFFF0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG18_l1_dest_addr": ConfigurationRegisterDescription(
        index=125, mask=0xFFFFFFFF, shift=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG18_uncompress": ConfigurationRegisterDescription(
        index=126, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG18_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
        index=126, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG18_reserved_0": ConfigurationRegisterDescription(
        index=126, mask=0xC, shift=2, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG18_out_data_format": ConfigurationRegisterDescription(
        index=126, mask=0xF0, shift=4, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG18_in_data_format": ConfigurationRegisterDescription(
        index=126, mask=0xF00, shift=8, data_type=REGISTER_DATA_TYPE.TENSIX_DATA_FORMAT
    ),
    "PACK_CONFIG18_reserved_1": ConfigurationRegisterDescription(
        index=126, mask=0xF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG18_src_if_sel": ConfigurationRegisterDescription(
        index=126, mask=0x10000, shift=16, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG18_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=126, mask=0xFE0000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG18_l1_src_addr": ConfigurationRegisterDescription(
        index=126, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PACK_CONFIG18_downsample_mask": ConfigurationRegisterDescription(
        index=127, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    "PACK_CONFIG18_downsample_shift_count": ConfigurationRegisterDescription(
        index=127, mask=0x70000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG18_read_mode": ConfigurationRegisterDescription(
        index=127, mask=0x80000, shift=19, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG18_exp_threshold_en": ConfigurationRegisterDescription(
        index=127, mask=0x100000, shift=20, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG18_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
        index=127, mask=0x600000, shift=21, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_CONFIG18_reserved_2": ConfigurationRegisterDescription(
        index=127, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_CONFIG18_exp_threshold": ConfigurationRegisterDescription(
        index=127, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
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
    "DISABLE_RISC_BP_Disable_bmp_clear_ncrisc": ConfigurationRegisterDescription(
        index=2, mask=0x80000000, shift=31, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    # DEST RD CTRL
    "PACK_DEST_RD_CTRL_Read_32b_data": ConfigurationRegisterDescription(
        index=14, mask=0x1, shift=0, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_DEST_RD_CTRL_Read_unsigned": ConfigurationRegisterDescription(
        index=14, mask=0x2, shift=1, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_DEST_RD_CTRL_Read_int8": ConfigurationRegisterDescription(
        index=14, mask=0x4, shift=2, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_DEST_RD_CTRL_Round_10b_mant": ConfigurationRegisterDescription(
        index=14, mask=0x8, shift=3, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_DEST_RD_CTRL_Reserved": ConfigurationRegisterDescription(
        index=14, mask=0xFFFFFFF0, shift=4, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # EDGE OFFSET SEC 0
    "PACK_EDGE_OFFSET0_mask": ConfigurationRegisterDescription(
        index=20, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    "PACK_EDGE_OFFSET0_mode": ConfigurationRegisterDescription(
        index=20, mask=0x10000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_tile_row_set_select_pack0": ConfigurationRegisterDescription(
        index=20, mask=0x60000, shift=17, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_tile_row_set_select_pack1": ConfigurationRegisterDescription(
        index=20, mask=0x180000, shift=19, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_tile_row_set_select_pack2": ConfigurationRegisterDescription(
        index=20, mask=0x600000, shift=21, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_tile_row_set_select_pack3": ConfigurationRegisterDescription(
        index=20, mask=0x1800000, shift=23, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_EDGE_OFFSET0_reserved": ConfigurationRegisterDescription(
        index=20, mask=0xFE000000, shift=25, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # EDGE OFFSET SEC 1
    "PACK_EDGE_OFFSET1_mask": ConfigurationRegisterDescription(
        index=21, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    # EDGE OFFSET SEC 2
    "PACK_EDGE_OFFSET2_mask": ConfigurationRegisterDescription(
        index=22, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    # EDGE OFFSET SEC 3
    "PACK_EDGE_OFFSET3_mask": ConfigurationRegisterDescription(
        index=23, mask=0xFFFF, shift=0, data_type=REGISTER_DATA_TYPE.MASK
    ),
    # PACK COUNTERS SEC 0
    "PACK_COUNTERS0_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=24, mask=0xFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS0_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
        index=24, mask=0xFF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS0_pack_xys_per_til": ConfigurationRegisterDescription(
        index=24, mask=0x7F0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS0_pack_yz_transposed": ConfigurationRegisterDescription(
        index=24, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_COUNTERS0_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
        index=24, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK COUNTERS SEC 1
    "PACK_COUNTERS1_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=25, mask=0xFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS1_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
        index=25, mask=0xFF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS1_pack_xys_per_til": ConfigurationRegisterDescription(
        index=25, mask=0x7F0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS1_pack_yz_transposed": ConfigurationRegisterDescription(
        index=25, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_COUNTERS1_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
        index=25, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK COUNTERS SEC 2
    "PACK_COUNTERS2_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=26, mask=0xFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS2_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
        index=26, mask=0xFF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS2_pack_xys_per_til": ConfigurationRegisterDescription(
        index=26, mask=0x7F0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS2_pack_yz_transposed": ConfigurationRegisterDescription(
        index=26, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_COUNTERS2_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
        index=26, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK COUNTERS SEC 3
    "PACK_COUNTERS3_pack_per_xy_plane": ConfigurationRegisterDescription(
        index=27, mask=0xFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS3_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
        index=27, mask=0xFF00, shift=8, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS3_pack_xys_per_til": ConfigurationRegisterDescription(
        index=27, mask=0x7F0000, shift=16, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_COUNTERS3_pack_yz_transposed": ConfigurationRegisterDescription(
        index=27, mask=0x800000, shift=23, data_type=REGISTER_DATA_TYPE.FLAGS
    ),
    "PACK_COUNTERS3_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
        index=27, mask=0xFF000000, shift=24, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK STRIDES REG 0
    "PACK_STRIDES0_x_stride": ConfigurationRegisterDescription(
        index=8, mask=0xFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES0_y_stride": ConfigurationRegisterDescription(
        index=8, mask=0xFFF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES0_z_stride": ConfigurationRegisterDescription(
        index=9, mask=0xFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES0_w_stride": ConfigurationRegisterDescription(
        index=9, mask=0xFFFF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # PACK STRIDES REG 1
    "PACK_STRIDES1_x_stride": ConfigurationRegisterDescription(
        index=10, mask=0xFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES1_y_stride": ConfigurationRegisterDescription(
        index=10, mask=0xFFF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES1_z_stride": ConfigurationRegisterDescription(
        index=11, mask=0xFFF, shift=0, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    "PACK_STRIDES1_w_stride": ConfigurationRegisterDescription(
        index=11, mask=0xFFFF000, shift=12, data_type=REGISTER_DATA_TYPE.INT_VALUE
    ),
    # GENERAL PURPOSE REGISTERS
    # https://github.com/tenstorrent/tt-llk/blob/main/tt_llk_wormhole/common/inc/ckernel_gpr_map.h
    # THREAD 0
    "ZERO_T0": TensixGeneralPurposeRegisterDescription(index=0, thread_id=0),
    "DBG_RESERVED_T0": TensixGeneralPurposeRegisterDescription(index=1, thread_id=0),
    "DBG_MSG_T0": TensixGeneralPurposeRegisterDescription(index=2, thread_id=0),
    "DBG_CKID_T0": TensixGeneralPurposeRegisterDescription(index=3, thread_id=0),
    "OPERAND_BASE_ADDR_T0": TensixGeneralPurposeRegisterDescription(
        index=4, thread_id=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "OPERAND_OFFSET_ADDR_T0": TensixGeneralPurposeRegisterDescription(
        index=5, thread_id=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "GPR_6_T0": TensixGeneralPurposeRegisterDescription(index=6, thread_id=0),
    "GPR_7_T0": TensixGeneralPurposeRegisterDescription(index=7, thread_id=0),
    "ZERO_0_T0": TensixGeneralPurposeRegisterDescription(index=8, thread_id=0),
    "ZERO_1_T0": TensixGeneralPurposeRegisterDescription(index=9, thread_id=0),
    "ZERO_2_T0": TensixGeneralPurposeRegisterDescription(index=10, thread_id=0),
    "ZERO_3_T0": TensixGeneralPurposeRegisterDescription(index=11, thread_id=0),
    "TMP0_T0": TensixGeneralPurposeRegisterDescription(index=12, thread_id=0),
    "TMP1_T0": TensixGeneralPurposeRegisterDescription(index=13, thread_id=0),
    "TILE_SIZE_T0": TensixGeneralPurposeRegisterDescription(index=14, thread_id=0),
    "TILE_OFFSET_T0": TensixGeneralPurposeRegisterDescription(index=15, thread_id=0),
    "GPR_16_T0": TensixGeneralPurposeRegisterDescription(index=16, thread_id=0),
    "L1_BUFFER_ADDR_T0": TensixGeneralPurposeRegisterDescription(
        index=17, thread_id=0, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "TMP_LO_T0": TensixGeneralPurposeRegisterDescription(index=18, thread_id=0),
    "TMP_HI_T0": TensixGeneralPurposeRegisterDescription(index=19, thread_id=0),
    "GPR_20_T0": TensixGeneralPurposeRegisterDescription(index=20, thread_id=0),
    "GPR_21_T0": TensixGeneralPurposeRegisterDescription(index=21, thread_id=0),
    "GPR_22_T0": TensixGeneralPurposeRegisterDescription(index=22, thread_id=0),
    "GPR_23_T0": TensixGeneralPurposeRegisterDescription(index=23, thread_id=0),
    "GPR_24_T0": TensixGeneralPurposeRegisterDescription(index=24, thread_id=0),
    "GPR_25_T0": TensixGeneralPurposeRegisterDescription(index=25, thread_id=0),
    "GPR_26_T0": TensixGeneralPurposeRegisterDescription(index=26, thread_id=0),
    "GPR_27_T0": TensixGeneralPurposeRegisterDescription(index=27, thread_id=0),
    "GPR_28_T0": TensixGeneralPurposeRegisterDescription(index=28, thread_id=0),
    "GPR_29_T0": TensixGeneralPurposeRegisterDescription(index=29, thread_id=0),
    "GPR_30_T0": TensixGeneralPurposeRegisterDescription(index=30, thread_id=0),
    "GPR_31_T0": TensixGeneralPurposeRegisterDescription(index=31, thread_id=0),
    "PERF_FIRST_UNP_LO_T0": TensixGeneralPurposeRegisterDescription(index=32, thread_id=0),
    "PERF_FIRST_UNP_HI_T0": TensixGeneralPurposeRegisterDescription(index=33, thread_id=0),
    "GPR_34_T0": TensixGeneralPurposeRegisterDescription(index=34, thread_id=0),
    "GPR_35_T0": TensixGeneralPurposeRegisterDescription(index=35, thread_id=0),
    "TILE_SIZE_A_T0": TensixGeneralPurposeRegisterDescription(index=36, thread_id=0),
    "TILE_SIZE_B_T0": TensixGeneralPurposeRegisterDescription(index=37, thread_id=0),
    "KT_DIM_T0": TensixGeneralPurposeRegisterDescription(index=38, thread_id=0),
    "GPR_39_T0": TensixGeneralPurposeRegisterDescription(index=39, thread_id=0),
    "FACE_DIM_16x16_T0": TensixGeneralPurposeRegisterDescription(index=40, thread_id=0),
    "FACE_DIM_8x16_T0": TensixGeneralPurposeRegisterDescription(index=41, thread_id=0),
    "FACE_DIM_4x16_T0": TensixGeneralPurposeRegisterDescription(index=42, thread_id=0),
    "FACE_DIM_2x16_T0": TensixGeneralPurposeRegisterDescription(index=43, thread_id=0),
    "FACE_DIM_1x16_T0": TensixGeneralPurposeRegisterDescription(index=44, thread_id=0),
    "PERF_UNPACK_NUM_TILES_0_T0": TensixGeneralPurposeRegisterDescription(index=45, thread_id=0),
    "PERF_UNPACK_NUM_TILES_1_T0": TensixGeneralPurposeRegisterDescription(index=46, thread_id=0),
    "PERF_UNPACK_NUM_TILES_2_T0": TensixGeneralPurposeRegisterDescription(index=47, thread_id=0),
    "PERF_UNPACK_NUM_TILES_3_T0": TensixGeneralPurposeRegisterDescription(index=48, thread_id=0),
    "GPR_49_T0": TensixGeneralPurposeRegisterDescription(index=49, thread_id=0),
    "GPR_50_T0": TensixGeneralPurposeRegisterDescription(index=50, thread_id=0),
    "GPR_51_T0": TensixGeneralPurposeRegisterDescription(index=51, thread_id=0),
    "UNPACK_STRIDE_T0": TensixGeneralPurposeRegisterDescription(index=52, thread_id=0),
    "GPR_53_T0": TensixGeneralPurposeRegisterDescription(index=53, thread_id=0),
    "SR_UNPACK_TILIZER_STATE_0_T0": TensixGeneralPurposeRegisterDescription(index=54, thread_id=0),
    "SR_UNPACK_TILIZER_STATE_1_T0": TensixGeneralPurposeRegisterDescription(index=55, thread_id=0),
    "SR_UNPACK_UNTILIZER_STATE_0_T0": TensixGeneralPurposeRegisterDescription(index=56, thread_id=0),
    "SR_UNPACK_UNTILIZER_STATE_1_T0": TensixGeneralPurposeRegisterDescription(index=57, thread_id=0),
    "SR_UNPACK_UNTILIZER_STATE_2_T0": TensixGeneralPurposeRegisterDescription(index=58, thread_id=0),
    "SR_UNPACK_UNTILIZER_STATE_3_T0": TensixGeneralPurposeRegisterDescription(index=59, thread_id=0),
    "GPR_60_T0": TensixGeneralPurposeRegisterDescription(index=60, thread_id=0),
    "GPR_61_T0": TensixGeneralPurposeRegisterDescription(index=61, thread_id=0),
    "GPR_62_T0": TensixGeneralPurposeRegisterDescription(index=62, thread_id=0),
    "GPR_63_T0": TensixGeneralPurposeRegisterDescription(index=63, thread_id=0),
    # THREAD 1
    "ZERO_T1": TensixGeneralPurposeRegisterDescription(index=0, thread_id=1),
    "DBG_RESERVED_T1": TensixGeneralPurposeRegisterDescription(index=1, thread_id=1),
    "DBG_MSG_T1": TensixGeneralPurposeRegisterDescription(index=2, thread_id=1),
    "DBG_CKID_T1": TensixGeneralPurposeRegisterDescription(index=3, thread_id=1),
    "PERF_DBUS_CNTL_T1": TensixGeneralPurposeRegisterDescription(index=4, thread_id=1),
    "PERF_MEM_DUMP_CNTL_CLEAR_T1": TensixGeneralPurposeRegisterDescription(index=5, thread_id=1),
    "PERF_MEM_DUMP_CNTL_SET_T1": TensixGeneralPurposeRegisterDescription(index=6, thread_id=1),
    "PERF_CNT_START_T1": TensixGeneralPurposeRegisterDescription(index=7, thread_id=1),
    "PERF_CNT_STOP_T1": TensixGeneralPurposeRegisterDescription(index=8, thread_id=1),
    "PERF_EPOCH_BASE_ADDR_T1": TensixGeneralPurposeRegisterDescription(
        index=9, thread_id=1, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "PERF_EPOCH_OFFSET_T1": TensixGeneralPurposeRegisterDescription(index=10, thread_id=1),
    "GPR_11_T1": TensixGeneralPurposeRegisterDescription(index=11, thread_id=1),
    "GPR_12_T1": TensixGeneralPurposeRegisterDescription(index=12, thread_id=1),
    "GPR_13_T1": TensixGeneralPurposeRegisterDescription(index=13, thread_id=1),
    "GPR_14_T1": TensixGeneralPurposeRegisterDescription(index=14, thread_id=1),
    "GPR_15_T1": TensixGeneralPurposeRegisterDescription(index=15, thread_id=1),
    "GPR_16_T1": TensixGeneralPurposeRegisterDescription(index=16, thread_id=1),
    "GPR_17_T1": TensixGeneralPurposeRegisterDescription(index=17, thread_id=1),
    "GPR_18_T1": TensixGeneralPurposeRegisterDescription(index=18, thread_id=1),
    "GPR_19_T1": TensixGeneralPurposeRegisterDescription(index=19, thread_id=1),
    "GPR_20_T1": TensixGeneralPurposeRegisterDescription(index=20, thread_id=1),
    "GPR_21_T1": TensixGeneralPurposeRegisterDescription(index=21, thread_id=1),
    "GPR_22_T1": TensixGeneralPurposeRegisterDescription(index=22, thread_id=1),
    "GPR_23_T1": TensixGeneralPurposeRegisterDescription(index=23, thread_id=1),
    "GPR_24_T1": TensixGeneralPurposeRegisterDescription(index=24, thread_id=1),
    "GPR_25_T1": TensixGeneralPurposeRegisterDescription(index=25, thread_id=1),
    "GPR_26_T1": TensixGeneralPurposeRegisterDescription(index=26, thread_id=1),
    "GPR_27_T1": TensixGeneralPurposeRegisterDescription(index=27, thread_id=1),
    "GPR_28_T1": TensixGeneralPurposeRegisterDescription(index=28, thread_id=1),
    "GPR_29_T1": TensixGeneralPurposeRegisterDescription(index=29, thread_id=1),
    "GPR_30_T1": TensixGeneralPurposeRegisterDescription(index=30, thread_id=1),
    "GPR_31_T1": TensixGeneralPurposeRegisterDescription(index=31, thread_id=1),
    "GPR_32_T1": TensixGeneralPurposeRegisterDescription(index=32, thread_id=1),
    "GPR_33_T1": TensixGeneralPurposeRegisterDescription(index=33, thread_id=1),
    "GPR_34_T1": TensixGeneralPurposeRegisterDescription(index=34, thread_id=1),
    "GPR_35_T1": TensixGeneralPurposeRegisterDescription(index=35, thread_id=1),
    "GPR_36_T1": TensixGeneralPurposeRegisterDescription(index=36, thread_id=1),
    "GPR_37_T1": TensixGeneralPurposeRegisterDescription(index=37, thread_id=1),
    "GPR_38_T1": TensixGeneralPurposeRegisterDescription(index=38, thread_id=1),
    "GPR_39_T1": TensixGeneralPurposeRegisterDescription(index=39, thread_id=1),
    "GPR_40_T1": TensixGeneralPurposeRegisterDescription(index=40, thread_id=1),
    "GPR_41_T1": TensixGeneralPurposeRegisterDescription(index=41, thread_id=1),
    "GPR_42_T1": TensixGeneralPurposeRegisterDescription(index=42, thread_id=1),
    "GPR_43_T1": TensixGeneralPurposeRegisterDescription(index=43, thread_id=1),
    "GPR_44_T1": TensixGeneralPurposeRegisterDescription(index=44, thread_id=1),
    "GPR_45_T1": TensixGeneralPurposeRegisterDescription(index=45, thread_id=1),
    "GPR_46_T1": TensixGeneralPurposeRegisterDescription(index=46, thread_id=1),
    "GPR_47_T1": TensixGeneralPurposeRegisterDescription(index=47, thread_id=1),
    "DEST_OP0_BASE_T1": TensixGeneralPurposeRegisterDescription(index=48, thread_id=1),
    "DEST_OP1_BASE_T1": TensixGeneralPurposeRegisterDescription(index=49, thread_id=1),
    "DEST_REGW_OFFSET_T1": TensixGeneralPurposeRegisterDescription(index=50, thread_id=1),
    "DEST_REGW_INCR_T1": TensixGeneralPurposeRegisterDescription(index=51, thread_id=1),
    "DEST_REGW_OFFSET2_T1": TensixGeneralPurposeRegisterDescription(index=52, thread_id=1),
    "DEST_REGW_INCR2_T1": TensixGeneralPurposeRegisterDescription(index=53, thread_id=1),
    "GPR_54_T1": TensixGeneralPurposeRegisterDescription(index=54, thread_id=1),
    "GPR_55_T1": TensixGeneralPurposeRegisterDescription(index=55, thread_id=1),
    "GPR_56_T1": TensixGeneralPurposeRegisterDescription(index=56, thread_id=1),
    "GPR_57_T1": TensixGeneralPurposeRegisterDescription(index=57, thread_id=1),
    "GPR_58_T1": TensixGeneralPurposeRegisterDescription(index=58, thread_id=1),
    "GPR_59_T1": TensixGeneralPurposeRegisterDescription(index=59, thread_id=1),
    "TMP0_T1": TensixGeneralPurposeRegisterDescription(index=60, thread_id=1),
    "NUM_DRAM_REQS_T1": TensixGeneralPurposeRegisterDescription(index=61, thread_id=1),
    "GPR_62_T1": TensixGeneralPurposeRegisterDescription(index=62, thread_id=1),
    "GPR_63_T1": TensixGeneralPurposeRegisterDescription(index=63, thread_id=1),
    # THREAD 2
    "ZERO_T2": TensixGeneralPurposeRegisterDescription(index=0, thread_id=2),
    "DBG_RESERVED_T2": TensixGeneralPurposeRegisterDescription(index=1, thread_id=2),
    "DBG_MSG_T2": TensixGeneralPurposeRegisterDescription(index=2, thread_id=2),
    "DBG_CKID_T2": TensixGeneralPurposeRegisterDescription(index=3, thread_id=2),
    "DEST_OFFSET_LO_T2": TensixGeneralPurposeRegisterDescription(index=4, thread_id=2),
    "GPR_5_T2": TensixGeneralPurposeRegisterDescription(index=5, thread_id=2),
    "GPR_6_T2": TensixGeneralPurposeRegisterDescription(index=6, thread_id=2),
    "GPR_7_T2": TensixGeneralPurposeRegisterDescription(index=7, thread_id=2),
    "DEST_OFFSET_HI_T2": TensixGeneralPurposeRegisterDescription(index=8, thread_id=2),
    "GPR_9_T2": TensixGeneralPurposeRegisterDescription(index=9, thread_id=2),
    "GPR_10_T2": TensixGeneralPurposeRegisterDescription(index=10, thread_id=2),
    "GPR_11_T2": TensixGeneralPurposeRegisterDescription(index=11, thread_id=2),
    "OUTPUT_ADDR_T2": TensixGeneralPurposeRegisterDescription(
        index=12, thread_id=2, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "GPR_13_T2": TensixGeneralPurposeRegisterDescription(index=13, thread_id=2),
    "GPR_14_T2": TensixGeneralPurposeRegisterDescription(index=14, thread_id=2),
    "GPR_15_T2": TensixGeneralPurposeRegisterDescription(index=15, thread_id=2),
    "TILE_HEADER_T2": TensixGeneralPurposeRegisterDescription(index=16, thread_id=2),
    "GPR_17_T2": TensixGeneralPurposeRegisterDescription(index=17, thread_id=2),
    "GPR_18_T2": TensixGeneralPurposeRegisterDescription(index=18, thread_id=2),
    "GPR_19_T2": TensixGeneralPurposeRegisterDescription(index=19, thread_id=2),
    "TEMP_TILE_OFFSET_T2": TensixGeneralPurposeRegisterDescription(index=20, thread_id=2),
    "GPR_21_T2": TensixGeneralPurposeRegisterDescription(index=21, thread_id=2),
    "GPR_22_T2": TensixGeneralPurposeRegisterDescription(index=22, thread_id=2),
    "GPR_23_T2": TensixGeneralPurposeRegisterDescription(index=23, thread_id=2),
    "NUM_MSGS_RECEIVED_T2": TensixGeneralPurposeRegisterDescription(index=24, thread_id=2),
    "ONE_MSG_RECEIVED_T2": TensixGeneralPurposeRegisterDescription(index=25, thread_id=2),
    "HEADER_ADDR_T2": TensixGeneralPurposeRegisterDescription(
        index=26, thread_id=2, data_type=REGISTER_DATA_TYPE.ADDRESS
    ),
    "GPR_27_T2": TensixGeneralPurposeRegisterDescription(index=27, thread_id=2),
    "TMP0_T2": TensixGeneralPurposeRegisterDescription(index=28, thread_id=2),
    "TMP1_T2": TensixGeneralPurposeRegisterDescription(index=29, thread_id=2),
    "TMP_LO_T2": TensixGeneralPurposeRegisterDescription(index=30, thread_id=2),
    "TMP_HI_T2": TensixGeneralPurposeRegisterDescription(index=31, thread_id=2),
    "PACK_STREAM_SYNC_T2": TensixGeneralPurposeRegisterDescription(index=32, thread_id=2),
    "GPR_33_T2": TensixGeneralPurposeRegisterDescription(index=33, thread_id=2),
    "GPR_34_T2": TensixGeneralPurposeRegisterDescription(index=34, thread_id=2),
    "GPR_35_T2": TensixGeneralPurposeRegisterDescription(index=35, thread_id=2),
    "GPR_36_T2": TensixGeneralPurposeRegisterDescription(index=36, thread_id=2),
    "GPR_37_T2": TensixGeneralPurposeRegisterDescription(index=37, thread_id=2),
    "GPR_38_T2": TensixGeneralPurposeRegisterDescription(index=38, thread_id=2),
    "GPR_39_T2": TensixGeneralPurposeRegisterDescription(index=39, thread_id=2),
    "GPR_40_T2": TensixGeneralPurposeRegisterDescription(index=40, thread_id=2),
    "GPR_41_T2": TensixGeneralPurposeRegisterDescription(index=41, thread_id=2),
    "GPR_42_T2": TensixGeneralPurposeRegisterDescription(index=42, thread_id=2),
    "GPR_43_T2": TensixGeneralPurposeRegisterDescription(index=43, thread_id=2),
    "GPR_44_T2": TensixGeneralPurposeRegisterDescription(index=44, thread_id=2),
    "GPR_45_T2": TensixGeneralPurposeRegisterDescription(index=45, thread_id=2),
    "GPR_46_T2": TensixGeneralPurposeRegisterDescription(index=46, thread_id=2),
    "GPR_47_T2": TensixGeneralPurposeRegisterDescription(index=47, thread_id=2),
    "GPR_48_T2": TensixGeneralPurposeRegisterDescription(index=48, thread_id=2),
    "GPR_49_T2": TensixGeneralPurposeRegisterDescription(index=49, thread_id=2),
    "OUTPUT_ADDR_OFFSET_T2": TensixGeneralPurposeRegisterDescription(index=50, thread_id=2),
    "PERF_PACK_NUM_TILES_T2": TensixGeneralPurposeRegisterDescription(index=51, thread_id=2),
    "EXP0_SEC_SIZE_BFP_T2": TensixGeneralPurposeRegisterDescription(index=52, thread_id=2),
    "EXP1_SEC_SIZE_BFP8_T2": TensixGeneralPurposeRegisterDescription(index=53, thread_id=2),
    "EXP2_SEC_SIZE_BFP8_T2": TensixGeneralPurposeRegisterDescription(index=54, thread_id=2),
    "EXP3_SEC_SIZE_BFP8_T2": TensixGeneralPurposeRegisterDescription(index=55, thread_id=2),
    "GPR_56_T2": TensixGeneralPurposeRegisterDescription(index=56, thread_id=2),
    "EXP1_SEC_SIZE_BFP4_T2": TensixGeneralPurposeRegisterDescription(index=57, thread_id=2),
    "EXP2_SEC_SIZE_BFP4_T2": TensixGeneralPurposeRegisterDescription(index=58, thread_id=2),
    "EXP3_SEC_SIZE_BFP4_T2": TensixGeneralPurposeRegisterDescription(index=59, thread_id=2),
    "GPR_60_T2": TensixGeneralPurposeRegisterDescription(index=60, thread_id=2),
    "EXP1_SEC_SIZE_BFP2_T2": TensixGeneralPurposeRegisterDescription(index=61, thread_id=2),
    "EXP2_SEC_SIZE_BFP2_T2": TensixGeneralPurposeRegisterDescription(index=62, thread_id=2),
    "EXP3_SEC_SIZE_BFP2_T2": TensixGeneralPurposeRegisterDescription(index=63, thread_id=2),
    # REST
    "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=157, mask=0x1F),
    "TRISC_RESET_PC_SEC0_PC": ConfigurationRegisterDescription(index=158),
    "TRISC_RESET_PC_SEC1_PC": ConfigurationRegisterDescription(index=159),
    "TRISC_RESET_PC_SEC2_PC": ConfigurationRegisterDescription(index=160),
    "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=161, mask=0x7),
    "NCRISC_RESET_PC_PC": ConfigurationRegisterDescription(index=162),
    "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=163, mask=0x1),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG0": DebugRegisterDescription(offset=0x048),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG1": DebugRegisterDescription(offset=0x04C),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG2": DebugRegisterDescription(offset=0x050),
    "RISCV_DEBUG_REG_DBG_BUS_CNTL_REG": DebugRegisterDescription(offset=0x54),
    "RISCV_DEBUG_REG_CFGREG_RD_CNTL": DebugRegisterDescription(offset=0x58),
    "RISCV_DEBUG_REG_DBG_RD_DATA": DebugRegisterDescription(offset=0x5C),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_EN": DebugRegisterDescription(offset=0x60),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD": DebugRegisterDescription(offset=0x64),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA": DebugRegisterDescription(offset=0x6C),
    "RISCV_DEBUG_REG_CFGREG_RDDATA": DebugRegisterDescription(offset=0x78),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": DebugRegisterDescription(offset=0x80),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": DebugRegisterDescription(offset=0x84),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": DebugRegisterDescription(offset=0x88),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": DebugRegisterDescription(offset=0x8C),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0": DebugRegisterDescription(offset=0xA0),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL1": DebugRegisterDescription(offset=0xA4),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS": DebugRegisterDescription(offset=0xA8),
    "RISCV_DEBUG_REG_SOFT_RESET_0": DebugRegisterDescription(offset=0x1B0),
}


NUM_UNPACKERS = 2
NUM_PACKERS = 4


def get_unpack_tile_descriptor() -> list[dict[str, str]]:
    struct_name = "UNPACK_TILE_DESCRIPTOR"
    fields = [
        "in_data_format",
        "uncompressed",
        "reserved_0",
        "blobs_per_xy_plane",
        "reserved_1",
        "x_dim",
        "y_dim",
        "z_dim",
        "w_dim",
        "blobs_y_start_lo",
        "blobs_y_start_hi",
        "digest_type",
        "digest_size",
    ]

    return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(NUM_UNPACKERS)]


def get_unpack_config() -> list[dict[str, str]]:
    struct_name = "UNPACK_CONFIG"
    fields = [
        "out_data_format",
        "throttle_mode",
        "context_count",
        "haloize_mode",
        "tileize_mode",
        "unpack_src_reg_set_upd",
        "unpack_if_sel",
        "upsample_rate",
        "reserved_1",
        "upsample_and_interleave",
        "shift_amount",
        "uncompress_cntx0_3",
        "unpack_if_sel_cntx0_3",
        "force_shared_exp",
        "reserved_2",
        "uncompress_cntx4_7",
        "unpack_if_sel_cntx4_7",
        "reserved_3",
        "limit_addr",
        "reserved_4",
        "fifo_size",
        "reserved_5",
    ]

    return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(NUM_UNPACKERS)]


def get_pack_config() -> list[dict[str, str]]:
    struct_name = "PACK_CONFIG"

    fields = [
        "row_ptr_section_size",
        "exp_section_size",
        "l1_dest_addr",
        "uncompress",
        "add_l1_dest_addr_offset",
        "reserved_0",
        "out_data_format",
        "in_data_format",
        "reserved_1",
        "src_if_sel",
        "l1_src_addr",
        "downsample_mask",
        "downsample_shift_count",
        "read_mode",
        "exp_threshold_en",
        "pack_l1_acc_disable_pack_zero_flag",
        "reserved_2",
        "exp_threshold",
    ]

    return [{field: f"{struct_name}{i}{j}_{field}" for field in fields} for i in [0, 1] for j in [1, 8]]


def get_pack_edge_offset() -> list[dict[str, str]]:
    struct_name = "PACK_EDGE_OFFSET"
    fields = [
        "mask",
        "mode",
        "tile_row_set_select_pack0",
        "tile_row_set_select_pack1",
        "tile_row_set_select_pack2",
        "tile_row_set_select_pack3",
    ]

    return [
        {field: f"{struct_name}{i}_{field}" for field in (fields if i == 0 else fields[:1])} for i in range(NUM_PACKERS)
    ]


def get_pack_counters() -> list[dict[str, str]]:
    struct_name = "PACK_COUNTERS"
    fields = [
        "pack_per_xy_plane",
        "pack_reads_per_xy_plane",
        "pack_xys_per_til",
        "pack_yz_transposed",
        "pack_per_xy_plane_offset",
    ]

    return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(NUM_PACKERS)]


def get_pack_strides() -> list[dict[str, str]]:
    struct_name = "PACK_STRIDES"
    fields = ["x_stride", "y_stride", "z_stride", "w_stride"]

    return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(2)]


def get_general_purpose_registers() -> list[dict[str, str]]:
    register_mapping_by_thread: list[dict[str, str]] = [dict() for _ in range(3)]
    for register_name in register_map.keys():
        register_desc = register_map[register_name]
        if isinstance(register_desc, TensixGeneralPurposeRegisterDescription):
            assert isinstance(register_desc, TensixGeneralPurposeRegisterDescription)
            thread_id = register_desc.thread_id
            register_mapping_by_thread[thread_id][register_name[:-3].lower()] = register_name

    return register_mapping_by_thread


configuration_registers_descriptions = TensixRegisterDescription(
    # ALU CONFIG
    alu_config=[
        {
            "Fpu_srnd_en": "ALU_ROUNDING_MODE_Fpu_srnd_en",
            "Gasket_srnd_en": "ALU_ROUNDING_MODE_Gasket_srnd_en",
            "Packer_srnd_en": "ALU_ROUNDING_MODE_Packer_srnd_en",
            "Padding": "ALU_ROUNDING_MODE_Padding",
            "GS_LF": "ALU_ROUNDING_MODE_GS_LF",
            "Bfp8_HF": "ALU_ROUNDING_MODE_Bfp8_HF",
            "SrcAUnsigned": "ALU_FORMAT_SPEC_REG0_SrcAUnsigned",
            "SrcBUnsigned": "ALU_FORMAT_SPEC_REG0_SrcBUnsigned",
            "Format_SrcA": "ALU_FORMAT_SPEC_REG0_SrcA",
            "Format_SrcB": "ALU_FORMAT_SPEC_REG1_SrcB",
            "Format_Dstacc": "ALU_FORMAT_SPEC_REG2_Dstacc",
            "Fp32_enabled": "ALU_ACC_CTRL_Fp32_enabled",
            "SFPU_Fp32_enabled": "ALU_ACC_CTRL_SFPU_Fp32_enabled",
            "INT8_math_enabled": "ALU_ACC_CTRL_INT8_math_enabled",
        }
    ],
    # UNPACKER CONFIG
    unpack_config=get_unpack_config(),
    unpack_tile_descriptor=get_unpack_tile_descriptor(),
    # PACKER CONFIG
    pack_config=get_pack_config(),
    relu_config=[
        {
            "disabled_src": "ALU_ACC_CTRL_Zero_Flag_disabled_src",
            "disabled_dst": "ALU_ACC_CTRL_Zero_Flag_disabled_dst",
            "apply_relu": "STACC_RELU_ApplyRelu",
            "relu_threshold": "STACC_RELU_ReluThreshold",
            "disable_main": "DISABLE_RISC_BP_Disable_main",
            "disable_trisc": "DISABLE_RISC_BP_Disable_trisc",
            "disable_ncrisc": "DISABLE_RISC_BP_Disable_ncrisc",
            "disable_bmp_clear_main": "DISABLE_RISC_BP_Disable_bmp_clear_main",
            "disable_bmp_clear_trisc": "DISABLE_RISC_BP_Disable_bmp_clear_trisc",
            "disable_bmp_clear_ncrisc": "DISABLE_RISC_BP_Disable_bmp_clear_ncrisc",
        }
    ],
    pack_dest_rd_ctrl=[
        {
            "read_32b_data": "PACK_DEST_RD_CTRL_Read_32b_data",
            "read_unsigned": "PACK_DEST_RD_CTRL_Read_unsigned",
            "read_int8": "PACK_DEST_RD_CTRL_Read_int8",
            "round_10b_mant": "PACK_DEST_RD_CTRL_Round_10b_mant",
            "reserved": "PACK_DEST_RD_CTRL_Reserved",
        }
    ],
    pack_edge_offset=get_pack_edge_offset(),
    pack_counters=get_pack_counters(),
    pack_strides=get_pack_strides(),
    general_purpose_registers=get_general_purpose_registers(),
)
