# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from ttexalens.hardware.memory_block import MemoryBlock
from intervaltree import Interval, IntervalTree


@dataclass
class MemoryMapBlockInfo:
    name: str
    memory_block: MemoryBlock
    safe_to_read: Callable[[int, int], bool] | bool | None = None
    safe_to_write: Callable[[int, int], bool] | bool | None = None
    access_check: Callable[[], bool] | None = None

    @property
    def is_safe_to_read(self, address: int, num_bytes: int) -> bool:
        if callable(self.safe_to_read):
            return self.safe_to_read(address, num_bytes)
        return self.safe_to_read if self.safe_to_read is not None else True

    @property
    def is_safe_to_write(self, address: int, num_bytes: int) -> bool:
        if callable(self.safe_to_write):
            return self.safe_to_write(address, num_bytes)
        return self.safe_to_write if self.safe_to_write is not None else False

    @property
    def is_accessible(self) -> bool:
        if self.access_check is None:
            return True
        return self.access_check()


class MemoryMap:
    """Catalog of memory blocks with address or name based lookup."""

    def __init__(self):
        self._noc_addresses = IntervalTree()
        self._private_addresses = IntervalTree()
        self._bar0_addresses = IntervalTree()
        self._blocks_info: dict[str, MemoryMapBlockInfo] = {}

    def add_block(self, block_info: MemoryMapBlockInfo):
        if block_info.name in self._blocks_info:
            raise ValueError(f"Memory block with name '{block_info.name}' is already mapped")
        self._blocks_info[block_info.name] = block_info

        # Add to appropriate interval tree(s)
        if block_info.memory_block.address.noc_address is not None:
            self._noc_addresses.addi(
                block_info.memory_block.address.noc_address,
                block_info.memory_block.address.noc_address + block_info.memory_block.size - 1,
                block_info,
            )
        if block_info.memory_block.address.private_address is not None:
            self._private_addresses.addi(
                block_info.memory_block.address.private_address,
                block_info.memory_block.address.private_address + block_info.memory_block.size - 1,
                block_info,
            )
        if block_info.memory_block.address.bar0_address is not None:
            self._bar0_addresses.addi(
                block_info.memory_block.address.bar0_address,
                block_info.memory_block.address.bar0_address + block_info.memory_block.size - 1,
                block_info,
            )

    def add_blocks(self, blocks: list[MemoryMapBlockInfo]) -> None:
        for block_info in blocks:
            self.add_block(block_info)

    def map_block(
        self,
        name: str,
        memory_block: MemoryBlock,
        safe_to_read: bool,
        safe_to_write: bool,
        access_check: Callable[[], bool] | None = None,
    ) -> None:
        self.add_block(
            MemoryMapBlockInfo(
                name, memory_block, safe_to_read=safe_to_read, safe_to_write=safe_to_write, access_check=access_check
            )
        )

    def find_by_noc_address(self, noc_address: int) -> MemoryMapBlockInfo | None:
        return MemoryMap._find_by_address(noc_address, self._noc_addresses)

    def find_next_by_noc_address(self, noc_address: int) -> MemoryMapBlockInfo | None:
        return MemoryMap._find_next_block(noc_address, self._noc_addresses)

    def find_by_private_address(self, private_address: int) -> MemoryMapBlockInfo | None:
        return MemoryMap._find_by_address(private_address, self._private_addresses)

    def find_next_by_private_address(self, private_address: int) -> MemoryMapBlockInfo | None:
        return MemoryMap._find_next_block(private_address, self._private_addresses)

    def find_by_bar0_address(self, bar0_address: int) -> MemoryMapBlockInfo | None:
        return MemoryMap._find_by_address(bar0_address, self._bar0_addresses)

    def find_next_by_bar0_address(self, bar0_address: int) -> MemoryMapBlockInfo | None:
        return MemoryMap._find_next_block(bar0_address, self._bar0_addresses)

    def find_by_name(self, name: str) -> MemoryMapBlockInfo | None:
        return self._blocks_info.get(name, None)

    @staticmethod
    def _find_by_address(address: int, tree: IntervalTree) -> MemoryMapBlockInfo | None:
        intervals: set[Interval] = tree.at(address)
        if not intervals:
            return None

        assert len(intervals) == 1, "MemoryMap cannot have overlapping memory blocks"
        result: MemoryMapBlockInfo = next(iter(intervals)).data
        return result

    @staticmethod
    def _find_next_block(address: int, tree: IntervalTree) -> MemoryMapBlockInfo | None:
        next: Interval | None = None
        for interval in tree:
            if interval.begin > address:
                if next is None or interval.begin < next.begin:
                    next = interval
        return next.data if next is not None else None
