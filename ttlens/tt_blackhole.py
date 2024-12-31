# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util
from ttlens import tt_device
from ttlens.tt_device import ConfigurationRegisterDescription, DebugRegisterDescription


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
        "ALU_FORMAT_SPEC_REG2_Dstacc": ConfigurationRegisterDescription(index=1, mask=0x1E000000, shift=25),
        "ALU_ACC_CTRL_Fp32_enabled": ConfigurationRegisterDescription(index=1, mask=0x20000000, shift=29),
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
