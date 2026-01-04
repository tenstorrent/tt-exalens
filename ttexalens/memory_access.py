# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ttexalens.hardware.memory_block import MemoryBlock

if TYPE_CHECKING:
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.hardware.risc_debug import RiscDebug, RiscLocation


class RestrictedMemoryAccessError(Exception):
    """
    Raised when attempting to access memory outside of allowed regions
    (e.g., outside L1 or data private memory when restricted_access for them is is enabled).
    """

    def __init__(self, access_start: int, access_end: int, location: OnChipCoordinate | RiscLocation):
        """
        Args:
            access_start: Starting address of the attempted access
            access_end: Ending address of the attempted access (inclusive)
            location: Location of the RISC or on-chip memory where the access was attempted
        """

        from ttexalens.coordinate import OnChipCoordinate

        self.access_start = access_start
        self.access_end = access_end
        if isinstance(location, OnChipCoordinate):
            self.risc_name = None
            self.neo_id = None
            self.location = location
        else:
            self.risc_name = location.risc_name
            self.neo_id = location.neo_id
            self.location = location.location

    def __str__(self) -> str:
        """Generate error message lazily when the exception is converted to string."""

        msg = f"Restricted access: Address range [0x{self.access_start:08x}, 0x{self.access_end:08x}] is outside allowed memory regions."
        if self.risc_name:
            if self.neo_id is not None:
                return f"RISC '{self.risc_name}' (Neo ID {self.neo_id}) at {self.location.to_user_str()}, {msg}"
            else:
                return f"RISC '{self.risc_name}' at {self.location.to_user_str()}, {msg}"

        return f"{self.location.to_user_str()}, {msg}"


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
    def create(
        risc_debug: RiscDebug, ensure_halted_access: bool = True, restricted_access: bool = True
    ) -> "MemoryAccess":
        return RiscDebugMemoryAccess(
            risc_debug, ensure_halted_access=ensure_halted_access, restricted_access=restricted_access
        )

    @staticmethod
    def create_l1(location: OnChipCoordinate) -> "MemoryAccess":
        return L1MemoryAccess(location)


class L1MemoryAccess(MemoryAccess):
    """
    MemoryAccess implementation that talks directly to on‑chip memory at a given
    OnChipCoordinate via tt_exalens_lib.{read,write}_from_device.

    This is used when we know an address is L1 and we want to access
    it without going through the RiscDebug abstraction.
    """

    def __init__(self, location: OnChipCoordinate):
        self._location = location
        l1 = location.noc_block.get_noc_memory_map().get_block_by_name("l1")
        if l1 is None:
            raise Exception(f"Could not find L1 memory block at location {location}")
        if l1.address.noc_address is None:
            raise Exception(f"Found L1 memory block without NOC address at location {location}")

        self.base_address = l1.address.noc_address
        self.size = l1.size

    def read(self, address: int, size_bytes: int) -> bytes:
        self.validate_access(address, size_bytes)
        return self._location.noc_read(address, size_bytes)

    def write(self, address: int, data: bytes) -> None:
        self.validate_access(address, len(data))
        self._location.noc_write(address, data)

    def validate_access(self, address: int, size_bytes: int) -> None:
        if address < self.base_address or address + size_bytes > self.base_address + self.size:
            raise RestrictedMemoryAccessError(
                access_start=address, access_end=address + size_bytes - 1, location=self._location
            )


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
            assert l1.address.private_address is not None, "L1 memory block has no private address"

            data_private_memory: MemoryBlock | None = self._risc_debug.get_data_private_memory()
            if data_private_memory is not None:
                assert (
                    data_private_memory.address.private_address is not None
                ), "Data Private Memory block has no private address"

            address_end = address + size_bytes - 1
            inside_l1: bool = l1.contains_private_address(address) and l1.contains_private_address(address_end)
            inside_data_private_memory: bool = (
                data_private_memory is not None
                and data_private_memory.contains_private_address(address)
                and data_private_memory.contains_private_address(address_end)
            )

            if not inside_l1 and not inside_data_private_memory:
                raise RestrictedMemoryAccessError(
                    access_start=address, access_end=address_end, location=self._risc_debug.risc_location.location
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
