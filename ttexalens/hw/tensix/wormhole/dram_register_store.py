# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from typing import Union
from ttexalens.hw.tensix.wormhole.noc_registers import noc_registers_offset_map
from ttexalens.register_store import (
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
    NocStatusRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


def get_register_base_address_location_0_noc0(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, NocControlRegisterDescription):
        return 0x100080000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0x100080100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0x100080200
    else:
        return None


def get_register_base_address_location_0_noc1(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, NocControlRegisterDescription):
        return 0x100088000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0x100088100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0x100088200
    else:
        return None


def get_register_base_address_location_1_noc0(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, NocControlRegisterDescription):
        return 0x100090000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0x100090100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0x100090200
    else:
        return None


def get_register_base_address_location_1_noc1(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, NocControlRegisterDescription):
        return 0x100098000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0x100098100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0x100098200
    else:
        return None


def get_register_base_address_location_2_noc0(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, NocControlRegisterDescription):
        return 0x1000A0000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0x1000A0100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0x1000A0200
    else:
        return None


def get_register_base_address_location_2_noc1(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, NocControlRegisterDescription):
        return 0x1000A8000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0x1000A8100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0x1000A8200
    else:
        return None


register_map_location_0_noc0 = RegisterStore.initialize_register_map(
    noc_registers_offset_map, get_register_base_address_location_0_noc0, get_register_base_address_location_0_noc0
)
register_map_location_1_noc0 = RegisterStore.initialize_register_map(
    noc_registers_offset_map, get_register_base_address_location_1_noc0, get_register_base_address_location_1_noc0
)
register_map_location_2_noc0 = RegisterStore.initialize_register_map(
    noc_registers_offset_map, get_register_base_address_location_2_noc0, get_register_base_address_location_2_noc0
)
register_map_location_0_noc1 = RegisterStore.initialize_register_map(
    noc_registers_offset_map, get_register_base_address_location_0_noc1, get_register_base_address_location_0_noc1
)
register_map_location_1_noc1 = RegisterStore.initialize_register_map(
    noc_registers_offset_map, get_register_base_address_location_1_noc1, get_register_base_address_location_1_noc1
)
register_map_location_2_noc1 = RegisterStore.initialize_register_map(
    noc_registers_offset_map, get_register_base_address_location_2_noc1, get_register_base_address_location_2_noc1
)
