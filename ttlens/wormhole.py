# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from typing import List
from ttlens import util
from ttlens.debug_tensix import TensixDebug, ValueType
from ttlens.device import (
    TensixInstructions,
    Device,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    TensixRegisterDescription,
    NocStatusRegisterDescription,
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
    DebugBusSignalDescription,
)


class WormholeInstructions(TensixInstructions):
    def __init__(self):
        import ttlens.wormhole_ops as ops

        super().__init__(ops)


#
# Device
#
class WormholeDevice(Device):
    # Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    DIE_Y_TO_NOC_0_Y = [0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6]
    DIE_X_TO_NOC_1_X = [9, 0, 8, 1, 7, 2, 6, 3, 5, 4]
    DIE_Y_TO_NOC_1_Y = [11, 0, 10, 1, 9, 2, 8, 3, 7, 4, 6, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    PCI_ARC_RESET_BASE_ADDR = 0x1FF30000
    PCI_ARC_CSM_DATA_BASE_ADDR = 0x1FE80000
    PCI_ARC_ROM_DATA_BASE_ADDR = 0x1FF00000

    NOC_ARC_RESET_BASE_ADDR = 0x880030000
    NOC_ARC_CSM_DATA_BASE_ADDR = 0x810000000
    NOC_ARC_ROM_DATA_BASE_ADDR = 0x880000000

    EFUSE_PCI = 0x1FF42200
    EFUSE_JTAG_AXI = 0x80042200
    EFUSE_NOC = 0x880042200

    CONFIGURATION_REGISTER_BASE = 0xFFEF0000
    DEBUG_REGISTER_BASE = 0xFFB12000
    NOC_CONTROL_REGISTER_BASE = 0xFFB20000
    NOC_CONFIGURATION_REGISTER_BASE = 0xFFB20100
    NOC_STATUS_REGISTER_BASE = 0xFFB20200

    NUM_UNPACKERS = 2
    NUM_PACKERS = 4

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )
        self.instructions = WormholeInstructions()

    def is_translated_coordinate(self, x: int, y: int) -> bool:
        return x >= 16 and y >= 16

    def _get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription:
        """Overrides the base class method to provide register descriptions for Wormhole device."""
        if register_name in WormholeDevice.__register_map:
            return WormholeDevice.__register_map[register_name]
        return None

    def _get_tensix_register_base_address(self, register_description: TensixRegisterDescription) -> int:
        """Overrides the base class method to provide register base addresses for Wormhole device."""
        if isinstance(register_description, ConfigurationRegisterDescription):
            return WormholeDevice.CONFIGURATION_REGISTER_BASE
        elif isinstance(register_description, DebugRegisterDescription):
            return WormholeDevice.DEBUG_REGISTER_BASE
        elif isinstance(register_description, NocStatusRegisterDescription):
            return WormholeDevice.NOC_STATUS_REGISTER_BASE
        elif isinstance(register_description, NocConfigurationRegisterDescription):
            return WormholeDevice.NOC_CONFIGURATION_REGISTER_BASE
        else:
            return None

    __register_map = {
        # UNPACK TILE DESCRIPTOR SEC 0
        "UNPACK_TILE_DESCRIPTOR0_in_data_format": ConfigurationRegisterDescription(index=52, mask=0xF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_uncompressed": ConfigurationRegisterDescription(index=52, mask=0x10, shift=4),
        "UNPACK_TILE_DESCRIPTOR0_reserved_0": ConfigurationRegisterDescription(index=52, mask=0xE0, shift=5),
        "UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane": ConfigurationRegisterDescription(index=52, mask=0xF00, shift=8),
        "UNPACK_TILE_DESCRIPTOR0_reserved_1": ConfigurationRegisterDescription(index=52, mask=0xF000, shift=12),
        "UNPACK_TILE_DESCRIPTOR0_x_dim": ConfigurationRegisterDescription(index=52, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_y_dim": ConfigurationRegisterDescription(index=53, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_z_dim": ConfigurationRegisterDescription(index=53, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_w_dim": ConfigurationRegisterDescription(index=54, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=54, mask=0xFFFF0000, shift=16
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi": ConfigurationRegisterDescription(index=55, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_digest_type": ConfigurationRegisterDescription(index=55, mask=0xFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_digest_size": ConfigurationRegisterDescription(index=55, mask=0xFF000000, shift=24),
        # UNPACK TILE DESCRIPTOR SEC 1
        "UNPACK_TILE_DESCRIPTOR1_in_data_format": ConfigurationRegisterDescription(index=92, mask=0xF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_uncompressed": ConfigurationRegisterDescription(index=92, mask=0x10, shift=4),
        "UNPACK_TILE_DESCRIPTOR1_reserved_0": ConfigurationRegisterDescription(index=92, mask=0xE0, shift=5),
        "UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane": ConfigurationRegisterDescription(index=92, mask=0xF00, shift=8),
        "UNPACK_TILE_DESCRIPTOR1_reserved_1": ConfigurationRegisterDescription(index=92, mask=0xF000, shift=12),
        "UNPACK_TILE_DESCRIPTOR1_x_dim": ConfigurationRegisterDescription(index=92, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_y_dim": ConfigurationRegisterDescription(index=93, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_z_dim": ConfigurationRegisterDescription(index=93, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_w_dim": ConfigurationRegisterDescription(index=94, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=94, mask=0xFFFF0000, shift=16
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi": ConfigurationRegisterDescription(index=95, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_digest_type": ConfigurationRegisterDescription(index=95, mask=0xFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_digest_size": ConfigurationRegisterDescription(index=95, mask=0xFF000000, shift=24),
        # UNPACK CONFIG SEC 0
        "UNPACK_CONFIG0_out_data_format": ConfigurationRegisterDescription(index=60, mask=0xF, shift=0),
        "UNPACK_CONFIG0_throttle_mode": ConfigurationRegisterDescription(index=60, mask=0x30, shift=4),
        "UNPACK_CONFIG0_context_count": ConfigurationRegisterDescription(index=60, mask=0xC0, shift=6),
        "UNPACK_CONFIG0_haloize_mode": ConfigurationRegisterDescription(index=60, mask=0x100, shift=8),
        "UNPACK_CONFIG0_tileize_mode": ConfigurationRegisterDescription(index=60, mask=0x200, shift=9),
        "UNPACK_CONFIG0_unpack_src_reg_set_upd": ConfigurationRegisterDescription(index=60, mask=0x400, shift=10),
        "UNPACK_CONFIG0_unpack_if_sel": ConfigurationRegisterDescription(index=60, mask=0x800, shift=11),
        "UNPACK_CONFIG0_upsample_rate": ConfigurationRegisterDescription(index=60, mask=0x3000, shift=12),
        "UNPACK_CONFIG0_reserved_1": ConfigurationRegisterDescription(index=60, mask=0x4000, shift=14),
        "UNPACK_CONFIG0_upsample_and_interleave": ConfigurationRegisterDescription(index=60, mask=0x8000, shift=15),
        "UNPACK_CONFIG0_shift_amount": ConfigurationRegisterDescription(index=60, mask=0xFFFF0000, shift=16),
        "UNPACK_CONFIG0_uncompress_cntx0_3": ConfigurationRegisterDescription(index=61, mask=0xF, shift=0),
        "UNPACK_CONFIG0_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(index=61, mask=0xF0, shift=4),
        "UNPACK_CONFIG0_force_shared_exp": ConfigurationRegisterDescription(index=61, mask=0x100, shift=8),
        "UNPACK_CONFIG0_reserved_2": ConfigurationRegisterDescription(index=61, mask=0xFE00, shift=9),
        "UNPACK_CONFIG0_uncompress_cntx4_7": ConfigurationRegisterDescription(index=61, mask=0xF0000, shift=16),
        "UNPACK_CONFIG0_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(index=61, mask=0xF00000, shift=20),
        "UNPACK_CONFIG0_reserved_3": ConfigurationRegisterDescription(index=61, mask=0xFF000000, shift=24),
        "UNPACK_CONFIG0_limit_addr": ConfigurationRegisterDescription(index=62, mask=0x1FFFF, shift=0),
        "UNPACK_CONFIG0_reserved_4": ConfigurationRegisterDescription(index=62, mask=0xFFFE0000, shift=17),
        "UNPACK_CONFIG0_fifo_size": ConfigurationRegisterDescription(index=63, mask=0x1FFFF, shift=0),
        "UNPACK_CONFIG0_reserved_5": ConfigurationRegisterDescription(index=63, mask=0xFFFE0000, shift=17),
        # UNPACK CONFIG SEC 1
        "UNPACK_CONFIG1_out_data_format": ConfigurationRegisterDescription(index=100, mask=0xF, shift=0),
        "UNPACK_CONFIG1_throttle_mode": ConfigurationRegisterDescription(index=100, mask=0x30, shift=4),
        "UNPACK_CONFIG1_context_count": ConfigurationRegisterDescription(index=100, mask=0xC0, shift=6),
        "UNPACK_CONFIG1_haloize_mode": ConfigurationRegisterDescription(index=100, mask=0x100, shift=8),
        "UNPACK_CONFIG1_tileize_mode": ConfigurationRegisterDescription(index=100, mask=0x200, shift=9),
        "UNPACK_CONFIG1_unpack_src_reg_set_upd": ConfigurationRegisterDescription(index=100, mask=0x400, shift=10),
        "UNPACK_CONFIG1_unpack_if_sel": ConfigurationRegisterDescription(index=100, mask=0x800, shift=11),
        "UNPACK_CONFIG1_upsample_rate": ConfigurationRegisterDescription(index=100, mask=0x3000, shift=12),
        "UNPACK_CONFIG1_reserved_1": ConfigurationRegisterDescription(index=100, mask=0x4000, shift=14),
        "UNPACK_CONFIG1_upsample_and_interleave": ConfigurationRegisterDescription(index=100, mask=0x8000, shift=15),
        "UNPACK_CONFIG1_shift_amount": ConfigurationRegisterDescription(index=100, mask=0xFFFF0000, shift=16),
        "UNPACK_CONFIG1_uncompress_cntx0_3": ConfigurationRegisterDescription(index=101, mask=0xF, shift=0),
        "UNPACK_CONFIG1_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(index=101, mask=0xF0, shift=4),
        "UNPACK_CONFIG1_force_shared_exp": ConfigurationRegisterDescription(index=101, mask=0x100, shift=8),
        "UNPACK_CONFIG1_reserved_2": ConfigurationRegisterDescription(index=101, mask=0xFE00, shift=9),
        "UNPACK_CONFIG1_uncompress_cntx4_7": ConfigurationRegisterDescription(index=101, mask=0xF0000, shift=16),
        "UNPACK_CONFIG1_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(index=101, mask=0xF00000, shift=20),
        "UNPACK_CONFIG1_reserved_3": ConfigurationRegisterDescription(index=101, mask=0xFF000000, shift=24),
        "UNPACK_CONFIG1_limit_addr": ConfigurationRegisterDescription(index=102, mask=0x1FFFF, shift=0),
        "UNPACK_CONFIG1_reserved_4": ConfigurationRegisterDescription(index=102, mask=0xFFFE0000, shift=17),
        "UNPACK_CONFIG1_fifo_size": ConfigurationRegisterDescription(index=103, mask=0x1FFFF, shift=0),
        "UNPACK_CONFIG1_reserved_5": ConfigurationRegisterDescription(index=103, mask=0xFFFE0000, shift=17),
        # ALU CONFIG
        "ALU_ROUNDING_MODE_Fpu_srnd_en": ConfigurationRegisterDescription(index=1, mask=0x1, shift=0),
        "ALU_ROUNDING_MODE_Gasket_srnd_en": ConfigurationRegisterDescription(index=1, mask=0x2, shift=1),
        "ALU_ROUNDING_MODE_Packer_srnd_en": ConfigurationRegisterDescription(index=1, mask=0x4, shift=2),
        "ALU_ROUNDING_MODE_Padding": ConfigurationRegisterDescription(index=1, mask=0x1FF8, shift=3),
        "ALU_ROUNDING_MODE_GS_LF": ConfigurationRegisterDescription(index=1, mask=0x2000, shift=13),
        "ALU_ROUNDING_MODE_Bfp8_HF": ConfigurationRegisterDescription(index=1, mask=0x4000, shift=14),
        "ALU_FORMAT_SPEC_REG0_SrcAUnsigned": ConfigurationRegisterDescription(index=1, mask=0x8000, shift=15),
        "ALU_FORMAT_SPEC_REG0_SrcBUnsigned": ConfigurationRegisterDescription(index=1, mask=0x10000, shift=16),
        "ALU_FORMAT_SPEC_REG0_SrcA": ConfigurationRegisterDescription(index=1, mask=0x1E0000, shift=17),
        "ALU_FORMAT_SPEC_REG1_SrcB": ConfigurationRegisterDescription(index=1, mask=0x1E00000, shift=21),
        "ALU_FORMAT_SPEC_REG2_Dstacc": ConfigurationRegisterDescription(index=1, mask=0x1E000000, shift=25),
        "ALU_ACC_CTRL_Fp32_enabled": ConfigurationRegisterDescription(index=1, mask=0x20000000, shift=29),
        "ALU_ACC_CTRL_SFPU_Fp32_enabled": ConfigurationRegisterDescription(index=1, mask=0x40000000, shift=30),
        "ALU_ACC_CTRL_INT8_math_enabled": ConfigurationRegisterDescription(index=1, mask=0x80000000, shift=31),
        # PACK CONFIG SEC 0 REG 1
        "PACK_CONFIG01_row_ptr_section_size": ConfigurationRegisterDescription(index=56, mask=0xFFFF, shift=0),
        "PACK_CONFIG01_exp_section_size": ConfigurationRegisterDescription(index=56, mask=0xFFFF0000, shift=16),
        "PACK_CONFIG01_l1_dest_addr": ConfigurationRegisterDescription(index=57, mask=0xFFFFFFFF, shift=0),
        "PACK_CONFIG01_uncompress": ConfigurationRegisterDescription(index=58, mask=0x1, shift=0),
        "PACK_CONFIG01_add_l1_dest_addr_offset": ConfigurationRegisterDescription(index=58, mask=0x2, shift=1),
        "PACK_CONFIG01_reserved_0": ConfigurationRegisterDescription(index=58, mask=0xC, shift=2),
        "PACK_CONFIG01_out_data_format": ConfigurationRegisterDescription(index=58, mask=0xF0, shift=4),
        "PACK_CONFIG01_in_data_format": ConfigurationRegisterDescription(index=58, mask=0xF00, shift=8),
        "PACK_CONFIG01_reserved_1": ConfigurationRegisterDescription(index=58, mask=0xF000, shift=12),
        "PACK_CONFIG01_src_if_sel": ConfigurationRegisterDescription(index=58, mask=0x10000, shift=16),
        "PACK_CONFIG01_pack_per_xy_plane": ConfigurationRegisterDescription(index=58, mask=0xFE0000, shift=17),
        "PACK_CONFIG01_l1_src_addr": ConfigurationRegisterDescription(index=58, mask=0xFF000000, shift=24),
        "PACK_CONFIG01_downsample_mask": ConfigurationRegisterDescription(index=59, mask=0xFFFF, shift=0),
        "PACK_CONFIG01_downsample_shift_count": ConfigurationRegisterDescription(index=59, mask=0x70000, shift=16),
        "PACK_CONFIG01_read_mode": ConfigurationRegisterDescription(index=59, mask=0x80000, shift=19),
        "PACK_CONFIG01_exp_threshold_en": ConfigurationRegisterDescription(index=59, mask=0x100000, shift=20),
        "PACK_CONFIG01_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=59, mask=0x600000, shift=21
        ),
        "PACK_CONFIG01_reserved_2": ConfigurationRegisterDescription(index=59, mask=0x800000, shift=23),
        "PACK_CONFIG01_exp_threshold": ConfigurationRegisterDescription(index=59, mask=0xFF000000, shift=24),
        # PACK CONFIG SEC 0 REG 8
        "PACK_CONFIG08_row_ptr_section_size": ConfigurationRegisterDescription(index=84, mask=0xFFFF, shift=0),
        "PACK_CONFIG08_exp_section_size": ConfigurationRegisterDescription(index=84, mask=0xFFFF0000, shift=16),
        "PACK_CONFIG08_l1_dest_addr": ConfigurationRegisterDescription(index=85, mask=0xFFFFFFFF, shift=0),
        "PACK_CONFIG08_uncompress": ConfigurationRegisterDescription(index=86, mask=0x1, shift=0),
        "PACK_CONFIG08_add_l1_dest_addr_offset": ConfigurationRegisterDescription(index=86, mask=0x2, shift=1),
        "PACK_CONFIG08_reserved_0": ConfigurationRegisterDescription(index=86, mask=0xC, shift=2),
        "PACK_CONFIG08_out_data_format": ConfigurationRegisterDescription(index=86, mask=0xF0, shift=4),
        "PACK_CONFIG08_in_data_format": ConfigurationRegisterDescription(index=86, mask=0xF00, shift=8),
        "PACK_CONFIG08_reserved_1": ConfigurationRegisterDescription(index=86, mask=0xF000, shift=12),
        "PACK_CONFIG08_src_if_sel": ConfigurationRegisterDescription(index=86, mask=0x10000, shift=16),
        "PACK_CONFIG08_pack_per_xy_plane": ConfigurationRegisterDescription(index=86, mask=0xFE0000, shift=17),
        "PACK_CONFIG08_l1_src_addr": ConfigurationRegisterDescription(index=86, mask=0xFF000000, shift=24),
        "PACK_CONFIG08_downsample_mask": ConfigurationRegisterDescription(index=87, mask=0xFFFF, shift=0),
        "PACK_CONFIG08_downsample_shift_count": ConfigurationRegisterDescription(index=87, mask=0x70000, shift=16),
        "PACK_CONFIG08_read_mode": ConfigurationRegisterDescription(index=87, mask=0x80000, shift=19),
        "PACK_CONFIG08_exp_threshold_en": ConfigurationRegisterDescription(index=87, mask=0x100000, shift=20),
        "PACK_CONFIG08_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=87, mask=0x600000, shift=21
        ),
        "PACK_CONFIG08_reserved_2": ConfigurationRegisterDescription(index=87, mask=0x800000, shift=23),
        "PACK_CONFIG08_exp_threshold": ConfigurationRegisterDescription(index=87, mask=0xFF000000, shift=24),
        # PACK CONFIG SEC 1 REG 1
        "PACK_CONFIG11_row_ptr_section_size": ConfigurationRegisterDescription(index=96, mask=0xFFFF, shift=0),
        "PACK_CONFIG11_exp_section_size": ConfigurationRegisterDescription(index=96, mask=0xFFFF0000, shift=16),
        "PACK_CONFIG11_l1_dest_addr": ConfigurationRegisterDescription(index=97, mask=0xFFFFFFFF, shift=0),
        "PACK_CONFIG11_uncompress": ConfigurationRegisterDescription(index=98, mask=0x1, shift=0),
        "PACK_CONFIG11_add_l1_dest_addr_offset": ConfigurationRegisterDescription(index=98, mask=0x2, shift=1),
        "PACK_CONFIG11_reserved_0": ConfigurationRegisterDescription(index=98, mask=0xC, shift=2),
        "PACK_CONFIG11_out_data_format": ConfigurationRegisterDescription(index=98, mask=0xF0, shift=4),
        "PACK_CONFIG11_in_data_format": ConfigurationRegisterDescription(index=98, mask=0xF00, shift=8),
        "PACK_CONFIG11_reserved_1": ConfigurationRegisterDescription(index=98, mask=0xF000, shift=12),
        "PACK_CONFIG11_src_if_sel": ConfigurationRegisterDescription(index=98, mask=0x10000, shift=16),
        "PACK_CONFIG11_pack_per_xy_plane": ConfigurationRegisterDescription(index=98, mask=0xFE0000, shift=17),
        "PACK_CONFIG11_l1_src_addr": ConfigurationRegisterDescription(index=98, mask=0xFF000000, shift=24),
        "PACK_CONFIG11_downsample_mask": ConfigurationRegisterDescription(index=99, mask=0xFFFF, shift=0),
        "PACK_CONFIG11_downsample_shift_count": ConfigurationRegisterDescription(index=99, mask=0x70000, shift=16),
        "PACK_CONFIG11_read_mode": ConfigurationRegisterDescription(index=99, mask=0x80000, shift=19),
        "PACK_CONFIG11_exp_threshold_en": ConfigurationRegisterDescription(index=99, mask=0x100000, shift=20),
        "PACK_CONFIG11_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=99, mask=0x600000, shift=21
        ),
        "PACK_CONFIG11_reserved_2": ConfigurationRegisterDescription(index=99, mask=0x800000, shift=23),
        "PACK_CONFIG11_exp_threshold": ConfigurationRegisterDescription(index=99, mask=0xFF000000, shift=24),
        # PACK CONFIG SEC 1 REG 8
        "PACK_CONFIG18_row_ptr_section_size": ConfigurationRegisterDescription(index=124, mask=0xFFFF, shift=0),
        "PACK_CONFIG18_exp_section_size": ConfigurationRegisterDescription(index=124, mask=0xFFFF0000, shift=16),
        "PACK_CONFIG18_l1_dest_addr": ConfigurationRegisterDescription(index=125, mask=0xFFFFFFFF, shift=0),
        "PACK_CONFIG18_uncompress": ConfigurationRegisterDescription(index=126, mask=0x1, shift=0),
        "PACK_CONFIG18_add_l1_dest_addr_offset": ConfigurationRegisterDescription(index=126, mask=0x2, shift=1),
        "PACK_CONFIG18_reserved_0": ConfigurationRegisterDescription(index=126, mask=0xC, shift=2),
        "PACK_CONFIG18_out_data_format": ConfigurationRegisterDescription(index=126, mask=0xF0, shift=4),
        "PACK_CONFIG18_in_data_format": ConfigurationRegisterDescription(index=126, mask=0xF00, shift=8),
        "PACK_CONFIG18_reserved_1": ConfigurationRegisterDescription(index=126, mask=0xF000, shift=12),
        "PACK_CONFIG18_src_if_sel": ConfigurationRegisterDescription(index=126, mask=0x10000, shift=16),
        "PACK_CONFIG18_pack_per_xy_plane": ConfigurationRegisterDescription(index=126, mask=0xFE0000, shift=17),
        "PACK_CONFIG18_l1_src_addr": ConfigurationRegisterDescription(index=126, mask=0xFF000000, shift=24),
        "PACK_CONFIG18_downsample_mask": ConfigurationRegisterDescription(index=127, mask=0xFFFF, shift=0),
        "PACK_CONFIG18_downsample_shift_count": ConfigurationRegisterDescription(index=127, mask=0x70000, shift=16),
        "PACK_CONFIG18_read_mode": ConfigurationRegisterDescription(index=127, mask=0x80000, shift=19),
        "PACK_CONFIG18_exp_threshold_en": ConfigurationRegisterDescription(index=127, mask=0x100000, shift=20),
        "PACK_CONFIG18_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=127, mask=0x600000, shift=21
        ),
        "PACK_CONFIG18_reserved_2": ConfigurationRegisterDescription(index=127, mask=0x800000, shift=23),
        "PACK_CONFIG18_exp_threshold": ConfigurationRegisterDescription(index=127, mask=0xFF000000, shift=24),
        # RELU CONFIG
        "ALU_ACC_CTRL_Zero_Flag_disabled_src": ConfigurationRegisterDescription(index=2, mask=0x1, shift=0),
        "ALU_ACC_CTRL_Zero_Flag_disabled_dst": ConfigurationRegisterDescription(index=2, mask=0x2, shift=1),
        "STACC_RELU_ApplyRelu": ConfigurationRegisterDescription(index=2, mask=0x3C, shift=2),
        "STACC_RELU_ReluThreshold": ConfigurationRegisterDescription(index=2, mask=0x3FFFC0, shift=6),
        "DISABLE_RISC_BP_Disable_main": ConfigurationRegisterDescription(index=2, mask=0x400000, shift=22),
        "DISABLE_RISC_BP_Disable_trisc": ConfigurationRegisterDescription(index=2, mask=0x3800000, shift=23),
        "DISABLE_RISC_BP_Disable_ncrisc": ConfigurationRegisterDescription(index=2, mask=0x4000000, shift=26),
        "DISABLE_RISC_BP_Disable_bmp_clear_main": ConfigurationRegisterDescription(index=2, mask=0x8000000, shift=27),
        "DISABLE_RISC_BP_Disable_bmp_clear_trisc": ConfigurationRegisterDescription(index=2, mask=0x70000000, shift=28),
        "DISABLE_RISC_BP_Disable_bmp_clear_ncrisc": ConfigurationRegisterDescription(
            index=2, mask=0x80000000, shift=31
        ),
        # DEST RD CTRL
        "PACK_DEST_RD_CTRL_Read_32b_data": ConfigurationRegisterDescription(index=14, mask=0x1, shift=0),
        "PACK_DEST_RD_CTRL_Read_unsigned": ConfigurationRegisterDescription(index=14, mask=0x2, shift=1),
        "PACK_DEST_RD_CTRL_Read_int8": ConfigurationRegisterDescription(index=14, mask=0x4, shift=2),
        "PACK_DEST_RD_CTRL_Round_10b_mant": ConfigurationRegisterDescription(index=14, mask=0x8, shift=3),
        "PACK_DEST_RD_CTRL_Reserved": ConfigurationRegisterDescription(index=14, mask=0xFFFFFFF0, shift=4),
        # EDGE OFFSET SEC 0
        "PACK_EDGE_OFFSET0_mask": ConfigurationRegisterDescription(index=20, mask=0xFFFF, shift=0),
        "PACK_EDGE_OFFSET0_mode": ConfigurationRegisterDescription(index=20, mask=0x10000, shift=16),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack0": ConfigurationRegisterDescription(
            index=20, mask=0x60000, shift=17
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack1": ConfigurationRegisterDescription(
            index=20, mask=0x180000, shift=19
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack2": ConfigurationRegisterDescription(
            index=20, mask=0x600000, shift=21
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack3": ConfigurationRegisterDescription(
            index=20, mask=0x1800000, shift=23
        ),
        "PACK_EDGE_OFFSET0_reserved": ConfigurationRegisterDescription(index=20, mask=0xFE000000, shift=25),
        # EDGE OFFSET SEC 1
        "PACK_EDGE_OFFSET1_mask": ConfigurationRegisterDescription(index=21, mask=0xFFFF, shift=0),
        # EDGE OFFSET SEC 2
        "PACK_EDGE_OFFSET2_mask": ConfigurationRegisterDescription(index=22, mask=0xFFFF, shift=0),
        # EDGE OFFSET SEC 3
        "PACK_EDGE_OFFSET3_mask": ConfigurationRegisterDescription(index=23, mask=0xFFFF, shift=0),
        # PACK COUNTERS SEC 0
        "PACK_COUNTERS0_pack_per_xy_plane": ConfigurationRegisterDescription(index=24, mask=0xFF, shift=0),
        "PACK_COUNTERS0_pack_reads_per_xy_plane": ConfigurationRegisterDescription(index=24, mask=0xFF00, shift=8),
        "PACK_COUNTERS0_pack_xys_per_til": ConfigurationRegisterDescription(index=24, mask=0x7F0000, shift=16),
        "PACK_COUNTERS0_pack_yz_transposed": ConfigurationRegisterDescription(index=24, mask=800000, shift=23),
        "PACK_COUNTERS0_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=24, mask=0xFF000000, shift=24
        ),
        # PACK COUNTERS SEC 1
        "PACK_COUNTERS1_pack_per_xy_plane": ConfigurationRegisterDescription(index=25, mask=0xFF, shift=0),
        "PACK_COUNTERS1_pack_reads_per_xy_plane": ConfigurationRegisterDescription(index=25, mask=0xFF00, shift=8),
        "PACK_COUNTERS1_pack_xys_per_til": ConfigurationRegisterDescription(index=25, mask=0x7F0000, shift=16),
        "PACK_COUNTERS1_pack_yz_transposed": ConfigurationRegisterDescription(index=25, mask=800000, shift=23),
        "PACK_COUNTERS1_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=25, mask=0xFF000000, shift=24
        ),
        # PACK COUNTERS SEC 2
        "PACK_COUNTERS2_pack_per_xy_plane": ConfigurationRegisterDescription(index=26, mask=0xFF, shift=0),
        "PACK_COUNTERS2_pack_reads_per_xy_plane": ConfigurationRegisterDescription(index=26, mask=0xFF00, shift=8),
        "PACK_COUNTERS2_pack_xys_per_til": ConfigurationRegisterDescription(index=26, mask=0x7F0000, shift=16),
        "PACK_COUNTERS2_pack_yz_transposed": ConfigurationRegisterDescription(index=26, mask=800000, shift=23),
        "PACK_COUNTERS2_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=26, mask=0xFF000000, shift=24
        ),
        # PACK COUNTERS SEC 3
        "PACK_COUNTERS3_pack_per_xy_plane": ConfigurationRegisterDescription(index=27, mask=0xFF, shift=0),
        "PACK_COUNTERS3_pack_reads_per_xy_plane": ConfigurationRegisterDescription(index=27, mask=0xFF00, shift=8),
        "PACK_COUNTERS3_pack_xys_per_til": ConfigurationRegisterDescription(index=27, mask=0x7F0000, shift=16),
        "PACK_COUNTERS3_pack_yz_transposed": ConfigurationRegisterDescription(index=27, mask=800000, shift=23),
        "PACK_COUNTERS3_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=27, mask=0xFF000000, shift=24
        ),
        # PACK STRIDES REG 0
        "PACK_STRIDES0_x_stride": ConfigurationRegisterDescription(index=8, mask=0xFFF, shift=0),
        "PACK_STRIDES0_y_stride": ConfigurationRegisterDescription(index=8, mask=0xFFF000, shift=12),
        "PACK_STRIDES0_z_stride": ConfigurationRegisterDescription(index=9, mask=0xFFF, shift=0),
        "PACK_STRIDES0_w_stride": ConfigurationRegisterDescription(index=9, mask=0xFFFF000, shift=12),
        # PACK STRIDES REG 1
        "PACK_STRIDES1_x_stride": ConfigurationRegisterDescription(index=10, mask=0xFFF, shift=0),
        "PACK_STRIDES1_y_stride": ConfigurationRegisterDescription(index=10, mask=0xFFF000, shift=12),
        "PACK_STRIDES1_z_stride": ConfigurationRegisterDescription(index=11, mask=0xFFF, shift=0),
        "PACK_STRIDES1_w_stride": ConfigurationRegisterDescription(index=11, mask=0xFFFF000, shift=12),
        "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=157, mask=0x1F),
        "TRISC_RESET_PC_SEC0_PC": ConfigurationRegisterDescription(index=158),
        "TRISC_RESET_PC_SEC1_PC": ConfigurationRegisterDescription(index=159),
        "TRISC_RESET_PC_SEC2_PC": ConfigurationRegisterDescription(index=160),
        "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=161, mask=0x7),
        "NCRISC_RESET_PC_PC": ConfigurationRegisterDescription(index=162),
        "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=163, mask=0x1),
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
        # NOC Registers
        "NIU_MST_ATOMIC_RESP_RECEIVED": NocStatusRegisterDescription(address=0x0),
        "NIU_MST_WR_ACK_RECEIVED": NocStatusRegisterDescription(address=0x4),
        "NIU_MST_RD_RESP_RECEIVED": NocStatusRegisterDescription(address=0x8),
        "NIU_MST_RD_DATA_WORD_RECEIVED": NocStatusRegisterDescription(address=0xC),
        "NIU_MST_CMD_ACCEPTED": NocStatusRegisterDescription(address=0x10),
        "NIU_MST_RD_REQ_SENT": NocStatusRegisterDescription(address=0x14),
        "NIU_MST_NONPOSTED_ATOMIC_SENT": NocStatusRegisterDescription(address=0x18),
        "NIU_MST_POSTED_ATOMIC_SENT": NocStatusRegisterDescription(address=0x1C),
        "NIU_MST_NONPOSTED_WR_DATA_WORD_SENT": NocStatusRegisterDescription(address=0x20),
        "NIU_MST_POSTED_WR_DATA_WORD_SENT": NocStatusRegisterDescription(address=0x24),
        "NIU_MST_NONPOSTED_WR_REQ_SENT": NocStatusRegisterDescription(address=0x28),
        "NIU_MST_POSTED_WR_REQ_SENT": NocStatusRegisterDescription(address=0x2C),
        "NIU_MST_NONPOSTED_WR_REQ_STARTED": NocStatusRegisterDescription(address=0x30),
        "NIU_MST_POSTED_WR_REQ_STARTED": NocStatusRegisterDescription(address=0x34),
        "NIU_MST_RD_REQ_STARTED": NocStatusRegisterDescription(address=0x38),
        "NIU_MST_NONPOSTED_ATOMIC_STARTED": NocStatusRegisterDescription(address=0x3C),
        "NIU_MST_REQS_OUTSTANDING_ID": NocStatusRegisterDescription(address=0x40),  # 16 registers
        "NIU_MST_WRITE_REQS_OUTGOING_ID": NocStatusRegisterDescription(address=0x80),  # 16 registers
        "NIU_SLV_ATOMIC_RESP_SENT": NocStatusRegisterDescription(address=0xC0),
        "NIU_SLV_WR_ACK_SENT": NocStatusRegisterDescription(address=0xC4),
        "NIU_SLV_RD_RESP_SENT": NocStatusRegisterDescription(address=0xC8),
        "NIU_SLV_RD_DATA_WORD_SENT": NocStatusRegisterDescription(address=0xCC),
        "NIU_SLV_REQ_ACCEPTED": NocStatusRegisterDescription(address=0xD0),
        "NIU_SLV_RD_REQ_RECEIVED": NocStatusRegisterDescription(address=0xD4),
        "NIU_SLV_NONPOSTED_ATOMIC_RECEIVED": NocStatusRegisterDescription(address=0xD8),
        "NIU_SLV_POSTED_ATOMIC_RECEIVED": NocStatusRegisterDescription(address=0xDC),
        "NIU_SLV_NONPOSTED_WR_DATA_WORD_RECEIVED": NocStatusRegisterDescription(address=0xE0),
        "NIU_SLV_POSTED_WR_DATA_WORD_RECEIVED": NocStatusRegisterDescription(address=0xE4),
        "NIU_SLV_NONPOSTED_WR_REQ_RECEIVED": NocStatusRegisterDescription(address=0xE8),
        "NIU_SLV_POSTED_WR_REQ_RECEIVED": NocStatusRegisterDescription(address=0xEC),
        "NIU_SLV_NONPOSTED_WR_REQ_STARTED": NocStatusRegisterDescription(address=0xF0),
        "NIU_SLV_POSTED_WR_REQ_STARTED": NocStatusRegisterDescription(address=0xF4),
        "NIU_CFG_0": NocConfigurationRegisterDescription(address=0x0),
        "ROUTER_CFG_0": NocConfigurationRegisterDescription(address=0x4),
        "ROUTER_CFG_1": NocConfigurationRegisterDescription(address=0x8),
        "ROUTER_CFG_2": NocConfigurationRegisterDescription(address=0xC),
        "ROUTER_CFG_3": NocConfigurationRegisterDescription(address=0x10),
        "ROUTER_CFG_4": NocConfigurationRegisterDescription(address=0x14),
        "ROUTER_CFG_5": NocConfigurationRegisterDescription(address=0x18),
        "NOC_X_ID_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(address=0x1C),
        "NOC_X_ID_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(address=0x20),
        "NOC_X_ID_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(address=0x24),
        "NOC_X_ID_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(address=0x28),
        "NOC_Y_ID_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(address=0x2C),
        "NOC_Y_ID_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(address=0x30),
        "NOC_Y_ID_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(address=0x34),
        "NOC_Y_ID_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(address=0x38),
        "NOC_ID_LOGICAL": NocConfigurationRegisterDescription(address=0x3C),
        "NOC_TARG_ADDR_LO": NocControlRegisterDescription(address=0x0),
        "NOC_TARG_ADDR_MID": NocControlRegisterDescription(address=0x4),
        "NOC_TARG_ADDR_HI": NocControlRegisterDescription(address=0x8),
        "NOC_RET_ADDR_LO": NocControlRegisterDescription(address=0xC),
        "NOC_RET_ADDR_MID": NocControlRegisterDescription(address=0x10),
        "NOC_RET_ADDR_HI": NocControlRegisterDescription(address=0x14),
        "NOC_PACKET_TAG": NocControlRegisterDescription(address=0x18),
        "NOC_CTRL": NocControlRegisterDescription(address=0x1C),
        "NOC_AT_LEN_BE": NocControlRegisterDescription(address=0x20),
        "NOC_AT_DATA": NocControlRegisterDescription(address=0x24),
        "NOC_CMD_CTRL": NocControlRegisterDescription(address=0x28),
        "NOC_NODE_ID": NocControlRegisterDescription(address=0x2C),
        "NOC_ENDPOINT_ID": NocControlRegisterDescription(address=0x30),
        "NUM_MEM_PARITY_ERR": NocControlRegisterDescription(address=0x40),
        "NUM_HEADER_1B_ERR": NocControlRegisterDescription(address=0x44),
        "NUM_HEADER_2B_ERR": NocControlRegisterDescription(address=0x48),
        "ECC_CTRL": NocControlRegisterDescription(address=0x4C),
        "NOC_CLEAR_OUTSTANDING_REQ_CNT": NocControlRegisterDescription(address=0x50),
    }

    def _get_debug_bus_signal_description(self, name):
        """Overrides the base class method to provide debug bus signal descriptions for Wormhole device."""
        if name in WormholeDevice.__debug_bus_signal_map:
            return WormholeDevice.__debug_bus_signal_map[name]
        return None

    __debug_bus_signal_map = {
        # For the other signals applying the pc_mask.
        "brisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 5, mask=0x7FFFFFFF),
        "trisc0_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 6, mask=0x7FFFFFFF),
        "trisc1_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 7, mask=0x7FFFFFFF),
        "trisc2_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 8, mask=0x7FFFFFFF),
        "ncrisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 12, mask=0x7FFFFFFF),
    }

    def get_debug_bus_signal_names(self) -> List[str]:
        return list(self.__debug_bus_signal_map.keys())

    # UNPACKER GETTERS

    def get_alu_config(self, debug_tensix: TensixDebug) -> list[dict]:
        alu_config = {}

        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Fpu_srnd_en", alu_config, ValueType.BOOL)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Gasket_srnd_en", alu_config, ValueType.BOOL)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Packer_srnd_en", alu_config, ValueType.BOOL)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Padding", alu_config, ValueType.HEX)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_GS_LF", alu_config, ValueType.HEX)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Bfp8_HF", alu_config, ValueType.HEX)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG0_SrcAUnsigned", alu_config, ValueType.HEX)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG0_SrcBUnsigned", alu_config, ValueType.HEX)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG0_SrcA", alu_config, ValueType.FORMAT)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG1_SrcB", alu_config, ValueType.FORMAT)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG2_Dstacc", alu_config, ValueType.FORMAT)
        debug_tensix.get_config_field("ALU_ACC_CTRL_Fp32_enabled", alu_config, ValueType.BOOL)
        debug_tensix.get_config_field("ALU_ACC_CTRL_SFPU_Fp32_enabled", alu_config, ValueType.BOOL)
        debug_tensix.get_config_field("ALU_ACC_CTRL_INT8_math_enabled", alu_config, ValueType.BOOL)

        return [alu_config]

    def get_unpack_tile_descriptor(self, debug_tensix: TensixDebug) -> list[dict]:
        struct_name = "UNPACK_TILE_DESCRIPTOR"

        tile_descriptor_list = []

        for i in range(self.NUM_UNPACKERS):
            tile_descriptor = {}

            register_name = struct_name + str(i)

            start = len(register_name) + 1  # ignores name prefix

            debug_tensix.get_config_field(register_name + "_in_data_format", tile_descriptor, ValueType.FORMAT, start)
            debug_tensix.get_config_field(register_name + "_uncompressed", tile_descriptor, ValueType.BOOL, start)
            debug_tensix.get_config_field(register_name + "_reserved_0", tile_descriptor, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_blobs_per_xy_plane", tile_descriptor, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_reserved_1", tile_descriptor, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_x_dim", tile_descriptor, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_y_dim", tile_descriptor, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_z_dim", tile_descriptor, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_w_dim", tile_descriptor, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_blobs_y_start_lo", tile_descriptor, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_blobs_y_start_hi", tile_descriptor, ValueType.DEC, start)
            tile_descriptor["blobs_y_start"] = (tile_descriptor["blobs_y_start_hi"] << 16) | tile_descriptor[
                "blobs_y_start_lo"
            ]
            del tile_descriptor["blobs_y_start_lo"]
            del tile_descriptor["blobs_y_start_hi"]
            debug_tensix.get_config_field(register_name + "_digest_type", tile_descriptor, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_digest_size", tile_descriptor, ValueType.DEC, start)

            tile_descriptor_list.append(tile_descriptor)

        return tile_descriptor_list

    def get_unpack_config(self, debug_tensix: TensixDebug) -> list[dict]:
        struct_name = "UNPACK_CONFIG"

        unpack_config_list = []

        for i in range(self.NUM_UNPACKERS):
            unpack_config = {}

            register_name = struct_name + str(i)

            start = len(register_name) + 1  # ignores name prefix

            debug_tensix.get_config_field(register_name + "_out_data_format", unpack_config, ValueType.FORMAT, start)
            debug_tensix.get_config_field(register_name + "_throttle_mode", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_context_count", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_haloize_mode", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_tileize_mode", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(
                register_name + "_unpack_src_reg_set_upd", unpack_config, ValueType.BOOL, start
            )
            debug_tensix.get_config_field(register_name + "_unpack_if_sel", unpack_config, ValueType.BOOL, start)
            debug_tensix.get_config_field(register_name + "_upsample_rate", unpack_config, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_reserved_1", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(
                register_name + "_upsample_and_interleave", unpack_config, ValueType.BOOL, start
            )
            debug_tensix.get_config_field(register_name + "_shift_amount", unpack_config, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_uncompress_cntx0_3", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_unpack_if_sel_cntx0_3", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_force_shared_exp", unpack_config, ValueType.BOOL, start)
            debug_tensix.get_config_field(register_name + "_reserved_2", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_uncompress_cntx4_7", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_unpack_if_sel_cntx4_7", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_reserved_3", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_limit_addr", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_reserved_4", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_fifo_size", unpack_config, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_reserved_5", unpack_config, ValueType.HEX, start)

            unpack_config_list.append(unpack_config)

        return unpack_config_list

    def get_pack_config(self, debug_tensix: TensixDebug) -> list[dict]:
        struct_name = "PACK_CONFIG"

        pack_config_list = []

        for i in [0, 1]:
            for j in [1, 8]:
                pack_config = {}

                register_name = struct_name + str(i) + str(j)

                start = len(register_name) + 1  # ignores name prefix

                debug_tensix.get_config_field(
                    register_name + "_row_ptr_section_size", pack_config, ValueType.DEC, start
                )
                debug_tensix.get_config_field(register_name + "_exp_section_size", pack_config, ValueType.DEC, start)
                debug_tensix.get_config_field(register_name + "_l1_dest_addr", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_uncompress", pack_config, ValueType.BOOL, start)
                debug_tensix.get_config_field(
                    register_name + "_add_l1_dest_addr_offset", pack_config, ValueType.HEX, start
                )
                debug_tensix.get_config_field(register_name + "_reserved_0", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_out_data_format", pack_config, ValueType.FORMAT, start)
                debug_tensix.get_config_field(register_name + "_in_data_format", pack_config, ValueType.FORMAT, start)
                debug_tensix.get_config_field(register_name + "_reserved_1", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_src_if_sel", pack_config, ValueType.BOOL, start)
                debug_tensix.get_config_field(register_name + "_pack_per_xy_plane", pack_config, ValueType.DEC, start)
                debug_tensix.get_config_field(register_name + "_l1_src_addr", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_downsample_mask", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(
                    register_name + "_downsample_shift_count", pack_config, ValueType.HEX, start
                )
                debug_tensix.get_config_field(register_name + "_read_mode", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_exp_threshold_en", pack_config, ValueType.BOOL, start)
                debug_tensix.get_config_field(
                    register_name + "_pack_l1_acc_disable_pack_zero_flag", pack_config, ValueType.HEX, start
                )
                debug_tensix.get_config_field(register_name + "_reserved_2", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_exp_threshold", pack_config, ValueType.DEC, start)

                pack_config_list.append(pack_config)

        return pack_config_list

    def get_relu_config(self, debug_tensix: TensixDebug) -> list[dict]:
        relu_config = {}

        debug_tensix.get_config_field("ALU_ACC_CTRL_Zero_Flag_disabled_src", relu_config, ValueType.BOOL)
        debug_tensix.get_config_field("ALU_ACC_CTRL_Zero_Flag_disabled_dst", relu_config, ValueType.BOOL)
        debug_tensix.get_config_field("STACC_RELU_ApplyRelu", relu_config, ValueType.HEX)
        debug_tensix.get_config_field("STACC_RELU_ReluThreshold", relu_config, ValueType.DEC)
        debug_tensix.get_config_field("DISABLE_RISC_BP_Disable_main", relu_config, ValueType.BOOL)
        debug_tensix.get_config_field("DISABLE_RISC_BP_Disable_trisc", relu_config, ValueType.HEX)
        debug_tensix.get_config_field("DISABLE_RISC_BP_Disable_ncrisc", relu_config, ValueType.BOOL)
        debug_tensix.get_config_field("DISABLE_RISC_BP_Disable_bmp_clear_main", relu_config, ValueType.BOOL)
        debug_tensix.get_config_field("DISABLE_RISC_BP_Disable_bmp_clear_trisc", relu_config, ValueType.HEX)
        debug_tensix.get_config_field("DISABLE_RISC_BP_Disable_bmp_clear_ncrisc", relu_config, ValueType.BOOL)

        return [relu_config]

    def get_pack_dest_rd_ctrl(self, debug_tensix: TensixDebug) -> list[dict]:
        dest = {}

        start = 18

        debug_tensix.get_config_field("PACK_DEST_RD_CTRL_Read_32b_data", dest, ValueType.BOOL, start)
        debug_tensix.get_config_field("PACK_DEST_RD_CTRL_Read_unsigned", dest, ValueType.BOOL, start)
        debug_tensix.get_config_field("PACK_DEST_RD_CTRL_Read_int8", dest, ValueType.BOOL, start)
        debug_tensix.get_config_field("PACK_DEST_RD_CTRL_Round_10b_mant", dest, ValueType.BOOL, start)
        debug_tensix.get_config_field("PACK_DEST_RD_CTRL_Reserved", dest, ValueType.HEX, start)

        return [dest]

    def get_pack_edge_offset(self, debug_tensix: TensixDebug) -> list[dict]:
        struct_name = "PACK_EDGE_OFFSET"

        edge_list = []

        for i in range(self.NUM_PACKERS):
            edge = {}

            register_name = struct_name + str(i)

            start = len(register_name) + 1  # ignores name prefix

            debug_tensix.get_config_field(register_name + "_mask", edge, ValueType.HEX, start)

            if i == 0:
                debug_tensix.get_config_field(register_name + "_mode", edge, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_tile_row_set_select_pack0", edge, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_tile_row_set_select_pack1", edge, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_tile_row_set_select_pack2", edge, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_tile_row_set_select_pack3", edge, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_reserved", edge, ValueType.HEX, start)

            edge_list.append(edge)

        return edge_list

    def get_pack_counters(self, debug_tensix: TensixDebug) -> list[dict]:
        struct_name = "PACK_COUNTERS"

        counters_list = []

        for i in range(self.NUM_PACKERS):
            counters = {}

            register_name = struct_name + str(i)

            start = len(register_name) + 1  # ignores name prefix

            debug_tensix.get_config_field(register_name + "_pack_per_xy_plane", counters, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_pack_reads_per_xy_plane", counters, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_pack_xys_per_til", counters, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_pack_yz_transposed", counters, ValueType.BOOL, start)
            debug_tensix.get_config_field(register_name + "_pack_per_xy_plane_offset", counters, ValueType.DEC, start)

            counters_list.append(counters)

        return counters_list

    def get_pack_strides(self, debug_tensix: TensixDebug) -> list[dict]:
        struct_name = "PACK_STRIDES"

        strides_list = []

        for i in range(2):
            strides = {}

            register_name = struct_name + str(i)

            start = len(register_name) + 1  # ignores name prefix

            debug_tensix.get_config_field(register_name + "_x_stride", strides, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_y_stride", strides, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_z_stride", strides, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_w_stride", strides, ValueType.DEC, start)

            strides_list.append(strides)

        return strides_list


# end of class WormholeDevice
