# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.wormhole.niu_registers import get_niu_register_base_address_callable, niu_register_map
from ttexalens.hardware.wormhole.noc_block import WormholeNocBlock
from ttexalens.register_store import (
    REGISTER_DATA_TYPE,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


debug_bus_signal_map = {
    # For the other signals applying the pc_mask.
    "brisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 5, mask=0x7FFFFFFF),
    "trisc0_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 6, mask=0x7FFFFFFF),
    "trisc1_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 7, mask=0x7FFFFFFF),
    "trisc2_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 8, mask=0x7FFFFFFF),
    "ncrisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 12, mask=0x7FFFFFFF),
}

register_map = {
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
    # REST
    "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=157, mask=0x1F),
    "TRISC_RESET_PC_SEC0_PC": ConfigurationRegisterDescription(index=158),
    "TRISC_RESET_PC_SEC1_PC": ConfigurationRegisterDescription(index=159),
    "TRISC_RESET_PC_SEC2_PC": ConfigurationRegisterDescription(index=160),
    "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=161, mask=0x7),
    "NCRISC_RESET_PC_PC": ConfigurationRegisterDescription(index=162),
    "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=163, mask=0x1),
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


def get_register_base_address_callable(noc_id: int) -> Callable[[RegisterDescription], DeviceAddress]:
    def get_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
        if isinstance(register_description, ConfigurationRegisterDescription):
            return DeviceAddress(private_address=0xFFEF0000)
        elif isinstance(register_description, DebugRegisterDescription):
            return DeviceAddress(private_address=0xFFB12000, noc_address=0xFFB12000)
        elif noc_id == 0:
            return get_niu_register_base_address_callable(
                DeviceAddress(private_address=0xFFB20000, noc_address=0xFFB20000)
            )(register_description)
        else:
            assert noc_id == 1
            return get_niu_register_base_address_callable(
                DeviceAddress(private_address=0xFFB30000, noc_address=0xFFB30000)
            )(register_description)

    return get_register_base_address


register_store_noc0_initialization = RegisterStore.create_initialization(
    [register_map, niu_register_map], get_register_base_address_callable(noc_id=0)
)
register_store_noc1_initialization = RegisterStore.create_initialization(
    [register_map, niu_register_map], get_register_base_address_callable(noc_id=1)
)


class WormholeFunctionalWorkerBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(
            location, block_type="functional_workers", debug_bus=DebugBusSignalStore(debug_bus_signal_map, location)
        )

        self.l1 = MemoryBlock(
            size=1464 * 1024, address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000)
        )

        self.brisc = BabyRiscInfo(
            risc_name="brisc",
            risc_id=0,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=11,
            branch_prediction_register="DISABLE_RISC_BP_Disable_main",
            branch_prediction_mask=1,
            default_code_start_address=0,
            code_start_address_register="",
            code_start_address_enable_register="",
            code_start_address_enable_bit=0,
            data_private_memory=MemoryBlock(
                size=4 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
            can_change_code_start_address=False,
        )

        self.trisc0 = BabyRiscInfo(
            risc_name="trisc0",
            risc_id=1,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=12,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b001,
            default_code_start_address=0x6000,
            code_start_address_register="TRISC_RESET_PC_SEC0_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b001,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc1 = BabyRiscInfo(
            risc_name="trisc1",
            risc_id=2,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=13,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b010,
            default_code_start_address=0xA000,
            code_start_address_register="TRISC_RESET_PC_SEC1_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b010,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc2 = BabyRiscInfo(
            risc_name="trisc2",
            risc_id=3,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=14,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b100,
            default_code_start_address=0xE000,
            code_start_address_register="TRISC_RESET_PC_SEC2_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b100,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.ncrisc = BabyRiscInfo(
            risc_name="ncrisc",
            risc_id=4,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=18,
            branch_prediction_register="DISABLE_RISC_BP_Disable_ncrisc",
            branch_prediction_mask=0x1,
            default_code_start_address=0xFFC00000,
            code_start_address_register="NCRISC_RESET_PC_PC",
            code_start_address_enable_register="NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b1,
            data_private_memory=MemoryBlock(
                size=4 * 1024,  # TODO: Check if this is correct
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=MemoryBlock(
                size=4 * 1024,  # TODO: Check if this is correct
                address=DeviceAddress(private_address=0xFFC00000),
            ),
            debug_hardware_present=False,
        )

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)
