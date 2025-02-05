# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util
from ttlens.tt_device import (
    TensixInstructions,
    Device,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    TensixRegisterDescription,
    NocStatusRegisterDescription,
)


class WormholeInstructions(TensixInstructions):
    def __init__(self):
        import ttlens.tt_wormhole_ops as ops

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
    NOC_STATUS_REGISTER_BASE = 0xFFB22000

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
        else:
            return None

    __register_map = {
        "ALU_FORMAT_SPEC_REG2_Dstacc": ConfigurationRegisterDescription(index=1, mask=0x1E000000, shift=25),
        "ALU_ACC_CTRL_Fp32_enabled": ConfigurationRegisterDescription(index=1, mask=0x20000000, shift=29),
        "DISABLE_RISC_BP_Disable_main": ConfigurationRegisterDescription(index=2, mask=0x400000, shift=22),
        "DISABLE_RISC_BP_Disable_trisc": ConfigurationRegisterDescription(index=2, mask=0x3800000, shift=23),
        "DISABLE_RISC_BP_Disable_ncrisc": ConfigurationRegisterDescription(index=2, mask=0x4000000, shift=26),
        "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=157, mask=0x1F),
        "TRISC_RESET_PC_SEC0_PC": ConfigurationRegisterDescription(index=158),
        "TRISC_RESET_PC_SEC1_PC": ConfigurationRegisterDescription(index=159),
        "TRISC_RESET_PC_SEC2_PC": ConfigurationRegisterDescription(index=160),
        "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=161, mask=0x7),
        "NCRISC_RESET_PC_PC": ConfigurationRegisterDescription(index=162),
        "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=163, mask=0x1),
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
    }
