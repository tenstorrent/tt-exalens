# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from typing import TypedDict


class MemoryRegion(TypedDict):
    """A simple memory region descriptor."""

    noc_address: int
    size: int


class NocMemoryMap:
    """Catalog of memory regions with address-based lookup."""

    def __init__(self, regions: dict[str, MemoryRegion]):
        """Initialize memory map with named regions.

        Args:
            regions: Dictionary mapping region names to their descriptors
        """
        self.regions = regions

    def get_region_by_noc_address(self, noc_address: int) -> str | None:
        """Find the region name for a given NOC address.

        Args:
            noc_address: The NOC address to look up

        Returns:
            The name of the region containing the address, or None if not found
        """
        for name, region in self.regions.items():
            region_start = region["noc_address"]
            region_end = region_start + region["size"]
            if region_start <= noc_address < region_end:
                return name
        return None

    def get_region_by_name(self, name: str) -> MemoryRegion | None:
        """Get a memory region by its name.

        Args:
            name: The name of the region to retrieve

        Returns:
            The MemoryRegion descriptor, or None if not found
        """
        return self.regions.get(name)
