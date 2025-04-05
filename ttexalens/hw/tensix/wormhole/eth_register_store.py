# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from typing import Union
from ttexalens.hw.tensix.wormhole.noc_registers import noc_registers_offset_map
from ttexalens.register_store import (
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
    NocStatusRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


def get_register_noc_base_address_noc0(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, ConfigurationRegisterDescription):
        return None
    return get_register_internal_base_address_noc0(register_description)


def get_register_internal_base_address_noc0(register_description: RegisterDescription) -> int:
    if isinstance(register_description, ConfigurationRegisterDescription):
        return 0xFFEF0000
    elif isinstance(register_description, DebugRegisterDescription):
        return 0xFFB12000
    elif isinstance(register_description, NocControlRegisterDescription):
        return 0xFFB20000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0xFFB20100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0xFFB20200
    else:
        return None


def get_register_noc_base_address_noc1(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, ConfigurationRegisterDescription):
        return None
    return get_register_internal_base_address_noc1(register_description)


def get_register_internal_base_address_noc1(register_description: RegisterDescription) -> int:
    if isinstance(register_description, ConfigurationRegisterDescription):
        return 0xFFEF0000
    elif isinstance(register_description, DebugRegisterDescription):
        return 0xFFB12000
    elif isinstance(register_description, NocControlRegisterDescription):
        return 0xFFB30000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0xFFB30100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0xFFB30200
    else:
        return None


register_offset_map = {
    "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=157, mask=0x1F),
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
}

register_map_noc0 = RegisterStore.initialize_register_map(
    [register_offset_map, noc_registers_offset_map],
    get_register_internal_base_address_noc0,
    get_register_noc_base_address_noc0,
)
register_map_noc1 = RegisterStore.initialize_register_map(
    [register_offset_map, noc_registers_offset_map],
    get_register_internal_base_address_noc1,
    get_register_noc_base_address_noc1,
)
