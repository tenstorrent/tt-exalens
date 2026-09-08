# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from functools import cached_property
from typing import TYPE_CHECKING

import tt_umd

from ttexalens.exceptions import TTException
from ttexalens.util import FirmwareVersion

if TYPE_CHECKING:
    from ttexalens.context import NocId
    from ttexalens.device import Device

# For new firmware version (18.4 or higher) we have same telemetry tags for both wormhole and blackhole
# We no longer support firmware telemetry for firmware versions 18.3 and lower

CUTOFF_FIRMWARE_VERSION = FirmwareVersion(18, 4, 0)

# Telemetry tags are defined by UMD
telemetry_tags_map: dict[str, int] = {tag.name: tag.value for tag in tt_umd.TelemetryTag}


class FirmwareTelemetry:
    """Firmware telemetry of a single device.

    Telemetry is served by the device firmware and read through UMD's FirmwareTelemetryReader,
    so it is not tied to any particular NOC block. Reads are delegated to the device, which
    keeps NOC failover and reset/retry handling in one place.
    """

    def __init__(self, device: Device):
        self.device = device

    @cached_property
    def is_supported(self) -> bool:
        """Returns whether the device firmware is new enough to serve telemetry."""
        return self.device.firmware_version >= CUTOFF_FIRMWARE_VERSION

    @property
    def telemetry_tags(self) -> dict[str, int]:
        """Returns the telemetry tags map, raising if the firmware is too old to serve telemetry."""
        if not self.is_supported:
            raise TTException(
                f"We no longer support firmware telemetry for firmware versions 18.3 and lower. This device is running firmware version {self.device.firmware_version}"
            )
        return telemetry_tags_map

    @property
    def telemetry_tag_ids(self) -> set[int]:
        """Returns the set of known telemetry tag IDs."""
        return set(self.telemetry_tags.values())

    def has_telemetry_tag_id(self, tag_id: int) -> bool:
        """Returns whether the given telemetry tag ID exists."""
        return tag_id in self.telemetry_tag_ids

    def get_telemetry_tag_id(self, tag_name: str) -> int | None:
        """Returns the telemetry tag ID for a given tag name, or None if there is no such tag."""
        return self.telemetry_tags.get(tag_name)

    def read_entry(self, telemetry_tag: int | str, noc_id: NocId | None = None) -> int:
        """Reads a telemetry entry, given either its tag name or its tag ID.

        Args:
            telemetry_tag (int | str): Name or ID of the tag to read.
            noc_id (NocId, optional): NOC ID to use. If None, the device's active NOC is used.

        Returns:
            int: Value of the telemetry entry.
        """
        if isinstance(telemetry_tag, str):
            telemetry_tag_id = self.get_telemetry_tag_id(telemetry_tag)
            if telemetry_tag_id is None:
                raise TTException(f"Telemetry tag {telemetry_tag} does not exist.")
        else:
            if not self.has_telemetry_tag_id(telemetry_tag):
                raise TTException(f"Telemetry tag ID {telemetry_tag} does not exist.")
            telemetry_tag_id = telemetry_tag

        return self.device.read_firmware_telemetry_entry(noc_id, telemetry_tag_id)
