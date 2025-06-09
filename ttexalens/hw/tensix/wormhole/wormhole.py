# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from functools import cache
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.tensix_configuration_registers_description import TensixConfigurationRegistersDescription
from ttexalens.hardware.wormhole.arc_block import WormholeArcBlock
from ttexalens.hardware.wormhole.dram_block import WormholeDramBlock
from ttexalens.hardware.wormhole.eth_block import WormholeEthBlock
from ttexalens.hardware.wormhole.functional_worker_registers import configuration_registers_descriptions
from ttexalens.hardware.wormhole.functional_worker_block import WormholeFunctionalWorkerBlock
from ttexalens.hardware.wormhole.harvested_worker_block import WormholeHarvestedWorkerBlock
from ttexalens.hardware.wormhole.pcie_block import WormholePcieBlock
from ttexalens.hardware.wormhole.router_only_block import WormholeRouterOnlyBlock
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


class WormholeInstructions(TensixInstructions):
    def __init__(self):
        import ttexalens.hw.tensix.wormhole.wormhole_ops as ops

        super().__init__(ops)


#
# Device
#
class WormholeDevice(Device):
    # Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    DIE_Y_TO_NOC_0_Y = [0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)

    EFUSE_PCI = 0x1FF42200
    EFUSE_JTAG_AXI = 0x80042200
    EFUSE_NOC = 0x880042200

    CONFIGURATION_REGISTER_BASE = 0xFFEF0000
    DEBUG_REGISTER_BASE = 0xFFB12000
    NOC_CONTROL_REGISTER_BASE = 0xFFB20000
    NOC_CONFIGURATION_REGISTER_BASE = 0xFFB20100
    NOC_STATUS_REGISTER_BASE = 0xFFB20200
    NOC_REGISTER_OFFSET = 0x10000

    CONFIGURATION_REGISTER_END = 0xFFEFFFFF

    # RISC LOCAL MEMORY
    RISC_LOCAL_MEM_BASE = 0xFFB00000
    BRISC_LOCAL_MEM_SIZE = 4 * 1024  # 4KB
    NCRISC_LOCAL_MEM_SIZE = 4 * 1024  # 4KB
    TRISC_LOCAL_MEM_SIZE = 2 * 1024  # 2KB

    MAX_CFG_REG_INDEX = 2**14 - 1

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

    def _get_tensix_register_map_keys(self) -> list[str]:
        return list(WormholeDevice.__register_map.keys())

    def _get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription | None:
        """Overrides the base class method to provide register descriptions for Wormhole device."""
        if register_name in WormholeDevice.__register_map:
            return WormholeDevice.__register_map[register_name]
        return None

    def _get_tensix_register_base_address(self, register_description: TensixRegisterDescription) -> int | None:
        """Overrides the base class method to provide register base addresses for Wormhole device."""
        if isinstance(register_description, ConfigurationRegisterDescription):
            return WormholeDevice.CONFIGURATION_REGISTER_BASE
        elif isinstance(register_description, DebugRegisterDescription):
            return WormholeDevice.DEBUG_REGISTER_BASE
        elif isinstance(register_description, NocControlRegisterDescription):
            return WormholeDevice.NOC_CONTROL_REGISTER_BASE
        elif isinstance(register_description, NocConfigurationRegisterDescription):
            return WormholeDevice.NOC_CONFIGURATION_REGISTER_BASE
        elif isinstance(register_description, NocStatusRegisterDescription):
            return WormholeDevice.NOC_STATUS_REGISTER_BASE
        else:
            return None

    def _get_tensix_register_end_address(self, register_description: TensixRegisterDescription) -> int | None:
        """Overrides the base class method to provide register end addresses for Wormhole device."""
        if isinstance(register_description, ConfigurationRegisterDescription):
            return WormholeDevice.CONFIGURATION_REGISTER_END
        else:
            return None

    def _get_riscv_local_memory_base_address(self) -> int:
        return WormholeDevice.RISC_LOCAL_MEM_BASE

    def _get_riscv_local_memory_size(self, risc_id):
        if risc_id == 0:
            return WormholeDevice.BRISC_LOCAL_MEM_SIZE
        elif 1 <= risc_id <= 3:
            return WormholeDevice.TRISC_LOCAL_MEM_SIZE
        elif risc_id == 4:
            return WormholeDevice.NCRISC_LOCAL_MEM_SIZE
        else:
            return None

    __register_map = {
        # UNPACK TILE DESCRIPTOR SEC 0
        "UNPACK_TILE_DESCRIPTOR0_in_data_format": ConfigurationRegisterDescription(
            index=52, mask=0xF, shift=0, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "UNPACK_TILE_DESCRIPTOR0_uncompressed": ConfigurationRegisterDescription(
            index=52, mask=0x10, shift=4, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_TILE_DESCRIPTOR0_reserved_0": ConfigurationRegisterDescription(
            index=52, mask=0xE0, shift=5, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_per_xy_plane": ConfigurationRegisterDescription(
            index=52, mask=0xF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_reserved_1": ConfigurationRegisterDescription(
            index=52, mask=0xF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_x_dim": ConfigurationRegisterDescription(
            index=52, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_y_dim": ConfigurationRegisterDescription(
            index=53, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_z_dim": ConfigurationRegisterDescription(
            index=53, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_w_dim": ConfigurationRegisterDescription(
            index=54, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=54, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi": ConfigurationRegisterDescription(
            index=55, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_digest_type": ConfigurationRegisterDescription(
            index=55, mask=0xFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR0_digest_size": ConfigurationRegisterDescription(
            index=55, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # UNPACK TILE DESCRIPTOR SEC 1
        "UNPACK_TILE_DESCRIPTOR1_in_data_format": ConfigurationRegisterDescription(
            index=92, mask=0xF, shift=0, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "UNPACK_TILE_DESCRIPTOR1_uncompressed": ConfigurationRegisterDescription(
            index=92, mask=0x10, shift=4, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_TILE_DESCRIPTOR1_reserved_0": ConfigurationRegisterDescription(
            index=92, mask=0xE0, shift=5, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_per_xy_plane": ConfigurationRegisterDescription(
            index=92, mask=0xF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_reserved_1": ConfigurationRegisterDescription(
            index=92, mask=0xF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_x_dim": ConfigurationRegisterDescription(
            index=92, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_y_dim": ConfigurationRegisterDescription(
            index=93, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_z_dim": ConfigurationRegisterDescription(
            index=93, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_w_dim": ConfigurationRegisterDescription(
            index=94, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_lo": ConfigurationRegisterDescription(
            index=94, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_blobs_y_start_hi": ConfigurationRegisterDescription(
            index=95, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_digest_type": ConfigurationRegisterDescription(
            index=95, mask=0xFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_TILE_DESCRIPTOR1_digest_size": ConfigurationRegisterDescription(
            index=95, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # UNPACK CONFIG SEC 0
        "UNPACK_CONFIG0_out_data_format": ConfigurationRegisterDescription(
            index=60, mask=0xF, shift=0, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "UNPACK_CONFIG0_throttle_mode": ConfigurationRegisterDescription(
            index=60, mask=0x30, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_context_count": ConfigurationRegisterDescription(
            index=60, mask=0xC0, shift=6, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_haloize_mode": ConfigurationRegisterDescription(
            index=60, mask=0x100, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_tileize_mode": ConfigurationRegisterDescription(
            index=60, mask=0x200, shift=9, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_unpack_src_reg_set_upd": ConfigurationRegisterDescription(
            index=60, mask=0x400, shift=10, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG0_unpack_if_sel": ConfigurationRegisterDescription(
            index=60, mask=0x800, shift=11, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG0_upsample_rate": ConfigurationRegisterDescription(
            index=60, mask=0x3000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_reserved_1": ConfigurationRegisterDescription(
            index=60, mask=0x4000, shift=14, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_upsample_and_interleave": ConfigurationRegisterDescription(
            index=60, mask=0x8000, shift=15, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG0_shift_amount": ConfigurationRegisterDescription(
            index=60, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_uncompress_cntx0_3": ConfigurationRegisterDescription(
            index=61, mask=0xF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(
            index=61, mask=0xF0, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_force_shared_exp": ConfigurationRegisterDescription(
            index=61, mask=0x100, shift=8, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG0_reserved_2": ConfigurationRegisterDescription(
            index=61, mask=0xFE00, shift=9, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_uncompress_cntx4_7": ConfigurationRegisterDescription(
            index=61, mask=0xF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(
            index=61, mask=0xF00000, shift=20, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_reserved_3": ConfigurationRegisterDescription(
            index=61, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_limit_addr": ConfigurationRegisterDescription(
            index=62, mask=0x1FFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "UNPACK_CONFIG0_reserved_4": ConfigurationRegisterDescription(
            index=62, mask=0xFFFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_fifo_size": ConfigurationRegisterDescription(
            index=63, mask=0x1FFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG0_reserved_5": ConfigurationRegisterDescription(
            index=63, mask=0xFFFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        # UNPACK CONFIG SEC 1
        "UNPACK_CONFIG1_out_data_format": ConfigurationRegisterDescription(
            index=100, mask=0xF, shift=0, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "UNPACK_CONFIG1_throttle_mode": ConfigurationRegisterDescription(
            index=100, mask=0x30, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_context_count": ConfigurationRegisterDescription(
            index=100, mask=0xC0, shift=6, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_haloize_mode": ConfigurationRegisterDescription(
            index=100, mask=0x100, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_tileize_mode": ConfigurationRegisterDescription(
            index=100, mask=0x200, shift=9, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_unpack_src_reg_set_upd": ConfigurationRegisterDescription(
            index=100, mask=0x400, shift=10, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG1_unpack_if_sel": ConfigurationRegisterDescription(
            index=100, mask=0x800, shift=11, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG1_upsample_rate": ConfigurationRegisterDescription(
            index=100, mask=0x3000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_reserved_1": ConfigurationRegisterDescription(
            index=100, mask=0x4000, shift=14, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_upsample_and_interleave": ConfigurationRegisterDescription(
            index=100, mask=0x8000, shift=15, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG1_shift_amount": ConfigurationRegisterDescription(
            index=100, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_uncompress_cntx0_3": ConfigurationRegisterDescription(
            index=101, mask=0xF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_unpack_if_sel_cntx0_3": ConfigurationRegisterDescription(
            index=101, mask=0xF0, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_force_shared_exp": ConfigurationRegisterDescription(
            index=101, mask=0x100, shift=8, data_type=DATA_TYPE.FLAGS
        ),
        "UNPACK_CONFIG1_reserved_2": ConfigurationRegisterDescription(
            index=101, mask=0xFE00, shift=9, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_uncompress_cntx4_7": ConfigurationRegisterDescription(
            index=101, mask=0xF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_unpack_if_sel_cntx4_7": ConfigurationRegisterDescription(
            index=101, mask=0xF00000, shift=20, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_reserved_3": ConfigurationRegisterDescription(
            index=101, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_limit_addr": ConfigurationRegisterDescription(
            index=102, mask=0x1FFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "UNPACK_CONFIG1_reserved_4": ConfigurationRegisterDescription(
            index=102, mask=0xFFFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_fifo_size": ConfigurationRegisterDescription(
            index=103, mask=0x1FFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "UNPACK_CONFIG1_reserved_5": ConfigurationRegisterDescription(
            index=103, mask=0xFFFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
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
            index=56, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_exp_section_size": ConfigurationRegisterDescription(
            index=56, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_l1_dest_addr": ConfigurationRegisterDescription(
            index=57, mask=0xFFFFFFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG01_uncompress": ConfigurationRegisterDescription(
            index=58, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
            index=58, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_reserved_0": ConfigurationRegisterDescription(
            index=58, mask=0xC, shift=2, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_out_data_format": ConfigurationRegisterDescription(
            index=58, mask=0xF0, shift=4, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG01_in_data_format": ConfigurationRegisterDescription(
            index=58, mask=0xF00, shift=8, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG01_reserved_1": ConfigurationRegisterDescription(
            index=58, mask=0xF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_src_if_sel": ConfigurationRegisterDescription(
            index=58, mask=0x10000, shift=16, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=58, mask=0xFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_l1_src_addr": ConfigurationRegisterDescription(
            index=58, mask=0xFF000000, shift=24, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG01_downsample_mask": ConfigurationRegisterDescription(
            index=59, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        "PACK_CONFIG01_downsample_shift_count": ConfigurationRegisterDescription(
            index=59, mask=0x70000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_read_mode": ConfigurationRegisterDescription(
            index=59, mask=0x80000, shift=19, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_exp_threshold_en": ConfigurationRegisterDescription(
            index=59, mask=0x100000, shift=20, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=59, mask=0x600000, shift=21, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG01_reserved_2": ConfigurationRegisterDescription(
            index=59, mask=0x800000, shift=23, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG01_exp_threshold": ConfigurationRegisterDescription(
            index=59, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK CONFIG SEC 0 REG 8
        "PACK_CONFIG08_row_ptr_section_size": ConfigurationRegisterDescription(
            index=84, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG08_exp_section_size": ConfigurationRegisterDescription(
            index=84, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG08_l1_dest_addr": ConfigurationRegisterDescription(
            index=85, mask=0xFFFFFFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG08_uncompress": ConfigurationRegisterDescription(
            index=86, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG08_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
            index=86, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG08_reserved_0": ConfigurationRegisterDescription(
            index=86, mask=0xC, shift=2, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG08_out_data_format": ConfigurationRegisterDescription(
            index=86, mask=0xF0, shift=4, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG08_in_data_format": ConfigurationRegisterDescription(
            index=86, mask=0xF00, shift=8, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG08_reserved_1": ConfigurationRegisterDescription(
            index=86, mask=0xF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG08_src_if_sel": ConfigurationRegisterDescription(
            index=86, mask=0x10000, shift=16, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG08_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=86, mask=0xFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG08_l1_src_addr": ConfigurationRegisterDescription(
            index=86, mask=0xFF000000, shift=24, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG08_downsample_mask": ConfigurationRegisterDescription(
            index=87, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        "PACK_CONFIG08_downsample_shift_count": ConfigurationRegisterDescription(
            index=87, mask=0x70000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG08_read_mode": ConfigurationRegisterDescription(
            index=87, mask=0x80000, shift=19, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG08_exp_threshold_en": ConfigurationRegisterDescription(
            index=87, mask=0x100000, shift=20, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG08_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=87, mask=0x600000, shift=21, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG08_reserved_2": ConfigurationRegisterDescription(
            index=87, mask=0x800000, shift=23, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG08_exp_threshold": ConfigurationRegisterDescription(
            index=87, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK CONFIG SEC 1 REG 1
        "PACK_CONFIG11_row_ptr_section_size": ConfigurationRegisterDescription(
            index=96, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG11_exp_section_size": ConfigurationRegisterDescription(
            index=96, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG11_l1_dest_addr": ConfigurationRegisterDescription(
            index=97, mask=0xFFFFFFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG11_uncompress": ConfigurationRegisterDescription(
            index=98, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG11_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
            index=98, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG11_reserved_0": ConfigurationRegisterDescription(
            index=98, mask=0xC, shift=2, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG11_out_data_format": ConfigurationRegisterDescription(
            index=98, mask=0xF0, shift=4, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG11_in_data_format": ConfigurationRegisterDescription(
            index=98, mask=0xF00, shift=8, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG11_reserved_1": ConfigurationRegisterDescription(
            index=98, mask=0xF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG11_src_if_sel": ConfigurationRegisterDescription(
            index=98, mask=0x10000, shift=16, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG11_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=98, mask=0xFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG11_l1_src_addr": ConfigurationRegisterDescription(
            index=98, mask=0xFF000000, shift=24, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG11_downsample_mask": ConfigurationRegisterDescription(
            index=99, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        "PACK_CONFIG11_downsample_shift_count": ConfigurationRegisterDescription(
            index=99, mask=0x70000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG11_read_mode": ConfigurationRegisterDescription(
            index=99, mask=0x80000, shift=19, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG11_exp_threshold_en": ConfigurationRegisterDescription(
            index=99, mask=0x100000, shift=20, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG11_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=99, mask=0x600000, shift=21, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG11_reserved_2": ConfigurationRegisterDescription(
            index=99, mask=0x800000, shift=23, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG11_exp_threshold": ConfigurationRegisterDescription(
            index=99, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK CONFIG SEC 1 REG 8
        "PACK_CONFIG18_row_ptr_section_size": ConfigurationRegisterDescription(
            index=124, mask=0xFFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG18_exp_section_size": ConfigurationRegisterDescription(
            index=124, mask=0xFFFF0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG18_l1_dest_addr": ConfigurationRegisterDescription(
            index=125, mask=0xFFFFFFFF, shift=0, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG18_uncompress": ConfigurationRegisterDescription(
            index=126, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG18_add_l1_dest_addr_offset": ConfigurationRegisterDescription(
            index=126, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG18_reserved_0": ConfigurationRegisterDescription(
            index=126, mask=0xC, shift=2, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG18_out_data_format": ConfigurationRegisterDescription(
            index=126, mask=0xF0, shift=4, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG18_in_data_format": ConfigurationRegisterDescription(
            index=126, mask=0xF00, shift=8, data_type=DATA_TYPE.TENSIX_DATA_FORMAT
        ),
        "PACK_CONFIG18_reserved_1": ConfigurationRegisterDescription(
            index=126, mask=0xF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG18_src_if_sel": ConfigurationRegisterDescription(
            index=126, mask=0x10000, shift=16, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG18_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=126, mask=0xFE0000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG18_l1_src_addr": ConfigurationRegisterDescription(
            index=126, mask=0xFF000000, shift=24, data_type=DATA_TYPE.ADDRESS
        ),
        "PACK_CONFIG18_downsample_mask": ConfigurationRegisterDescription(
            index=127, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        "PACK_CONFIG18_downsample_shift_count": ConfigurationRegisterDescription(
            index=127, mask=0x70000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG18_read_mode": ConfigurationRegisterDescription(
            index=127, mask=0x80000, shift=19, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG18_exp_threshold_en": ConfigurationRegisterDescription(
            index=127, mask=0x100000, shift=20, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG18_pack_l1_acc_disable_pack_zero_flag": ConfigurationRegisterDescription(
            index=127, mask=0x600000, shift=21, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_CONFIG18_reserved_2": ConfigurationRegisterDescription(
            index=127, mask=0x800000, shift=23, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_CONFIG18_exp_threshold": ConfigurationRegisterDescription(
            index=127, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
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
            index=2, mask=0x80000000, shift=31, data_type=DATA_TYPE.FLAGS
        ),
        # DEST RD CTRL
        "PACK_DEST_RD_CTRL_Read_32b_data": ConfigurationRegisterDescription(
            index=14, mask=0x1, shift=0, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_DEST_RD_CTRL_Read_unsigned": ConfigurationRegisterDescription(
            index=14, mask=0x2, shift=1, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_DEST_RD_CTRL_Read_int8": ConfigurationRegisterDescription(
            index=14, mask=0x4, shift=2, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_DEST_RD_CTRL_Round_10b_mant": ConfigurationRegisterDescription(
            index=14, mask=0x8, shift=3, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_DEST_RD_CTRL_Reserved": ConfigurationRegisterDescription(
            index=14, mask=0xFFFFFFF0, shift=4, data_type=DATA_TYPE.INT_VALUE
        ),
        # EDGE OFFSET SEC 0
        "PACK_EDGE_OFFSET0_mask": ConfigurationRegisterDescription(
            index=20, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        "PACK_EDGE_OFFSET0_mode": ConfigurationRegisterDescription(
            index=20, mask=0x10000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack0": ConfigurationRegisterDescription(
            index=20, mask=0x60000, shift=17, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack1": ConfigurationRegisterDescription(
            index=20, mask=0x180000, shift=19, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack2": ConfigurationRegisterDescription(
            index=20, mask=0x600000, shift=21, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_tile_row_set_select_pack3": ConfigurationRegisterDescription(
            index=20, mask=0x1800000, shift=23, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_EDGE_OFFSET0_reserved": ConfigurationRegisterDescription(
            index=20, mask=0xFE000000, shift=25, data_type=DATA_TYPE.INT_VALUE
        ),
        # EDGE OFFSET SEC 1
        "PACK_EDGE_OFFSET1_mask": ConfigurationRegisterDescription(
            index=21, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        # EDGE OFFSET SEC 2
        "PACK_EDGE_OFFSET2_mask": ConfigurationRegisterDescription(
            index=22, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        # EDGE OFFSET SEC 3
        "PACK_EDGE_OFFSET3_mask": ConfigurationRegisterDescription(
            index=23, mask=0xFFFF, shift=0, data_type=DATA_TYPE.MASK
        ),
        # PACK COUNTERS SEC 0
        "PACK_COUNTERS0_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=24, mask=0xFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS0_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
            index=24, mask=0xFF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS0_pack_xys_per_til": ConfigurationRegisterDescription(
            index=24, mask=0x7F0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS0_pack_yz_transposed": ConfigurationRegisterDescription(
            index=24, mask=0x800000, shift=23, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_COUNTERS0_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=24, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK COUNTERS SEC 1
        "PACK_COUNTERS1_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=25, mask=0xFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS1_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
            index=25, mask=0xFF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS1_pack_xys_per_til": ConfigurationRegisterDescription(
            index=25, mask=0x7F0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS1_pack_yz_transposed": ConfigurationRegisterDescription(
            index=25, mask=0x800000, shift=23, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_COUNTERS1_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=25, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK COUNTERS SEC 2
        "PACK_COUNTERS2_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=26, mask=0xFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS2_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
            index=26, mask=0xFF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS2_pack_xys_per_til": ConfigurationRegisterDescription(
            index=26, mask=0x7F0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS2_pack_yz_transposed": ConfigurationRegisterDescription(
            index=26, mask=0x800000, shift=23, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_COUNTERS2_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=26, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK COUNTERS SEC 3
        "PACK_COUNTERS3_pack_per_xy_plane": ConfigurationRegisterDescription(
            index=27, mask=0xFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS3_pack_reads_per_xy_plane": ConfigurationRegisterDescription(
            index=27, mask=0xFF00, shift=8, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS3_pack_xys_per_til": ConfigurationRegisterDescription(
            index=27, mask=0x7F0000, shift=16, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_COUNTERS3_pack_yz_transposed": ConfigurationRegisterDescription(
            index=27, mask=0x800000, shift=23, data_type=DATA_TYPE.FLAGS
        ),
        "PACK_COUNTERS3_pack_per_xy_plane_offset": ConfigurationRegisterDescription(
            index=27, mask=0xFF000000, shift=24, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK STRIDES REG 0
        "PACK_STRIDES0_x_stride": ConfigurationRegisterDescription(
            index=8, mask=0xFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES0_y_stride": ConfigurationRegisterDescription(
            index=8, mask=0xFFF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES0_z_stride": ConfigurationRegisterDescription(
            index=9, mask=0xFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES0_w_stride": ConfigurationRegisterDescription(
            index=9, mask=0xFFFF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        # PACK STRIDES REG 1
        "PACK_STRIDES1_x_stride": ConfigurationRegisterDescription(
            index=10, mask=0xFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES1_y_stride": ConfigurationRegisterDescription(
            index=10, mask=0xFFF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES1_z_stride": ConfigurationRegisterDescription(
            index=11, mask=0xFFF, shift=0, data_type=DATA_TYPE.INT_VALUE
        ),
        "PACK_STRIDES1_w_stride": ConfigurationRegisterDescription(
            index=11, mask=0xFFFF000, shift=12, data_type=DATA_TYPE.INT_VALUE
        ),
        # REST
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

    @cache
    def get_block(self, location):
        block_type = self.get_block_type(location)
        if block_type == "arc":
            return WormholeArcBlock(location)
        elif block_type == "dram":
            return WormholeDramBlock(location)
        elif block_type == "eth":
            return WormholeEthBlock(location)
        elif block_type == "functional_workers":
            return WormholeFunctionalWorkerBlock(location)
        elif block_type == "harvested_workers":
            return WormholeHarvestedWorkerBlock(location)
        elif block_type == "pcie":
            return WormholePcieBlock(location)
        elif block_type == "router_only":
            return WormholeRouterOnlyBlock(location)
        raise ValueError(f"Unsupported block type: {block_type}")

    def get_tensix_configuration_registers_description(self) -> TensixConfigurationRegistersDescription:
        return configuration_registers_descriptions


# end of class WormholeDevice
