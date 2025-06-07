# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.arc_block import ArcBlock
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.wormhole.niu_registers import get_niu_register_base_address_callable, niu_register_map
from ttexalens.register_store import (
    ArcCsmRegisterDescription,
    ArcResetRegisterDescription,
    ArcRomRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


telemetry_tags_map: dict[str, int] = {
    "TAG_ENUM_VERSION": 0,
    "TAG_DEVICE_ID": 1,
    "TAG_ASIC_RO": 2,
    "TAG_ASIC_IDD": 3,
    "TAG_BOARD_ID_HIGH": 4,
    "TAG_BOARD_ID_LOW": 5,
    "TAG_ARC0_FW_VERSION": 6,
    "TAG_ARC1_FW_VERSION": 7,
    "TAG_ARC2_FW_VERSION": 8,
    "TAG_ARC3_FW_VERSION": 9,
    "TAG_SPIBOOTROM_FW_VERSION": 10,
    "TAG_ETH_FW_VERSION": 11,
    "TAG_M3_BL_FW_VERSION": 12,
    "TAG_M3_APP_FW_VERSION": 13,
    "TAG_DDR_STATUS": 14,
    "TAG_ETH_STATUS0": 15,
    "TAG_ETH_STATUS1": 16,
    "TAG_PCIE_STATUS": 17,
    "TAG_FAULTS": 18,
    "TAG_ARC0_HEALTH": 19,
    "TAG_ARC1_HEALTH": 20,
    "TAG_ARC2_HEALTH": 21,
    "TAG_ARC3_HEALTH": 22,
    "TAG_FAN_SPEED": 23,
    "TAG_AICLK": 24,
    "TAG_AXICLK": 25,
    "TAG_ARCCLK": 26,
    "TAG_THROTTLER": 27,
    "TAG_VCORE": 28,
    "TAG_ASIC_TEMPERATURE": 29,
    "TAG_VREG_TEMPERATURE": 30,
    "TAG_BOARD_TEMPERATURE": 31,
    "TAG_TDP": 32,
    "TAG_TDC": 33,
    "TAG_VDD_LIMITS": 34,
    "TAG_THM_LIMITS": 35,
    "TAG_WH_FW_DATE": 36,
    "TAG_ASIC_TMON0": 37,
    "TAG_ASIC_TMON1": 38,
    "TAG_MVDDQ_POWER": 39,
    "TAG_GDDR_TRAIN_TEMP0": 40,
    "TAG_GDDR_TRAIN_TEMP1": 41,
    "TAG_BOOT_DATE": 42,
    "TAG_RT_SECONDS": 43,
    "TAG_ETH_DEBUG_STATUS0": 44,
    "TAG_ETH_DEBUG_STATUS1": 45,
    "TAG_TT_FLASH_VERSION": 46,
    "TAG_ETH_LOOPBACK_STATUS": 47,
    "TAG_ETH_LIVE_STATUS": 48,
    "TAG_FW_BUNDLE_VERSION": 49,
}

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
                return DeviceAddress(noc_address=0x880030000)
        elif isinstance(register_description, ArcCsmRegisterDescription):
            if has_mmio:
                return DeviceAddress(raw_address=0x1FE80000)
            else:
                return DeviceAddress(noc_address=0x810000000)
        elif isinstance(register_description, ArcRomRegisterDescription):
            if has_mmio:
                return DeviceAddress(raw_address=0x1FF00000)
            else:
                return DeviceAddress(noc_address=0x880000000)
        elif noc_id == 0:
            return get_niu_register_base_address_callable(DeviceAddress(noc_address=0xFFFB20000, noc_id=0))(
                register_description
            )
        else:
            assert noc_id == 1
            return get_niu_register_base_address_callable(DeviceAddress(noc_address=0xFFFB20000, noc_id=1))(
                register_description
            )

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


class WormholeArcBlock(ArcBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="arc", telemetry_tags=telemetry_tags_map)

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
