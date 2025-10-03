# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.arc_block import ArcBlock
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.blackhole.niu_registers import get_niu_register_base_address_callable, niu_register_map
from ttexalens.register_store import (
    ArcCsmRegisterDescription,
    ArcResetRegisterDescription,
    ArcRomRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


register_map = {
    "ARC_RESET_ARC_MISC_CNTL": ArcResetRegisterDescription(offset=0x100),
    "ARC_RESET_ARC_MISC_STATUS": ArcResetRegisterDescription(offset=0x104),
    "ARC_RESET_ARC_UDMIAXI_REGION": ArcResetRegisterDescription(offset=0x10C),
    "ARC_RESET_SCRATCH0": ArcResetRegisterDescription(offset=0x060),  # Postcode
    "ARC_RESET_SCRATCH1": ArcResetRegisterDescription(offset=0x064),  # SPI boost code
    "ARC_RESET_SCRATCH2": ArcResetRegisterDescription(offset=0x068),  # Msg ID for secondary msg queue
    "ARC_RESET_SCRATCH3": ArcResetRegisterDescription(offset=0x06C),  # Argument value for primary msg queue
    "ARC_RESET_SCRATCH4": ArcResetRegisterDescription(offset=0x070),  # Argument value for secondary msg queue
    "ARC_RESET_SCRATCH5": ArcResetRegisterDescription(offset=0x074),  # Msg ID for primary msg queue
    "ARC_RESET_SCRATCH6": ArcResetRegisterDescription(offset=0x078),  # Drives armisc_info to PCIE controller
    "ARC_RESET_SCRATCH7": ArcResetRegisterDescription(offset=0x07C),  # Drives awmisc_info to PCIE controller
    "ARC_CSM_DATA": ArcCsmRegisterDescription(offset=0),
    "ARC_ROM_DATA": ArcRomRegisterDescription(offset=0),
}


def get_register_base_address_callable(noc_id: int, has_mmio: bool) -> Callable[[RegisterDescription], DeviceAddress]:
    def get_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
        if isinstance(register_description, ArcResetRegisterDescription):
            if has_mmio:
                return DeviceAddress(raw_address=0x1FF30000)
            else:
                return DeviceAddress(noc_address=0x80030000)
        elif isinstance(register_description, ArcCsmRegisterDescription):
            if has_mmio:
                return DeviceAddress(raw_address=0x1FE80000)
            else:
                return DeviceAddress(noc_address=0x10000000)
        elif isinstance(register_description, ArcRomRegisterDescription):
            if has_mmio:
                return DeviceAddress(raw_address=0x1FF00000)
            else:
                return DeviceAddress(noc_address=0x80000000)
        elif noc_id == 0:
            return get_niu_register_base_address_callable(DeviceAddress(noc_address=0x80050000))(register_description)
        else:
            assert noc_id == 1
            return get_niu_register_base_address_callable(DeviceAddress(noc_address=0x80058000))(register_description)

    return get_register_base_address


register_store_noc0_initialization_local = RegisterStore.create_initialization(
    [register_map, niu_register_map], get_register_base_address_callable(noc_id=0, has_mmio=True)
)
register_store_noc1_initialization_local = RegisterStore.create_initialization(
    [register_map, niu_register_map], get_register_base_address_callable(noc_id=1, has_mmio=True)
)
register_store_noc0_initialization_remote = RegisterStore.create_initialization(
    [register_map, niu_register_map], get_register_base_address_callable(noc_id=0, has_mmio=False)
)
register_store_noc1_initialization_remote = RegisterStore.create_initialization(
    [register_map, niu_register_map], get_register_base_address_callable(noc_id=1, has_mmio=False)
)


class BlackholeArcBlock(ArcBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="arc")

        if self.device._has_mmio:
            self.register_store_noc0 = RegisterStore(register_store_noc0_initialization_local, self.location)
            self.register_store_noc1 = RegisterStore(register_store_noc1_initialization_local, self.location)
        else:
            self.register_store_noc0 = RegisterStore(register_store_noc0_initialization_remote, self.location)
            self.register_store_noc1 = RegisterStore(register_store_noc1_initialization_remote, self.location)

    def get_register_store(self, noc_id: int = 0, neo_id: int | None = None) -> RegisterStore:
        if noc_id == 0:
            return self.register_store_noc0
        elif noc_id == 1:
            return self.register_store_noc1
        else:
            raise ValueError(f"Invalid NOC ID: {noc_id}")
