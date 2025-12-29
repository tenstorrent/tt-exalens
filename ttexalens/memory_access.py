# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ttexalens.hardware.memory_block import MemoryBlock

if TYPE_CHECKING:
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.hardware.risc_debug import RiscDebug


class MemoryAccess(ABC):
    """
    Abstract interface for reading and writing data from a target address space.
    """

    @abstractmethod
    def read(self, address: int, size_bytes: int) -> bytes:
        """
        Read 'size_bytes' bytes from 'address' and return them as bytes.
        """
        pass

    def read_word(self, address: int) -> int:
        """
        Read a word from 'address' and return it as an integer.
        """
        data_bytes = self.read(address, 4)
        return int.from_bytes(data_bytes, byteorder="little")

    @abstractmethod
    def write(self, address: int, data: bytes) -> None:
        """
        Write 'data' bytes to 'address'.
        """
        pass

    def write_word(self, address: int, value: int) -> None:
        """
        Write a word to 'address'.
        """
        data_bytes = value.to_bytes(4, byteorder="little")
        self.write(address, data_bytes)

    @staticmethod
    def get(risc_debug: RiscDebug, ensure_halted_access: bool = True, restricted_access: bool = True) -> "MemoryAccess":
        return RiscDebugMemoryAccess(
            risc_debug, ensure_halted_access=ensure_halted_access, restricted_access=restricted_access
        )

    @staticmethod
    def get_l1(location: OnChipCoordinate) -> "MemoryAccess":
        return L1MemoryAccess(location)


class L1MemoryAccess(MemoryAccess):
    """
    MemoryAccess implementation that talks directly to on‑chip memory at a given
    OnChipCoordinate via tt_exalens_lib.{read,write}_from_device.

    This is used when we know an address is in the device’s global address space
    (e.g. L1 or other device-visible memory mapped region) and we want to access
    it without going through the RiscDebug abstraction.
    """

    def __init__(self, location: OnChipCoordinate):
        self._location = location

    def read(self, address: int, size_bytes: int) -> bytes:
        from ttexalens.tt_exalens_lib import read_from_device

        return read_from_device(location=self._location, addr=address, num_bytes=size_bytes)

    def write(self, address: int, data: bytes) -> None:
        from ttexalens.tt_exalens_lib import write_to_device

        write_to_device(location=self._location, addr=address, data=data)


class FixedMemoryAccess(MemoryAccess):
    """
    Read‑only MemoryAccess backed by an in‑memory byte buffer.

    Used when DWARF evaluation has already produced the bytes for a value
    (e.g. a temporary, non‑addressable expression result), so further reads
    should come from that snapshot rather than device memory. Writes are
    forbidden and will raise.
    """

    def __init__(self, data: bytes):
        self._data = data

    def read(self, address: int, size_bytes: int) -> bytes:
        return self._data[address : address + size_bytes]

    def write(self, address: int, data: bytes) -> None:
        raise Exception("FixedMemoryAccess is read-only")


class RiscDebugMemoryAccess(MemoryAccess):
    """
    MemoryAccess implementation that uses a RiscDebug instance to read/write
    a core’s private address space (L1 + data private memory by default).

    It can optionally:
      * ensure the core is halted while accessing memory, and
      * restrict accesses to L1/DataPrivate regions only, rejecting any
        address outside those MemoryBlocks to avoid accidental global
        or invalid accesses.
    """

    def __init__(self, risc_debug: RiscDebug, ensure_halted_access: bool = True, restricted_access: bool = True):
        self._risc_debug = risc_debug
        self._ensure_halted_access = ensure_halted_access  # will ensure the RISC will be halted for memory access
        self._restricted_access = restricted_access  # restrict access to only L1 and Data Private Memory

    def read(self, address: int, size_bytes: int) -> bytes:
        self.validate_access(address, size_bytes)

        if self._ensure_halted_access or self._risc_debug.can_debug():
            with self._risc_debug.ensure_private_memory_access():
                return self._risc_debug.read_memory_bytes(address, size_bytes)
        else:
            return self._risc_debug.read_memory_bytes(address, size_bytes)

    def write(self, address: int, data: bytes) -> None:
        self.validate_access(address, len(data))

        if self._ensure_halted_access or self._risc_debug.can_debug():
            with self._risc_debug.ensure_private_memory_access():
                self._risc_debug.write_memory_bytes(address, data)
        else:
            self._risc_debug.write_memory_bytes(address, data)

    def validate_access(self, address: int, size_bytes: int) -> None:
        if self._restricted_access:
            l1: MemoryBlock = self._risc_debug.get_l1()
            data_private_memory: MemoryBlock | None = self._risc_debug.get_data_private_memory()
            inside_l1: bool = l1.contains_private_address(address) and l1.contains_private_address(
                address + size_bytes - 1
            )
            inside_data_private_memory: bool = (
                data_private_memory is not None
                and data_private_memory.contains_private_address(address)
                and data_private_memory.contains_private_address(address + size_bytes - 1)
            )

            if not inside_l1 and not inside_data_private_memory:
                raise Exception(
                    f"RiscDebugMemoryAccess restricted access: Address 0x{address:08x} is outside of L1 and Data Private Memory"
                )


class CachedReadMemoryAccess(MemoryAccess):
    """
    MemoryAccess implementation that serves reads from a cached byte range when
    possible, and otherwise falls back to an underlying MemoryAccess.
    """

    def __init__(self, cached_address: int, cached_data: bytes, base_mem_access: MemoryAccess):
        self._base_mem_access = base_mem_access
        self._cached_address = cached_address
        self._cached_data = cached_data

    def read(self, address: int, size_bytes: int) -> bytes:
        if address >= self._cached_address and address + size_bytes <= self._cached_address + len(self._cached_data):
            offset = address - self._cached_address
            return self._cached_data[offset : offset + size_bytes]
        else:
            return self._base_mem_access.read(address, size_bytes)

    def write(self, address: int, data: bytes) -> None:
        self._base_mem_access.write(address, data)
