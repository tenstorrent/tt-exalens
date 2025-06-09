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


telemetry_tags_map = {
    "TAG_BOARD_ID_HIGH": 1,
    "TAG_BOARD_ID_LOW": 2,
    "TAG_ASIC_ID": 3,
    "TAG_HARVESTING_STATE": 4,
    "TAG_UPDATE_TELEM_SPEED": 5,
    "TAG_VCORE": 6,
    "TAG_TDP": 7,
    "TAG_TDC": 8,
    "TAG_VDD_LIMITS": 9,
    "TAG_THM_LIMIT_SHUTDOWN": 10,
    "TAG_THM_LIMITS": 10,  # Same as TAG_THM_LIMIT_SHUTDOWN
    "TAG_ASIC_TEMPERATURE": 11,
    "TAG_VREG_TEMPERATURE": 12,
    "TAG_BOARD_TEMPERATURE": 13,
    "TAG_AICLK": 14,
    "TAG_AXICLK": 15,
    "TAG_ARCCLK": 16,
    "TAG_L2CPUCLK0": 17,
    "TAG_L2CPUCLK1": 18,
    "TAG_L2CPUCLK2": 19,
    "TAG_L2CPUCLK3": 20,
    "TAG_ETH_LIVE_STATUS": 21,
    "TAG_GDDR_STATUS": 22,
    "TAG_GDDR_SPEED": 23,
    "TAG_ETH_FW_VERSION": 24,
    "TAG_GDDR_FW_VERSION": 25,
    "TAG_BM_APP_FW_VERSION": 26,
    "TAG_BM_BL_FW_VERSION": 27,
    "TAG_FLASH_BUNDLE_VERSION": 28,
    "TAG_CM_FW_VERSION": 29,
    "TAG_L2CPU_FW_VERSION": 30,
    "TAG_FAN_SPEED": 31,
    "TAG_TIMER_HEARTBEAT": 32,
    "TAG_TELEM_ENUM_COUNT": 33,
    "TAG_ENABLED_TENSIX_COL": 34,
    "TAG_ENABLED_ETH": 35,
    "TAG_ENABLED_GDDR": 36,
    "TAG_ENABLED_L2CPU": 37,
    "TAG_PCIE_USAGE": 38,
    "TAG_INPUT_CURRENT": 39,
    "TAG_NOC_TRANSLATION": 40,
    "TAG_FAN_RPM": 41,
    "TAG_GDDR_0_1_TEMP": 42,
    "TAG_GDDR_2_3_TEMP": 43,
    "TAG_GDDR_4_5_TEMP": 44,
    "TAG_GDDR_6_7_TEMP": 45,
    "TAG_GDDR_0_1_CORR_ERRS": 46,
    "TAG_GDDR_2_3_CORR_ERRS": 47,
    "TAG_GDDR_4_5_CORR_ERRS": 48,
    "TAG_GDDR_6_7_CORR_ERRS": 49,
    "TAG_GDDR_UNCORR_ERRS": 50,
    "TAG_MAX_GDDR_TEMP": 51,
    "TAG_ASIC_LOCATION": 52,
    "TAG_AICLK_LIMIT_MAX": 53,
    "TAG_TDP_LIMIT_MAX": 54,
    "TAG_TDC_LIMIT_MAX": 55,
    "TAG_THM_LIMIT_THROTTLE": 56,
    "TAG_FW_BUILD_DATE": 57,
    "TAG_TT_FLASH_VERSION": 58,
    "TAG_ENABLED_TENSIX_ROW": 59,
    "TAG_THERM_TRIP_COUNT": 61,
    "TAG_ASIC_ID_HIGH": 62,
    "TAG_ASIC_ID_LOW": 63,
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
