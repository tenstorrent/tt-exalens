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
    "ROUTER_CFG_5": NocConfigurationRegisterDescription(offset=0x18),
    "NOC_X_ID_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(offset=0x1C),
    "NOC_X_ID_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(offset=0x20),
    "NOC_X_ID_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(offset=0x24),
    "NOC_X_ID_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(offset=0x28),
    "NOC_Y_ID_TRANSLATE_TABLE_0": NocConfigurationRegisterDescription(offset=0x2C),
    "NOC_Y_ID_TRANSLATE_TABLE_1": NocConfigurationRegisterDescription(offset=0x30),
    "NOC_Y_ID_TRANSLATE_TABLE_2": NocConfigurationRegisterDescription(offset=0x34),
    "NOC_Y_ID_TRANSLATE_TABLE_3": NocConfigurationRegisterDescription(offset=0x38),
    "NOC_ID_LOGICAL": NocConfigurationRegisterDescription(offset=0x3C),
    # Command buffer 0 registers (base offset 0x0)
    "NOC_TARG_ADDR_LO_CB0": NocControlRegisterDescription(offset=0x0),
    "NOC_TARG_ADDR_MID_CB0": NocControlRegisterDescription(offset=0x4),
    "NOC_TARG_ADDR_HI_CB0": NocControlRegisterDescription(offset=0x8),
    "NOC_RET_ADDR_LO_CB0": NocControlRegisterDescription(offset=0xC),
    "NOC_RET_ADDR_MID_CB0": NocControlRegisterDescription(offset=0x10),
    "NOC_RET_ADDR_HI_CB0": NocControlRegisterDescription(offset=0x14),
    "NOC_PACKET_TAG_CB0": NocControlRegisterDescription(offset=0x18),
    "NOC_CTRL_CB0": NocControlRegisterDescription(offset=0x1C),
    "NOC_AT_LEN_BE_CB0": NocControlRegisterDescription(offset=0x20),
    "NOC_AT_DATA_CB0": NocControlRegisterDescription(offset=0x24),
    "NOC_CMD_CTRL_CB0": NocControlRegisterDescription(offset=0x28),
    "NOC_NODE_ID": NocControlRegisterDescription(offset=0x2C),
    "NOC_NODE_ID_CB0": NocControlRegisterDescription(offset=0x2C),
    "NOC_ENDPOINT_ID_CB0": NocControlRegisterDescription(offset=0x30),
    # Command buffer 1 registers (base offset 0x400)
    "NOC_TARG_ADDR_LO_CB1": NocControlRegisterDescription(offset=0x400),
    "NOC_TARG_ADDR_MID_CB1": NocControlRegisterDescription(offset=0x404),
    "NOC_TARG_ADDR_HI_CB1": NocControlRegisterDescription(offset=0x408),
    "NOC_RET_ADDR_LO_CB1": NocControlRegisterDescription(offset=0x40C),
    "NOC_RET_ADDR_MID_CB1": NocControlRegisterDescription(offset=0x410),
    "NOC_RET_ADDR_HI_CB1": NocControlRegisterDescription(offset=0x414),
    "NOC_PACKET_TAG_CB1": NocControlRegisterDescription(offset=0x418),
    "NOC_CTRL_CB1": NocControlRegisterDescription(offset=0x41C),
    "NOC_AT_LEN_BE_CB1": NocControlRegisterDescription(offset=0x420),
    "NOC_AT_DATA_CB1": NocControlRegisterDescription(offset=0x424),
    "NOC_CMD_CTRL_CB1": NocControlRegisterDescription(offset=0x428),
    "NOC_NODE_ID_CB1": NocControlRegisterDescription(offset=0x42C),
    "NOC_ENDPOINT_ID_CB1": NocControlRegisterDescription(offset=0x430),
    # Command buffer 2 registers (base offset 0x800)
    "NOC_TARG_ADDR_LO_CB2": NocControlRegisterDescription(offset=0x800),
    "NOC_TARG_ADDR_MID_CB2": NocControlRegisterDescription(offset=0x804),
    "NOC_TARG_ADDR_HI_CB2": NocControlRegisterDescription(offset=0x808),
    "NOC_RET_ADDR_LO_CB2": NocControlRegisterDescription(offset=0x80C),
    "NOC_RET_ADDR_MID_CB2": NocControlRegisterDescription(offset=0x810),
    "NOC_RET_ADDR_HI_CB2": NocControlRegisterDescription(offset=0x814),
    "NOC_PACKET_TAG_CB2": NocControlRegisterDescription(offset=0x818),
    "NOC_CTRL_CB2": NocControlRegisterDescription(offset=0x81C),
    "NOC_AT_LEN_BE_CB2": NocControlRegisterDescription(offset=0x820),
    "NOC_AT_DATA_CB2": NocControlRegisterDescription(offset=0x824),
    "NOC_CMD_CTRL_CB2": NocControlRegisterDescription(offset=0x828),
    "NOC_NODE_ID_CB2": NocControlRegisterDescription(offset=0x82C),
    "NOC_ENDPOINT_ID_CB2": NocControlRegisterDescription(offset=0x830),
    # Command buffer 3 registers (base offset 0xC00)
    "NOC_TARG_ADDR_LO_CB3": NocControlRegisterDescription(offset=0xC00),
    "NOC_TARG_ADDR_MID_CB3": NocControlRegisterDescription(offset=0xC04),
    "NOC_TARG_ADDR_HI_CB3": NocControlRegisterDescription(offset=0xC08),
    "NOC_RET_ADDR_LO_CB3": NocControlRegisterDescription(offset=0xC0C),
    "NOC_RET_ADDR_MID_CB3": NocControlRegisterDescription(offset=0xC10),
    "NOC_RET_ADDR_HI_CB3": NocControlRegisterDescription(offset=0xC14),
    "NOC_PACKET_TAG_CB3": NocControlRegisterDescription(offset=0xC18),
    "NOC_CTRL_CB3": NocControlRegisterDescription(offset=0xC1C),
    "NOC_AT_LEN_BE_CB3": NocControlRegisterDescription(offset=0xC20),
    "NOC_AT_DATA_CB3": NocControlRegisterDescription(offset=0xC24),
    "NOC_CMD_CTRL_CB3": NocControlRegisterDescription(offset=0xC28),
    "NOC_NODE_ID_CB3": NocControlRegisterDescription(offset=0xC2C),
    "NOC_ENDPOINT_ID_CB3": NocControlRegisterDescription(offset=0xC30),
    "NUM_MEM_PARITY_ERR": NocControlRegisterDescription(offset=0x40),
    "NUM_HEADER_1B_ERR": NocControlRegisterDescription(offset=0x44),
    "NUM_HEADER_2B_ERR": NocControlRegisterDescription(offset=0x48),
    "ECC_CTRL": NocControlRegisterDescription(offset=0x4C),
    "NOC_CLEAR_OUTSTANDING_REQ_CNT": NocControlRegisterDescription(offset=0x50),
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
    DeviceAddress(noc_address=0xFFB20000, noc_id=0)
)
default_niu_register_store_noc1_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0xFFB20000, noc_id=1)
)
