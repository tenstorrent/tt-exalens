# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from typing import TYPE_CHECKING

from ttexalens._native_ttexalens import MemoryAccess, NoMemoryAccess
from ttexalens.exceptions import ReadOnlyMemoryError, RestrictedMemoryAccessError
from ttexalens.hardware.memory_block import MemoryBlock

if TYPE_CHECKING:
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.hardware.risc_debug import RiscDebug


def create_memory_access(
    risc_debug: RiscDebug,
    ensure_halted_access: bool = True,
    restricted_access: bool = True,
    safe_mode: bool | None = None,
) -> MemoryAccess:
    return RiscDebugMemoryAccess(
        risc_debug,
        ensure_halted_access=ensure_halted_access,
        restricted_access=restricted_access,
        safe_mode=safe_mode,
    )


def create_l1_memory_access(location: OnChipCoordinate) -> MemoryAccess:
    return L1MemoryAccess(location)


# Singleton MemoryAccess that raises on every operation. Use this whenever a
# MemoryAccess is required but no live target is available.
NO_MEMORY_ACCESS: MemoryAccess = NoMemoryAccess.instance()


class L1MemoryAccess(MemoryAccess):
    """
    MemoryAccess implementation that talks directly to on-chip memory at a given
    OnChipCoordinate via tt_exalens_lib.{read,write}_from_device.

    This is used when we know an address is L1 and we want to access
    it without going through the RiscDebug abstraction.
    """

    def __init__(self, location: OnChipCoordinate):
        super().__init__()
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

    def read(self, address: int, buffer: memoryview | bytearray) -> None:
        self._validate_access(address, len(buffer))
        noc_address = self._tranlate_to_noc_address(address)
        buffer[:] = self._location.noc_read(noc_address, len(buffer))

    def write(self, address: int, data: bytes | bytearray | memoryview) -> None:
        self._validate_access(address, len(data))
        noc_address = self._tranlate_to_noc_address(address)
        self._location.noc_write(noc_address, bytes(data))

    def read_register(self, register_index: int) -> int:
        raise NotImplementedError("L1MemoryAccess does not support register access")

    def write_register(self, register_index: int, value: int) -> None:
        raise NotImplementedError("L1MemoryAccess does not support register access")

    def _validate_access(self, address: int, size_bytes: int) -> None:
        base_address = self.l1_block.address.private_address
        assert base_address is not None, "L1 memory block has no private address"
        if address < base_address or address + size_bytes > base_address + self.l1_block.size:
            raise RestrictedMemoryAccessError(
                access_start=address, access_end=address + size_bytes - 1, location=self._location
            )


class FixedMemoryAccess(MemoryAccess):
    """
    Read-only MemoryAccess backed by an in-memory byte buffer.

    Used when DWARF evaluation has already produced the bytes for a value
    (e.g. a temporary, non-addressable expression result), so further reads
    should come from that snapshot rather than device memory. Writes are
    forbidden and will raise.
    """

    def __init__(self, data: bytes):
        super().__init__()
        self._data = data

    def read(self, address: int, buffer: memoryview | bytearray) -> None:
        size = len(buffer)
        buffer[:] = self._data[address : address + size]

    def write(self, address: int, data: bytes | bytearray | memoryview) -> None:
        raise ReadOnlyMemoryError(address, len(data))

    def read_register(self, register_index: int) -> int:
        raise NotImplementedError("FixedMemoryAccess does not support register access")

    def write_register(self, register_index: int, value: int) -> None:
        raise NotImplementedError("FixedMemoryAccess does not support register access")


class RiscDebugMemoryAccess(MemoryAccess):
    """
    MemoryAccess implementation that uses a RiscDebug instance to read/write
    a core's private address space (L1 + data private memory by default).

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
        super().__init__()
        self._risc_debug = risc_debug
        self._ensure_halted_access = ensure_halted_access  # will ensure the RISC will be halted for memory access
        self._restricted_access = restricted_access  # restrict access to only L1 and Data Private Memory
        self._safe_mode = safe_mode  # additional safety checks to prevent access to known unsafe memory regions

    def read(self, address: int, buffer: memoryview | bytearray) -> None:
        size_bytes = len(buffer)
        self._validate_access(address, size_bytes)

        if self._ensure_halted_access or self._risc_debug.can_debug():
            with self._risc_debug.ensure_private_memory_access():
                buffer[:] = self._risc_debug.read_memory_bytes(address, size_bytes, safe_mode=self._safe_mode)
        else:
            buffer[:] = self._risc_debug.read_memory_bytes(address, size_bytes, safe_mode=self._safe_mode)

    def write(self, address: int, data: bytes | bytearray | memoryview) -> None:
        raw = bytes(data)
        self._validate_access(address, len(raw))

        if self._ensure_halted_access or self._risc_debug.can_debug():
            with self._risc_debug.ensure_private_memory_access():
                self._risc_debug.write_memory_bytes(address, raw, safe_mode=self._safe_mode)
        else:
            self._risc_debug.write_memory_bytes(address, raw, safe_mode=self._safe_mode)

    def read_register(self, register_index: int) -> int:
        return self._risc_debug.read_gpr(register_index)

    def write_register(self, register_index: int, value: int) -> None:
        self._risc_debug.write_gpr(register_index, value)

    def _validate_access(self, address: int, size_bytes: int) -> None:
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
                    access_start=address,
                    access_end=address_end,
                    location=self._risc_debug.risc_location.location,
                )
