# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util
from ttlens import tt_device
from ttlens.tt_device import ConfigurationRegisterDescription, DebugRegisterDescription
from ttlens.tt_debug_tensix import TensixDebug


class BlackholeInstructions(tt_device.TensixInstructions):
    def __init__(self):
        import ttlens.tt_blackhole_ops as ops

        super().__init__(ops)


#
# Device
#
class BlackholeDevice(tt_device.Device):
    # Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10, 8, 9]
    DIE_Y_TO_NOC_0_Y = [0, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6]
    DIE_X_TO_NOC_1_X = [16, 15, 0, 14, 1, 13, 2, 12, 3, 11, 4, 10, 5, 9, 6, 8, 7]
    DIE_Y_TO_NOC_1_Y = [11, 10, 0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    PCI_ARC_RESET_BASE_ADDR = 0x1FF30000
    PCI_ARC_CSM_DATA_BASE_ADDR = 0x1FE80000
    PCI_ARC_ROM_DATA_BASE_ADDR = 0x1FF00000

    NOC_ARC_RESET_BASE_ADDR = 0x80030000
    NOC_ARC_CSM_DATA_BASE_ADDR = 0x10000000
    NOC_ARC_ROM_DATA_BASE_ADDR = 0x80000000

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )
        self.instructions = BlackholeInstructions()

    def get_tensix_configuration_register_base(self) -> int:
        return 0xFFEF0000

    __configuration_register_map = {
        # UNPACK TILE DESCRIPTOR SEC0
        "UNPACK_TILE_DESCRIPTOR0_in_data_format": ConfigurationRegisterDescription(index=64, mask=0xF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_uncompressed": ConfigurationRegisterDescription(index=64, mask=0x10, shift=4),
        "UNPACK_TILE_DESCRIPTOR0_reserved_0": ConfigurationRegisterDescription(index=64, mask=0xE0, shift=5),
        "UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane": ConfigurationRegisterDescription(index=64, mask=0xF00, shift=8),
        "UNPACK_TILE_DESCRIPTOR0_reserved_1": ConfigurationRegisterDescription(index=64, mask=0xF000, shift=12),
        "UNPACK_TILE_DESCRIPTOR0_x_dim": ConfigurationRegisterDescription(index=64, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_y_dim": ConfigurationRegisterDescription(index=65, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_z_dim": ConfigurationRegisterDescription(index=65, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_w_dim": ConfigurationRegisterDescription(index=66, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=66, mask=0xFFFF0000, shift=16
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi": ConfigurationRegisterDescription(index=67, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_digest_type": ConfigurationRegisterDescription(index=67, mask=0xFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_digest_size": ConfigurationRegisterDescription(index=67, mask=0xFF000000, shift=24),
        # UNPACK TILE DESCRIPTOR SEC1
        "UNPACK_TILE_DESCRIPTOR1_in_data_format": ConfigurationRegisterDescription(index=112, mask=0xF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_uncompressed": ConfigurationRegisterDescription(index=112, mask=0x10, shift=4),
        "UNPACK_TILE_DESCRIPTOR1_reserved_0": ConfigurationRegisterDescription(index=112, mask=0xE0, shift=5),
        "UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane": ConfigurationRegisterDescription(index=112, mask=0xF00, shift=8),
        "UNPACK_TILE_DESCRIPTOR1_reserved_1": ConfigurationRegisterDescription(index=112, mask=0xF000, shift=12),
        "UNPACK_TILE_DESCRIPTOR1_x_dim": ConfigurationRegisterDescription(index=112, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_y_dim": ConfigurationRegisterDescription(index=113, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_z_dim": ConfigurationRegisterDescription(index=113, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_w_dim": ConfigurationRegisterDescription(index=114, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=114, mask=0xFFFF0000, shift=16
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi": ConfigurationRegisterDescription(index=115, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_digest_type": ConfigurationRegisterDescription(index=115, mask=0xFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_digest_size": ConfigurationRegisterDescription(index=115, mask=0xFF000000, shift=24),
        # UNPACK CONFIG SEC0
        "UNPACK_CONFIG0_out_data_format": ConfigurationRegisterDescription(index=72, mask=0xF, shift=0),
        "UNPACK_CONFIG0_throttle_mode": ConfigurationRegisterDescription(index=72, mask=0x30, shift=4),
        "UNPACK_CONFIG0_context_count": ConfigurationRegisterDescription(index=72, mask=0xC0, shift=6),
        "UNPACK_CONFIG0_haloize_mode": ConfigurationRegisterDescription(index=72, mask=0x100, shift=8),
        "UNPACK_CONFIG0_tileize_mode": ConfigurationRegisterDescription(index=72, mask=0x200, shift=9),
        "UNPACK_CONFIG0_unpack_src_reg_set_upd": ConfigurationRegisterDescription(index=72, mask=0x400, shift=10),
        "UNPACK_CONFIG0_unpack_if_sel": ConfigurationRegisterDescription(index=72, mask=0x800, shift=11),
        "UNPACK_CONFIG0_upsample_rate": ConfigurationRegisterDescription(index=72, mask=0x3000, shift=12),
        "UNPACK_CONFIG0_reserved_1": ConfigurationRegisterDescription(index=72, mask=0x4000, shift=14),
        "UNPACK_CONFIG0_upsample_and_interleave": ConfigurationRegisterDescription(index=72, mask=0x8000, shift=15),
        "UNPACK_CONFIG0_shift_amount": ConfigurationRegisterDescription(index=72, mask=0xFFFF0000, shift=16),
        "UNPACK_CONFIG0_uncompress_cntx0_3": ConfigurationRegisterDescription(index=73, mask=0xF, shift=0),
        "UNPACK_CONFIG0_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(index=73, mask=0xF0, shift=4),
        "UNPACK_CONFIG0_force_shared_exp": ConfigurationRegisterDescription(index=73, mask=0x100, shift=8),
        "UNPACK_CONFIG0_reserved_2": ConfigurationRegisterDescription(index=73, mask=0xFE00, shift=9),
        "UNPACK_CONFIG0_uncompress_cntx4_7": ConfigurationRegisterDescription(index=73, mask=0xF0000, shift=16),
        "UNPACK_CONFIG0_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(index=73, mask=0xF00000, shift=20),
        "UNPACK_CONFIG0_reserved_3": ConfigurationRegisterDescription(index=73, mask=0xFF000000, shift=24),
        "UNPACK_CONFIG0_limit_addr": ConfigurationRegisterDescription(index=74, mask=0x1FFFF, shift=0),
        "UNPACK_CONFIG0_reserved_4": ConfigurationRegisterDescription(index=74, mask=0xFFFE0000, shift=17),
        "UNPACK_CONFIG0_fifo_size": ConfigurationRegisterDescription(index=75, mask=0x1FFFF, shift=0),
        "UNPACK_CONFIG0_reserved_5": ConfigurationRegisterDescription(index=75, mask=0xFFFE0000, shift=17),
        # UNPACK CONFIG SEC1
        "UNPACK_CONFIG1_out_data_format": ConfigurationRegisterDescription(index=120, mask=0xF, shift=0),
        "UNPACK_CONFIG1_throttle_mode": ConfigurationRegisterDescription(index=120, mask=0x30, shift=4),
        "UNPACK_CONFIG1_context_count": ConfigurationRegisterDescription(index=120, mask=0xC0, shift=6),
        "UNPACK_CONFIG1_haloize_mode": ConfigurationRegisterDescription(index=120, mask=0x100, shift=8),
        "UNPACK_CONFIG1_tileize_mode": ConfigurationRegisterDescription(index=120, mask=0x200, shift=9),
        "UNPACK_CONFIG1_unpack_src_reg_set_upd": ConfigurationRegisterDescription(index=120, mask=0x400, shift=10),
        "UNPACK_CONFIG1_unpack_if_sel": ConfigurationRegisterDescription(index=120, mask=0x800, shift=11),
        "UNPACK_CONFIG1_upsample_rate": ConfigurationRegisterDescription(index=120, mask=0x3000, shift=12),
        "UNPACK_CONFIG1_reserved_1": ConfigurationRegisterDescription(index=120, mask=0x4000, shift=14),
        "UNPACK_CONFIG1_upsample_and_interleave": ConfigurationRegisterDescription(index=120, mask=0x8000, shift=15),
        "UNPACK_CONFIG1_shift_amount": ConfigurationRegisterDescription(index=120, mask=0xFFFF0000, shift=16),
        "UNPACK_CONFIG1_uncompress_cntx0_3": ConfigurationRegisterDescription(index=121, mask=0xF, shift=0),
        "UNPACK_CONFIG1_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(index=121, mask=0xF0, shift=4),
        "UNPACK_CONFIG1_force_shared_exp": ConfigurationRegisterDescription(index=121, mask=0x100, shift=8),
        "UNPACK_CONFIG1_reserved_2": ConfigurationRegisterDescription(index=121, mask=0xFE00, shift=9),
        "UNPACK_CONFIG1_uncompress_cntx4_7": ConfigurationRegisterDescription(index=121, mask=0xF0000, shift=16),
        "UNPACK_CONFIG1_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(index=121, mask=0xF00000, shift=20),
        "UNPACK_CONFIG1_reserved_3": ConfigurationRegisterDescription(index=121, mask=0xFF000000, shift=24),
        "UNPACK_CONFIG1_limit_addr": ConfigurationRegisterDescription(index=122, mask=0x1FFFF, shift=0),
        "UNPACK_CONFIG1_reserved_4": ConfigurationRegisterDescription(index=122, mask=0xFFFE0000, shift=17),
        "UNPACK_CONFIG1_fifo_size": ConfigurationRegisterDescription(index=123, mask=0x1FFFF, shift=0),
        "UNPACK_CONFIG1_reserved_5": ConfigurationRegisterDescription(index=123, mask=0xFFFE0000, shift=17),
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
        # REST
        "DISABLE_RISC_BP_Disable_main": ConfigurationRegisterDescription(index=2, mask=0x400000, shift=22),
        "DISABLE_RISC_BP_Disable_trisc": ConfigurationRegisterDescription(index=2, mask=0x3800000, shift=23),
        "DISABLE_RISC_BP_Disable_ncrisc": ConfigurationRegisterDescription(index=2, mask=0x4000000, shift=26),
        "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=185, mask=0x1F),
    }

    def get_configuration_register_description(self, register_name: str) -> ConfigurationRegisterDescription:
        if register_name in BlackholeDevice.__configuration_register_map:
            return BlackholeDevice.__configuration_register_map[register_name]
        return None

    def get_tenxis_debug_register_base(self) -> int:
        return 0xFFB12000

    __debug_register_map = {
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

    def get_debug_register_description(self, register_name: str) -> DebugRegisterDescription:
        if register_name in BlackholeDevice.__debug_register_map:
            return BlackholeDevice.__debug_register_map[register_name]
        return None

    def get_alu_config(self, debug_tensix: TensixDebug) -> list[dict]:
        alu_config = {}

        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Fpu_srnd_en", alu_config)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Gasket_srnd_en", alu_config)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Packer_srnd_en", alu_config)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Padding", alu_config)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_GS_LF", alu_config)
        debug_tensix.get_config_field("ALU_ROUNDING_MODE_Bfp8_HF", alu_config)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG0_SrcAUnsigned", alu_config)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG0_SrcBUnsigned", alu_config)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG0_SrcA", alu_config)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG1_SrcB", alu_config)
        debug_tensix.get_config_field("ALU_FORMAT_SPEC_REG2_Dstacc", alu_config)
        debug_tensix.get_config_field("ALU_ACC_CTRL_Fp32_enabled", alu_config)
        debug_tensix.get_config_field("ALU_ACC_CTRL_SFPU_Fp32_enabled", alu_config)
        debug_tensix.get_config_field("ALU_ACC_CTRL_INT8_math_enabled", alu_config)

        return [alu_config]

    def get_unpack_tile_descriptor(self, debug_tensix: TensixDebug) -> list[dict]:
        tile_descriptor0 = {}
        tile_descriptor1 = {}

        start = 24  # ignores field name prefix

        # REG_ID = 1
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_in_data_format", tile_descriptor0, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_uncompressed", tile_descriptor0, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_reserved_0", tile_descriptor0, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane", tile_descriptor0, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_reserved_1", tile_descriptor0, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_x_dim", tile_descriptor0, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_y_dim", tile_descriptor0, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_z_dim", tile_descriptor0, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_w_dim", tile_descriptor0, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo", tile_descriptor0, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi", tile_descriptor0, start)
        tile_descriptor0["blobs_y_start"] = (tile_descriptor0["blobs_y_start_hi"] << 16) | tile_descriptor0[
            "blobs_y_start_lo"
        ]
        del tile_descriptor0["blobs_y_start_lo"]
        del tile_descriptor0["blobs_y_start_hi"]
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_digest_type", tile_descriptor0, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR0_digest_size", tile_descriptor0, start)

        # REG_ID = 2
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_in_data_format", tile_descriptor1, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_uncompressed", tile_descriptor1, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_reserved_0", tile_descriptor1, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane", tile_descriptor1, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_reserved_1", tile_descriptor1, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_x_dim", tile_descriptor1, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_y_dim", tile_descriptor1, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_z_dim", tile_descriptor1, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_w_dim", tile_descriptor1, start, True)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo", tile_descriptor1, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi", tile_descriptor1, start)
        tile_descriptor1["blobs_y_start"] = (tile_descriptor1["blobs_y_start_hi"] << 16) | tile_descriptor1[
            "blobs_y_start_lo"
        ]
        del tile_descriptor1["blobs_y_start_lo"]
        del tile_descriptor1["blobs_y_start_hi"]
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_digest_type", tile_descriptor1, start)
        debug_tensix.get_config_field("UNPACK_TILE_DESCRIPTOR1_digest_size", tile_descriptor1, start)

        tile_descriptor = [tile_descriptor0, tile_descriptor1]
        return tile_descriptor

    def get_unpack_config(self, debug_tensix: TensixDebug) -> list[dict]:
        unpack_config0 = {}
        unpack_config1 = {}

        start = 15  # ignores field name prefix

        # REG_ID = 1
        debug_tensix.get_config_field("UNPACK_CONFIG0_out_data_format", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_throttle_mode", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_context_count", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_haloize_mode", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_tileize_mode", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_unpack_src_reg_set_upd", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_unpack_if_sel", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_upsample_rate", unpack_config0, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG0_reserved_1", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_upsample_and_interleave", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_shift_amount", unpack_config0, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG0_uncompress_cntx0_3", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_unpack_if_sel_cntx0_3", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_force_shared_exp", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_reserved_2", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_uncompress_cntx4_7", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_unpack_if_sel_cntx4_7", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_reserved_3", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_limit_addr", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_reserved_4", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_fifo_size", unpack_config0, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG0_reserved_5", unpack_config0, start)

        # REG_ID = 2
        debug_tensix.get_config_field("UNPACK_CONFIG1_out_data_format", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_throttle_mode", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_context_count", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_haloize_mode", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_tileize_mode", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_unpack_src_reg_set_upd", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_unpack_if_sel", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_upsample_rate", unpack_config1, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG1_reserved_1", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_upsample_and_interleave", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_shift_amount", unpack_config1, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG1_uncompress_cntx0_3", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_unpack_if_sel_cntx0_3", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_force_shared_exp", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_reserved_2", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_uncompress_cntx4_7", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_unpack_if_sel_cntx4_7", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_reserved_3", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_limit_addr", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_reserved_4", unpack_config1, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_fifo_size", unpack_config1, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG1_reserved_5", unpack_config1, start)

        unpack_config = [unpack_config0, unpack_config1]
        return unpack_config
