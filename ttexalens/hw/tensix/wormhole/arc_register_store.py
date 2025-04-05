# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from typing import Union
from ttexalens.hw.tensix.wormhole.noc_registers import noc_registers_offset_map
from ttexalens.register_store import (
    ArcCsmRegisterDescription,
    ArcResetRegisterDescription,
    ArcRomRegisterDescription,
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
    NocStatusRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


def get_mmio_register_raw_base_address(register_description: RegisterDescription) -> int:
    if isinstance(register_description, ArcResetRegisterDescription):
        return 0x1FF30000
    elif isinstance(register_description, ArcCsmRegisterDescription):
        return 0x1FE80000
    elif isinstance(register_description, ArcRomRegisterDescription):
        return 0x1FF00000
    elif isinstance(register_description, NocControlRegisterDescription):
        return 0xFFFB20000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0xFFFB20100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0xFFFB20200
    else:
        return 0


def get_remote_register_noc_base_address(register_description: RegisterDescription) -> Union[int, None]:
    if isinstance(register_description, ArcResetRegisterDescription):
        return 0x880030000
    elif isinstance(register_description, ArcCsmRegisterDescription):
        return 0x810000000
    elif isinstance(register_description, ArcRomRegisterDescription):
        return 0x880000000
    elif isinstance(register_description, NocControlRegisterDescription):
        return 0xFFFB20000
    elif isinstance(register_description, NocConfigurationRegisterDescription):
        return 0xFFFB20100
    elif isinstance(register_description, NocStatusRegisterDescription):
        return 0xFFFB20200
    else:
        return None


register_offset_map = {
    "ARC_RESET_ARC_MISC_CNTL": ArcResetRegisterDescription(address=0x100),
    "ARC_RESET_ARC_MISC_STATUS": ArcResetRegisterDescription(address=0x104),
    "ARC_RESET_ARC_UDMIAXI_REGION": ArcResetRegisterDescription(address=0x10C),
    "ARC_RESET_SCRATCH0": ArcResetRegisterDescription(address=0x060),
    "ARC_RESET_SCRATCH1": ArcResetRegisterDescription(address=0x064),
    "ARC_RESET_SCRATCH2": ArcResetRegisterDescription(address=0x068),
    "ARC_RESET_SCRATCH3": ArcResetRegisterDescription(address=0x06C),
    "ARC_RESET_SCRATCH4": ArcResetRegisterDescription(address=0x070),
    "ARC_RESET_SCRATCH5": ArcResetRegisterDescription(address=0x074),
    "ARC_CSM_DATA": ArcCsmRegisterDescription(address=0),
    "ARC_ROM_DATA": ArcRomRegisterDescription(address=0),
}

register_map = RegisterStore.initialize_register_map(
    [register_offset_map, noc_registers_offset_map],
    get_mmio_register_raw_base_address,
    get_remote_register_noc_base_address,
)
