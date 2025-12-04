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
        # Note: sortedBlocks only contains blocks with noc_address
        self.sortedBlocks: list[tuple[MemoryBlock, str]] = sorted(
            [(block, name) for name, block in blocks.items() if block.address.noc_address is not None],
            key=lambda item: item[0].address.noc_address,  # type: ignore[return-value,arg-type]
        )

    def get_block_name_by_address(self, address: int) -> str | None:
        """
        Find the block name for a given address.
        Currently only NOC addresses are supported.

        Args:
            address: The NOC address to look up

        Returns:
            The name of the block containing the address, or None if not found
        """

        # Linear search is sufficient since the number of blocks is small
        # Move to binary search if the number of blocks increases
        for block, name in self.sortedBlocks:
            noc_addr = block.address.noc_address
            assert noc_addr is not None  # Guaranteed by sortedBlocks construction
            if noc_addr <= address < noc_addr + block.size:
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
