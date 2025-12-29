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
    Simple class that allows reading and writing memory from a given address.
    """

    @abstractmethod
    def read(self, address: int, size_bytes: int) -> bytes:
        """
        Read 'size_bytes' bytes from 'address' and return them as bytes.
        """
        pass

    @abstractmethod
    def write(self, address: int, data: bytes) -> None:
        """
        Write 'data' bytes to 'address'.
        """
        pass

    @staticmethod
    def get(risc_debug: RiscDebug, ensure_halted_access: bool = True, restricted_access: bool = True) -> "MemoryAccess":
        return RiscDebugMemoryAccess(
            risc_debug, ensure_halted_access=ensure_halted_access, restricted_access=restricted_access
        )

    @staticmethod
    def get_l1(location: OnChipCoordinate) -> "MemoryAccess":
        return L1MemoryAccess(location)


class L1MemoryAccess(MemoryAccess):
    def __init__(self, location: OnChipCoordinate):
        self._location = location

    def read(self, address: int, size_bytes: int) -> bytes:
        from ttexalens.tt_exalens_lib import read_from_device

        return read_from_device(location=self._location, addr=address, num_bytes=size_bytes)

    def write(self, address: int, data: bytes) -> None:
        from ttexalens.tt_exalens_lib import write_to_device

        write_to_device(location=self._location, addr=address, data=data)


class FixedMemoryAccess(MemoryAccess):
    def __init__(self, data: bytes):
        self._data = data

    def read(self, address: int, size_bytes: int) -> bytes:
        return self._data[address : address + size_bytes]

    def write(self, address: int, data: bytes) -> None:
        raise Exception("FixedMemoryAccess is read-only")


class RiscDebugMemoryAccess(MemoryAccess):
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
