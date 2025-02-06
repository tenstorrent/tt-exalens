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
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
)


class BlackholeInstructions(TensixInstructions):
    def __init__(self):
        import ttlens.tt_blackhole_ops as ops

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

    # Register base addresses
    CONFIGURATION_REGISTER_BASE = 0xFFEF0000
    DEBUG_REGISTER_BASE = 0xFFB12000
    NOC_CONTROL_REGISTER_BASE = 0xFFB20000
    NOC_CONFIGURATION_REGISTER_BASE = 0xFFB20100
    NOC_STATUS_REGISTER_BASE = 0xFFB20200

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )
        self.instructions = BlackholeInstructions()

    def _get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription:
        """Overrides the base class method to provide register descriptions for Blackhole device."""
        if register_name in BlackholeDevice.__register_map:
            return BlackholeDevice.__register_map[register_name]
        else:
            return None

    def _get_tensix_register_base_address(self, register_description: TensixRegisterDescription) -> int:
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

    __register_map = {
        "ALU_FORMAT_SPEC_REG2_Dstacc": ConfigurationRegisterDescription(index=1, mask=0x1E000000, shift=25),
        "ALU_ACC_CTRL_Fp32_enabled": ConfigurationRegisterDescription(index=1, mask=0x20000000, shift=29),
        "DISABLE_RISC_BP_Disable_main": ConfigurationRegisterDescription(index=2, mask=0x400000, shift=22),
        "DISABLE_RISC_BP_Disable_trisc": ConfigurationRegisterDescription(index=2, mask=0x3800000, shift=23),
        "DISABLE_RISC_BP_Disable_ncrisc": ConfigurationRegisterDescription(index=2, mask=0x4000000, shift=26),
        "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=185, mask=0x1F),
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
        "NIU_MST_REQS_OUTSTANDING_ID" : NocStatusRegisterDescription(address=0x40), # 16 registers
        "NIU_MST_WRITE_REQS_OUTGOING_ID" : NocStatusRegisterDescription(address=0x80), # 16 registers
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
        "NIU_CFG_0" : NocConfigurationRegisterDescription(address=0x0),
        "ROUTER_CFG_0" : NocConfigurationRegisterDescription(address=0x4),
        "ROUTER_CFG_1" : NocConfigurationRegisterDescription(address=0x8),
        "ROUTER_CFG_2" : NocConfigurationRegisterDescription(address=0xC),
        "ROUTER_CFG_3" : NocConfigurationRegisterDescription(address=0x10),
        "ROUTER_CFG_4" : NocConfigurationRegisterDescription(address=0x14),
        "NOC_X_ID_TRANSLATE_TABLE_0" : NocConfigurationRegisterDescription(address=0x18),
        "NOC_X_ID_TRANSLATE_TABLE_1" : NocConfigurationRegisterDescription(address=0x1C),
        "NOC_X_ID_TRANSLATE_TABLE_2" : NocConfigurationRegisterDescription(address=0x20),
        "NOC_X_ID_TRANSLATE_TABLE_3" : NocConfigurationRegisterDescription(address=0x24),
        "NOC_X_ID_TRANSLATE_TABLE_4" : NocConfigurationRegisterDescription(address=0x28),
        "NOC_X_ID_TRANSLATE_TABLE_5" : NocConfigurationRegisterDescription(address=0x2C),
        "NOC_Y_ID_TRANSLATE_TABLE_0" : NocConfigurationRegisterDescription(address=0x30),
        "NOC_Y_ID_TRANSLATE_TABLE_1" : NocConfigurationRegisterDescription(address=0x34),
        "NOC_Y_ID_TRANSLATE_TABLE_2" : NocConfigurationRegisterDescription(address=0x38),
        "NOC_Y_ID_TRANSLATE_TABLE_3" : NocConfigurationRegisterDescription(address=0x3C),
        "NOC_Y_ID_TRANSLATE_TABLE_4" : NocConfigurationRegisterDescription(address=0x40),
        "NOC_Y_ID_TRANSLATE_TABLE_5" : NocConfigurationRegisterDescription(address=0x44),
        "NOC_ID_LOGICAL" : NocConfigurationRegisterDescription(address=0x48),
        "MEMORY_SHUTDOWN_CONTROL" : NocConfigurationRegisterDescription(address=0x4C),
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
        "NOC_SEC_FENCE_RANGE": NocControlRegisterDescription(address=0x400), # 32 instances
        "NOC_SEC_FENCE_ATTRIBUTE": NocControlRegisterDescription(address=0x480), # 8 instances
        "NOC_SEC_FENCE_MASTER_LEVEL": NocControlRegisterDescription(address=0x4A0),
        "NOC_SEC_FENCE_FIFO_STATUS": NocControlRegisterDescription(address=0x4A4),
        "NOC_SEC_FENCE_FIFO_RDDATA": NocControlRegisterDescription(address=0x4A8),
        "PORT1_FLIT_COUNTER_LOWER": NocControlRegisterDescription(address=0x500), # 16 instances
        "PORT1_FLIT_COUNTER_UPPER": NocControlRegisterDescription(address=0x540), # 16 instances
        "PORT2_FLIT_COUNTER_LOWER": NocControlRegisterDescription(address=0x580), # 16 instances
        "PORT2_FLIT_COUNTER_UPPER": NocControlRegisterDescription(address=0x5C0), # 16 instances
    }
