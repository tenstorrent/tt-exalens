# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.noc_block import NocBlock


telemetry_tags_map: dict[str, int] = {
    "TAG_BOARD_ID": 1,
    "TAG_AICLK": 2,
    "TAG_AXICLK": 3,
    "TAG_ARCCLK": 4,
    "TAG_HEARTBEAT": 5,
}


class ArcBlock(NocBlock):
    def __init__(
        self, location: OnChipCoordinate, block_type: str, telemetry_tags: dict[str, int] = telemetry_tags_map
    ):
        super().__init__(location, block_type)

        self.telemetry_tags = telemetry_tags
        self.telemetry_tag_ids: set[int] = set(telemetry_tags.values())

    def has_telemetry_tag_id(self, tag_id: int) -> bool:
        """Returns the keys of the ARC telemetry tags map."""
        return tag_id in self.telemetry_tag_ids

    def get_telemetry_tag_id(self, tag_name) -> int | None:
        """Returns the telemetry tag ID for a given tag name."""
        if tag_name in self.telemetry_tags:
            return self.telemetry_tags[tag_name]
        return None
