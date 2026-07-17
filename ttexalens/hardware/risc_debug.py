# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generator
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.risc_info import RiscInfo

if TYPE_CHECKING:
    from ttexalens.context import Context
    from ttexalens.device import Device


@dataclass
class RiscLocation:
    location: OnChipCoordinate
    neo_id: int | None
    risc_name: str

    def __hash__(self) -> int:
        return hash((self.location, self.neo_id, self.risc_name))

    def __str__(self) -> str:
        return f"{self.location.to_user_str()} [neo: {self.neo_id}, risc: {self.risc_name}]"


@dataclass
class RiscDebugStatus:
    is_halted: bool
    is_pc_watchpoint_hit: bool
    is_memory_watchpoint_hit: bool
    is_ebreak_hit: bool
    watchpoints_hit: list[bool]


@dataclass
class RiscDebugWatchpointState:
    is_enabled: bool
    is_memory: bool
    is_read: bool
    is_write: bool

    @property
    def is_access(self):
        return self.is_memory and self.is_read and self.is_write

    @property
    def is_breakpoint(self):
        return not self.is_memory


class RiscDebug:
    """
    Abstract base class for RISC debug interface.
    This class defines the interface for interacting with a RISC core for debugging purposes.
    """

    def __init__(self, risc_location: RiscLocation, risc_info: RiscInfo):
        self.risc_location = risc_location
        self.risc_info = risc_info

    @staticmethod
    def get_instance(risc_location: RiscLocation) -> "RiscDebug":
        noc_block = risc_location.location.device.get_block(risc_location.location)
        return noc_block.get_risc_debug(risc_location.risc_name, risc_location.neo_id)

    @property
    def device(self) -> Device:
        return self.risc_info.noc_block.device

    @property
    def context(self) -> Context:
        return self.device._context

    @abstractmethod
    def is_in_reset(self) -> bool:
        """Check if the RISC core is in reset."""
        pass

    @abstractmethod
    def set_reset_signal(self, value: bool) -> None:
        """
        Set the reset signal for the RISC core.
        Args:
            value (bool): True to set the reset signal, False to clear it.
        """
        pass

    @abstractmethod
    def is_halted(self) -> bool:
        """Check if the RISC core is halted."""
        pass

    @abstractmethod
    def is_ebreak_hit(self) -> bool:
        """Check if an ebreak instruction was hit and RISC got halted."""
        pass

    @abstractmethod
    def halt(self) -> None:
        """Halt the RISC core."""
        pass

    @abstractmethod
    def step(self) -> None:
        """Step the RISC core."""
        pass

    @abstractmethod
    def cont(self) -> None:
        """Continue the RISC core."""
        pass

    @abstractmethod
    @contextmanager
    def ensure_halted(self) -> Generator[None, Any, None]:
        pass

    @abstractmethod
    @contextmanager
    def ensure_private_memory_access(self) -> Generator[None, Any, None]:
        pass

    @abstractmethod
    def read_gpr(self, register_index: int) -> int:
        """
        Read a general purpose register.
        Args:
            register_index (int): Register index to read.
        Returns:
            int: Value of the register.
        """
        pass

    @abstractmethod
    def write_gpr(self, register_index: int, value: int) -> None:
        """
        Write a general purpose register.
        Args:
            register_index (int): Register index to write.
            value (int): Value to write to the register.
        """
        pass

    @abstractmethod
    def get_pc(self) -> int:
        """
        Get PC through debug bus if available,
        otherwise pause risc and read PC from GPR.
        """
        pass

    def _validate_32_bit_value(self, value: int):
        """Validate that a value fits within 32 bits for SBA access."""
        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError(f"Value out of bounds: value=0x{value:08x}. Value must fit within 32 bits.")

    def _validate_safe_access(self, address: int, size_bytes: int) -> None:
        """Safety validations to be added. tt-exalens:#913"""
        pass

    def _read_memory_bytes(
        self,
        address: int,
        buffer: bytearray | memoryview,
        read_word: Callable[[int], int],
        safe_mode: bool | None = None,
    ) -> None:
        size_bytes = len(buffer)
        safe_mode = safe_mode if safe_mode is not None else self.context.safe_mode
        if safe_mode:
            self._validate_safe_access(address, size_bytes)

        word_size = 4
        pos = 0
        while pos < size_bytes:
            addr = address + pos
            word_addr = addr - (addr % word_size)
            word = read_word(word_addr)
            word_bytes = word.to_bytes(word_size, byteorder="little")
            start_in_word = addr - word_addr
            n = min(word_size - start_in_word, size_bytes - pos)
            buffer[pos : pos + n] = word_bytes[start_in_word : start_in_word + n]
            pos += n

    def _write_memory_bytes(
        self,
        address: int,
        data: bytes | bytearray | memoryview,
        read_word: Callable[[int], int],
        write_word: Callable[[int, int], None],
        safe_mode: bool | None = None,
    ) -> None:
        safe_mode = safe_mode if safe_mode is not None else self.context.safe_mode
        if safe_mode:
            self._validate_safe_access(address, len(data))

        word_size = 4
        data = memoryview(data)
        size = len(data)
        if size == 0:
            return

        # Unaligned prefix
        first_unaligned = address % word_size
        if first_unaligned != 0:
            aligned_address = address - first_unaligned
            word_bytes = bytearray(read_word(aligned_address).to_bytes(word_size, byteorder="little"))
            n = min(word_size - first_unaligned, size)
            word_bytes[first_unaligned : first_unaligned + n] = data[:n]
            write_word(aligned_address, int.from_bytes(word_bytes, byteorder="little"))
            data = data[n:]
            address += n
            size -= n

        aligned_size = size - (size % word_size)
        for offset in range(0, aligned_size, word_size):
            word = int.from_bytes(data[offset : offset + word_size], byteorder="little")
            write_word(address + offset, word)
        data = data[aligned_size:]
        address += aligned_size
        size -= aligned_size

        # Unaligned suffix
        if size != 0:
            word_bytes = bytearray(read_word(address).to_bytes(word_size, byteorder="little"))
            word_bytes[:size] = data[:size]
            write_word(address, int.from_bytes(word_bytes, byteorder="little"))

    @abstractmethod
    def _read_memory(self, address: int) -> int:
        raise NotImplementedError("_read_memory must be implemented by subclasses of RiscDebug")

    def read_memory(self, address: int, safe_mode: bool | None = None) -> int:
        """
        Read a memory address.
        Args:
            address (int): Memory address to read.
            safe_mode (bool | None): If True, apply additional safety checks to prevent access to known unsafe memory regions.
        Returns:
            int: Value at the memory address.
        """
        self._validate_32_bit_value(address)
        return self._read_memory(address)

    @abstractmethod
    def read_memory_bytes(self, address: int, buffer: bytearray | memoryview, safe_mode: bool | None = None) -> None:
        """
        Read len(buffer) bytes from a memory address into 'buffer'.
        Args:
            address (int): Memory address to read.
            buffer (bytearray | memoryview): Destination buffer; exactly len(buffer) bytes are read into it.
            safe_mode (bool | None): If True, apply additional safety checks to prevent access to known unsafe memory regions.
        """
        pass

    @abstractmethod
    def _write_memory(self, address: int, data: int) -> None:
        raise NotImplementedError("_write_memory must be implemented by subclasses of RiscDebug")

    def write_memory(self, address: int, data: int, safe_mode: bool | None = None) -> None:
        """
        Write data to a memory address.
        Args:
            address (int): Memory address to write.
            data (int): Data to write to the memory address.
            safe_mode (bool | None): If True, apply additional safety checks to prevent access to known unsafe memory regions.
        """
        self._validate_32_bit_value(address)
        self._validate_32_bit_value(data)
        self._write_memory(address, data)

    @abstractmethod
    def write_memory_bytes(
        self, address: int, data: bytes | bytearray | memoryview, safe_mode: bool | None = None
    ) -> None:
        """
        Write len(data) bytes to a memory address.
        Args:
            address (int): Memory address to write.
            data (bytes | bytearray | memoryview): Bytes to write to the memory address.
            safe_mode (bool | None): If True, apply additional safety checks to prevent access to known unsafe memory regions.
        """
        pass

    @abstractmethod
    def read_status(self) -> RiscDebugStatus:
        """
        Read the debugging status of the RISC core.
        Returns:
            RiscDebugStatus: Debugging status of the RISC core.
        """
        pass

    @abstractmethod
    def read_watchpoints_state(self) -> list[RiscDebugWatchpointState]:
        """
        Read the state of all watchpoints.
        Returns:
            list[RiscDebugWatchpointState]: List of watchpoint states.
        """
        pass

    @abstractmethod
    def read_watchpoint_address(self, watchpoint_index: int) -> int:
        """
        Read the address of a watchpoint.
        Args:
            watchpoint_index (int): Index of the watchpoint to read.
        Returns:
            int: Address of the watchpoint.
        """
        pass

    @abstractmethod
    def disable_watchpoint(self, watchpoint_index: int) -> None:
        """
        Disable a watchpoint.
        Args:
            watchpoint_index (int): Index of the watchpoint to disable.
        """
        pass

    @abstractmethod
    def set_watchpoint_on_pc_address(self, watchpoint_index: int, address: int) -> None:
        """
        Set a watchpoint on the program counter address.
        Args:
            watchpoint_index (int): Index of the watchpoint to set.
            address (int): Address to set the watchpoint on.
        """
        pass

    @abstractmethod
    def set_watchpoint_on_memory_read(self, watchpoint_index: int, address: int) -> None:
        """
        Set a watchpoint on memory read.
        Args:
            watchpoint_index (int): Index of the watchpoint to set.
            address (int): Address to set the watchpoint on.
        """
        pass

    @abstractmethod
    def set_watchpoint_on_memory_write(self, watchpoint_index: int, address: int) -> None:
        """
        Set a watchpoint on memory write.
        Args:
            watchpoint_index (int): Index of the watchpoint to set.
            address (int): Address to set the watchpoint on.
        """
        pass

    @abstractmethod
    def set_watchpoint_on_memory_access(self, watchpoint_index: int, address: int) -> None:
        """
        Set a watchpoint on memory access.
        Args:
            watchpoint_index (int): Index of the watchpoint to set.
            address (int): Address to set the watchpoint on.
        """
        pass

    @abstractmethod
    def set_branch_prediction(self, enable: bool) -> None:
        """
        Set the branch prediction.
        Args:
            enable (bool): True to enable branch prediction, False to disable.
        """
        pass

    @abstractmethod
    def can_debug(self) -> bool:
        """
        Check if the RISC core supports debugging.
        Returns:
            bool: True if debugging is supported, False otherwise.
        """
        pass

    @abstractmethod
    def set_code_start_address(self, address: int | None) -> None:
        """
        Set the start address for the RISC core when taken out of reset.
        Args:
            address (int | None): Address to set as the start address, or None to put it to its default value.
        """
        pass

    @abstractmethod
    def get_l1(self) -> MemoryBlock:
        """
        Get the L1 memory block for the RISC core.
        Returns:
            MemoryBlock: L1 memory block.
        """
        pass

    @abstractmethod
    def get_data_private_memory(self) -> MemoryBlock | None:
        """
        Get the data private memory block for the RISC core.
        Returns:
            MemoryBlock | None: Data private memory block, or None if not available.
        """
        pass

    @abstractmethod
    def get_code_private_memory(self) -> MemoryBlock | None:
        """
        Get the code private memory block for the RISC core.
        This was used on older architectures and is replaced by instruction cache on newer ones.
        Returns:
            MemoryBlock | None: Code private memory block, or None if not available.
        """
        pass
