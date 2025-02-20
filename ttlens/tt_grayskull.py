# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util
from ttlens import tt_device
from ttlens.tt_device import ConfigurationRegisterDescription, DebugRegisterDescription
from ttlens.tt_debug_tensix import TensixDebug, ValueType


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
        # PACK CONFIG SEC 0 REG 1
        "PACK_CONFIG01_row_ptr_section_size": ConfigurationRegisterDescription(index=52, mask=0xFFFF, shift=0),
        "PACK_CONFIG01_exp_section_size": ConfigurationRegisterDescription(index=52, mask=0xFFFF0000, shift=16),
        "PACK_CONFIG01_l1_dest_addr": ConfigurationRegisterDescription(index=53, mask=0xFFFFFFFF, shift=0),
        "PACK_CONFIG01_uncompress": ConfigurationRegisterDescription(index=54, mask=0x1, shift=0),
        "PACK_CONFIG01_add_l1_dest_addr_offset": ConfigurationRegisterDescription(index=54, mask=0x2, shift=1),
        "PACK_CONFIG01_reserved_0": ConfigurationRegisterDescription(index=54, mask=0xC, shift=2),
        "PACK_CONFIG01_out_data_format": ConfigurationRegisterDescription(index=54, mask=0xF0, shift=4),
        "PACK_CONFIG01_in_data_format": ConfigurationRegisterDescription(index=54, mask=0xF00, shift=8),
        "PACK_CONFIG01_reserved_1": ConfigurationRegisterDescription(index=54, mask=0xF000, shift=12),
        "PACK_CONFIG01_src_if_sel": ConfigurationRegisterDescription(index=54, mask=0x10000, shift=16),
        "PACK_CONFIG01_pack_per_xy_plane": ConfigurationRegisterDescription(index=54, mask=0xFE0000, shift=17),
        "PACK_CONFIG01_l1_src_addr": ConfigurationRegisterDescription(index=54, mask=0xFF000000, shift=24),
        "PACK_CONFIG01_downsample_mask": ConfigurationRegisterDescription(index=55, mask=0xFFFF, shift=0),
        "PACK_CONFIG01_downsample_shift_count": ConfigurationRegisterDescription(index=55, mask=0x70000, shift=16),
        "PACK_CONFIG01_read_mode": ConfigurationRegisterDescription(index=55, mask=0x80000, shift=19),
        "PACK_CONFIG01_exp_threshold_en": ConfigurationRegisterDescription(index=55, mask=0x100000, shift=20),
        "PACK_CONFIG01_reserved_2": ConfigurationRegisterDescription(index=55, mask=0xE00000, shift=21),
        "PACK_CONFIG01_exp_threshold": ConfigurationRegisterDescription(index=55, mask=0xFF000000, shift=24),
        # PACK CONFIG SEC 0 REG 8
        "PACK_CONFIG08_row_ptr_section_size": ConfigurationRegisterDescription(index=80, mask=0xFFFF, shift=0),
        "PACK_CONFIG08_exp_section_size": ConfigurationRegisterDescription(index=80, mask=0xFFFF0000, shift=16),
        "PACK_CONFIG08_l1_dest_addr": ConfigurationRegisterDescription(index=81, mask=0xFFFFFFFF, shift=0),
        "PACK_CONFIG08_uncompress": ConfigurationRegisterDescription(index=82, mask=0x1, shift=0),
        "PACK_CONFIG08_add_l1_dest_addr_offset": ConfigurationRegisterDescription(index=82, mask=0x2, shift=1),
        "PACK_CONFIG08_reserved_0": ConfigurationRegisterDescription(index=82, mask=0xC, shift=2),
        "PACK_CONFIG08_out_data_format": ConfigurationRegisterDescription(index=82, mask=0xF0, shift=4),
        "PACK_CONFIG08_in_data_format": ConfigurationRegisterDescription(index=82, mask=0xF00, shift=8),
        "PACK_CONFIG08_reserved_1": ConfigurationRegisterDescription(index=82, mask=0xF000, shift=12),
        "PACK_CONFIG08_src_if_sel": ConfigurationRegisterDescription(index=82, mask=0x10000, shift=16),
        "PACK_CONFIG08_pack_per_xy_plane": ConfigurationRegisterDescription(index=82, mask=0xFE0000, shift=17),
        "PACK_CONFIG08_l1_src_addr": ConfigurationRegisterDescription(index=82, mask=0xFF000000, shift=24),
        "PACK_CONFIG08_downsample_mask": ConfigurationRegisterDescription(index=83, mask=0xFFFF, shift=0),
        "PACK_CONFIG08_downsample_shift_count": ConfigurationRegisterDescription(index=83, mask=0x70000, shift=16),
        "PACK_CONFIG08_read_mode": ConfigurationRegisterDescription(index=83, mask=0x80000, shift=19),
        "PACK_CONFIG08_exp_threshold_en": ConfigurationRegisterDescription(index=83, mask=0x100000, shift=20),
        "PACK_CONFIG08_reserved_2": ConfigurationRegisterDescription(index=83, mask=0xE00000, shift=21),
        "PACK_CONFIG08_exp_threshold": ConfigurationRegisterDescription(index=83, mask=0xFF000000, shift=24),
        # PACK CONFIG SEC 1 REG 1
        "PACK_CONFIG11_row_ptr_section_size": ConfigurationRegisterDescription(index=88, mask=0xFFFF, shift=0),
        "PACK_CONFIG11_exp_section_size": ConfigurationRegisterDescription(index=88, mask=0xFFFF0000, shift=16),
        "PACK_CONFIG11_l1_dest_addr": ConfigurationRegisterDescription(index=89, mask=0xFFFFFFFF, shift=0),
        "PACK_CONFIG11_uncompress": ConfigurationRegisterDescription(index=90, mask=0x1, shift=0),
        "PACK_CONFIG11_add_l1_dest_addr_offset": ConfigurationRegisterDescription(index=90, mask=0x2, shift=1),
        "PACK_CONFIG11_reserved_0": ConfigurationRegisterDescription(index=90, mask=0xC, shift=2),
        "PACK_CONFIG11_out_data_format": ConfigurationRegisterDescription(index=90, mask=0xF0, shift=4),
        "PACK_CONFIG11_in_data_format": ConfigurationRegisterDescription(index=90, mask=0xF00, shift=8),
        "PACK_CONFIG11_reserved_1": ConfigurationRegisterDescription(index=90, mask=0xF000, shift=12),
        "PACK_CONFIG11_src_if_sel": ConfigurationRegisterDescription(index=90, mask=0x10000, shift=16),
        "PACK_CONFIG11_pack_per_xy_plane": ConfigurationRegisterDescription(index=90, mask=0xFE0000, shift=17),
        "PACK_CONFIG11_l1_src_addr": ConfigurationRegisterDescription(index=90, mask=0xFF000000, shift=24),
        "PACK_CONFIG11_downsample_mask": ConfigurationRegisterDescription(index=91, mask=0xFFFF, shift=0),
        "PACK_CONFIG11_downsample_shift_count": ConfigurationRegisterDescription(index=91, mask=0x70000, shift=16),
        "PACK_CONFIG11_read_mode": ConfigurationRegisterDescription(index=91, mask=0x80000, shift=19),
        "PACK_CONFIG11_exp_threshold_en": ConfigurationRegisterDescription(index=91, mask=0x100000, shift=20),
        "PACK_CONFIG11_reserved_2": ConfigurationRegisterDescription(index=91, mask=0xE00000, shift=21),
        "PACK_CONFIG11_exp_threshold": ConfigurationRegisterDescription(index=91, mask=0xFF000000, shift=24),
        # PACK CONFIG SEC 1 REG 8
        "PACK_CONFIG18_row_ptr_section_size": ConfigurationRegisterDescription(index=116, mask=0xFFFF, shift=0),
        "PACK_CONFIG18_exp_section_size": ConfigurationRegisterDescription(index=116, mask=0xFFFF0000, shift=16),
        "PACK_CONFIG18_l1_dest_addr": ConfigurationRegisterDescription(index=117, mask=0xFFFFFFFF, shift=0),
        "PACK_CONFIG18_uncompress": ConfigurationRegisterDescription(index=118, mask=0x1, shift=0),
        "PACK_CONFIG18_add_l1_dest_addr_offset": ConfigurationRegisterDescription(index=118, mask=0x2, shift=1),
        "PACK_CONFIG18_reserved_0": ConfigurationRegisterDescription(index=118, mask=0xC, shift=2),
        "PACK_CONFIG18_out_data_format": ConfigurationRegisterDescription(index=118, mask=0xF0, shift=4),
        "PACK_CONFIG18_in_data_format": ConfigurationRegisterDescription(index=118, mask=0xF00, shift=8),
        "PACK_CONFIG18_reserved_1": ConfigurationRegisterDescription(index=118, mask=0xF000, shift=12),
        "PACK_CONFIG18_src_if_sel": ConfigurationRegisterDescription(index=118, mask=0x10000, shift=16),
        "PACK_CONFIG18_pack_per_xy_plane": ConfigurationRegisterDescription(index=118, mask=0xFE0000, shift=17),
        "PACK_CONFIG18_l1_src_addr": ConfigurationRegisterDescription(index=118, mask=0xFF000000, shift=24),
        "PACK_CONFIG18_downsample_mask": ConfigurationRegisterDescription(index=119, mask=0xFFFF, shift=0),
        "PACK_CONFIG18_downsample_shift_count": ConfigurationRegisterDescription(index=119, mask=0x70000, shift=16),
        "PACK_CONFIG18_read_mode": ConfigurationRegisterDescription(index=119, mask=0x80000, shift=19),
        "PACK_CONFIG18_exp_threshold_en": ConfigurationRegisterDescription(index=119, mask=0x100000, shift=20),
        "PACK_CONFIG18_reserved_2": ConfigurationRegisterDescription(index=119, mask=0xE00000, shift=21),
        "PACK_CONFIG18_exp_threshold": ConfigurationRegisterDescription(index=119, mask=0xFF000000, shift=24),
        # EDGE OFFSET SEC 0
        "PACK_EDGE_OFFSET0_mask": ConfigurationRegisterDescription(index=20, mask=0xffff, shift=0),
        "PACK_EDGE_OFFSET0_mode": ConfigurationRegisterDescription(index=20, mask=0x10000, shift=16),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack0": ConfigurationRegisterDescription(index=20, mask=0x60000, shift=17),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack1": ConfigurationRegisterDescription(index=20, mask=0x180000, shift=19),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack2": ConfigurationRegisterDescription(index=20, mask=0x600000, shift=21),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack3": ConfigurationRegisterDescription(index=20, mask=0x1800000, shift=23),
        "PACK_EDGE_OFFSET0_reserved": ConfigurationRegisterDescription(index=20,mask=0xfe000000, shift=25),
        # EDGE OFFSET SEC 1
        "PACK_EDGE_OFFSET1_mask": ConfigurationRegisterDescription(index=21, mask=0xffff, shift=0),
        # EDGE OFFSET SEC 2
        "PACK_EDGE_OFFSET2_mask": ConfigurationRegisterDescription(index=22, mask=0xffff, shift=0),
        # EDGE OFFSET SEC 3
        "PACK_EDGE_OFFSET3_mask": ConfigurationRegisterDescription(index=23, mask=0xffff, shift=0),
        # PACK COUNTERS SEC 0
        "PACK_COUNTERS0_pack_per_xy_plane": ConfigurationRegisterDescription(index=24, mask=0xff, shift=0),
        "PACK_COUNTERS0_pack_reads_per_xy_plane": ConfigurationRegisterDescription(index=24, mask=0xff00, shift=8),
        "PACK_COUNTERS0_pack_xys_per_til": ConfigurationRegisterDescription(index=24, mask=0x7f0000, shift=16),
        "PACK_COUNTERS0_pack_yz_transposed": ConfigurationRegisterDescription(index=24, mask=800000, shift=23),
        "PACK_COUNTERS0_pack_per_xy_plane_offset": ConfigurationRegisterDescription(index=24, mask=0xff000000, shift=24),
        # PACK COUNTERS SEC 1
        "PACK_COUNTERS1_pack_per_xy_plane": ConfigurationRegisterDescription(index=25, mask=0xff, shift=0),
        "PACK_COUNTERS1_pack_reads_per_xy_plane": ConfigurationRegisterDescription(index=25, mask=0xff00, shift=8),
        "PACK_COUNTERS1_pack_xys_per_til": ConfigurationRegisterDescription(index=25, mask=0x7f0000, shift=16),
        "PACK_COUNTERS1_pack_yz_transposed": ConfigurationRegisterDescription(index=25, mask=800000, shift=23),
        "PACK_COUNTERS1_pack_per_xy_plane_offset": ConfigurationRegisterDescription(index=25, mask=0xff000000, shift=24), 
        # PACK COUNTERS SEC 2
        "PACK_COUNTERS2_pack_per_xy_plane": ConfigurationRegisterDescription(index=26, mask=0xff, shift=0),
        "PACK_COUNTERS2_pack_reads_per_xy_plane": ConfigurationRegisterDescription(index=26, mask=0xff00, shift=8),
        "PACK_COUNTERS2_pack_xys_per_til": ConfigurationRegisterDescription(index=26, mask=0x7f0000, shift=16),
        "PACK_COUNTERS2_pack_yz_transposed": ConfigurationRegisterDescription(index=26, mask=800000, shift=23),
        "PACK_COUNTERS2_pack_per_xy_plane_offset": ConfigurationRegisterDescription(index=26, mask=0xff000000, shift=24),
        # PACK COUNTERS SEC 3
        "PACK_COUNTERS3_pack_per_xy_plane": ConfigurationRegisterDescription(index=27, mask=0xff, shift=0),
        "PACK_COUNTERS3_pack_reads_per_xy_plane": ConfigurationRegisterDescription(index=27, mask=0xff00, shift=8),
        "PACK_COUNTERS3_pack_xys_per_til": ConfigurationRegisterDescription(index=27, mask=0x7f0000, shift=16),
        "PACK_COUNTERS3_pack_yz_transposed": ConfigurationRegisterDescription(index=27, mask=800000, shift=23),
        "PACK_COUNTERS3_pack_per_xy_plane_offset": ConfigurationRegisterDescription(index=27, mask=0xff000000, shift=24),
        # PACK STRIDES REG 0
        "PACK_STRIDES0_x_stride": ConfigurationRegisterDescription(index=8, mask=0xfff, shift=0),
        "PACK_STRIDES0_y_stride": ConfigurationRegisterDescription(index=8, mask=0xfff000, shift=12),
        "PACK_STRIDES0_z_stride": ConfigurationRegisterDescription(index=9, mask=0xfff, shift=0),
        "PACK_STRIDES0_w_stride": ConfigurationRegisterDescription(index=9, mask=0xffff000, shift=12),
        # PACK STRIDES REG 1
        "PACK_STRIDES1_x_stride": ConfigurationRegisterDescription(index=10, mask=0xfff, shift=0),
        "PACK_STRIDES1_y_stride": ConfigurationRegisterDescription(index=10, mask=0xfff000, shift=12),
        "PACK_STRIDES1_z_stride": ConfigurationRegisterDescription(index=11, mask=0xfff, shift=0),
        "PACK_STRIDES1_w_stride": ConfigurationRegisterDescription(index=11, mask=0xffff000, shift=12),  
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
        struct_name = "UNPACK_TILE_DESCRIPTOR"
        
        tile_descriptor_list = []

        start = 24  # ignores field name prefix

        for i in range(self.NUM_UNPACKERS):
            tile_descriptor = {}

            register_name = struct_name + str(i)

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

        start = 15  # ignores field name prefix

        for i in range(self.NUM_UNPACKERS):
            unpack_config = {}

            register_name = struct_name + str(i)

            debug_tensix.get_config_field(register_name + "_out_data_format", unpack_config, ValueType.FORMAT, start)
            debug_tensix.get_config_field(register_name + "_throttle_mode", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_context_count", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_haloize_mode", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_tileize_mode", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_force_shared_exp", unpack_config, ValueType.BOOL, start)
            debug_tensix.get_config_field(register_name + "_reserved_0", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_upsample_rate", unpack_config, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_upsample_and_interleave", unpack_config, ValueType.BOOL, start)
            debug_tensix.get_config_field(register_name + "_shift_amount", unpack_config, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_uncompress_cntx0_3", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_reserved_1", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_uncompress_cntx4_7", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_reserved_2", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_limit_addr", unpack_config, ValueType.HEX, start)
            debug_tensix.get_config_field(register_name + "_fifo_size", unpack_config, ValueType.HEX, start)

            unpack_config_list.append(unpack_config)

        return unpack_config_list
    
    def get_pack_config(self, debug_tensix: TensixDebug) -> list[dict]:
        struct_name = "PACK_CONFIG"

        pack_config_list = []

        start = 14 # ignores field name prefix

        for i in [0,1]:
            for j in [1,8]:
                pack_config = {}

                register_name = struct_name + str(i) + str(j)

                debug_tensix.get_config_field(register_name + "_row_ptr_section_size", pack_config, ValueType.DEC, start, True)
                debug_tensix.get_config_field(register_name + "_exp_section_size", pack_config, ValueType.DEC, start)
                debug_tensix.get_config_field(register_name + "_l1_dest_addr", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_uncompress", pack_config, ValueType.BOOL, start)
                debug_tensix.get_config_field(register_name + "_add_l1_dest_addr_offset", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_reserved_0", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_out_data_format", pack_config, ValueType.FORMAT, start)
                debug_tensix.get_config_field(register_name + "_in_data_format", pack_config, ValueType.FORMAT, start)
                debug_tensix.get_config_field(register_name + "_reserved_1", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_src_if_sel", pack_config, ValueType.BOOL, start)
                debug_tensix.get_config_field(register_name + "_pack_per_xy_plane", pack_config, ValueType.DEC, start)
                debug_tensix.get_config_field(register_name + "_l1_src_addr", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_downsample_mask", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_downsample_shift_count", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_read_mode", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_exp_threshold_en", pack_config, ValueType.BOOL, start)
                debug_tensix.get_config_field(register_name + "_reserved_2", pack_config, ValueType.HEX, start)
                debug_tensix.get_config_field(register_name + "_exp_threshold", pack_config, ValueType.DEC, start)

                pack_config_list.append(pack_config)

        return pack_config_list
    
    def get_pack_edge_offset(self, debug_tensix: TensixDebug) -> list[dict]:
        struct_name = "PACK_EDGE_OFFSET"

        edge_list = []

        start = 18

        for i in range(self.NUM_PACKERS):
            edge = {}

            register_name = struct_name + str(i)

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

        start = 15

        for i in range(self.NUM_PACKERS):
            counters = {}

            register_name = struct_name + str(i)

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

        start = 14

        for i in range(2):
            strides = {}
            
            register_name = struct_name + str(i)

            debug_tensix.get_config_field(register_name + "_x_stride", strides, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_y_stride", strides, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_z_stride", strides, ValueType.DEC, start)
            debug_tensix.get_config_field(register_name + "_w_stride", strides, ValueType.DEC, start)
        
            strides_list.append(strides)
        
        return strides_list