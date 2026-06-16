# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from bisect import bisect_right
from dataclasses import dataclass
import threading
from typing import Callable
from ttexalens.hardware.memory_block import MemoryBlock


@dataclass
class MemoryMapBlockInfo:
    name: str
    memory_block: MemoryBlock
    safe_to_read: Callable[[int, int], bool] | bool | None = None
    safe_to_write: Callable[[int, int], bool] | bool | None = None
    access_check: Callable[[], bool] | None = None

    def is_safe_to_read(self, address: int, num_bytes: int) -> bool:
        if callable(self.safe_to_read):
            return self.safe_to_read(address, num_bytes)
        return self.safe_to_read if self.safe_to_read is not None else True

    def is_safe_to_write(self, address: int, num_bytes: int) -> bool:
        if callable(self.safe_to_write):
            return self.safe_to_write(address, num_bytes)
        return self.safe_to_write if self.safe_to_write is not None else False

    @property
    def is_accessible(self) -> bool:
        if self.access_check is None:
            return True
        return self.access_check()


@dataclass
class Interval:
    """A half-open address range ``[start, end)`` (start inclusive, end exclusive) and the block mapped to it."""

    start: int
    end: int
    block: MemoryMapBlockInfo


class IntervalMap:
    """Sorted, non-overlapping address intervals supporting binary-search lookup."""

    def __init__(self, intervals: list[Interval]):
        self._intervals = sorted(intervals, key=lambda interval: interval.start)
        self._starts = [interval.start for interval in self._intervals]
        for i in range(len(self._intervals) - 1):
            current = self._intervals[i]
            following = self._intervals[i + 1]
            assert current.end <= following.start, (
                f"MemoryMap cannot have overlapping memory blocks: "
                f"'{current.block.name}' [{current.start:#x}, {current.end:#x}) overlaps "
                f"'{following.block.name}' [{following.start:#x}, {following.end:#x})"
            )
        # Cache the last interval a lookup landed in; callers usually hit the same block repeatedly.
        self._last_found: Interval | None = None

    def _find_index(self, address: int) -> int:
        # Index of the rightmost interval whose start is <= address (-1 if address precedes all).
        return bisect_right(self._starts, address) - 1

    def find(self, address: int) -> MemoryMapBlockInfo | None:
        # Fast path: the previous lookup's interval often contains this address too.
        cached = self._last_found
        if cached is not None and cached.start <= address < cached.end:
            return cached.block

        # Only the rightmost interval starting at or before the address can contain it.
        index = self._find_index(address)
        if index < 0:
            return None
        interval = self._intervals[index]
        if address < interval.end:
            self._last_found = interval
            return interval.block
        return None

    def find_next(self, address: int) -> MemoryMapBlockInfo | None:
        # First interval whose start is strictly greater than address.
        index = self._find_index(address) + 1
        if index < len(self._intervals):
            return self._intervals[index].block
        return None


class MemoryMap:
    """Catalog of memory blocks with address or name based lookup."""

    __cache_of_memory_maps: dict[tuple[type, str], MemoryMap] = {}
    __cache_lock: threading.Lock = threading.Lock()

    def __init__(self):
        self._noc_addresses = IntervalMap([])
        self._private_addresses = IntervalMap([])
        self._bar0_addresses = IntervalMap([])
        self._blocks_info: dict[str, MemoryMapBlockInfo] = {}

    def initialize_blocks(self, blocks: list[MemoryMapBlockInfo]) -> None:
        noc_intervals: list[Interval] = []
        private_intervals: list[Interval] = []
        bar0_intervals: list[Interval] = []

        for block_info in blocks:
            if block_info.name in self._blocks_info:
                raise ValueError(f"Memory block with name '{block_info.name}' is already mapped")
            self._blocks_info[block_info.name] = block_info

            address = block_info.memory_block.address
            size = block_info.memory_block.size
            if address.noc_address is not None:
                noc_intervals.append(Interval(address.noc_address, address.noc_address + size, block_info))
            if address.private_address is not None:
                private_intervals.append(Interval(address.private_address, address.private_address + size, block_info))
            if address.bar0_address is not None:
                bar0_intervals.append(Interval(address.bar0_address, address.bar0_address + size, block_info))

        self._noc_addresses = IntervalMap(noc_intervals)
        self._private_addresses = IntervalMap(private_intervals)
        self._bar0_addresses = IntervalMap(bar0_intervals)

    def find_by_noc_address(self, noc_address: int) -> MemoryMapBlockInfo | None:
        return self._noc_addresses.find(noc_address)

    def find_next_by_noc_address(self, noc_address: int) -> MemoryMapBlockInfo | None:
        return self._noc_addresses.find_next(noc_address)

    def find_by_private_address(self, private_address: int) -> MemoryMapBlockInfo | None:
        return self._private_addresses.find(private_address)

    def find_next_by_private_address(self, private_address: int) -> MemoryMapBlockInfo | None:
        return self._private_addresses.find_next(private_address)

    def find_by_bar0_address(self, bar0_address: int) -> MemoryMapBlockInfo | None:
        return self._bar0_addresses.find(bar0_address)

    def find_next_by_bar0_address(self, bar0_address: int) -> MemoryMapBlockInfo | None:
        return self._bar0_addresses.find_next(bar0_address)

    def find_by_name(self, name: str) -> MemoryMapBlockInfo | None:
        return self._blocks_info.get(name, None)

    @staticmethod
    def get_memory_map_from_cache(
        type_to_cache: type, cache_key: str, block_list_lambda: Callable[[], list[MemoryMapBlockInfo]]
    ) -> MemoryMap:
        with MemoryMap.__cache_lock:
            memory_map = MemoryMap.__cache_of_memory_maps.get((type_to_cache, cache_key))
            if memory_map is None:
                memory_map = MemoryMap()
                memory_map.initialize_blocks(block_list_lambda())
                MemoryMap.__cache_of_memory_maps[(type_to_cache, cache_key)] = memory_map
            return memory_map
