# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from ttexalens.hardware.memory_block import MemoryBlock


class MemoryMap:
    """Catalog of memory blocks with address or name based lookup."""

    def __init__(self, blocks: dict[str, MemoryBlock]):
        """
        Initialize memory map with named blocks.

        Args:
            blocks: Dictionary mapping block names to their descriptors
        """

        self.blocks: dict[str, MemoryBlock] = blocks
        self.sortedBlocks: list[tuple[MemoryBlock, str]] = sorted(
            [(block, name) for name, block in blocks.items()], key=lambda item: item[0].address.noc_address
        )

    def get_block_by_address(self, noc_address: int) -> str | None:
        """
        Find the block name for a given NOC address.

        Args:
            noc_address: The NOC address to look up

        Returns:
            The name of the block containing the address, or None if not found
        """

        # Linear search is sufficient since the number of blocks is small
        # Move to binary search if the number of blocks increases
        for block, name in self.sortedBlocks:
            if block.address.noc_address <= noc_address < block.address.noc_address + block.size:
                return name
        return None

    def get_block_by_name(self, name: str) -> MemoryBlock | None:
        """
        Get a memory block by its name.
        Args:
            name: The name of the block to retrieve

        Returns:
            The MemoryBlock descriptor, or None if not found
        """
        return self.blocks.get(name)
