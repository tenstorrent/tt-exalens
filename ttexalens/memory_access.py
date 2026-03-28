# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.exceptions import ReadOnlyMemoryError, RestrictedMemoryAccessError

if TYPE_CHECKING:
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.hardware.risc_debug import RiscDebug, RiscLocation


class MemoryAccess(ABC):
    """
    Abstract interface for reading and writing data from a target address space.
    """

    @abstractmethod
    def read(self, private_address: int, size_bytes: int) -> bytes:
        """
        Read 'size_bytes' bytes from 'private_address' and return them as bytes.
        'private_address' is the address as seen from the core's private address space, which may be translated to a NOC address by the implementation.
        """
        pass

    def read_word(self, private_address: int) -> int:
        """
        Read a word from 'private_address' and return it as an integer.
        'private_address' is the address as seen from the core's private address space, which may be translated to a NOC address by the implementation.
        """
        data_bytes = self.read(private_address, 4)
        return int.from_bytes(data_bytes, byteorder="little")

    @abstractmethod
    def write(self, private_address: int, data: bytes) -> None:
        """
        Write 'data' bytes to 'private_address'.
        'private_address' is the address as seen from the core's private address space, which may be translated to a NOC address by the implementation.
        """
        pass

    def write_word(self, private_address: int, value: int) -> None:
        """
        Write a word to 'private_address'.
        'private_address' is the address as seen from the core's private address space, which may be translated to a NOC address by the implementation.
        """
        data_bytes = value.to_bytes(4, byteorder="little")
        self.write(private_address, data_bytes)

    @staticmethod
    def create(
        risc_debug: RiscDebug,
        ensure_halted_access: bool = True,
        restricted_access: bool = True,
        safe_mode: bool | None = None,
    ) -> "MemoryAccess":
        return RiscDebugMemoryAccess(
            risc_debug,
            ensure_halted_access=ensure_halted_access,
            restricted_access=restricted_access,
            safe_mode=safe_mode,
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
        from ttexalens.exceptions import MemoryLayoutError

        self._location = location
        l1 = location.noc_block.noc_memory_map.find_by_name("l1")
        if l1 is None:
            raise MemoryLayoutError(f"Could not find L1 memory block at location {location}", location)
        if l1.memory_block.address.private_address is None:
            raise MemoryLayoutError(f"Found L1 memory block without private address at location {location}", location)
        if l1.memory_block.address.noc_address is None:
            raise MemoryLayoutError(f"Found L1 memory block without NOC address at location {location}", location)
        self.l1_block = l1.memory_block

    def _tranlate_to_noc_address(self, private_address: int) -> int:
        assert self.l1_block.address.private_address is not None, "L1 memory block has no private address"
        assert self.l1_block.address.noc_address is not None, "L1 memory block has no NOC address"
        offset = private_address - self.l1_block.address.private_address
        return self.l1_block.address.noc_address + offset

    def read(self, private_address: int, size_bytes: int) -> bytes:
        self._validate_access(private_address, size_bytes)
        noc_address = self._tranlate_to_noc_address(private_address)
        return self._location.noc_read(noc_address, size_bytes)

    def write(self, private_address: int, data: bytes) -> None:
        self._validate_access(private_address, len(data))
        noc_address = self._tranlate_to_noc_address(private_address)
        self._location.noc_write(noc_address, data)

    def _validate_access(self, private_address: int, size_bytes: int) -> None:
        base_address = self.l1_block.address.private_address
        assert base_address is not None, "L1 memory block has no private address"
        if private_address < base_address or private_address + size_bytes > base_address + self.l1_block.size:
            raise RestrictedMemoryAccessError(
                access_start=private_address, access_end=private_address + size_bytes - 1, location=self._location
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

    def read(self, private_address: int, size_bytes: int) -> bytes:
        return self._data[private_address : private_address + size_bytes]

    def write(self, private_address: int, data: bytes) -> None:
        raise ReadOnlyMemoryError(private_address, len(data))


class RiscDebugMemoryAccess(MemoryAccess):
    """
    MemoryAccess implementation that uses a RiscDebug instance to read/write
    a core’s private address space (L1 + data private memory by default).

    It can optionally:
      * ensure the core is halted while accessing memory, and
      * restrict accesses to L1/DataPrivate regions only, rejecting any
        address outside those MemoryBlocks to avoid accidental global
        or invalid accesses.
      * apply additional safety checks to prevent access to known unsafe
        memory regions (if safe_mode is enabled).
    """

    def __init__(
        self,
        risc_debug: RiscDebug,
        ensure_halted_access: bool = True,
        restricted_access: bool = True,
        safe_mode: bool | None = None,
    ):
        self._risc_debug = risc_debug
        self._ensure_halted_access = ensure_halted_access  # will ensure the RISC will be halted for memory access
        self._restricted_access = restricted_access  # restrict access to only L1 and Data Private Memory
        self._safe_mode = safe_mode  # additional safety checks to prevent access to known unsafe memory regions

    def read(self, private_address: int, size_bytes: int) -> bytes:
        self._validate_access(private_address, size_bytes)

        if self._ensure_halted_access or self._risc_debug.can_debug():
            with self._risc_debug.ensure_private_memory_access():
                return self._risc_debug.read_memory_bytes(private_address, size_bytes, safe_mode=self._safe_mode)
        else:
            return self._risc_debug.read_memory_bytes(private_address, size_bytes, safe_mode=self._safe_mode)

    def write(self, private_address: int, data: bytes) -> None:
        self._validate_access(private_address, len(data))

        if self._ensure_halted_access or self._risc_debug.can_debug():
            with self._risc_debug.ensure_private_memory_access():
                self._risc_debug.write_memory_bytes(private_address, data, safe_mode=self._safe_mode)
        else:
            self._risc_debug.write_memory_bytes(private_address, data, safe_mode=self._safe_mode)

    def _validate_access(self, private_address: int, size_bytes: int) -> None:
        if self._restricted_access:
            l1: MemoryBlock = self._risc_debug.get_l1()
            assert l1.address.private_address is not None, "L1 memory block has no private address"

            data_private_memory: MemoryBlock | None = self._risc_debug.get_data_private_memory()
            if data_private_memory is not None:
                assert (
                    data_private_memory.address.private_address is not None
                ), "Data Private Memory block has no private address"

            address_end = private_address + size_bytes - 1
            inside_l1: bool = l1.contains_private_address(private_address) and l1.contains_private_address(address_end)
            inside_data_private_memory: bool = (
                data_private_memory is not None
                and data_private_memory.contains_private_address(private_address)
                and data_private_memory.contains_private_address(address_end)
            )

            if not inside_l1 and not inside_data_private_memory:
                raise RestrictedMemoryAccessError(
                    access_start=private_address,
                    access_end=address_end,
                    location=self._risc_debug.risc_location.location,
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

    def read(self, private_address: int, size_bytes: int) -> bytes:
        if private_address >= self._cached_address and private_address + size_bytes <= self._cached_address + len(
            self._cached_data
        ):
            offset = private_address - self._cached_address
            return self._cached_data[offset : offset + size_bytes]
        else:
            return self._base_mem_access.read(private_address, size_bytes)

    def write(self, private_address: int, data: bytes) -> None:
        self._base_mem_access.write(private_address, data)
