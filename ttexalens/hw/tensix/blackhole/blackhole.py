# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from functools import cache
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.blackhole.arc_block import BlackholeArcBlock
from ttexalens.hardware.blackhole.dram_block import BlackholeDramBlock
from ttexalens.hardware.blackhole.eth_block import BlackholeEthBlock
from ttexalens.hardware.blackhole.functional_worker_block import BlackholeFunctionalWorkerBlock
from ttexalens.hardware.blackhole.harvested_worker_block import BlackholeHarvestedWorkerBlock
from ttexalens.hardware.blackhole.l2cpu_block import BlackholeL2cpuBlock
from ttexalens.hardware.blackhole.pcie_block import BlackholePcieBlock
from ttexalens.hardware.blackhole.router_only_block import BlackholeRouterOnlyBlock
from ttexalens.hardware.blackhole.security_block import BlackholeSecurityBlock
import ttexalens.util as util
from ttexalens.debug_tensix import TensixDebug
from ttexalens.util import DATA_TYPE
from typing import List
from ttexalens.device import (
    TensixInstructions,
    Device,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    TensixRegisterDescription,
    NocStatusRegisterDescription,
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
)
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore


class BlackholeInstructions(TensixInstructions):
    def __init__(self):
        import ttexalens.hw.tensix.blackhole.blackhole_ops as ops

        super().__init__(ops)


