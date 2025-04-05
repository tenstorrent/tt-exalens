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


def get_register_noc_base_address(register_description: RegisterDescription) -> Union[int, None]:
    return get_register_internal_base_address(register_description)


def get_register_internal_base_address(register_description: RegisterDescription) -> int:
    if isinstance(register_description, NocControlRegisterDescription):
        return 0xFFB20000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0xFFB20100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0xFFB20200
    else:
        return None


register_map = RegisterStore.initialize_register_map(
    noc_registers_offset_map, get_register_internal_base_address, get_register_noc_base_address
)
