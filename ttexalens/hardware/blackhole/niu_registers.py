# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from typing import Callable
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.register_store import (
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
    NocStatusRegisterDescription,
    RegisterDescription,
    RegisterStore,
    RegisterStoreInitialization,
)


niu_register_map = {
    "NIU_MST_ATOMIC_RESP_RECEIVED": NocStatusRegisterDescription(offset=0x0),
    "NIU_MST_WR_ACK_RECEIVED": NocStatusRegisterDescription(offset=0x4),
    "NIU_MST_RD_RESP_RECEIVED": NocStatusRegisterDescription(offset=0x8),
    "NIU_MST_RD_DATA_WORD_RECEIVED": NocStatusRegisterDescription(offset=0xC),
    "NIU_MST_CMD_ACCEPTED": NocStatusRegisterDescription(offset=0x10),
    "NIU_MST_RD_REQ_SENT": NocStatusRegisterDescription(offset=0x14),
    "NIU_MST_NONPOSTED_ATOMIC_SENT": NocStatusRegisterDescription(offset=0x18),
    "NIU_MST_POSTED_ATOMIC_SENT": NocStatusRegisterDescription(offset=0x1C),
    "NIU_MST_NONPOSTED_WR_DATA_WORD_SENT": NocStatusRegisterDescription(offset=0x20),
    "NIU_MST_POSTED_WR_DATA_WORD_SENT": NocStatusRegisterDescription(offset=0x24),
    "NIU_MST_NONPOSTED_WR_REQ_SENT": NocStatusRegisterDescription(offset=0x28),
    "NIU_MST_POSTED_WR_REQ_SENT": NocStatusRegisterDescription(offset=0x2C),
    "NIU_MST_NONPOSTED_WR_REQ_STARTED": NocStatusRegisterDescription(offset=0x30),
    "NIU_MST_POSTED_WR_REQ_STARTED": NocStatusRegisterDescription(offset=0x34),
    "NIU_MST_RD_REQ_STARTED": NocStatusRegisterDescription(offset=0x38),
    "NIU_MST_NONPOSTED_ATOMIC_STARTED": NocStatusRegisterDescription(offset=0x3C),
    "NIU_MST_REQS_OUTSTANDING_ID": NocStatusRegisterDescription(offset=0x40),  # 16 registers
    "NIU_MST_WRITE_REQS_OUTGOING_ID": NocStatusRegisterDescription(offset=0x80),  # 16 registers
    "NIU_SLV_ATOMIC_RESP_SENT": NocStatusRegisterDescription(offset=0xC0),
    "NIU_SLV_WR_ACK_SENT": NocStatusRegisterDescription(offset=0xC4),
    "NIU_SLV_RD_RESP_SENT": NocStatusRegisterDescription(offset=0xC8),
    "NIU_SLV_RD_DATA_WORD_SENT": NocStatusRegisterDescription(offset=0xCC),
    "NIU_SLV_REQ_ACCEPTED": NocStatusRegisterDescription(offset=0xD0),
    "NIU_SLV_RD_REQ_RECEIVED": NocStatusRegisterDescription(offset=0xD4),
    "NIU_SLV_NONPOSTED_ATOMIC_RECEIVED": NocStatusRegisterDescription(offset=0xD8),
    "NIU_SLV_POSTED_ATOMIC_RECEIVED": NocStatusRegisterDescription(offset=0xDC),
    "NIU_SLV_NONPOSTED_WR_DATA_WORD_RECEIVED": NocStatusRegisterDescription(offset=0xE0),
    "NIU_SLV_POSTED_WR_DATA_WORD_RECEIVED": NocStatusRegisterDescription(offset=0xE4),
    "NIU_SLV_NONPOSTED_WR_REQ_RECEIVED": NocStatusRegisterDescription(offset=0xE8),
    "NIU_SLV_POSTED_WR_REQ_RECEIVED": NocStatusRegisterDescription(offset=0xEC),
    "NIU_SLV_NONPOSTED_WR_REQ_STARTED": NocStatusRegisterDescription(offset=0xF0),
    "NIU_SLV_POSTED_WR_REQ_STARTED": NocStatusRegisterDescription(offset=0xF4),
    "NIU_CFG_0": NocConfigurationRegisterDescription(offset=0x0),
    "ROUTER_CFG_0": NocConfigurationRegisterDescription(offset=0x4),
    "ROUTER_CFG_1": NocConfigurationRegisterDescription(offset=0x8),
    "ROUTER_CFG_2": NocConfigurationRegisterDescription(offset=0xC),
    "ROUTER_CFG_3": NocConfigurationRegisterDescription(offset=0x10),
    "ROUTER_CFG_4": NocConfigurationRegisterDescription(offset=0x14),
    "NOC_X_ID_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(offset=0x18),
    "NOC_X_ID_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(offset=0x1C),
    "NOC_X_ID_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(offset=0x20),
    "NOC_X_ID_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(offset=0x24),
    "NOC_X_ID_TRANSLATE_TABLE_4": NocConfigurationRegisterDescription(offset=0x28),
    "NOC_X_ID_TRANSLATE_TABLE_5": NocConfigurationRegisterDescription(offset=0x2C),
    "NOC_Y_ID_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(offset=0x30),
    "NOC_Y_ID_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(offset=0x34),
    "NOC_Y_ID_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(offset=0x38),
    "NOC_Y_ID_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(offset=0x3C),
    "NOC_Y_ID_TRANSLATE_TABLE_4": NocConfigurationRegisterDescription(offset=0x40),
    "NOC_Y_ID_TRANSLATE_TABLE_5": NocConfigurationRegisterDescription(offset=0x44),
    "NOC_ID_LOGICAL": NocConfigurationRegisterDescription(offset=0x48),
    "MEMORY_SHUTDOWN_CONTROL": NocConfigurationRegisterDescription(offset=0x4C),
    "NOC_ID_TRANSLATE_COL_MASK": NocConfigurationRegisterDescription(offset=0x50),
    "NOC_ID_TRANSLATE_ROW_MASK": NocConfigurationRegisterDescription(offset=0x54),
    "DDR_COORD_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(offset=0x58),
    "DDR_COORD_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(offset=0x5C),
    "DDR_COORD_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(offset=0x60),
    "DDR_COORD_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(offset=0x64),
    "DDR_COORD_TRANSLATE_TABLE_4": NocConfigurationRegisterDescription(offset=0x68),
    "DDR_COORD_TRANSLATE_TABLE_5": NocConfigurationRegisterDescription(offset=0x6C),
    "DDR_COORD_TRANSLATE_COL_SWAP": NocConfigurationRegisterDescription(offset=0x70),
    "DEBUG_COUNTER_RESET": NocConfigurationRegisterDescription(offset=0x74),
    "NIU_TRANS_COUNT_RTZ_CFG": NocConfigurationRegisterDescription(offset=0x78),
    "NIU_TRANS_COUNT_RTZ_CLR": NocConfigurationRegisterDescription(offset=0x7C),
    "NOC_TARG_ADDR_LO": NocControlRegisterDescription(offset=0x0),
    "NOC_TARG_ADDR_MID": NocControlRegisterDescription(offset=0x4),
    "NOC_TARG_ADDR_HI": NocControlRegisterDescription(offset=0x8),
    "NOC_RET_ADDR_LO": NocControlRegisterDescription(offset=0xC),
    "NOC_RET_ADDR_MID": NocControlRegisterDescription(offset=0x10),
    "NOC_RET_ADDR_HI": NocControlRegisterDescription(offset=0x14),
    "NOC_PACKET_TAG": NocControlRegisterDescription(offset=0x18),
    "NOC_CTRL": NocControlRegisterDescription(offset=0x1C),
    "NOC_AT_LEN_BE": NocControlRegisterDescription(offset=0x20),
    "NOC_AT_LEN_BE_1": NocControlRegisterDescription(offset=0x24),
    "NOC_AT_DATA": NocControlRegisterDescription(offset=0x28),
    "NOC_BRCST_EXCLUEDE": NocControlRegisterDescription(offset=0x2C),
    "NOC_L1_ACC_AT_INSTRN": NocControlRegisterDescription(offset=0x30),
    "NOC_SEC_CTRL": NocControlRegisterDescription(offset=0x34),
    "NOC_CMD_CTRL": NocControlRegisterDescription(offset=0x40),
    "NOC_NODE_ID": NocControlRegisterDescription(offset=0x44),
    "NOC_ENDPOINT_ID": NocControlRegisterDescription(offset=0x48),
    "NUM_MEM_PARITY_ERR": NocControlRegisterDescription(offset=0x50),
    "NUM_HEADER_1B_ERR": NocControlRegisterDescription(offset=0x54),
    "NUM_HEADER_2B_ERR": NocControlRegisterDescription(offset=0x58),
    "ECC_CTRL": NocControlRegisterDescription(offset=0x5C),
    "NOC_CLEAR_OUTSTANDING_REQ_CNT": NocControlRegisterDescription(offset=0x60),
    "NOC_SEC_FENCE_RANGE": NocControlRegisterDescription(offset=0x400),  # 32 instances
    "NOC_SEC_FENCE_ATTRIBUTE": NocControlRegisterDescription(offset=0x480),  # 8 instances
    "NOC_SEC_FENCE_MASTER_LEVEL": NocControlRegisterDescription(offset=0x4A0),
    "NOC_SEC_FENCE_FIFO_STATUS": NocControlRegisterDescription(offset=0x4A4),
    "NOC_SEC_FENCE_FIFO_RDDATA": NocControlRegisterDescription(offset=0x4A8),
    "PORT1_FLIT_COUNTER_LOWER": NocControlRegisterDescription(offset=0x500),  # 16 instances
    "PORT1_FLIT_COUNTER_UPPER": NocControlRegisterDescription(offset=0x540),  # 16 instances
    "PORT2_FLIT_COUNTER_LOWER": NocControlRegisterDescription(offset=0x580),  # 16 instances
    "PORT2_FLIT_COUNTER_UPPER": NocControlRegisterDescription(offset=0x5C0),  # 16 instances
}


