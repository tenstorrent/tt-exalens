# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from functools import cache
from ttexalens.hardware.blackhole.arc_block import BlackholeArcBlock
from ttexalens.hardware.blackhole.dram_block import BlackholeDramBlock
from ttexalens.hardware.blackhole.eth_block import BlackholeEthBlock
from ttexalens.hardware.blackhole.functional_worker_registers import configuration_registers_descriptions
from ttexalens.hardware.blackhole.functional_worker_block import BlackholeFunctionalWorkerBlock
from ttexalens.hardware.blackhole.harvested_worker_block import BlackholeHarvestedWorkerBlock
from ttexalens.hardware.blackhole.l2cpu_block import BlackholeL2cpuBlock
from ttexalens.hardware.blackhole.pcie_block import BlackholePcieBlock
from ttexalens.hardware.blackhole.router_only_block import BlackholeRouterOnlyBlock
from ttexalens.hardware.blackhole.security_block import BlackholeSecurityBlock
from ttexalens.hardware.tensix_configuration_registers_description import TensixConfigurationRegistersDescription
import ttexalens.util as util
from ttexalens.debug_tensix import TensixDebug
from ttexalens.util import DATA_TYPE
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
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)

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

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )
        self.instructions = BlackholeInstructions()

    def _get_tensix_register_map_keys(self) -> list[str]:
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

    def _get_arc_telemetry_tags_map_keys(self) -> list[str]:
        """Returns the keys of the ARC telemetry tags map."""
        return list(BlackholeDevice.__arc_telemetry_tags_map.keys())

    def _get_arc_telemetry_tag_id(self, tag_name) -> int | None:
        """Returns the telemetry tag ID for a given tag name."""
        if tag_name in BlackholeDevice.__arc_telemetry_tags_map:
            return BlackholeDevice.__arc_telemetry_tags_map[tag_name]
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

    __arc_telemetry_tags_map = {
        "TAG_BOARD_ID_HIGH": 1,
        "TAG_BOARD_ID_LOW": 2,
        "TAG_ASIC_ID": 3,
        "TAG_HARVESTING_STATE": 4,
        "TAG_UPDATE_TELEM_SPEED": 5,
        "TAG_VCORE": 6,
        "TAG_TDP": 7,
        "TAG_TDC": 8,
        "TAG_VDD_LIMITS": 9,
        "TAG_THM_LIMIT_SHUTDOWN": 10,
        "TAG_THM_LIMITS": 10,  # Same as TAG_THM_LIMIT_SHUTDOWN
        "TAG_ASIC_TEMPERATURE": 11,
        "TAG_VREG_TEMPERATURE": 12,
        "TAG_BOARD_TEMPERATURE": 13,
        "TAG_AICLK": 14,
        "TAG_AXICLK": 15,
        "TAG_ARCCLK": 16,
        "TAG_L2CPUCLK0": 17,
        "TAG_L2CPUCLK1": 18,
        "TAG_L2CPUCLK2": 19,
        "TAG_L2CPUCLK3": 20,
        "TAG_ETH_LIVE_STATUS": 21,
        "TAG_GDDR_STATUS": 22,
        "TAG_GDDR_SPEED": 23,
        "TAG_ETH_FW_VERSION": 24,
        "TAG_GDDR_FW_VERSION": 25,
        "TAG_BM_APP_FW_VERSION": 26,
        "TAG_BM_BL_FW_VERSION": 27,
        "TAG_FLASH_BUNDLE_VERSION": 28,
        "TAG_CM_FW_VERSION": 29,
        "TAG_L2CPU_FW_VERSION": 30,
        "TAG_FAN_SPEED": 31,
        "TAG_TIMER_HEARTBEAT": 32,
        "TAG_TELEM_ENUM_COUNT": 33,
        "TAG_ENABLED_TENSIX_COL": 34,
        "TAG_ENABLED_ETH": 35,
        "TAG_ENABLED_GDDR": 36,
        "TAG_ENABLED_L2CPU": 37,
        "TAG_PCIE_USAGE": 38,
        "TAG_INPUT_CURRENT": 39,
        "TAG_NOC_TRANSLATION": 40,
        "TAG_FAN_RPM": 41,
        "TAG_GDDR_0_1_TEMP": 42,
        "TAG_GDDR_2_3_TEMP": 43,
        "TAG_GDDR_4_5_TEMP": 44,
        "TAG_GDDR_6_7_TEMP": 45,
        "TAG_GDDR_0_1_CORR_ERRS": 46,
        "TAG_GDDR_2_3_CORR_ERRS": 47,
        "TAG_GDDR_4_5_CORR_ERRS": 48,
        "TAG_GDDR_6_7_CORR_ERRS": 49,
        "TAG_GDDR_UNCORR_ERRS": 50,
        "TAG_MAX_GDDR_TEMP": 51,
        "TAG_ASIC_LOCATION": 52,
        "TAG_AICLK_LIMIT_MAX": 53,
        "TAG_TDP_LIMIT_MAX": 54,
        "TAG_TDC_LIMIT_MAX": 55,
        "TAG_THM_LIMIT_THROTTLE": 56,
        "TAG_FW_BUILD_DATE": 57,
        "TAG_TT_FLASH_VERSION": 58,
        "TAG_ENABLED_TENSIX_ROW": 59,
        "TAG_THERM_TRIP_COUNT": 61,
        "TAG_ASIC_ID_HIGH": 62,
        "TAG_ASIC_ID_LOW": 63,
    }

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

    def get_tensix_configuration_registers_description(self) -> TensixConfigurationRegistersDescription:
        return configuration_registers_descriptions
