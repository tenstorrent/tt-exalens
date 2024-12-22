# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util
from ttlens import tt_device

#
# Device
#
class WormholeDevice(tt_device.Device):
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

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )

    def is_translated_coordinate(self, x: int, y: int) -> bool:
        return x >= 16 and y >= 16

    def get_tensix_configuration_register_base(self) -> int:
        return 0xFFEF0000

    __configuration_register_map = {
        "DISABLE_RISC_BP_Disable_main": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x400000, shift=22),
        "DISABLE_RISC_BP_Disable_trisc": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x3800000, shift=23),
        "DISABLE_RISC_BP_Disable_ncrisc": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x4000000, shift=26),
        "RISCV_IC_INVALIDATE_InvalidateAll": tt_device.TensixRegisterDescription(address=157 * 4, mask=0x1F, shift=0),
        "TRISC_RESET_PC_SEC0_PC": tt_device.TensixRegisterDescription(address=158 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_SEC1_PC": tt_device.TensixRegisterDescription(address=159 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_SEC2_PC": tt_device.TensixRegisterDescription(address=160 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": tt_device.TensixRegisterDescription(
            address=161 * 4, mask=0x7, shift=0
        ),
        "NCRISC_RESET_PC_PC": tt_device.TensixRegisterDescription(address=162 * 4, mask=0xFFFFFFFF, shift=0),
        "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": tt_device.TensixRegisterDescription(
            address=163 * 4, mask=0x1, shift=0
        ),
    }

    def get_configuration_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in WormholeDevice.__configuration_register_map:
            return WormholeDevice.__configuration_register_map[register_name]
        return None

    def get_tenxis_debug_register_base(self) -> int:
        return 0xFFB12000

    __debug_register_map = {
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": tt_device.TensixRegisterDescription(address=0x80, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": tt_device.TensixRegisterDescription(address=0x84, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": tt_device.TensixRegisterDescription(
            address=0x88, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": tt_device.TensixRegisterDescription(
            address=0x8C, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_SOFT_RESET_0": tt_device.TensixRegisterDescription(address=0x1B0, mask=0xFFFFFFFF, shift=0),
    }

    def get_debug_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in WormholeDevice.__debug_register_map:
            return WormholeDevice.__debug_register_map[register_name]
        return None
