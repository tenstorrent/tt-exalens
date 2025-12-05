# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from ttexalens.hardware.memory_block import MemoryBlock
from intervaltree import Interval, IntervalTree


class MemoryMap:
    """Catalog of memory blocks with address or name based lookup."""

    def __init__(self):
        self.noc_address_to_block_name_mapping = IntervalTree()
        self.name_to_block_mapping: dict[str, MemoryBlock] = {}

    def map_block(self, name: str, memory_block: MemoryBlock) -> None:
        # Currently doing mapping for blocks having NoC address
        if memory_block.address.noc_address is None:
            return

        self.name_to_block_mapping[name] = memory_block
        self.noc_address_to_block_name_mapping.addi(
            memory_block.address.noc_address,
            memory_block.address.noc_address + memory_block.size - 1,
            name,
        )

    def map_blocks(self, blocks: dict[str, MemoryBlock]) -> None:
        for name, memory_block in blocks.items():
            self.map_block(name, memory_block)

    def get_block_name_by_noc_address(self, noc_address: int) -> str | None:
        intervals = self.noc_address_to_block_name_mapping.at(noc_address)
        if not intervals:
            return None

        assert len(intervals) == 1, "MemoryMap cannot have overlapping memory blocks"
        return next(iter(intervals)).data

    def get_block_by_name(self, name: str) -> MemoryBlock | None:
        return self.name_to_block_mapping.get(name, None)