#
# Device
#
class BlackholeDevice(Device):
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
    NOC_REGISTER_OFFSET = 0x10000

    # Register base addresses
    CONFIGURATION_REGISTER_BASE = 0xFFEF0000
    DEBUG_REGISTER_BASE = 0xFFB12000
    NOC_CONTROL_REGISTER_BASE = 0xFFB20000
    NOC_CONFIGURATION_REGISTER_BASE = 0xFFB20100
    NOC_STATUS_REGISTER_BASE = 0xFFB20200

    CONFIGURATION_REGISTER_END = 0xFFEFFFFF

    # RISC LOCAL MEMORY
    RISC_LOCAL_MEM_BASE = 0xFFB00000
    BRISC_LOCAL_MEM_SIZE = 8 * 1024  # 8KB
    NCRISC_LOCAL_MEM_SIZE = 8 * 1024  # 8KB
    TRISC_LOCAL_MEM_SIZE = 4 * 1024  # 4KB

    NUM_UNPACKERS = 2
    NUM_PACKERS = 1

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )
        self.instructions = BlackholeInstructions()

    def _get_tensix_register_map_keys(self) -> List[str]:
        return list(BlackholeDevice.__register_map.keys())

    def _get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription | None:
        """Overrides the base class method to provide register descriptions for Blackhole device."""
        if register_name in BlackholeDevice.__register_map:
            return BlackholeDevice.__register_map[register_name]
        else:
            return None

    def _get_tensix_register_base_address(self, register_description: TensixRegisterDescription) -> int | None:
        """Overrides the base class method to provide register base addresses for Blackhole device."""
        if isinstance(register_description, ConfigurationRegisterDescription):
            return BlackholeDevice.CONFIGURATION_REGISTER_BASE
        elif isinstance(register_description, DebugRegisterDescription):
            return BlackholeDevice.DEBUG_REGISTER_BASE
        elif isinstance(register_description, NocControlRegisterDescription):
            return BlackholeDevice.NOC_CONTROL_REGISTER_BASE
        elif isinstance(register_description, NocConfigurationRegisterDescription):
            return BlackholeDevice.NOC_CONFIGURATION_REGISTER_BASE
        elif isinstance(register_description, NocStatusRegisterDescription):
            return BlackholeDevice.NOC_STATUS_REGISTER_BASE
        else:
            return None

    def _get_tensix_register_end_address(self, register_description: TensixRegisterDescription) -> int | None:
        """Overrides the base class method to provide register end addresses for Wormhole device."""
        if isinstance(register_description, ConfigurationRegisterDescription):
            return BlackholeDevice.CONFIGURATION_REGISTER_END
        else:
            return None

    def _get_riscv_local_memory_base_address(self) -> int:
        return BlackholeDevice.RISC_LOCAL_MEM_BASE

    def _get_riscv_local_memory_size(self, risc_id):
        if risc_id == 0:
            return BlackholeDevice.BRISC_LOCAL_MEM_SIZE
        elif 1 <= risc_id <= 3:
            return BlackholeDevice.TRISC_LOCAL_MEM_SIZE
        elif risc_id == 4:
            return BlackholeDevice.NCRISC_LOCAL_MEM_SIZE
        else:
            return None

    __register_map = {
        # UNPACK TILE DESCRIPTOR SEC0
        "UNPACK_TILE_DESCRIPTOR0_in_data_format": ConfigurationRegisterDescription(
            index=64, mask=0xF, shift=0, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "UNPACK_TILE_DESCRIPTOR0_uncompressed": ConfigurationRegisterDescription(
            index=64, mask=0x10, shift=4, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_TILE_DESCRIPTOR0_reserved_0": ConfigurationRegisterDescription(
            index=64, mask=0xE0, shift=5, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane": ConfigurationRegisterDescription(
            index=64, mask=0xF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_reserved_1": ConfigurationRegisterDescription(
            index=64, mask=0xF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_x_dim": ConfigurationRegisterDescription(
            index=64, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_y_dim": ConfigurationRegisterDescription(
            index=65, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_z_dim": ConfigurationRegisterDescription(
            index=65, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_w_dim": ConfigurationRegisterDescription(
            index=66, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=66, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi": ConfigurationRegisterDescription(
            index=67, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_digest_type": ConfigurationRegisterDescription(
            index=67, mask=0xFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_digest_size": ConfigurationRegisterDescription(
            index=67, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # UNPACK TILE DESCRIPTOR SEC1
        "UNPACK_TILE_DESCRIPTOR1_in_data_format": ConfigurationRegisterDescription(
            index=112, mask=0xF, shift=0, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "UNPACK_TILE_DESCRIPTOR1_uncompressed": ConfigurationRegisterDescription(
            index=112, mask=0x10, shift=4, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_TILE_DESCRIPTOR1_reserved_0": ConfigurationRegisterDescription(
            index=112, mask=0xE0, shift=5, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane": ConfigurationRegisterDescription(
            index=112, mask=0xF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_reserved_1": ConfigurationRegisterDescription(
            index=112, mask=0xF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_x_dim": ConfigurationRegisterDescription(
            index=112, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_y_dim": ConfigurationRegisterDescription(
            index=113, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_z_dim": ConfigurationRegisterDescription(
            index=113, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_w_dim": ConfigurationRegisterDescription(
            index=114, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=114, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi": ConfigurationRegisterDescription(
            index=115, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_digest_type": ConfigurationRegisterDescription(
            index=115, mask=0xFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_digest_size": ConfigurationRegisterDescription(
            index=115, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # UNPACK CONFIG SEC 0
        "UNPACK_CONFIG0_out_data_format": ConfigurationRegisterDescription(
            index=72, mask=0xF, shift=0, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "UNPACK_CONFIG0_throttle_mode": ConfigurationRegisterDescription(
            index=72, mask=0x30, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_context_count": ConfigurationRegisterDescription(
            index=72, mask=0xC0, shift=6, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_haloize_mode": ConfigurationRegisterDescription(
            index=72, mask=0x100, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_tileize_mode": ConfigurationRegisterDescription(
            index=72, mask=0x200, shift=9, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_unpack_src_reg_set_upd": ConfigurationRegisterDescription(
            index=72, mask=0x400, shift=10, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG0_unpack_if_sel": ConfigurationRegisterDescription(
            index=72, mask=0x800, shift=11, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG0_upsample_rate": ConfigurationRegisterDescription(
            index=72, mask=0x3000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_reserved_1": ConfigurationRegisterDescription(
            index=72, mask=0x4000, shift=14, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_upsample_and_interleave": ConfigurationRegisterDescription(
            index=72, mask=0x8000, shift=15, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG0_shift_amount": ConfigurationRegisterDescription(
            index=72, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_uncompress_cntx0_3": ConfigurationRegisterDescription(
            index=73, mask=0xF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(
            index=73, mask=0xF0, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_force_shared_exp": ConfigurationRegisterDescription(
            index=73, mask=0x100, shift=8, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG0_reserved_2": ConfigurationRegisterDescription(
            index=73, mask=0xFE00, shift=9, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_uncompress_cntx4_7": ConfigurationRegisterDescription(
            index=73, mask=0xF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(
            index=73, mask=0xF00000, shift=20, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_reserved_3": ConfigurationRegisterDescription(
            index=73, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_limit_addr": ConfigurationRegisterDescription(
            index=74, mask=0x1FFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "UNPACK_CONFIG0_reserved_4": ConfigurationRegisterDescription(
            index=74, mask=0xFFFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_fifo_size": ConfigurationRegisterDescription(
            index=75, mask=0x1FFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_reserved_5": ConfigurationRegisterDescription(
            index=75, mask=0xFFFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        # UNPACK CONFIG SEC 1
        "UNPACK_CONFIG1_out_data_format": ConfigurationRegisterDescription(
            index=120, mask=0xF, shift=0, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "UNPACK_CONFIG1_throttle_mode": ConfigurationRegisterDescription(
            index=120, mask=0x30, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_context_count": ConfigurationRegisterDescription(
            index=120, mask=0xC0, shift=6, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_haloize_mode": ConfigurationRegisterDescription(
            index=120, mask=0x100, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_tileize_mode": ConfigurationRegisterDescription(
            index=120, mask=0x200, shift=9, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_unpack_src_reg_set_upd": ConfigurationRegisterDescription(
            index=120, mask=0x400, shift=10, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG1_unpack_if_sel": ConfigurationRegisterDescription(
            index=120, mask=0x800, shift=11, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG1_upsample_rate": ConfigurationRegisterDescription(
            index=120, mask=0x3000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_reserved_1": ConfigurationRegisterDescription(
            index=120, mask=0x4000, shift=14, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_upsample_and_interleave": ConfigurationRegisterDescription(
            index=120, mask=0x8000, shift=15, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG1_shift_amount": ConfigurationRegisterDescription(
            index=120, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_uncompress_cntx0_3": ConfigurationRegisterDescription(
            index=121, mask=0xF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(
            index=121, mask=0xF0, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_force_shared_exp": ConfigurationRegisterDescription(
            index=121, mask=0x100, shift=8, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG1_reserved_2": ConfigurationRegisterDescription(
            index=121, mask=0xFE00, shift=9, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_uncompress_cntx4_7": ConfigurationRegisterDescription(
            index=121, mask=0xF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(
            index=121, mask=0xF00000, shift=20, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_reserved_3": ConfigurationRegisterDescription(
            index=121, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_limit_addr": ConfigurationRegisterDescription(
            index=122, mask=0x1FFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "UNPACK_CONFIG1_reserved_4": ConfigurationRegisterDescription(
            index=122, mask=0xFFFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_fifo_size": ConfigurationRegisterDescription(
            index=123, mask=0x1FFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_reserved_5": ConfigurationRegisterDescription(
            index=123, mask=0xFFFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        # ALU CONFIG
        "ALU_ROUNDING_MODE_Fpu_srnd_en": ConfigurationRegisterDescription(
            index=1, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_ROUNDING_MODE_Gasket_srnd_en": ConfigurationRegisterDescription(
            index=1, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_ROUNDING_MODE_Packer_srnd_en": ConfigurationRegisterDescription(
            index=1, mask=0x4, shift=2, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_ROUNDING_MODE_Padding": ConfigurationRegisterDescription(
            index=1, mask=0x1FF8, shift=3, data_type=DATA_TYPE.INT_VALUE
        ),
        "ALU_ROUNDING_MODE_GS_LF": ConfigurationRegisterDescription(
            index=1, mask=0x2000, shift=13, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_ROUNDING_MODE_Bfp8_HF": ConfigurationRegisterDescription(
            index=1, mask=0x4000, shift=14, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_FORMAT_SPEC_REG0_SrcAUnsigned": ConfigurationRegisterDescription(
            index=1, mask=0x8000, shift=15, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_FORMAT_SPEC_REG0_SrcBUnsigned": ConfigurationRegisterDescription(
            index=1, mask=0x10000, shift=16, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_FORMAT_SPEC_REG0_SrcA": ConfigurationRegisterDescription(
            index=1, mask=0x1E0000, shift=17, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "ALU_FORMAT_SPEC_REG1_SrcB": ConfigurationRegisterDescription(
            index=1, mask=0x1E00000, shift=21, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "ALU_FORMAT_SPEC_REG2_Dstacc": ConfigurationRegisterDescription(
            index=1, mask=0x1E000000, shift=25, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "ALU_ACC_CTRL_Fp32_enabled": ConfigurationRegisterDescription(
            index=1, mask=0x20000000, shift=29, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_ACC_CTRL_SFPU_Fp32_enabled": ConfigurationRegisterDescription(
            index=1, mask=0x40000000, shift=30, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_ACC_CTRL_INT8_math_enabled": ConfigurationRegisterDescription(
            index=1, mask=0x80000000, shift=31, data_type=DATA_TYPE.FLAGS
        ),
        # PACK CONFIG SEC 0 REG 1
        "PACK_CONFIG01_row_ptr_section_size": ConfigurationRegisterDescription(
            index=68, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_exp_section_size": ConfigurationRegisterDescription(
            index=68, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_l1_dest_addr": ConfigurationRegisterDescription(
            index=69, mask=0xFFFFFFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG01_uncompress": ConfigurationRegisterDescription(
            index=70, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
            index=70, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=70, mask=0x4, shift=2, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_reserved_0": ConfigurationRegisterDescription(
            index=70, mask=0x8, shift=3, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_out_data_format": ConfigurationRegisterDescription(
            index=70, mask=0xF0, shift=4, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG01_in_data_format": ConfigurationRegisterDescription(
            index=70, mask=0xF00, shift=8, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG01_dis_shared_exp_assembler": ConfigurationRegisterDescription(
            index=70, mask=0x1000, shift=12, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_auto_set_last_pacr_intf_sel": ConfigurationRegisterDescription(
            index=70, mask=0x2000, shift=13, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_enable_out_fifo": ConfigurationRegisterDescription(
            index=70, mask=0x4000, shift=14, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_sub_l1_tile_header_size": ConfigurationRegisterDescription(
            index=70, mask=0x8000, shift=15, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_src_if_sel": ConfigurationRegisterDescription(
            index=70, mask=0x10000, shift=16, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_pack_start_intf_pos": ConfigurationRegisterDescription(
            index=70, mask=0x1E0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_all_pack_disable_zero_compress_ovrd": ConfigurationRegisterDescription(
            index=70, mask=0x200000, shift=21, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_add_tile_header_size": ConfigurationRegisterDescription(
            index=70, mask=0x400000, shift=22, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_pack_dis_y_pos_start_offset": ConfigurationRegisterDescription(
            index=70, mask=0x800000, shift=23, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_l1_src_addr": ConfigurationRegisterDescription(
            index=70, mask=0xFF000000, shift=24, data_type=DATA_TYPE.ADDRESS
        ),
        # RELU CONFIG
        "ALU_ACC_CTRL_Zero_Flag_disabled_src": ConfigurationRegisterDescription(
            index=2, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "ALU_ACC_CTRL_Zero_Flag_disabled_dst": ConfigurationRegisterDescription(
            index=2, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "STACC_RELU_ApplyRelu": ConfigurationRegisterDescription(
            index=2, mask=0x3C, shift=2, data_type=DATA_TYPE.INT_VALUE
        ),
        "STACC_RELU_ReluThreshold": ConfigurationRegisterDescription(
            index=2, mask=0x3FFFC0, shift=6, data_type=DATA_TYPE.INT_VALUE
        ),
        "DISABLE_RISC_BP_Disable_main": ConfigurationRegisterDescription(
            index=2, mask=0x400000, shift=22, data_type=DATA_TYPE.FLAGS
        ),
        "DISABLE_RISC_BP_Disable_trisc": ConfigurationRegisterDescription(
            index=2, mask=0x3800000, shift=23, data_type=DATA_TYPE.FLAGS
        ),
        "DISABLE_RISC_BP_Disable_ncrisc": ConfigurationRegisterDescription(
            index=2, mask=0x4000000, shift=26, data_type=DATA_TYPE.FLAGS
        ),
        "DISABLE_RISC_BP_Disable_bmp_clear_main": ConfigurationRegisterDescription(
            index=2, mask=0x8000000, shift=27, data_type=DATA_TYPE.FLAGS
        ),
        "DISABLE_RISC_BP_Disable_bmp_clear_trisc": ConfigurationRegisterDescription(
            index=2, mask=0x70000000, shift=28, data_type=DATA_TYPE.FLAGS
        ),
        "DISABLE_RISC_BP_Disable_bmp_clear_ncrisc": ConfigurationRegisterDescription(
            index=2, mask=0x80000000, shift=31
        ),
        # DEST RD CTRL
        "PACK_DEST_RD_CTRL_Read_32b_data": ConfigurationRegisterDescription(
            index=18, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_DEST_RD_CTRL_Read_unsigned": ConfigurationRegisterDescription(
            index=18, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_DEST_RD_CTRL_Read_int8": ConfigurationRegisterDescription(
            index=18, mask=0x4, shift=2, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_DEST_RD_CTRL_Round_10b_mant": ConfigurationRegisterDescription(
            index=18, mask=0x8, shift=3, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_DEST_RD_CTRL_Reserved": ConfigurationRegisterDescription(
            index=18, mask=0xFFFFFFF0, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        # EDGE OFFSET SEC 0
        "PACK_EDGE_OFFSET0_mask": ConfigurationRegisterDescription(
            index=24, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        "PACK_EDGE_OFFSET0_mode": ConfigurationRegisterDescription(
            index=24, mask=0x10000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack0": ConfigurationRegisterDescription(
            index=24, mask=0x60000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack1": ConfigurationRegisterDescription(
            index=24, mask=0x180000, shift=19, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack2": ConfigurationRegisterDescription(
            index=24, mask=0x600000, shift=21, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack3": ConfigurationRegisterDescription(
            index=24, mask=0x1800000, shift=23, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_reserved": ConfigurationRegisterDescription(
            index=24, mask=0xFE000000, shift=25, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK COUNTERS SEC 0
        "PACK_COUNTERS0_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=28, mask=0xFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS0_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
            index=28, mask=0xFF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS0_pack_xys_per_til": ConfigurationRegisterDescription(
            index=28, mask=0x7F0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS0_pack_yz_transposed": ConfigurationRegisterDescription(
            index=28, mask=0x800000, shift=23, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_COUNTERS0_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=28, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK STRIDES REG 0
        "PACK_STRIDES0_x_stride": ConfigurationRegisterDescription(
            index=12, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES0_y_stride": ConfigurationRegisterDescription(
            index=12, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES0_z_stride": ConfigurationRegisterDescription(
            index=13, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES0_w_stride": ConfigurationRegisterDescription(
            index=13, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK STRIDES REG 1
        "PACK_STRIDES1_x_stride": ConfigurationRegisterDescription(
            index=14, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES1_y_stride": ConfigurationRegisterDescription(
            index=14, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES1_z_stride": ConfigurationRegisterDescription(
            index=15, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES1_w_stride": ConfigurationRegisterDescription(
            index=15, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
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
        "NOC_X_ID_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(address=0x18),
        "NOC_X_ID_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(address=0x1C),
        "NOC_X_ID_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(address=0x20),
        "NOC_X_ID_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(address=0x24),
        "NOC_X_ID_TRANSLATE_TABLE_4": NocConfigurationRegisterDescription(address=0x28),
        "NOC_X_ID_TRANSLATE_TABLE_5": NocConfigurationRegisterDescription(address=0x2C),
        "NOC_Y_ID_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(address=0x30),
        "NOC_Y_ID_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(address=0x34),
        "NOC_Y_ID_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(address=0x38),
        "NOC_Y_ID_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(address=0x3C),
        "NOC_Y_ID_TRANSLATE_TABLE_4": NocConfigurationRegisterDescription(address=0x40),
        "NOC_Y_ID_TRANSLATE_TABLE_5": NocConfigurationRegisterDescription(address=0x44),
        "NOC_ID_LOGICAL": NocConfigurationRegisterDescription(address=0x48),
        "MEMORY_SHUTDOWN_CONTROL": NocConfigurationRegisterDescription(address=0x4C),
        "NOC_ID_TRANSLATE_COL_MASK": NocConfigurationRegisterDescription(address=0x50),
        "NOC_ID_TRANSLATE_ROW_MASK": NocConfigurationRegisterDescription(address=0x54),
        "DDR_COORD_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(address=0x58),
        "DDR_COORD_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(address=0x5C),
        "DDR_COORD_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(address=0x60),
        "DDR_COORD_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(address=0x64),
        "DDR_COORD_TRANSLATE_TABLE_4": NocConfigurationRegisterDescription(address=0x68),
        "DDR_COORD_TRANSLATE_TABLE_5": NocConfigurationRegisterDescription(address=0x6C),
        "DDR_COORD_TRANSLATE_COL_SWAP": NocConfigurationRegisterDescription(address=0x70),
        "DEBUG_COUNTER_RESET": NocConfigurationRegisterDescription(address=0x74),
        "NIU_TRANS_COUNT_RTZ_CFG": NocConfigurationRegisterDescription(address=0x78),
        "NIU_TRANS_COUNT_RTZ_CLR": NocConfigurationRegisterDescription(address=0x7C),
        "NOC_TARG_ADDR_LO": NocControlRegisterDescription(address=0x0),
        "NOC_TARG_ADDR_MID": NocControlRegisterDescription(address=0x4),
        "NOC_TARG_ADDR_HI": NocControlRegisterDescription(address=0x8),
        "NOC_RET_ADDR_LO": NocControlRegisterDescription(address=0xC),
        "NOC_RET_ADDR_MID": NocControlRegisterDescription(address=0x10),
        "NOC_RET_ADDR_HI": NocControlRegisterDescription(address=0x14),
        "NOC_PACKET_TAG": NocControlRegisterDescription(address=0x18),
        "NOC_CTRL": NocControlRegisterDescription(address=0x1C),
        "NOC_AT_LEN_BE": NocControlRegisterDescription(address=0x20),
        "NOC_AT_LEN_BE_1": NocControlRegisterDescription(address=0x24),
        "NOC_AT_DATA": NocControlRegisterDescription(address=0x28),
        "NOC_BRCST_EXCLUEDE": NocControlRegisterDescription(address=0x2C),
        "NOC_L1_ACC_AT_INSTRN": NocControlRegisterDescription(address=0x30),
        "NOC_SEC_CTRL": NocControlRegisterDescription(address=0x34),
        "NOC_CMD_CTRL": NocControlRegisterDescription(address=0x40),
        "NOC_NODE_ID": NocControlRegisterDescription(address=0x44),
        "NOC_ENDPOINT_ID": NocControlRegisterDescription(address=0x48),
        "NUM_MEM_PARITY_ERR": NocControlRegisterDescription(address=0x50),
        "NUM_HEADER_1B_ERR": NocControlRegisterDescription(address=0x54),
        "NUM_HEADER_2B_ERR": NocControlRegisterDescription(address=0x58),
        "ECC_CTRL": NocControlRegisterDescription(address=0x5C),
        "NOC_CLEAR_OUTSTANDING_REQ_CNT": NocControlRegisterDescription(address=0x60),
        "NOC_SEC_FENCE_RANGE": NocControlRegisterDescription(address=0x400),  # 32 instances
        "NOC_SEC_FENCE_ATTRIBUTE": NocControlRegisterDescription(address=0x480),  # 8 instances
        "NOC_SEC_FENCE_MASTER_LEVEL": NocControlRegisterDescription(address=0x4A0),
        "NOC_SEC_FENCE_FIFO_STATUS": NocControlRegisterDescription(address=0x4A4),
        "NOC_SEC_FENCE_FIFO_RDDATA": NocControlRegisterDescription(address=0x4A8),
        "PORT1_FLIT_COUNTER_LOWER": NocControlRegisterDescription(address=0x500),  # 16 instances
        "PORT1_FLIT_COUNTER_UPPER": NocControlRegisterDescription(address=0x540),  # 16 instances
        "PORT2_FLIT_COUNTER_LOWER": NocControlRegisterDescription(address=0x580),  # 16 instances
        "PORT2_FLIT_COUNTER_UPPER": NocControlRegisterDescription(address=0x5C0),  # 16 instances
    }

    def get_debug_bus_signal_store(self, location: OnChipCoordinate) -> DebugBusSignalStore:
        block_type = self.get_block_type(location)
        if block_type == "functional_workers":
            return DebugBusSignalStore(self.__debug_bus_signal_map, location)
        raise ValueError(f"Debug bus signal store not available for block type {block_type} at location {location}")

    __debug_bus_signal_map = {
        # For the other signals applying the pc_mask.
        "brisc_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 5 + 1, mask=0x3FFFFFFF),
        "trisc0_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 6 + 1, mask=0x3FFFFFFF),
        "trisc1_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 7 + 1, mask=0x3FFFFFFF),
        "trisc2_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 8 + 1, mask=0x3FFFFFFF),
        "ncrisc_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 12 + 1, mask=0x3FFFFFFF),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_IBUFFER_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=13, mask=0x80
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RISC_CFG_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=13, mask=0x40
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RISC_GPR_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=13, mask=0x20
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RISC_TDMA_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=13, mask=0x10
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_PREV_GEN_NO__3_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xF0000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_PREV_GEN_NO__7_4": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=13, mask=0xF
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x8000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x4000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x2000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x1000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x800000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_TARGET_CFG_SPACE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x700000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_CFG_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xC0000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_CFG": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_CFG": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_HEAD_GEN_NO": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xFF00
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_LSQ_FULL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x80
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x40
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x20
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x10
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x8
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x4
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_TARGET_CFG_SPACE__0_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x80000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_TARGET_CFG_SPACE__2_1": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x3
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_CFG_STATE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x60000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_CFG": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x10000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_CFG": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x8000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_HEAD_GEN_NO": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x7F80000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_TTSYNC_DBG_BITS_RQ_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x40000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_I_CG_TRISC_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_MACHINE_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_REQ_IRAMD_BUFFER_NOT_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x8000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_GPR_FILE_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x4000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_CFG_EXU_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x2000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_REQ_IRAMD_BUFFER_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x1000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_REQ_IRAMD_BUFFER_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x800
        ),
        "DEBUG_BUS_THREAD_STATE[0]_~IBUFFER_RTR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x400
        ),
        "DEBUG_BUS_THREAD_STATE[0]_IBUFFER_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x200
        ),
        "DEBUG_BUS_THREAD_STATE[0]_IBUFFER_EMPTY_RAW": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x100
        ),
        "DEBUG_BUS_THREAD_STATE[0]_THREAD_INST__23_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=12, mask=0xFFFFFF00
        ),
        "DEBUG_BUS_THREAD_STATE[0]_THREAD_INST__31_24": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0xFF
        ),
        "DEBUG_BUS_THREAD_STATE[0]_MATH_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x80),
        "DEBUG_BUS_THREAD_STATE[0]_TDMA_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x40),
        "DEBUG_BUS_THREAD_STATE[0]_PACK_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x20),
        "DEBUG_BUS_THREAD_STATE[0]_MOVE_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x10),
        "DEBUG_BUS_THREAD_STATE[0]_SFPU_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x8),
        "DEBUG_BUS_THREAD_STATE[0]_UNPACK_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x6),
        "DEBUG_BUS_THREAD_STATE[0]_XSEARCH_INST": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x1
        ),
        "DEBUG_BUS_THREAD_STATE[0]_THCON_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x80000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_SYNC_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x40000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_CFG_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x20000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_PACK_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x10000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_UNPACK_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xC000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_MATH_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x2000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_TDMA_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x1000000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_MOVE_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x800000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_XSEARCH_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x400000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_THCON_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x200000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_SYNC_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x100000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_CFG_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x80000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_STALLED_SFPU_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x40000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_TDMA_KICK_MOVE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_TDMA_KICK_PACK": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_TDMA_KICK_UNPACK": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xC000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_TDMA_KICK_XSEARCH": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x2000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_TDMA_KICK_THCON": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x1000
        ),
        "DEBUG_BUS_THREAD_STATE[0]_TDMA_STATUS_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xF80
        ),
        "DEBUG_BUS_THREAD_STATE[0]_PACKER_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x40
        ),
        "DEBUG_BUS_THREAD_STATE[0]_UNPACKER_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x30
        ),
        "DEBUG_BUS_THREAD_STATE[0]_THCON_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x8),
        "DEBUG_BUS_THREAD_STATE[0]_MOVE_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x4),
        "DEBUG_BUS_THREAD_STATE[0]_XSEARCH_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x3
        ),
        "DEBUG_BUS_STALL_INST_CNT[0]_PERF_CNT_INSTRN_THREAD_INST_PACK_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[0]_PERF_CNT_INSTRN_THREAD_INST_UNPACK_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[0]_PERF_CNT_INSTRN_THREAD_INST_MATH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[0]_PERF_CNT_INSTRN_THREAD_INST_MOVE_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[0]_PERF_CNT_INSTRN_THREAD_INST_XSEARCH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[0]_PERF_CNT_INSTRN_THREAD_INST_THCON_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[0]_PERF_CNT_INSTRN_THREAD_INST_SYNC_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[0]_PERF_CNT_INSTRN_THREAD_INST_CFG_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_IBUFFER_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=9, mask=0x80
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RISC_CFG_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=9, mask=0x40
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RISC_GPR_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=9, mask=0x20
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RISC_TDMA_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=9, mask=0x10
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_PREV_GEN_NO__3_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xF0000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_PREV_GEN_NO__7_4": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=9, mask=0xF
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x8000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x4000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x2000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x1000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x800000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_TARGET_CFG_SPACE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x700000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_CFG_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xC0000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_CFG": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_CFG": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_HEAD_GEN_NO": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xFF00
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_LSQ_FULL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x80
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x40
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x20
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x10
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x8
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x4
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_TARGET_CFG_SPACE__0_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x80000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_TARGET_CFG_SPACE__2_1": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x3
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_CFG_STATE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x60000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_CFG": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x10000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_CFG": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x8000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_HEAD_GEN_NO": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x7F80000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_TTSYNC_DBG_BITS_RQ_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x40000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_I_CG_TRISC_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_MACHINE_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_REQ_IRAMD_BUFFER_NOT_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x8000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_GPR_FILE_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x4000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_CFG_EXU_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x2000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_REQ_IRAMD_BUFFER_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x1000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_REQ_IRAMD_BUFFER_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x800
        ),
        "DEBUG_BUS_THREAD_STATE[1]_~IBUFFER_RTR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x400
        ),
        "DEBUG_BUS_THREAD_STATE[1]_IBUFFER_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x200
        ),
        "DEBUG_BUS_THREAD_STATE[1]_IBUFFER_EMPTY_RAW": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x100
        ),
        "DEBUG_BUS_THREAD_STATE[1]_THREAD_INST__23_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=8, mask=0xFFFFFF00
        ),
        "DEBUG_BUS_THREAD_STATE[1]_THREAD_INST__31_24": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0xFF
        ),
        "DEBUG_BUS_THREAD_STATE[1]_MATH_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x80),
        "DEBUG_BUS_THREAD_STATE[1]_TDMA_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x40),
        "DEBUG_BUS_THREAD_STATE[1]_PACK_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x20),
        "DEBUG_BUS_THREAD_STATE[1]_MOVE_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x10),
        "DEBUG_BUS_THREAD_STATE[1]_SFPU_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x8),
        "DEBUG_BUS_THREAD_STATE[1]_UNPACK_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x6),
        "DEBUG_BUS_THREAD_STATE[1]_XSEARCH_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x1),
        "DEBUG_BUS_THREAD_STATE[1]_THCON_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x80000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_SYNC_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x40000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_CFG_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x20000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_PACK_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x10000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_UNPACK_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xC000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_MATH_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x2000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_TDMA_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x1000000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_MOVE_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x800000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_XSEARCH_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x400000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_THCON_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x200000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_SYNC_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x100000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_CFG_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x80000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_STALLED_SFPU_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x40000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_TDMA_KICK_MOVE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_TDMA_KICK_PACK": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_TDMA_KICK_UNPACK": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xC000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_TDMA_KICK_XSEARCH": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x2000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_TDMA_KICK_THCON": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x1000
        ),
        "DEBUG_BUS_THREAD_STATE[1]_TDMA_STATUS_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xF80
        ),
        "DEBUG_BUS_THREAD_STATE[1]_PACKER_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x40),
        "DEBUG_BUS_THREAD_STATE[1]_UNPACKER_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x30
        ),
        "DEBUG_BUS_THREAD_STATE[1]_THCON_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x8),
        "DEBUG_BUS_THREAD_STATE[1]_MOVE_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x4),
        "DEBUG_BUS_THREAD_STATE[1]_XSEARCH_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x3),
        "DEBUG_BUS_STALL_INST_CNT[1]_PERF_CNT_INSTRN_THREAD_INST_PACK_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[1]_PERF_CNT_INSTRN_THREAD_INST_UNPACK_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[1]_PERF_CNT_INSTRN_THREAD_INST_MATH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[1]_PERF_CNT_INSTRN_THREAD_INST_MOVE_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[1]_PERF_CNT_INSTRN_THREAD_INST_XSEARCH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[1]_PERF_CNT_INSTRN_THREAD_INST_THCON_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[1]_PERF_CNT_INSTRN_THREAD_INST_SYNC_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[1]_PERF_CNT_INSTRN_THREAD_INST_CFG_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_IBUFFER_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=5, mask=0x80
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RISC_CFG_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=5, mask=0x40
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RISC_GPR_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=5, mask=0x20
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RISC_TDMA_STALL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=5, mask=0x10
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_PREV_GEN_NO__3_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xF0000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_PREV_GEN_NO__7_4": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=5, mask=0xF
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x8000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x4000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x2000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x1000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x800000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_TARGET_CFG_SPACE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x700000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_CFG_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xC0000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_WR_CFG": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_RSRCS_RD_CFG": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_HEAD_GEN_NO": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xFF00
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_LSQ_FULL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x80
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x40
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x20
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_TDMA": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x10
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x8
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_GPR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x4
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_TARGET_CFG_SPACE__0_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x80000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_TARGET_CFG_SPACE__2_1": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x3
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_CFG_STATE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x60000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_WR_CFG": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x10000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_RSRCS_RD_CFG": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x8000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_HEAD_GEN_NO": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x7F80000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_TTSYNC_DBG_BITS_RQ_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x40000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_I_CG_TRISC_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_MACHINE_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_REQ_IRAMD_BUFFER_NOT_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x8000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_GPR_FILE_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x4000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_CFG_EXU_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x2000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_REQ_IRAMD_BUFFER_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x1000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_REQ_IRAMD_BUFFER_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x800
        ),
        "DEBUG_BUS_THREAD_STATE[2]_~IBUFFER_RTR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x400
        ),
        "DEBUG_BUS_THREAD_STATE[2]_IBUFFER_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x200
        ),
        "DEBUG_BUS_THREAD_STATE[2]_IBUFFER_EMPTY_RAW": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x100
        ),
        "DEBUG_BUS_THREAD_STATE[2]_THREAD_INST__23_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=4, mask=0xFFFFFF00
        ),
        "DEBUG_BUS_THREAD_STATE[2]_THREAD_INST__31_24": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0xFF
        ),
        "DEBUG_BUS_THREAD_STATE[2]_MATH_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x80),
        "DEBUG_BUS_THREAD_STATE[2]_TDMA_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x40),
        "DEBUG_BUS_THREAD_STATE[2]_PACK_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x20),
        "DEBUG_BUS_THREAD_STATE[2]_MOVE_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x10),
        "DEBUG_BUS_THREAD_STATE[2]_SFPU_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x8),
        "DEBUG_BUS_THREAD_STATE[2]_UNPACK_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x6),
        "DEBUG_BUS_THREAD_STATE[2]_XSEARCH_INST": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x1),
        "DEBUG_BUS_THREAD_STATE[2]_THCON_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x80000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_SYNC_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x40000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_CFG_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x20000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_PACK_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x10000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_UNPACK_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xC000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_MATH_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x2000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_TDMA_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x1000000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_MOVE_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x800000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_XSEARCH_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x400000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_THCON_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x200000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_SYNC_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x100000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_CFG_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x80000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_STALLED_SFPU_INST": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x40000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_TDMA_KICK_MOVE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x20000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_TDMA_KICK_PACK": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x10000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_TDMA_KICK_UNPACK": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xC000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_TDMA_KICK_XSEARCH": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x2000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_TDMA_KICK_THCON": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x1000
        ),
        "DEBUG_BUS_THREAD_STATE[2]_TDMA_STATUS_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xF80
        ),
        "DEBUG_BUS_THREAD_STATE[2]_PACKER_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x40),
        "DEBUG_BUS_THREAD_STATE[2]_UNPACKER_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x30
        ),
        "DEBUG_BUS_THREAD_STATE[2]_THCON_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x8),
        "DEBUG_BUS_THREAD_STATE[2]_MOVE_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x4),
        "DEBUG_BUS_THREAD_STATE[2]_XSEARCH_BUSY": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x3),
        "DEBUG_BUS_STALL_INST_CNT[2]_PERF_CNT_INSTRN_THREAD_INST_PACK_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[2]_PERF_CNT_INSTRN_THREAD_INST_UNPACK_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[2]_PERF_CNT_INSTRN_THREAD_INST_MATH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[2]_PERF_CNT_INSTRN_THREAD_INST_MOVE_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[2]_PERF_CNT_INSTRN_THREAD_INST_XSEARCH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[2]_PERF_CNT_INSTRN_THREAD_INST_THCON_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[2]_PERF_CNT_INSTRN_THREAD_INST_SYNC_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_INST_CNT[2]_PERF_CNT_INSTRN_THREAD_INST_CFG_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_THREADS(WHEN_I_DBG_INSTRN_THREAD_PERF_CNT_MUX_SEL[0]==0)_PERF_CNT_INSTRN_THREAD_STALL_CNTS[0]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_THREADS(WHEN_I_DBG_INSTRN_THREAD_PERF_CNT_MUX_SEL[0]==0)_PERF_CNT_INSTRN_THREAD_STALL_CNTS[1]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_THREADS(WHEN_I_DBG_INSTRN_THREAD_PERF_CNT_MUX_SEL[0]==0)_PERF_CNT_INSTRN_THREAD_STALL_CNTS[2]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SEM_ZERO_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SEM_MAX_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCA_CLEARED_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCB_CLEARED_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCA_VALID_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCB_VALID_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_MOVE_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_TRISC_REG_ACCESS_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_THCON_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_UNPACK0_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_PACK0_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SFPU_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[0]_PERF_CNT_INSTRN_THREAD_STALL_RSN_MATH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SEM_ZERO_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SEM_MAX_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCA_CLEARED_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCB_CLEARED_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCA_VALID_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCB_VALID_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_MOVE_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_TRISC_REG_ACCESS_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_THCON_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_UNPACK0_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_PACK0_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SFPU_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[1]_PERF_CNT_INSTRN_THREAD_STALL_RSN_MATH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SEM_ZERO_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SEM_MAX_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCA_CLEARED_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCB_CLEARED_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCA_VALID_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SRCB_VALID_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_MOVE_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT0[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_TRISC_REG_ACCESS_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_THCON_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_UNPACK0_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_PACK0_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_SFPU_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_STALL_RSN_CNT1[2]_PERF_CNT_INSTRN_THREAD_STALL_RSN_MATH_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_THREADS(WHEN_I_DBG_INSTRN_THREAD_PERF_CNT_MUX_SEL[0]!=0)_PERF_CNT_INSTRN_THREAD_STALL_CNTS[0]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_THREADS(WHEN_I_DBG_INSTRN_THREAD_PERF_CNT_MUX_SEL[0]!=0)_PERF_CNT_INSTRN_THREAD_STALL_CNTS[1]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_THREADS(WHEN_I_DBG_INSTRN_THREAD_PERF_CNT_MUX_SEL[0]!=0)_PERF_CNT_INSTRN_THREAD_STALL_CNTS[2]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_THCON_P0_TID": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x30000),
        "DEBUG_BUS_THCON_P0_WREN": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x8000),
        "DEBUG_BUS_THCON_P0_RDEN": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x4000),
        "DEBUG_BUS_THCON_P0_GPR_ADDR": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x3C00),
        "DEBUG_BUS_THCON_P0_GPR_BYTEN__5_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xFC000000
        ),
        "DEBUG_BUS_THCON_P0_GPR_BYTEN__15_6": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x3FF),
        "DEBUG_BUS_P0_GPR_ACCEPT": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x2000000),
        "DEBUG_BUS_CFG_GPR_P0_REQ": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x1000000),
        "DEBUG_BUS_CFG_GPR_P0_TID": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xC00000),
        "DEBUG_BUS_CFG_GPR_P0_ADDR": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3C0000),
        "DEBUG_BUS_GPR_CFG_P0_ACCEPT": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x20000),
        "DEBUG_BUS_L1_RET_VLD": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x10000),
        "DEBUG_BUS_L1_RET_TID": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xC000),
        "DEBUG_BUS_L1_RET_GPR": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3C00),
        "DEBUG_BUS_L1_RET_BYTEN__5_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xFC000000),
        "DEBUG_BUS_L1_RET_BYTEN__15_6": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3FF),
        "DEBUG_BUS_L1_RETURN_ACCEPT": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x2000000),
        "DEBUG_BUS_THCON_P1_REQ_VLD": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x1000000),
        "DEBUG_BUS_THCON_P1_TID": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xC00000),
        "DEBUG_BUS_THCON_P1_GPR": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3C0000),
        "DEBUG_BUS_THCON_P1_REQ_ACCEPT": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x20000),
        "DEBUG_BUS_CFG_GPR_P1_REQ": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x10000),
        "DEBUG_BUS_CFG_GPR_P1_TID": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xC000),
        "DEBUG_BUS_CFG_GPR_P1_ADDR": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3C00),
        "DEBUG_BUS_CFG_GPR_P1_BYTEN__5_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=2, sig_sel=16, mask=0xFC000000
        ),
        "DEBUG_BUS_CFG_GPR_P1_BYTEN__15_6": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3FF),
        "DEBUG_BUS_GPR_CFG_P1_ACCEPT": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x2000000),
        "DEBUG_BUS_I_RISC_OUT_REG_RDEN": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1000000),
        "DEBUG_BUS_I_RISC_OUT_REG_WREN": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x800000),
        "DEBUG_BUS_RISCV_TID": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x600000),
        "DEBUG_BUS_I_RISC_OUT_REG_INDEX__5_2": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1E0000
        ),
        "DEBUG_BUS_I_RISC_OUT_REG_BYTEN": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1FFFE),
        "DEBUG_BUS_O_RISC_IN_REG_REQ_READY": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1),
        "DEBUG_BUS_THCON_P0_GPR_WRDATA__31_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_THCON_P0_GPR_WRDATA__63_32": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_THCON_P0_GPR_WRDATA__95_64": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_THCON_P0_GPR_WRDATA__127_96": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_P0_GPR_RET__31_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
        "DEBUG_BUS_P0_GPR_RET__63_32": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
        "DEBUG_BUS_P0_GPR_RET__95_64": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
        "DEBUG_BUS_P0_GPR_RET__127_96": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
        "DEBUG_BUS_GPR_CFG_P0_DATA__31_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_GPR_CFG_P0_DATA__63_32": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_GPR_CFG_P0_DATA__95_64": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_GPR_CFG_P0_DATA__127_96": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_L1_RET_WRDATA__31_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
        "DEBUG_BUS_L1_RET_WRDATA__63_32": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
        "DEBUG_BUS_L1_RET_WRDATA__95_64": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
        "DEBUG_BUS_L1_RET_WRDATA__127_96": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
        "DEBUG_BUS_THCON_P1_RET__31_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
        "DEBUG_BUS_THCON_P1_RET__63_32": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
        "DEBUG_BUS_THCON_P1_RET__95_64": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
        "DEBUG_BUS_THCON_P1_RET__127_96": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
        "DEBUG_BUS_CFG_GPR_P1_DATA__31_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
        "DEBUG_BUS_CFG_GPR_P1_DATA__63_32": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_CFG_GPR_P1_DATA__95_64": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_CFG_GPR_P1_DATA__127_96": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_I_RISC_OUT_REG_WRDATA__31_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_I_RISC_OUT_REG_WRDATA__63_32": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_I_RISC_OUT_REG_WRDATA__95_64": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_I_RISC_OUT_REG_WRDATA__127_96": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_O_RISC_IN_REG_RDDATA__31_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_O_RISC_IN_REG_RDDATA__63_32": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_O_RISC_IN_REG_RDDATA__95_64": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_O_RISC_IN_REG_RDDATA__127_96": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_MATH_INSTRN__20_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0xFFFFF800),
        "DEBUG_BUS_MATH_INSTRN__31_21": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=7, mask=0x7FF),
        "DEBUG_BUS_MATH_WINNER_THREAD": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0x600),
        "DEBUG_BUS_MATH_WINNER": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0x1C0),
        "DEBUG_BUS_S0_FIDELITY_PHASE_D": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0x30),
        "DEBUG_BUS_S0_SRCA_REG_ADDR_D__1_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=7, mask=0xC0000000
        ),
        "DEBUG_BUS_S0_SRCA_REG_ADDR_D__5_2": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0xF),
        "DEBUG_BUS_S0_SRCB_REG_ADDR_D": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0x3F000000),
        "DEBUG_BUS_S0_DST_REG_ADDR_D": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0xFFC000),
        "DEBUG_BUS_S0_MOV_DST_REG_ADDR_D": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0x3FF0),
        "DEBUG_BUS_S0_DEC_INSTR_SINGLE_OUTPUT_ROW_D": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=7, mask=0x8
        ),
        "DEBUG_BUS_FPU_RD_DATA_REQUIRED_D": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0x7),
        "DEBUG_BUS_TDMA_SRCA_REGIF_UNPACK_SRC_REG_SET_UPD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x10
        ),
        "DEBUG_BUS_DEBUG_ISSUE0_IN[3]_DMA_SRCA_WR_PORT_AVAIL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x8
        ),
        "DEBUG_BUS_DEBUG_ISSUE0_IN[3]_SRCA_WRITE_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x4
        ),
        "DEBUG_BUS_TDMA_SRCA_REGIF_UNPACK_IF_SEL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x2
        ),
        "DEBUG_BUS_TDMA_SRCA_REGIF_STATE_ID": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x1),
        "DEBUG_BUS_TDMA_SRCA_REGIF_ADDR": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0xFFFC0000),
        "DEBUG_BUS_TDMA_SRCA_REGIF_WREN__3_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=6, mask=0x3C000
        ),
        "DEBUG_BUS_TDMA_SRCA_REGIF_THREAD_ID": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0x3000),
        "DEBUG_BUS_TDMA_SRCA_REGIF_OUT_DATA_FORMAT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=6, mask=0xF00
        ),
        "DEBUG_BUS_TDMA_SRCA_REGIF_DATA_FORMAT": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0xF0),
        "DEBUG_BUS_TDMA_SRCA_REGIF_SHIFT_AMOUNT": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0xF),
        "DEBUG_BUS_TDMA_SRCB_REGIF_UNPACK_SRC_REG_SET_UPD": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_ISSUE0_IN[3]_DMA_SRCB_WR_PORT_AVAIL": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_ISSUE0_IN[3]_SRCB_WRITE_READY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x20000000
        ),
        "DEBUG_BUS_TDMA_SRCB_REGIF_STATE_ID": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x10000000
        ),
        "DEBUG_BUS_TDMA_SRCB_REGIF_ADDR": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0xFFFC000),
        "DEBUG_BUS_TDMA_SRCB_REGIF_WREN__3_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x3C00),
        "DEBUG_BUS_TDMA_SRCB_REGIF_THREAD_ID": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x300),
        "DEBUG_BUS_TDMA_SRCB_REGIF_OUT_DATA_FORMAT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=6, mask=0xF0
        ),
        "DEBUG_BUS_TDMA_SRCB_REGIF_DATA_FORMAT": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0xF),
        "DEBUG_BUS_TDMA_DSTAC_REGIF_RDEN_RAW": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=6, mask=0x80),
        "DEBUG_BUS_TDMA_DSTAC_REGIF_THREAD_ID": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=6, mask=0x60),
        "DEBUG_BUS_TDMA_DSTAC_REGIF_DATA_FORMAT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=6, mask=0x1E
        ),
        "DEBUG_BUS_DSTAC_REGIF_TDMA_REQIF_READY": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=6, mask=0x1),
        "DEBUG_BUS_TDMA_PACK_BUSY__0_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0x1000),
        "DEBUG_BUS_TDMA_UNPACK_BUSY": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0xFC0),
        "DEBUG_BUS_TDMA_TC_BUSY": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0x38),
        "DEBUG_BUS_TDMA_MOVE_BUSY": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0x4),
        "DEBUG_BUS_TDMA_XSEARCH_BUSY__3_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=5, mask=0xF0000000
        ),
        "DEBUG_BUS_TDMA_XSEARCH_BUSY__5_4": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0x3),
        "DEBUG_BUS_I_CG_REGBLOCKS_EN": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x2000000),
        "DEBUG_BUS_CG_REGBLOCKS_BUSY_D": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x1000000),
        "DEBUG_BUS_SRCB_REG_ADDR__4_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0xF80000),
        "DEBUG_BUS_SRCB_REG_ADDR_D__4_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x7C000),
        "DEBUG_BUS_FPU_OUTPUT_MODE_D": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x3800),
        "DEBUG_BUS_FPU_OUTPUT_MODE": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x700),
        "DEBUG_BUS_SRCB_SINGLE_ROW_RD_MODE_D": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x80),
        "DEBUG_BUS_SRCB_SINGLE_ROW_RD_MODE": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x40),
        "DEBUG_BUS_DEST_APPLY_RELU": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=5, mask=0x60),
        "DEBUG_BUS_TDMA_DSTAC_REGIF_STATE_ID": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=5, mask=0x10),
        "DEBUG_BUS_RELU_THRESH__11_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0xFFF00000),
        "DEBUG_BUS_RELU_THRESH__15_12": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=5, mask=0xF),
        "DEBUG_BUS_DEST_OFFSET_STATE_ID": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x80000),
        "DEBUG_BUS_DMA_DEST_OFFSET_APPLY_EN": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x40000),
        "DEBUG_BUS_SRCA_FPU_OUTPUT_ALU_FORMAT_S1": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x3C000
        ),
        "DEBUG_BUS_SRCB_FPU_OUTPUT_ALU_FORMAT_S1": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x3C00
        ),
        "DEBUG_BUS_DEST_FPU_OUTPUT_ALU_FORMAT_S1": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x3C0
        ),
        "DEBUG_BUS_DEST_DMA_OUTPUT_ALU_FORMAT__3_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x3C
        ),
        "DEBUG_BUS_SRCA_GATE_SRC_PIPELINE__0_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x10000000
        ),
        "DEBUG_BUS_SRCA_GATE_SRC_PIPELINE__1_1": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x8000000
        ),
        "DEBUG_BUS_SRCB_GATE_SRC_PIPELINE__0_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x4000000
        ),
        "DEBUG_BUS_SRCB_GATE_SRC_PIPELINE__1_1": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x2000000
        ),
        "DEBUG_BUS_SQUASH_ALU_INSTRN": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x1000000),
        "DEBUG_BUS_ALU_INST_ISSUE_READY": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x800000),
        "DEBUG_BUS_ALU_INST_ISSUE_READY_SRC": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x400000
        ),
        "DEBUG_BUS_SFPU_INST_ISSUE_READY_S1": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x200000
        ),
        "DEBUG_BUS_SFPU_INST_STORE_READY_S1": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x100000
        ),
        "DEBUG_BUS_LDDEST_INSTR_VALID": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x80000),
        "DEBUG_BUS_RDDEST_INSTR_VALID": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x40000),
        "DEBUG_BUS_DEST_REG_DEPS_SCOREBOARD_BANK_PENDING": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x30000
        ),
        "DEBUG_BUS_DEST_REG_DEPS_SCOREBOARD_SOMETHING_PENDING": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x8000
        ),
        "DEBUG_BUS_DEST_REG_DEPS_SCOREBOARD_PENDING_THREAD": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x7000
        ),
        "DEBUG_BUS_ALL_BUFFERS_EMPTY": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0xE00),
        "DEBUG_BUS_DEST_REG_DEPS_SCOREBOARD_STALL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x100
        ),
        "DEBUG_BUS_DEST_WR_PORT_STALL": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x80),
        "DEBUG_BUS_DEST_FPU_RD_PORT_STALL": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x40),
        "DEBUG_BUS_DEST2SRC_POST_STALL": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x20),
        "DEBUG_BUS_POST_SHIFTXB_STALL": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x10),
        "DEBUG_BUS_DEST2SRC_DEST_STALL": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x8),
        "DEBUG_BUS_POST_ALU_INSTR_STALL": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x4),
        "DEBUG_BUS_FIDELITY_PHASE_CNT__3_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=4, mask=0xF0000000
        ),
        "DEBUG_BUS_FIDELITY_PHASE_CNT__5_4": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x3),
        "DEBUG_BUS_MATH_INSTRN__1_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=4, mask=0xC000000),
        "DEBUG_BUS_MATH_WINNER_THREAD__5_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=4, mask=0xFC000000
        ),
        "DEBUG_BUS_MATH_WINNER_THREAD__31_6": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=4, mask=0x3FFFFFF
        ),
        "DEBUG_BUS_S0_SRCA_REG_ADDR": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x1F80000),
        "DEBUG_BUS_S0_SRCB_REG_ADDR": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x7E000),
        "DEBUG_BUS_S0_DST_REG_ADDR": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x1FF8),
        "DEBUG_BUS_S0_FIDELITY_PHASE": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x6),
        "DEBUG_BUS_S0_DEC_INSTR_SINGLE_OUTPUT_ROW": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x1
        ),
        "DEBUG_BUS_(|MATH_WINNER_COMBO&MATH_INSTRN_PIPE_ACK)": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_ISSUE0_DEBUG_ISSUE0_IN[0]_MATH_INSTRN_PIPE_ACK__251": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x8000000
        ),
        "DEBUG_BUS_O_MATH_INSTRNBUF_RDEN": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x4000000),
        "DEBUG_BUS_MATH_INSTRN_VALID": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x2000000),
        "DEBUG_BUS_SRC_DATA_READY": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x1000000),
        "DEBUG_BUS_SRCB_DATA_READY": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x800000),
        "DEBUG_BUS_SRCA_DATA_READY": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x400000),
        "DEBUG_BUS_DEBUG_ISSUE0_IN[0]_SRCB_WRITE_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x200000
        ),
        "DEBUG_BUS_DEBUG_ISSUE0_IN[0]_SRCA_WRITE_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x100000
        ),
        "DEBUG_BUS_SRCA_UPDATE_INST": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x80000),
        "DEBUG_BUS_SRCB_UPDATE_INST": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x40000),
        "DEBUG_BUS_ALLOW_REGFILE_UPDATE": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x20000),
        "DEBUG_BUS_MATH_SRCA_WR_PORT_AVAIL": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x10000),
        "DEBUG_BUS_DEBUG_ISSUE0_IN[0]_DMA_SRCA_WR_PORT_AVAIL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x8000
        ),
        "DEBUG_BUS_MATH_SRCB_WR_PORT_AVAIL": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x4000),
        "DEBUG_BUS_DEBUG_ISSUE0_IN[0]_DMA_SRCB_WR_PORT_AVAIL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x2000
        ),
        "DEBUG_BUS_S0_ALU_INST_DECODED": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x1C00),
        "DEBUG_BUS_S0_SFPU_INST_DECODED": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x380),
        "DEBUG_BUS_REGW_INCR_INST_DECODED": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x70),
        "DEBUG_BUS_REGMOV_INST_DECODED": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0xE),
        "DEBUG_BUS_MATH_INSTR_VALID_TH": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE0000000),
        "DEBUG_BUS_MATH_WINNER_THREAD_COMBO": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x18000000
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_ISSUE0_DEBUG_ISSUE0_IN[0]_MATH_INSTRN_PIPE_ACK__215": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x800000
        ),
        "DEBUG_BUS_MATH_WINNER_WO_PIPE_STALL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x380000
        ),
        "DEBUG_BUS_S0_SRCA_DATA_READY": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x70000),
        "DEBUG_BUS_S0_SRCB_DATA_READY": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE000),
        "DEBUG_BUS_MATH_THREAD_INST_DATA_VALID": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE00
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC0_OFFSET__2_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=1, mask=0xE0000000
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC0_OFFSET__11_3": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x1FF
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC1_OFFSET": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1FFE0000
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC2_OFFSET": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1FFE0
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC3_OFFSET__6_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=1, mask=0xFE000000
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC3_OFFSET__11_7": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1F
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC0_ZOFFSET": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x1F80000
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC1_ZOFFSET": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x7E000
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC2_ZOFFSET": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x1F80
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_PACK_SEC3_ZOFFSET": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x7E
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_MATH_OFFSET__34_24": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=0, mask=0xFFE00000
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_MATH_OFFSET__35_35": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x1
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_MATH_OFFSET__23_12": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=0, mask=0x1FFE00
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_MATH_OFFSET__2_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=3, sig_sel=0, mask=0xE0000000
        ),
        "DEBUG_BUS_I_DEST_TARGET_REG_CFG_MATH_OFFSET__11_3": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=3, sig_sel=0, mask=0x1FF
        ),
        "DEBUG_BUS_I_THREAD_STATE_ID": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=0, mask=0xE000000),
        "DEBUG_BUS_I_OPCODE__23_16": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=0, mask=0x1FE0000),
        "DEBUG_BUS_I_INSTRN_PAYLOAD__54_48": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=3, sig_sel=0, mask=0xFE000000
        ),
        "DEBUG_BUS_I_INSTRN_PAYLOAD__71_55": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=0, mask=0x1FFFF),
        "DEBUG_BUS_I_OPCODE__15_8": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=0, mask=0x1FE0000),
        "DEBUG_BUS_I_INSTRN_PAYLOAD__30_24": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=3, sig_sel=0, mask=0xFE000000
        ),
        "DEBUG_BUS_I_INSTRN_PAYLOAD__47_31": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=0, mask=0x1FFFF),
        "DEBUG_BUS_I_OPCODE__8_8": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=0, mask=0x1000000),
        "DEBUG_BUS_I_INSTRN_PAYLOAD__23_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=0, mask=0xFFFFFF),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[18]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=22, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[18]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=22, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[18]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=22, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[18]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=22, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[17]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=20, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[17]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=20, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[17]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=20, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[17]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=20, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[16]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=18, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[16]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=18, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[16]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=18, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[16]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=18, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[15]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=16, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[15]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=16, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[15]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=16, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[15]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=16, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[14]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[14]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[14]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[14]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[13]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[13]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[13]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[13]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[12]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[12]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[12]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[12]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[11]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[11]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[11]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[11]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[10]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[10]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[10]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[10]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[9]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[9]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[9]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[9]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[8]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=4, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[8]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=4, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[8]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=4, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[8]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=4, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[7]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=5, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[7]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=5, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[7]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=5, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[7]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=5, sig_sel=14, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[6]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=5, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[6]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=5, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[6]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=5, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[6]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=5, sig_sel=12, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[5]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=5, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[5]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=5, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[5]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=5, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[5]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=5, sig_sel=10, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[4]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=5, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[4]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=5, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[4]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=5, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[4]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=5, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[3]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=5, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[3]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=5, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[3]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=5, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[3]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=5, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[2]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=5, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[2]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=5, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[2]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=5, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[2]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=5, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[1]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=5, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[1]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=5, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[1]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=5, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[1]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=5, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[0]_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=5, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[0]_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=5, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[0]_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=5, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_INSTRN_ISSUE_DBG[0]_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=5, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DBG_DEST_SFPU_ZERO_RETURN": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=11, mask=0x1FE),
        "DEBUG_BUS_DEST_SFPU_WR_EN__6_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0xFE000000),
        "DEBUG_BUS_DEST_SFPU_WR_EN__7_7": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=11, mask=0x1),
        "DEBUG_BUS_DEST_SFPU_RD_EN": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x1FE0000),
        "DEBUG_BUS_SFPU_STORE_32BITS_S1": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x10000),
        "DEBUG_BUS_SFPU_LOAD_32BITS_S1": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x8000),
        "DEBUG_BUS_SFPU_DST_REG_ADDR_S1_Q": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x1FF8),
        "DEBUG_BUS_SFPU_UPDATE_ZERO_FLAGS_S1": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x4),
        "DEBUG_BUS_SFPU_INSTR_VALID_TH_S1S4__0_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x80000000
        ),
        "DEBUG_BUS_SFPU_INSTR_VALID_TH_S1S4__2_1": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x3
        ),
        "DEBUG_BUS_SFPU_EMPTY": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x70000000),
        "DEBUG_BUS_SFPU_ACTIVE_Q": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0xE000000),
        "DEBUG_BUS_SFPU_WINNER_COMBO_S0": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x1C00000),
        "DEBUG_BUS_I_SFPU_BUSY": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x200000),
        "DEBUG_BUS_SFPU_INSTRN_PIPE_ACK_S0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x100000
        ),
        "DEBUG_BUS_SFPU_INSTRNBUF_RDEN_S1": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x80000),
        "DEBUG_BUS_SFPU_INSTRUCTION_ISSUE_STALL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x40000
        ),
        "DEBUG_BUS_SFPU_INSTRN_VALID_S1": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x20000),
        "DEBUG_BUS_MATH_SRCB_DONE": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x30000000),
        "DEBUG_BUS_SRCB_WRITE_DONE": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x8000000),
        "DEBUG_BUS_CLR_SRC_B": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x4000000),
        "DEBUG_BUS_TDMA_UNPACK_CLR_SRC_B_CTRL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x3E00000
        ),
        "DEBUG_BUS_CLR_ALL_BANKS": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x100000),
        "DEBUG_BUS_RESET_DATAVALID": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x80000),
        "DEBUG_BUS_DISABLE_SRCB_DVALID_CLEAR": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x60000
        ),
        "DEBUG_BUS_DISABLE_SRCB_BANK_SWITCH": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x18000),
        "DEBUG_BUS_FPU_OP_VALID": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x6000),
        "DEBUG_BUS_I_CG_SRC_PIPELINE_GATESRCBPIPEEN": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x1000
        ),
        "DEBUG_BUS_GATE_SRCB_SRC_PIPELINE_RST": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x800),
        "DEBUG_BUS_SRCB_DATA_VALID": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x600),
        "DEBUG_BUS_SRCB_DATA_VALID_EXP": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x180),
        "DEBUG_BUS_SRCB_WRITE_MATH_ID": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x40),
        "DEBUG_BUS_SRCB_READ_MATH_ID": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x20),
        "DEBUG_BUS_SRCB_READ_MATH_ID_EXP": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x10),
        "DEBUG_BUS_SRCB_ADDR_CHG_TRACK_STATE_EXP": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=9, mask=0xC
        ),
        "DEBUG_BUS_SRCB_ADDR_CHG_TRACK_STATE_MAN": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x3
        ),
        "DEBUG_BUS_I_DEST_FP32_READ_EN": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=9, mask=0xF000),
        "DEBUG_BUS_I_PACK_UNSIGNED": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=9, mask=0xF00),
        "DEBUG_BUS_I_DEST_READ_INT8": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=9, mask=0xF0),
        "DEBUG_BUS_I_GASKET_ROUND_10B_MANT": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=9, mask=0xF),
        "DEBUG_BUS_I_PACK_REQ_DEST_OUTPUT_ALU_FORMAT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=9, mask=0xFFFF0000
        ),
        "DEBUG_BUS_I_PACK_REQ_DEST_X_POS": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=9, mask=0xFF00),
        "DEBUG_BUS_I_PACK_REQ_DEST_DS_RATE__3_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=9, mask=0xF0000000
        ),
        "DEBUG_BUS_I_PACK_REQ_DEST_DS_RATE__11_4": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=9, mask=0xFF
        ),
        "DEBUG_BUS_I_PACK_REQ_DEST_DS_MASK__3_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=8, mask=0xF0000000
        ),
        "DEBUG_BUS_I_PACK_REQ_DEST_DS_MASK__35_4": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_I_PACK_REQ_DEST_DS_MASK__63_36": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=9, mask=0xFFFFFFF
        ),
        "DEBUG_BUS_I_PACKER_Z_POS": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=8, mask=0xFFFFFF0),
        "DEBUG_BUS_I_PACKER_EDGE_MASK__27_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=8, mask=0xFFFFFFF0
        ),
        "DEBUG_BUS_I_PACKER_EDGE_MASK__59_28": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_I_PACKER_EDGE_MASK__63_60": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=8, mask=0xF),
        "DEBUG_BUS_I_PACKER_EDGE_MASK_MODE": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=8, mask=0xF),
        "DEBUG_BUS_DEC_INSTR_SINGLE_OUTPUT_ROW": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=7, mask=0x10),
        "DEBUG_BUS_CURR_ISSUE_INSTR_DEST_FPU_ADDR__5_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=7, mask=0xFC000000
        ),
        "DEBUG_BUS_CURR_ISSUE_INSTR_DEST_FPU_ADDR__9_6": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=7, mask=0xF
        ),
        "DEBUG_BUS_DEST_WRMASK": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x1E000),
        "DEBUG_BUS_DEST_FPU_WR_EN": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x1FE0),
        "DEBUG_BUS_DEST_FPU_RD_EN__1_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x18),
        "DEBUG_BUS_PACK_REQ_FIFO_WREN": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x4),
        "DEBUG_BUS_PACK_REQ_FIFO_RDEN": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x2),
        "DEBUG_BUS_PACK_REQ_FIFO_EMPTY": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x1),
        "DEBUG_BUS_PACK_REQ_FIFO_FULL": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=6, mask=0x80000000),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_W_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF000000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_W_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_Z_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_Z_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_Y_CR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=5, mask=0x1FFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_Y_COUNTER": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=5, mask=0x1FFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_X_CR__13_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=5, mask=0xFFFC0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_X_CR__17_14": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=5, mask=0xF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH1_STATE_X_COUNTER": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=5, mask=0x3FFFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_W_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF000000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_W_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_Z_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_Z_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_Y_CR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=4, mask=0x1FFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_Y_COUNTER": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=4, mask=0x1FFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_X_CR__13_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=4, mask=0xFFFC0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_X_CR__17_14": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=4, mask=0xF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[2]_DMA_CNT_CH0_STATE_X_COUNTER": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=4, mask=0x3FFFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_W_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF000000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_W_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_Z_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_Z_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_Y_CR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=3, mask=0x1FFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_Y_COUNTER": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=3, mask=0x1FFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_X_CR__13_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=3, mask=0xFFFC0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_X_CR__17_14": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=3, mask=0xF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH1_STATE_X_COUNTER": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=3, mask=0x3FFFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_W_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF000000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_W_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_Z_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_Z_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_Y_CR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=2, mask=0x1FFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_Y_COUNTER": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=2, mask=0x1FFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_X_CR__13_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=2, mask=0xFFFC0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_X_CR__17_14": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=2, mask=0xF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[1]_DMA_CNT_CH0_STATE_X_COUNTER": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=2, mask=0x3FFFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_W_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF000000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_W_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_Z_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_Z_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_Y_CR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=1, mask=0x1FFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_Y_COUNTER": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=1, mask=0x1FFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_X_CR__13_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=1, mask=0xFFFC0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_X_CR__17_14": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=1, mask=0xF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH1_STATE_X_COUNTER": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=1, mask=0x3FFFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_W_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF000000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_W_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_Z_CR__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_Z_COUNTER__7_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_Y_CR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=0, mask=0x1FFF0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_Y_COUNTER": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=6, sig_sel=0, mask=0x1FFF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_X_CR__13_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=0, mask=0xFFFC0000
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_X_CR__17_14": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=6, sig_sel=0, mask=0xF
        ),
        "DEBUG_BUS_DEBUG_ISSUE2_IN[0]_DMA_CNT_CH0_STATE_X_COUNTER": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=6, sig_sel=0, mask=0x3FFFF
        ),
        "DEBUG_BUS_SRCA_WREN_RESH_D[7]": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=28, mask=0x1000),
        "DEBUG_BUS_SRCA_WR_DATUM_EN_RESH_D[7]__5_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=28, mask=0xFC000000
        ),
        "DEBUG_BUS_SRCA_WR_DATUM_EN_RESH_D[7]__15_6": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=28, mask=0x3FF
        ),
        "DEBUG_BUS_SRCA_WRADDR_RESH_D[7]": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=28, mask=0x3FFF000),
        "DEBUG_BUS_SRCA_WR_FORMAT_RESH_D[7]": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=28, mask=0xF00),
        "DEBUG_BUS_H2_SFPU_DBG_BUS[7]": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF0000000),
        "DEBUG_BUS_H2_SFPU_DBG_BUS[6]": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF000000),
        "DEBUG_BUS_H2_SFPU_DBG_BUS[5]": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF00000),
        "DEBUG_BUS_H2_SFPU_DBG_BUS[4]": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF0000),
        "DEBUG_BUS_H2_SFPU_DBG_BUS[3]": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF000),
        "DEBUG_BUS_H2_SFPU_DBG_BUS[2]": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF00),
        "DEBUG_BUS_H2_SFPU_DBG_BUS[1]": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF0),
        "DEBUG_BUS_H2_SFPU_DBG_BUS[0]": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_O_PAR_ERR_RISC_LOCALMEM": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x80000000
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_I_MAILBOX_RDEN": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x78000000
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_I_MAILBOX_RD_TYPE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x7800000
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_O_MAILBOX_RD_REQ_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x780000
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_O_MAILBOX_RDVALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x78000
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_O_MAILBOX_RDDATA__6_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x7F00
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_INTF_WRACK_BRISC__10_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=27, mask=0xFFE00000
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_INTF_WRACK_BRISC__16_11": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=27, mask=0x3F
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_DMEM_TENSIX_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=27, mask=0x100000
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_DMEM_TENSIX_WREN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=27, mask=0x80000
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_ICACHE_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=27, mask=0x2
        ),
        "DEBUG_BUS_RISC_WRAPPER_NOC_CTRL_DEBUG_BUS_ICACHE_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=27, mask=0x1
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_O_BUSY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x200000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x100000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x80000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_MSHR_EMPTY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x40000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_MSHR_FULL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x20000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_WAY_HIT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x18000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_MSHR_PF_HIT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x4000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_MSHR_CPU_HIT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x2000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_SOME_MSHR_ALLOCATED": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x1000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_LATCHED_REQ_CPU_VLD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x800
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_CPU_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x400
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_LATCHED_REQ_PF_VLD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x200
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_PF_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x100
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_QUAL_RDEN": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x80
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_I_MISPREDICT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x40
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_O_REQ_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x20
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[2]_O_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x10
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_O_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x10000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x8000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x4000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_MSHR_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x2000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_MSHR_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x1000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_WAY_HIT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0xC00000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_MSHR_PF_HIT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x200000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_MSHR_CPU_HIT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x100000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_SOME_MSHR_ALLOCATED": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x80000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_LATCHED_REQ_CPU_VLD": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x40000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_CPU_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x20000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_LATCHED_REQ_PF_VLD": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x10000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_PF_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x8000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_QUAL_RDEN": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x4000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_I_MISPREDICT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x2000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_O_REQ_READY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x1000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[1]_O_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x800
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_O_BUSY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x8
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x4
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x2
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_MSHR_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x1
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_MSHR_FULL": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x80000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_WAY_HIT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x60000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_MSHR_PF_HIT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x10000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_MSHR_CPU_HIT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x8000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_SOME_MSHR_ALLOCATED": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x4000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_LATCHED_REQ_CPU_VLD": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x2000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_CPU_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x1000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_LATCHED_REQ_PF_VLD": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x800000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_PF_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x400000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_QUAL_RDEN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x200000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_I_MISPREDICT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x100000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_O_REQ_READY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x80000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_TRISC[0]_O_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x40000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_O_BUSY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x400
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x200
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x100
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_MSHR_EMPTY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x80
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_MSHR_FULL": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x40
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_WAY_HIT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x30
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_MSHR_PF_HIT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x8
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_MSHR_CPU_HIT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x4
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_SOME_MSHR_ALLOCATED": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x2
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_LATCHED_REQ_CPU_VLD": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x1
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_CPU_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x80000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_LATCHED_REQ_PF_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x40000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_PF_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x20000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_QUAL_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x10000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_I_MISPREDICT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x8000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_O_REQ_READY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x4000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_O_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x2000000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_O_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x20000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x10000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x8000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_MSHR_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x4000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_MSHR_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x2000
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_WAY_HIT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x1800
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_MSHR_PF_HIT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x400
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_MSHR_CPU_HIT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x200
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_SOME_MSHR_ALLOCATED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x100
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_LATCHED_REQ_CPU_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x80
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_CPU_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x40
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_LATCHED_REQ_PF_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x20
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_PF_REQ_DISPATCHED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x10
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_QUAL_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x8
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_I_MISPREDICT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x4
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_O_REQ_READY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x2
        ),
        "DEBUG_BUS_ICACHE_DEBUG_BUS_BRISCV_NOC_CTRL_O_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x1
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_12_EX_ID_RTR__3305": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x200
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_12_ID_EX_RTS__3304": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_IF_RTS": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x80),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_IF_EX_PREDICTED": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x20
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_IF_EX_DECO__36_32": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_IF_EX_DECO__31_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=25, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_12_ID_EX_RTS__3263": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_12_EX_ID_RTR__3262": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_ID_EX_PC__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_ID_RF_WR_FLAG": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_ID_RF_WRADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x1F00000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_ID_RF_P1_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x40000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_ID_RF_P1_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x7C00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_ID_RF_P0_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_ID_RF_P0_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_I_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_I_INSTRN__30_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_I_INSTRN_REQ_RTR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_(O_INSTRN_REQ_EARLY&~O_INSTRN_REQ_CANCEL)": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_O_INSTRN_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_DBG_OBS_MEM_WREN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_DBG_OBS_MEM_RDEN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_DBG_OBS_MEM_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_DBG_OBS_CMT_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_12_DBG_OBS_CMT_PC__30_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_TRISC_MOP_BUF_EMPTY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_TRISC_MOP_BUF_FULL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x20000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_DEBUG_MATH_LOOP_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x1C000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_DEBUG_UNPACK_LOOP_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_MOP_STAGE_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x400000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_MOP_STAGE_OPCODE__9_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=23, mask=0xFFC00000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_MOP_STAGE_OPCODE__31_10": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3FFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_MATH_LOOP_ACTIVE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x200000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_UNPACK_LOOP_ACTIVE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x100000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_O_INSTRN_VALID": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x80000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_O_INSTRN_OPCODE__12_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFFF80000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_MOP_DECODE_DEBUG_BUS_O_INSTRN_OPCODE__31_13": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x7FFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_SEMPOST_PENDING": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_SEMGET_PENDING": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_TRISC_READ_REQUEST_PENDING": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_TRISC_SYNC_ACTIVATED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_TRISC_SYNC_TYPE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x20000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_RISCV_SYNC_ACTIVATED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_PC_BUFFER_IDLE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x8000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_I_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x4000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_I_MOPS_OUTSTANDING": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x2000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_CMD_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x1000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_CMD_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_NEXT_CMD_FIFO_DATA__8_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=22, mask=0xFF800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_PC_BUFFER_DEBUG_BUS_NEXT_CMD_FIFO_DATA__31_9": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x7FFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_O_PAR_ERR_RISC_LOCALMEM": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x400000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_I_MAILBOX_RDEN": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_I_MAILBOX_RD_TYPE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RD_REQ_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDVALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C0
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDDATA__15_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=22, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDDATA__21_16": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_INTF_WRACK_TRISC__12_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x3FFE0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_DMEM_TENSIX_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x10000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_DMEM_TENSIX_WREN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x8000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_ICACHE_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x2
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_11_RISC_WRAPPER_DEBUG_BUS_TRISC_ICACHE_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x1
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_TRISC_MOP_BUF_EMPTY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_TRISC_MOP_BUF_FULL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x20000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_DEBUG_MATH_LOOP_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x1C000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_DEBUG_UNPACK_LOOP_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_MOP_STAGE_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x400000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_MOP_STAGE_OPCODE__9_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=21, mask=0xFFC00000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_MOP_STAGE_OPCODE__31_10": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3FFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_MATH_LOOP_ACTIVE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x200000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_UNPACK_LOOP_ACTIVE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x100000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_O_INSTRN_VALID": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x80000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_O_INSTRN_OPCODE__12_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFFF80000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_MOP_DECODE_DEBUG_BUS_O_INSTRN_OPCODE__31_13": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x7FFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_SEMPOST_PENDING": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_SEMGET_PENDING": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_TRISC_READ_REQUEST_PENDING": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_TRISC_SYNC_ACTIVATED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_TRISC_SYNC_TYPE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x20000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_RISCV_SYNC_ACTIVATED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_PC_BUFFER_IDLE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x8000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_I_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x4000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_I_MOPS_OUTSTANDING": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x2000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_CMD_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x1000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_CMD_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_NEXT_CMD_FIFO_DATA__8_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=20, mask=0xFF800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_PC_BUFFER_DEBUG_BUS_NEXT_CMD_FIFO_DATA__31_9": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x7FFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_O_PAR_ERR_RISC_LOCALMEM": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x400000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_I_MAILBOX_RDEN": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_I_MAILBOX_RD_TYPE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RD_REQ_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDVALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C0
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDDATA__15_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=20, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDDATA__21_16": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_INTF_WRACK_TRISC__12_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x3FFE0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_DMEM_TENSIX_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x10000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_DMEM_TENSIX_WREN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x8000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_ICACHE_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x2
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_10_RISC_WRAPPER_DEBUG_BUS_TRISC_ICACHE_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x1
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_TRISC_MOP_BUF_EMPTY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_TRISC_MOP_BUF_FULL": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x20000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_DEBUG_MATH_LOOP_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x1C000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_DEBUG_UNPACK_LOOP_STATE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_MOP_STAGE_VALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x400000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_MOP_STAGE_OPCODE__9_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=19, mask=0xFFC00000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_MOP_STAGE_OPCODE__31_10": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3FFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_MATH_LOOP_ACTIVE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x200000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_UNPACK_LOOP_ACTIVE": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x100000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_O_INSTRN_VALID": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x80000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_O_INSTRN_OPCODE__12_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFFF80000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_O_INSTRN_OPCODE__31_13": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x7FFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_SEMPOST_PENDING": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFF00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_SEMGET_PENDING": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_TRISC_READ_REQUEST_PENDING": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_TRISC_SYNC_ACTIVATED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_TRISC_SYNC_TYPE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x20000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_RISCV_SYNC_ACTIVATED": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_PC_BUFFER_IDLE": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x8000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_I_BUSY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x4000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_I_MOPS_OUTSTANDING": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x2000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_CMD_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_CMD_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_NEXT_CMD_FIFO_DATA__8_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=18, mask=0xFF800000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_NEXT_CMD_FIFO_DATA__31_9": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x7FFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_PAR_ERR_RISC_LOCALMEM": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x400000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_I_MAILBOX_RDEN": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_I_MAILBOX_RD_TYPE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RD_REQ_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDVALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C0
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDDATA__15_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=18, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDDATA__21_16": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_INTF_WRACK_TRISC__12_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x3FFE0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_DMEM_TENSIX_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x10000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_DMEM_TENSIX_WREN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x8000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_ICACHE_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x2
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_ICACHE_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x1
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_8_EX_ID_RTR__2281": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x200
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_8_ID_EX_RTS__2280": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_IF_RTS": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x80),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_IF_EX_PREDICTED": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x20
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_IF_EX_DECO__36_32": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_IF_EX_DECO__31_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=17, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_8_ID_EX_RTS__2239": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_8_EX_ID_RTR__2238": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_ID_EX_PC__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_ID_RF_WR_FLAG": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_ID_RF_WRADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x1F00000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_ID_RF_P1_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x40000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_ID_RF_P1_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x7C00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_ID_RF_P0_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_ID_RF_P0_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_I_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=16, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_I_INSTRN__30_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=16, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_I_INSTRN_REQ_RTR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_(O_INSTRN_REQ_EARLY&~O_INSTRN_REQ_CANCEL)": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_O_INSTRN_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_DBG_OBS_MEM_WREN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_DBG_OBS_MEM_RDEN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_DBG_OBS_MEM_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_DBG_OBS_CMT_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=16, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_8_DBG_OBS_CMT_PC__30_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=16, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_7_EX_ID_RTR__2025": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x200
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_7_ID_EX_RTS__2024": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_IF_RTS": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x80),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_IF_EX_PREDICTED": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x20
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_IF_EX_DECO__36_32": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_IF_EX_DECO__31_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=15, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_7_ID_EX_RTS__1983": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_7_EX_ID_RTR__1982": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_ID_EX_PC__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_ID_RF_WR_FLAG": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_ID_RF_WRADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x1F00000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_ID_RF_P1_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x40000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_ID_RF_P1_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x7C00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_ID_RF_P0_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_ID_RF_P0_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_I_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=14, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_I_INSTRN__30_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=14, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_I_INSTRN_REQ_RTR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_(O_INSTRN_REQ_EARLY&~O_INSTRN_REQ_CANCEL)": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_O_INSTRN_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_DBG_OBS_MEM_WREN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_DBG_OBS_MEM_RDEN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_DBG_OBS_MEM_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_DBG_OBS_CMT_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=14, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_7_DBG_OBS_CMT_PC__30_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=14, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_6_EX_ID_RTR__1769": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x200
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_6_ID_EX_RTS__1768": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_IF_RTS": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x80),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_IF_EX_PREDICTED": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x20
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_IF_EX_DECO__36_32": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_IF_EX_DECO__31_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=13, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_6_ID_EX_RTS__1727": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_6_EX_ID_RTR__1726": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_EX_PC__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_WR_FLAG": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_WRADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F00000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_P1_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x40000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_P1_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x7C00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_P0_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_P0_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_I_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_I_INSTRN__30_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_I_INSTRN_REQ_RTR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_(O_INSTRN_REQ_EARLY&~O_INSTRN_REQ_CANCEL)": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_O_INSTRN_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_MEM_WREN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_MEM_RDEN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_MEM_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_CMT_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_CMT_PC__30_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_5_EX_ID_RTR__1513": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x200
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_5_ID_EX_RTS__1512": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_IF_RTS": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x80),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_IF_EX_PREDICTED": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x20
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_IF_EX_DECO__36_32": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_IF_EX_DECO__31_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=11, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_5_ID_EX_RTS__1471": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_5_EX_ID_RTR__1470": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_EX_PC__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_WR_FLAG": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x10000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_WRADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F00000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_P1_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x40000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_P1_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x7C00
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_P0_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x100
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_P0_RDADDR": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_I_INSTRN_VLD": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_I_INSTRN__30_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_I_INSTRN_REQ_RTR": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_(O_INSTRN_REQ_EARLY&~O_INSTRN_REQ_CANCEL)": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_O_INSTRN_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_MEM_WREN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_MEM_RDEN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x40000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_MEM_ADDR__29_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_CMT_VLD": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x80000000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_CMT_PC__30_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_4_PERF_CNT_L1_DBG_STALL_CNT__1248": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=9, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_4_PERF_CNT_L1_DBG_GRANT_CNT__1216": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=9, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_4_PERF_CNT_L1_DBG_REQ_CNT__1184": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=9, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_4_PERF_CNT_L1_DBG_REF_CNT__1152": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=9, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_4_PERF_CNT_L1_DBG_STALL_CNT__1120": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_4_PERF_CNT_L1_DBG_GRANT_CNT__1088": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_4_PERF_CNT_L1_DBG_REQ_CNT__1056": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_4_PERF_CNT_L1_DBG_REF_CNT__1024": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=8, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_3_PERF_CNT_L1_DBG_STALL_CNT__992": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_3_PERF_CNT_L1_DBG_GRANT_CNT__960": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_3_PERF_CNT_L1_DBG_REQ_CNT__928": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_3_PERF_CNT_L1_DBG_REF_CNT__896": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=7, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_3_PERF_CNT_L1_DBG_STALL_CNT__864": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_3_PERF_CNT_L1_DBG_GRANT_CNT__832": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_3_PERF_CNT_L1_DBG_REQ_CNT__800": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_3_PERF_CNT_L1_DBG_REF_CNT__768": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=6, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_2_PERF_CNT_L1_DBG_STALL_CNT__736": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_2_PERF_CNT_L1_DBG_GRANT_CNT__704": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_2_PERF_CNT_L1_DBG_REQ_CNT__672": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_2_PERF_CNT_L1_DBG_REF_CNT__640": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_2_PERF_CNT_L1_DBG_STALL_CNT__608": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_2_PERF_CNT_L1_DBG_GRANT_CNT__576": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_2_PERF_CNT_L1_DBG_REQ_CNT__544": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_2_PERF_CNT_L1_DBG_REF_CNT__512": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=4, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_1_PERF_CNT_L1_DBG_STALL_CNT__480": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_1_PERF_CNT_L1_DBG_GRANT_CNT__448": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_1_PERF_CNT_L1_DBG_REQ_CNT__416": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_1_PERF_CNT_L1_DBG_REF_CNT__384": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=3, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_1_PERF_CNT_L1_DBG_STALL_CNT__352": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_1_PERF_CNT_L1_DBG_GRANT_CNT__320": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_1_PERF_CNT_L1_DBG_REQ_CNT__288": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_1_PERF_CNT_L1_DBG_REF_CNT__256": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=2, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_O_PAR_ERR_RISC_LOCALMEM": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x80000000
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_I_MAILBOX_RDEN": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x78000000
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_I_MAILBOX_RD_TYPE": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x7800000
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_O_MAILBOX_RD_REQ_READY": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x780000
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_O_MAILBOX_RDVALID": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x78000
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_O_MAILBOX_RDDATA__6_0": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x7F00
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_INTF_WRACK_BRISC__10_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=1, mask=0xFFE00000
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_INTF_WRACK_BRISC__16_11": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=1, mask=0x3F
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_DMEM_TENSIX_RDEN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x100000
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_DMEM_TENSIX_WREN": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x80000
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_ICACHE_REQ_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x2
        ),
        "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_ICACHE_REQ_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x1
        ),
        "DEBUG_BUS_PERF_CNT_FPU_DBG_0_STALL_CNT": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_FPU_DBG_0_GRANT_CNT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_FPU_DBG_0_REQ_CNT": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PERF_CNT_FPU_DBG_0_REF_CNT": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_L1_ADDR_P41__14_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=13, mask=0xFFFE0000),
        "DEBUG_BUS_L1_ADDR_P41__16_15": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=13, mask=0x3),
        "DEBUG_BUS_L1_ADDR_P40": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=13, mask=0x1FFFF),
        "DEBUG_BUS_L1_ADDR_P39": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=13, mask=0xFFFF8000),
        "DEBUG_BUS_L1_ADDR_P38__16_2": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=13, mask=0x7FFF),
        "DEBUG_BUS_L1_ADDR_P38__1_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=11, mask=0xC0000000),
        "DEBUG_BUS_L1_ADDR_P37": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=11, mask=0x3FFFE000),
        "DEBUG_BUS_L1_ADDR_P36__3_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=11, mask=0xF0000000),
        "DEBUG_BUS_L1_ADDR_P36__16_4": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=11, mask=0x1FFF),
        "DEBUG_BUS_L1_ADDR_P35": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=11, mask=0xFFFF800),
        "DEBUG_BUS_L1_ADDR_P34__5_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=11, mask=0xFC000000),
        "DEBUG_BUS_L1_ADDR_P34__16_6": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=11, mask=0x7FF),
        "DEBUG_BUS_L1_ADDR_P33": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=11, mask=0x3FFFE00),
        "DEBUG_BUS_L1_ADDR_P32__7_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=11, mask=0xFF000000),
        "DEBUG_BUS_L1_ADDR_P32__16_8": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=11, mask=0x1FF),
        "DEBUG_BUS_L1_ADDR_P31": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=11, mask=0xFFFF80),
        "DEBUG_BUS_L1_ADDR_P30__9_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=10, mask=0xFFC00000),
        "DEBUG_BUS_L1_ADDR_P30__16_10": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=11, mask=0x7F),
        "DEBUG_BUS_L1_ADDR_P29": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=10, mask=0x3FFFE0),
        "DEBUG_BUS_L1_ADDR_P28__11_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=10, mask=0xFFF00000),
        "DEBUG_BUS_L1_ADDR_P28__16_12": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=10, mask=0x1F),
        "DEBUG_BUS_L1_ADDR_P27": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=10, mask=0xFFFF8),
        "DEBUG_BUS_L1_ADDR_P26__13_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=10, mask=0xFFFC0000),
        "DEBUG_BUS_L1_ADDR_P26__16_14": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=10, mask=0x7),
        "DEBUG_BUS_L1_ADDR_P25": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=10, mask=0x3FFFE),
        "DEBUG_BUS_L1_ADDR_P24__15_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=10, mask=0xFFFF0000),
        "DEBUG_BUS_L1_ADDR_P24__16_16": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=10, mask=0x1),
        "DEBUG_BUS_L1_ADDR_P23__16_1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=10, mask=0xFFFF),
        "DEBUG_BUS_L1_ADDR_P23__0_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=9, mask=0x80000000),
        "DEBUG_BUS_L1_ADDR_P22": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=9, mask=0x7FFFC000),
        "DEBUG_BUS_L1_ADDR_P21__2_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=9, mask=0xE0000000),
        "DEBUG_BUS_L1_ADDR_P21__16_3": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=9, mask=0x3FFF),
        "DEBUG_BUS_L1_ADDR_P20": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=9, mask=0x1FFFF000),
        "DEBUG_BUS_L1_ADDR_P19__4_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=9, mask=0xF8000000),
        "DEBUG_BUS_L1_ADDR_P19__16_5": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=9, mask=0xFFF),
        "DEBUG_BUS_L1_ADDR_P18": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=9, mask=0x7FFFC00),
        "DEBUG_BUS_L1_ADDR_P17__6_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=9, mask=0xFE000000),
        "DEBUG_BUS_L1_ADDR_P17__16_7": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=9, mask=0x3FF),
        "DEBUG_BUS_L1_ADDR_P16": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=9, mask=0x1FFFF00),
        "DEBUG_BUS_L1_ADDR_P15__8_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=8, mask=0xFF800000),
        "DEBUG_BUS_L1_ADDR_P15__16_9": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=9, mask=0xFF),
        "DEBUG_BUS_L1_ADDR_P14": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=8, mask=0x7FFFC0),
        "DEBUG_BUS_L1_ADDR_P13__10_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=8, mask=0xFFE00000),
        "DEBUG_BUS_L1_ADDR_P13__16_11": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=8, mask=0x3F),
        "DEBUG_BUS_L1_ADDR_P12": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=8, mask=0x1FFFF0),
        "DEBUG_BUS_L1_ADDR_P11__12_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=8, mask=0xFFF80000),
        "DEBUG_BUS_L1_ADDR_P11__16_13": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=8, mask=0xF),
        "DEBUG_BUS_L1_ADDR_P10": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=8, mask=0x7FFFC),
        "DEBUG_BUS_L1_ADDR_P9__14_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=8, mask=0xFFFE0000),
        "DEBUG_BUS_L1_ADDR_P9__16_15": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=8, mask=0x3),
        "DEBUG_BUS_L1_ADDR_P8": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=8, mask=0x1FFFF),
        "DEBUG_BUS_L1_ADDR_P7__10_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=7, mask=0xFFE00000),
        "DEBUG_BUS_L1_ADDR_P6": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=7, mask=0x1FFFF0),
        "DEBUG_BUS_L1_ADDR_P5__12_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=7, mask=0xFFF80000),
        "DEBUG_BUS_L1_ADDR_P5__16_13": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=7, mask=0xF),
        "DEBUG_BUS_L1_ADDR_P4": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=7, mask=0x7FFFC),
        "DEBUG_BUS_L1_ADDR_P3__14_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=7, mask=0xFFFE0000),
        "DEBUG_BUS_L1_ADDR_P3__16_15": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=7, mask=0x3),
        "DEBUG_BUS_L1_ADDR_P2": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=7, mask=0x1FFFF),
        "DEBUG_BUS_L1_ADDR_P1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=7, mask=0xFFFF8000),
        "DEBUG_BUS_L1_ADDR_P0__1_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=6, mask=0xC0000000),
        "DEBUG_BUS_L1_ADDR_P0__16_2": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=7, mask=0x7FFF),
        "DEBUG_BUS_T_L1_REQIF_READY__11_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=6, mask=0xFFF00000
        ),
        "DEBUG_BUS_T_L1_REQIF_READY__41_12": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=6, mask=0x3FFFFFFF
        ),
        "DEBUG_BUS_T_L1_RDEN__21_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=6, mask=0xFFFFFC00),
        "DEBUG_BUS_T_L1_RDEN__41_22": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=6, mask=0xFFFFF),
        "DEBUG_BUS_T_L1_WREN__31_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=6, mask=0xFFFFFFFF),
        "DEBUG_BUS_T_L1_WREN__41_32": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=6, mask=0x3FF),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P9": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=5, mask=0xFFFF0000
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P8": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=5, mask=0xFFFF
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P7": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=4, mask=0xFFFF0000
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P6": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=4, mask=0xFFFF
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P5": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=4, mask=0xFFFF0000
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P4": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=4, mask=0xFFFF
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P3": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=4, mask=0xFFFF0000
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P2": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=4, mask=0xFFFF
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P1": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=4, mask=0xFFFF0000
        ),
        "DEBUG_BUS_T_L1_AT_INSTRN_L1_AT_INSTRN_P0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=4, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P15": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=3, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P14": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=3, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P13": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=3, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P12": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=3, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P11": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=3, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P10": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=3, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P9": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=3, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P8": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=3, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P7": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=2, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P6": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=2, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P5": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=2, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P4": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=2, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P3": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=2, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P2": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=2, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P1": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=2, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_1_L1_AT_INSTRN_P0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=2, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P15": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=1, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P14": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=1, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P13": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=1, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P12": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=1, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P11": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=1, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P10": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=1, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P9": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=1, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P8": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=1, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P7": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=0, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P6": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=8, sig_sel=0, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P5": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=0, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P4": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=8, sig_sel=0, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P3": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=0, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P2": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=8, sig_sel=0, mask=0xFFFF
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P1": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=0, mask=0xFFFF0000
        ),
        "DEBUG_BUS_DEBUG_TENSIX_W_L1_IN_0_L1_AT_INSTRN_P0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=8, sig_sel=0, mask=0xFFFF
        ),
        "DEBUG_BUS_O_EXP_SECTION_SIZE__11_0": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=10, sig_sel=3, mask=0xFFF00000
        ),
        "DEBUG_BUS_O_EXP_SECTION_SIZE__31_12": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=10, sig_sel=3, mask=0xFFFFF
        ),
        "DEBUG_BUS_O_ROWSTART_SECTION_SIZE__11_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=10, sig_sel=3, mask=0xFFF00000
        ),
        "DEBUG_BUS_O_ROWSTART_SECTION_SIZE__31_12": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=10, sig_sel=3, mask=0xFFFFF
        ),
        "DEBUG_BUS_O_ADD_L1_DESTINATION_ADDR_OFFSET__3_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=10, sig_sel=2, mask=0xF
        ),
        "DEBUG_BUS_DEBUG_IN_THCON_INSTRN": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=10, sig_sel=0, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_O_FIRST_DATUM_PREFIX_ZEROS": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=11, sig_sel=2, mask=0x1FFFE
        ),
        "DEBUG_BUS_O_START_DATUM_INDEX__14_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=11, sig_sel=2, mask=0xFFFE0000
        ),
        "DEBUG_BUS_O_START_DATUM_INDEX__15_15": DebugBusSignalDescription(rd_sel=2, daisy_sel=11, sig_sel=2, mask=0x1),
        "DEBUG_BUS_O_END_DATUM_INDEX": DebugBusSignalDescription(rd_sel=1, daisy_sel=11, sig_sel=2, mask=0x1FFFE),
        "DEBUG_BUS_O_FIRST_DATA_SKIP_ONE_PHASE__2_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=11, sig_sel=2, mask=0xE0000000
        ),
        "DEBUG_BUS_O_FIRST_DATA_SKIP_ONE_PHASE__3_3": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=11, sig_sel=2, mask=0x1
        ),
        "DEBUG_BUS_X_START_D": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0x1FFF0000),
        "DEBUG_BUS_X_END_D": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0xFFF8),
        "DEBUG_BUS_UNPACK_SEL_D": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0x4),
        "DEBUG_BUS_THREAD_ID_D": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0x3),
        "DEBUG_BUS_UNP0_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_DEMUX_FIFO_EMPTY__2_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=12, sig_sel=1, mask=0xE0000000
        ),
        "DEBUG_BUS_UNP0_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_DEMUX_FIFO_FULL__2_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=12, sig_sel=1, mask=0x1C000000
        ),
        "DEBUG_BUS_UNP0_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_&DEMUX_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=12, sig_sel=1, mask=0x2000000
        ),
        "DEBUG_BUS_UNP0_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_|DEMUX_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=12, sig_sel=1, mask=0x10000000
        ),
        "DEBUG_BUS_UNP0_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_REQ_PARAM_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=12, sig_sel=0, mask=0x80000000
        ),
        "DEBUG_BUS_UNP0_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_REQ_PARAM_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=12, sig_sel=0, mask=0x40000000
        ),
        "DEBUG_BUS_UNP0_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_PARAM_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=12, sig_sel=0, mask=0x20000000
        ),
        "DEBUG_BUS_UNP0_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_PARAM_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=12, sig_sel=0, mask=0x10000000
        ),
        "DEBUG_BUS_UNP1_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_DEMUX_FIFO_EMPTY__2_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=13, sig_sel=1, mask=0xE0000000
        ),
        "DEBUG_BUS_UNP1_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_DEMUX_FIFO_FULL__2_0": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=13, sig_sel=1, mask=0x1C000000
        ),
        "DEBUG_BUS_UNP1_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_&DEMUX_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=13, sig_sel=1, mask=0x2000000
        ),
        "DEBUG_BUS_UNP1_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_|DEMUX_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=13, sig_sel=1, mask=0x10000000
        ),
        "DEBUG_BUS_UNP1_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_REQ_PARAM_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=13, sig_sel=0, mask=0x80000000
        ),
        "DEBUG_BUS_UNP1_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_REQ_PARAM_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=13, sig_sel=0, mask=0x40000000
        ),
        "DEBUG_BUS_UNP1_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_PARAM_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=13, sig_sel=0, mask=0x20000000
        ),
        "DEBUG_BUS_UNP1_DEBUG_DAISY_STOP_DEBUG_IN_UNPACK_0_PARAM_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=1, daisy_sel=13, sig_sel=0, mask=0x10000000
        ),
        "DEBUG_BUS_O_TDMA_PACKER_Z_POS__15_0": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=14, sig_sel=6, mask=0xFFFF0000
        ),
        "DEBUG_BUS_O_TDMA_PACKER_Z_POS__23_16": DebugBusSignalDescription(rd_sel=1, daisy_sel=14, sig_sel=6, mask=0xFF),
        "DEBUG_BUS_O_TDMA_PACKER_Y_POS": DebugBusSignalDescription(rd_sel=0, daisy_sel=14, sig_sel=6, mask=0xFFFF),
        "DEBUG_BUS_PACKED_EXPS_P5__29_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=14, sig_sel=5, mask=0xFFFFFFFC),
        "DEBUG_BUS_PACKED_EXPS_P5__61_30": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PACKED_DATA_P5__27_0": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0xFFFFFFF0),
        "DEBUG_BUS_PACKED_DATA_P5__59_28": DebugBusSignalDescription(
            rd_sel=0, daisy_sel=14, sig_sel=5, mask=0xFFFFFFFF
        ),
        "DEBUG_BUS_PACKED_DATA_P5__61_60": DebugBusSignalDescription(rd_sel=1, daisy_sel=14, sig_sel=5, mask=0x3),
        "DEBUG_BUS_DRAM_DATA_FIFO_RDEN": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0x8),
        "DEBUG_BUS_DRAM_RDEN": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0x4),
        "DEBUG_BUS_DRAM_DATA_FIFO_RDEN_P2": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0x2),
        "DEBUG_BUS_DRAM_RDDATA_PHASE_ADJ_ASMBLD_ANY_VALID_P2": DebugBusSignalDescription(
            rd_sel=3, daisy_sel=14, sig_sel=4, mask=0x1
        ),
        "DEBUG_BUS_PIPE_DATA_CLKEN_P2": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x80000000),
        "DEBUG_BUS_PIPE_CLKEN_P2": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x40000000),
        "DEBUG_BUS_PIPE_CLKEN_P3": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x20000000),
        "DEBUG_BUS_PIPE_BUSY_P3": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x10000000),
        "DEBUG_BUS_PIPE_CLKEN_P4": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x8000000),
        "DEBUG_BUS_PIPE_BUSY_P4": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x4000000),
        "DEBUG_BUS_PIPE_BUSY_P5": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x2000000),
        "DEBUG_BUS_PIPE_BUSY_P6": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x1000000),
        "DEBUG_BUS_PIPE_BUSY_P6P7": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x800000),
        "DEBUG_BUS_PIPE_BUSY_P8": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x400000),
        "DEBUG_BUS_IN_PARAM_FIFO_EMPTY": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x200000),
        "DEBUG_BUS_FMT_BW_EXPAND_IN_PARAM_FIFO_EMPTY_P1": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x100000
        ),
        "DEBUG_BUS_&L1_REQ_FIFO_EMPTY": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x80000),
        "DEBUG_BUS_DRAM_REQ_FIFO_EMPTY": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x40000),
        "DEBUG_BUS_&L1_TO_L1_PACK_RESP_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x20000
        ),
        "DEBUG_BUS_&L1_TO_L1_PACK_RESP_DEMUX_FIFO_EMPTY": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x10000
        ),
        "DEBUG_BUS_|REQUESTER_BUSY": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x8000),
        "DEBUG_BUS_STALL_ON_TILE_END_DRAIN_Q": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x4000
        ),
        "DEBUG_BUS_STALL_ON_TILE_END_DRAIN_NXT": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x2000
        ),
        "DEBUG_BUS_LAST_ROW_END_VALID": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x1000),
        "DEBUG_BUS_SET_LAST_ROW_END_VALID": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x800),
        "DEBUG_BUS_DATA_CONV_BUSY_C0": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x400),
        "DEBUG_BUS_DATA_CONV_BUSY_C1": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x200),
        "DEBUG_BUS_IN_PARAM_FIFO_FULL": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x100),
        "DEBUG_BUS_FMT_BW_EXPAND_IN_PARAM_FIFO_FULL_P1": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x80
        ),
        "DEBUG_BUS_|L1_REQ_FIFO_FULL": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x40),
        "DEBUG_BUS_DRAM_REQ_FIFO_FULL": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x20),
        "DEBUG_BUS_|L1_TO_L1_PACK_RESP_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x10
        ),
        "DEBUG_BUS_|L1_TO_L1_PACK_RESP_DEMUX_FIFO_FULL": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x8
        ),
        "DEBUG_BUS_REG_FIFO_EMPTY": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x4),
        "DEBUG_BUS_REG_FIFO_FULL": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x2),
        "DEBUG_BUS_PARAM_FIFO_FLUSH_WA_BUFFERS_VLD_P2": DebugBusSignalDescription(
            rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x1
        ),
    }

    @cache
    def get_block(self, location):
        block_type = self.get_block_type(location)
        if block_type == "arc":
            return BlackholeArcBlock(location)
        elif block_type == "dram":
            return BlackholeDramBlock(location)
        elif block_type == "eth":
            return BlackholeEthBlock(location)
        elif block_type == "functional_workers":
            return BlackholeFunctionalWorkerBlock(location)
        elif block_type == "harvested_workers":
            return BlackholeHarvestedWorkerBlock(location)
        elif block_type == "l2cpu":
            return BlackholeL2cpuBlock(location)
        elif block_type == "pcie":
            return BlackholePcieBlock(location)
        elif block_type == "router_only":
            return BlackholeRouterOnlyBlock(location)
        elif block_type == "security":
            return BlackholeSecurityBlock(location)
        raise ValueError(f"Unsupported block type: {block_type}")

    def get_alu_config(self) -> List[dict]:
        return [
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
        ]

    # UNPACKER GETTERS

    def get_unpack_tile_descriptor(self) -> List[dict]:
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

        return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(self.NUM_UNPACKERS)]

    def get_unpack_config(self) -> List[dict]:
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

        return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(self.NUM_UNPACKERS)]

    def get_pack_config(self) -> List[dict]:
        struct_name = "PACK_CONFIG"

        fields = [
            "row_ptr_section_size",
            "exp_section_size",
            "l1_dest_addr",
            "uncompress",
            "add_l1_dest_addr_offset",
            "disable_pack_zero_flag",
            "reserved_0",
            "out_data_format",
            "in_data_format",
            "dis_shared_exp_assembler",
            "auto_set_last_pacr_intf_sel",
            "enable_out_fifo",
            "sub_l1_tile_header_size",
            "src_if_sel",
            "pack_start_intf_pos",
            "all_pack_disable_zero_compress_ovrd",
            "add_tile_header_size",
            "pack_dis_y_pos_start_offset",
            "l1_src_addr",
        ]

        return [{field: f"{struct_name}{i}{j}_{field}" for field in fields} for i in [0] for j in [1]]

    def get_relu_config(self) -> List[dict]:

        return [
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
        ]

    def get_pack_dest_rd_ctrl(self) -> List[dict]:
        return [
            {
                "read_32b_data": "PACK_DEST_RD_CTRL_Read_32b_data",
                "read_unsigned": "PACK_DEST_RD_CTRL_Read_unsigned",
                "read_int8": "PACK_DEST_RD_CTRL_Read_int8",
                "round_10b_mant": "PACK_DEST_RD_CTRL_Round_10b_mant",
                "reserved": "PACK_DEST_RD_CTRL_Reserved",
            }
        ]

    def get_pack_edge_offset(self) -> List[dict]:
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
            {field: f"{struct_name}{i}_{field}" for field in (fields if i == 0 else fields[:1])}
            for i in range(self.NUM_PACKERS)
        ]

    def get_pack_counters(self) -> List[dict]:
        struct_name = "PACK_COUNTERS"
        fields = [
            "pack_per_xy_plane",
            "pack_reads_per_xy_plane",
            "pack_xys_per_til",
            "pack_yz_transposed",
            "pack_per_xy_plane_offset",
        ]

        return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(self.NUM_PACKERS)]

    def get_pack_strides(self) -> List[dict]:
        struct_name = "PACK_STRIDES"
        fields = ["x_stride", "y_stride", "z_stride", "w_stride"]

        return [{field: f"{struct_name}{i}_{field}" for field in fields} for i in range(2)]
