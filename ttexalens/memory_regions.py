# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttexalens.hardware.memory_block import MemoryBlock


class MemoryRegions:
    """Catalog of memory regions with address-based lookup.

    Memory blocks are stored in sorted order by NOC address start for efficient lookup.
    """

    def __init__(self, blocks: list[MemoryBlock]):
        """Initialize memory regions with memory blocks sorted by NOC address.

        Args:
            blocks: List of MemoryBlock instances to map
        """
        self.blocks = sorted(
            blocks, key=lambda b: b.address.noc_address if b.address.noc_address is not None else float("inf")
        )
        self._blocks_by_name = {block.name: block for block in blocks if block.name is not None}

    def find_region_by_noc_address(self, noc_address: int) -> str:
        """Find the region name for a given NOC address.

        Args:
            noc_address: The NOC address to look up

        Returns:
            The name of the memory block containing the address, or "unknown" if not found
        """
        for block in self.blocks:
            if block.address.noc_address is not None and block.contains_noc_address(noc_address):
                return block.name if block.name is not None else "unknown"
        return "unknown"

    def find_region_by_private_address(self, private_address: int) -> str:
        """Find the region name for a given private address.

        Args:
            private_address: The private address to look up

        Returns:
            The name of the memory block containing the address, or "unknown" if not found
        """
        for block in self.blocks:
            if block.address.private_address is not None and block.contains_private_address(private_address):
                return block.name if block.name is not None else "unknown"
        return "unknown"

    def get_block(self, name: str) -> MemoryBlock:
        """Get a memory block by its name.

        Args:
            name: The name of the memory block to retrieve

        Returns:
            The MemoryBlock with the given name

        Raises:
            KeyError: If no block with the given name exists
        """
        if name not in self._blocks_by_name:
            raise KeyError(f"Memory block '{name}' not found in memory map")
        return self._blocks_by_name[name]
