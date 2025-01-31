# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util
from ttlens import tt_device
from ttlens.tt_device import ConfigurationRegisterDescription, DebugRegisterDescription
from ttlens.tt_debug_tensix import TensixDebug


class GrayskullInstructions(tt_device.TensixInstructions):
    def __init__(self):
        import ttlens.tt_grayskull_ops as ops

        super().__init__(ops)


#
# Device
#
class GrayskullDevice(tt_device.Device):
    # Physical location mapping
    DIE_X_TO_NOC_0_X = [0, 12, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6]
    DIE_Y_TO_NOC_0_Y = [0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6]
    DIE_X_TO_NOC_1_X = [12, 0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6]
    DIE_Y_TO_NOC_1_Y = [11, 0, 10, 1, 9, 2, 8, 3, 7, 4, 6, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    PCI_ARC_RESET_BASE_ADDR = 0x1FF30000
    PCI_ARC_CSM_DATA_BASE_ADDR = 0x1FE80000
    PCI_ARC_ROM_DATA_BASE_ADDR = 0x1FF00000

    EFUSE_PCI = 0x1FF40200
    EFUSE_JTAG_AXI = 0x80040200
    EFUSE_NOC = 0x80040200

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )
        self.instructions = GrayskullInstructions()

    def get_tensix_configuration_register_base(self) -> int:
        return 0xFFEF0000

    __configuration_register_map = {
        # UNPACK TILE DESCRIPTOR SEC0
        "UNPACK_TILE_DESCRIPTOR0_in_data_format": ConfigurationRegisterDescription(index=48, mask=0xF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_uncompressed": ConfigurationRegisterDescription(index=48, mask=0x10, shift=4),
        "UNPACK_TILE_DESCRIPTOR0_reserved_0": ConfigurationRegisterDescription(index=48, mask=0xE0, shift=5),
        "UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane": ConfigurationRegisterDescription(index=48, mask=0xF00, shift=8),
        "UNPACK_TILE_DESCRIPTOR0_reserved_1": ConfigurationRegisterDescription(index=48, mask=0xF000, shift=12),
        "UNPACK_TILE_DESCRIPTOR0_x_dim": ConfigurationRegisterDescription(index=48, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_y_dim": ConfigurationRegisterDescription(index=49, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_z_dim": ConfigurationRegisterDescription(index=49, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_w_dim": ConfigurationRegisterDescription(index=50, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=50, mask=0xFFFF0000, shift=16
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi": ConfigurationRegisterDescription(index=51, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR0_digest_type": ConfigurationRegisterDescription(index=51, mask=0xFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR0_digest_size": ConfigurationRegisterDescription(index=51, mask=0xFF000000, shift=24),
        # UNPACK TILE DESCRIPTOR SEC1
        "UNPACK_TILE_DESCRIPTOR1_in_data_format": ConfigurationRegisterDescription(index=84, mask=0xF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_uncompressed": ConfigurationRegisterDescription(index=84, mask=0x10, shift=4),
        "UNPACK_TILE_DESCRIPTOR1_reserved_0": ConfigurationRegisterDescription(index=84, mask=0xE0, shift=5),
        "UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane": ConfigurationRegisterDescription(index=84, mask=0xF00, shift=8),
        "UNPACK_TILE_DESCRIPTOR1_reserved_1": ConfigurationRegisterDescription(index=84, mask=0xF000, shift=12),
        "UNPACK_TILE_DESCRIPTOR1_x_dim": ConfigurationRegisterDescription(index=84, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_y_dim": ConfigurationRegisterDescription(index=85, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_z_dim": ConfigurationRegisterDescription(index=85, mask=0xFFFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_w_dim": ConfigurationRegisterDescription(index=86, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=86, mask=0xFFFF0000, shift=16
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi": ConfigurationRegisterDescription(index=87, mask=0xFFFF, shift=0),
        "UNPACK_TILE_DESCRIPTOR1_digest_type": ConfigurationRegisterDescription(index=87, mask=0xFF0000, shift=16),
        "UNPACK_TILE_DESCRIPTOR1_digest_size": ConfigurationRegisterDescription(index=87, mask=0xFF000000, shift=24),
        # UNPACK CONFIG SEC0
        "UNPACK_CONFIG0_out_data_format": ConfigurationRegisterDescription(index=56, mask=0xF, shift=0),
        "UNPACK_CONFIG0_throttle_mode": ConfigurationRegisterDescription(index=56, mask=0x30, shift=4),
        "UNPACK_CONFIG0_context_count": ConfigurationRegisterDescription(index=56, mask=0xC0, shift=6),
        "UNPACK_CONFIG0_haloize_mode": ConfigurationRegisterDescription(index=56, mask=0x100, shift=8),
        "UNPACK_CONFIG0_tileize_mode": ConfigurationRegisterDescription(index=56, mask=0x200, shift=9),
        "UNPACK_CONFIG0_force_shared_exp": ConfigurationRegisterDescription(index=56, mask=0x400, shift=10),
        "UNPACK_CONFIG0_reserved_0": ConfigurationRegisterDescription(index=56, mask=0x800, shift=11),
        "UNPACK_CONFIG0_upsample_rate": ConfigurationRegisterDescription(index=56, mask=0x7000, shift=12),
        "UNPACK_CONFIG0_upsamle_and_interlave": ConfigurationRegisterDescription(index=56, mask=0x8000, shift=15),
        "UNPACK_CONFIG0_shift_amount": ConfigurationRegisterDescription(index=56, mask=0xFFFF0000, shift=16),
        "UNPACK_CONFIG0_uncompress_cntx0_3": ConfigurationRegisterDescription(index=57, mask=0xF, shift=0),
        "UNPACK_CONFIG0_reserved_1": ConfigurationRegisterDescription(index=57, mask=0xFFF0, shift=4),
        "UNPACK_CONFIG0_uncompress_cntx4_7": ConfigurationRegisterDescription(index=57, mask=0xF0000, shift=16),
        "UNPACK_CONFIG0_reserved_2": ConfigurationRegisterDescription(index=57, mask=0xFFF00000, shift=20),
        "UNPACK_CONFIG0_limit_addr": ConfigurationRegisterDescription(index=58, mask=0xFFFF, shift=0),
        "UNPACK_CONFIG0_fifo_size": ConfigurationRegisterDescription(index=58, mask=0xFFFF0000, shift=16),
        # UNPACK CONFIG SEC1
        "UNPACK_CONFIG1_out_data_format": ConfigurationRegisterDescription(index=90, mask=0xF, shift=0),
        "UNPACK_CONFIG1_throttle_mode": ConfigurationRegisterDescription(index=90, mask=0x30, shift=4),
        "UNPACK_CONFIG1_context_count": ConfigurationRegisterDescription(index=90, mask=0xC0, shift=6),
        "UNPACK_CONFIG1_haloize_mode": ConfigurationRegisterDescription(index=90, mask=0x100, shift=8),
        "UNPACK_CONFIG1_tileize_mode": ConfigurationRegisterDescription(index=90, mask=0x200, shift=9),
        "UNPACK_CONFIG1_force_shared_exp": ConfigurationRegisterDescription(index=90, mask=0x400, shift=10),
        "UNPACK_CONFIG1_reserved_0": ConfigurationRegisterDescription(index=90, mask=0x800, shift=11),
        "UNPACK_CONFIG1_upsample_rate": ConfigurationRegisterDescription(index=90, mask=0x7000, shift=12),
        "UNPACK_CONFIG1_upsamle_and_interlave": ConfigurationRegisterDescription(index=90, mask=0x8000, shift=15),
        "UNPACK_CONFIG1_shift_amount": ConfigurationRegisterDescription(index=90, mask=0xFFFF0000, shift=16),
        "UNPACK_CONFIG1_uncompress_cntx0_3": ConfigurationRegisterDescription(index=91, mask=0xF, shift=0),
        "UNPACK_CONFIG1_reserved_1": ConfigurationRegisterDescription(index=91, mask=0xFFF0, shift=4),
        "UNPACK_CONFIG1_uncompress_cntx4_7": ConfigurationRegisterDescription(index=91, mask=0xF0000, shift=16),
        "UNPACK_CONFIG1_reserved_2": ConfigurationRegisterDescription(index=91, mask=0xFFF00000, shift=20),
        "UNPACK_CONFIG1_limit_addr": ConfigurationRegisterDescription(index=92, mask=0xFFFF, shift=0),
        "UNPACK_CONFIG1_fifo_size": ConfigurationRegisterDescription(index=92, mask=0xFFFF0000, shift=16),
        # REST
        "DISABLE_RISC_BP_Disable_main": ConfigurationRegisterDescription(index=2, mask=0x100000, shift=20),
        "DISABLE_RISC_BP_Disable_trisc": ConfigurationRegisterDescription(index=2, mask=0xE00000, shift=21),
        "DISABLE_RISC_BP_Disable_ncrisc": ConfigurationRegisterDescription(index=2, mask=0x1000000, shift=24),
        "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=177, mask=0x1F),
        "TRISC_RESET_PC_SEC0_PC": ConfigurationRegisterDescription(index=178),
        "TRISC_RESET_PC_SEC1_PC": ConfigurationRegisterDescription(index=179),
        "TRISC_RESET_PC_SEC2_PC": ConfigurationRegisterDescription(index=180),
        "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=181, mask=0x7),
        "NCRISC_RESET_PC_PC": ConfigurationRegisterDescription(index=182),
        "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=183, mask=0x1),
    }

    def get_configuration_register_description(self, register_name: str) -> ConfigurationRegisterDescription:
        if register_name in GrayskullDevice.__configuration_register_map:
            return GrayskullDevice.__configuration_register_map[register_name]
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
    }

    def get_debug_register_description(self, register_name: str) -> DebugRegisterDescription:
        if register_name in GrayskullDevice.__debug_register_map:
            return GrayskullDevice.__debug_register_map[register_name]
        return None

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
        debug_tensix.get_config_field("UNPACK_CONFIG0_force_shared_exp", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_reserved_0", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_upsample_rate", unpack_config0, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG0_upsample_and_interleave", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_shift_amount", unpack_config0, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG0_uncompress_cntx0_3", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_reserved_1", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_uncompress_cntx4_7", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_reserved_2", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_limit_addr", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG0_fifo_size", unpack_config0, start)

        # REG_ID = 2
        debug_tensix.get_config_field("UNPACK_CONFIG1_out_data_format", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_throttle_mode", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_context_count", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_haloize_mode", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_tileize_mode", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_force_shared_exp", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_reserved_0", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_upsample_rate", unpack_config0, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG1_upsample_and_interleave", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_shift_amount", unpack_config0, start, True)
        debug_tensix.get_config_field("UNPACK_CONFIG1_uncompress_cntx0_3", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_reserved_1", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_uncompress_cntx4_7", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_reserved_2", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_limit_addr", unpack_config0, start)
        debug_tensix.get_config_field("UNPACK_CONFIG1_fifo_size", unpack_config0, start)

        unpack_config = [unpack_config0, unpack_config1]
        return unpack_config
