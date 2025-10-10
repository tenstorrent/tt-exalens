# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.util import FirmwareVersion, TTException

# For new firmware version (18.4 or higher) we have same telemetry tags for both wormhole and blackhole
# We no longer support ARC telemetry for firmware versions 18.3 and lower

CUTOFF_FIRMWARE_VERSION = FirmwareVersion((18, 4, 0))

telemetry_tags_map: dict[str, int] = {
    "BOARD_ID_HIGH": 1,
    "BOARD_ID_LOW": 2,
    "ASIC_ID": 3,
    "HARVESTING_STATE": 4,
    "UPDATE_TELEM_SPEED": 5,
    "VCORE": 6,
    "TDP": 7,
    "TDC": 8,
    "VDD_LIMITS": 9,
    "THM_LIMITS": 10,
    "ASIC_TEMPERATURE": 11,
    "VREG_TEMPERATURE": 12,
    "BOARD_TEMPERATURE": 13,
    "AICLK": 14,
    "AXICLK": 15,
    "ARCCLK": 16,
    "L2CPUCLK0": 17,
    "L2CPUCLK1": 18,
    "L2CPUCLK2": 19,
    "L2CPUCLK3": 20,
    "ETH_LIVE_STATUS": 21,
    "DDR_STATUS": 22,
    "DDR_SPEED": 23,
    "ETH_FW_VERSION": 24,
    "DDR_FW_VERSION": 25,
    "BM_APP_FW_VERSION": 26,
    "BM_BL_FW_VERSION": 27,
    "FLASH_BUNDLE_VERSION": 28,
    "CM_FW_VERSION": 29,
    "L2CPU_FW_VERSION": 30,
    "FAN_SPEED": 31,
    "TIMER_HEARTBEAT": 32,
    "TELEMETRY_ENUM_COUNT": 33,
    "ENABLED_TENSIX_COL": 34,
    "ENABLED_ETH": 35,
    "ENABLED_GDDR": 36,
    "ENABLED_L2CPU": 37,
    "PCIE_USAGE": 38,
    "NUMBER_OF_TAGS": 39,
    "ASIC_LOCATION": 52,
    "AICLK_LIMIT_MAX": 63,
}


class ArcBlock(NocBlock):
    def __init__(
        self, location: OnChipCoordinate, block_type: str, telemetry_tags: dict[str, int] = telemetry_tags_map
    ):
        super().__init__(location, block_type)
        self.telemetry_tags = (
            telemetry_tags if self.location.device._firmware_version >= CUTOFF_FIRMWARE_VERSION else None
        )
        self.telemetry_tag_ids: set[int] | None = set(telemetry_tags.values()) if self.telemetry_tags else None

    def has_telemetry_tag_id(self, tag_id: int) -> bool:
        """Returns the keys of the ARC telemetry tags map."""
        if self.telemetry_tag_ids is None:
            raise TTException(
                f"We no longer support ARC telemetry for firmware versions 18.3 and lower. This device is running firmware version {self.location.device._firmware_version}"
            )
        return tag_id in self.telemetry_tag_ids

    def get_telemetry_tag_id(self, tag_name) -> int | None:
        """Returns the telemetry tag ID for a given tag name."""
        if self.telemetry_tags is None:
            raise TTException(
                f"We no longer support ARC telemetry for firmware versions 18.3 and lower. This device is running firmware version {self.location.device._firmware_version}"
            )
        if tag_name in self.telemetry_tags:
            return self.telemetry_tags[tag_name]
        return None