def get_niu_register_base_address_callable(
    base_address: DeviceAddress,
) -> Callable[[RegisterDescription], DeviceAddress]:
    def get_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
        if isinstance(register_description, NocControlRegisterDescription):
            return base_address
        elif isinstance(register_description, NocConfigurationRegisterDescription):
            return DeviceAddress(
                private_address=base_address.private_address + 0x100
                if base_address.private_address is not None
                else None,
                noc_address=base_address.noc_address + 0x100 if base_address.noc_address is not None else None,
                raw_address=base_address.raw_address + 0x100 if base_address.raw_address is not None else None,
                noc_id=base_address.noc_id,
            )
        elif isinstance(register_description, NocStatusRegisterDescription):
            return DeviceAddress(
                private_address=base_address.private_address + 0x200
                if base_address.private_address is not None
                else None,
                noc_address=base_address.noc_address + 0x200 if base_address.noc_address is not None else None,
                raw_address=base_address.raw_address + 0x200 if base_address.raw_address is not None else None,
                noc_id=base_address.noc_id,
            )
        else:
            raise ValueError(f"Unsupported register description type: {type(register_description)}")

    return get_register_base_address


def get_niu_register_store_initialization(base_address: DeviceAddress) -> RegisterStoreInitialization:
    return RegisterStore.create_initialization(niu_register_map, get_niu_register_base_address_callable(base_address))


default_niu_register_store_noc0_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0xFFFFFFFF_FF000000, noc_id=0)
)
default_niu_register_store_noc1_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0xFFFFFFFF_FF000000, noc_id=1)
)
