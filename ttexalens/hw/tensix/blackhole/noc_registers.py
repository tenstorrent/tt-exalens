# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.register_store import (
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
    NocStatusRegisterDescription,
)

noc_registers_offset_map = {
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
