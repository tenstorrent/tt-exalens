# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
from typing import Any, Generator

from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.risc_debug import (
    RiscDebug,
    RiscDebugStatus,
    RiscDebugWatchpointState,
    RiscLocation,
)


class RocketCoreDebug(RiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, enable_asserts: bool = True):
        super().__init__(RiscLocation(risc_info.noc_block.location, risc_info.neo_id, risc_info.risc_name), risc_info)
        register_store = risc_info.noc_block.get_register_store(neo_id=risc_info.neo_id)
        self.baby_risc_info = risc_info
        self.register_store = register_store
        self.enable_asserts = enable_asserts

    @property
    def device(self) -> Device:
        return self.baby_risc_info.noc_block.device

    @property
    def context(self) -> Context:
        return self.device._context

    def is_in_reset(self) -> bool:
        raise NotImplementedError("is_in_reset must be implemented by subclasses of RocketCoreDebug")

    def set_reset_signal(self, value: bool) -> None:
        raise NotImplementedError("set_reset_signal must be implemented by subclasses of RocketCoreDebug")

    @contextmanager
    def ensure_debug_module_is_active(self) -> Generator[None, Any, None]:
        raise NotImplementedError("ensure_debug_module_is_active must be implemented by subclasses of RocketCoreDebug")

    def is_halted(self) -> bool:
        raise NotImplementedError("is_halted must be implemented by subclasses of RocketCoreDebug")

    def is_ebreak_hit(self) -> bool:
        raise NotImplementedError("is_ebreak_hit must be implemented by subclasses of RocketCoreDebug")

    def halt(self) -> None:
        raise NotImplementedError("halt must be implemented by subclasses of RocketCoreDebug")

    def step(self) -> None:
        raise NotImplementedError("step must be implemented by subclasses of RocketCoreDebug")

    def cont(self) -> None:
        raise NotImplementedError("cont must be implemented by subclasses of RocketCoreDebug")

    @contextmanager
    def ensure_halted(self) -> Generator[None, Any, None]:
        raise NotImplementedError("ensure_halted must be implemented by subclasses of RocketCoreDebug")

    @contextmanager
    def ensure_private_memory_access(self) -> Generator[None, Any, None]:
        raise NotImplementedError("ensure_private_memory_access must be implemented by subclasses of RocketCoreDebug")

    def read_gpr(self, register_index: int) -> int:
        raise NotImplementedError("read_gpr must be implemented by subclasses of RocketCoreDebug")

    def write_gpr(self, register_index: int, value: int) -> None:
        raise NotImplementedError("write_gpr must be implemented by subclasses of RocketCoreDebug")

    def get_pc(self) -> int:
        raise NotImplementedError("get_pc must be implemented by subclasses of RocketCoreDebug")

    def _read_word(self, word_address: int) -> int:
        """Read a single 32-bit word. 'word_address' must be 4-byte aligned."""
        raise NotImplementedError("_read_word must be implemented by subclasses of RocketCoreDebug")

    def _write_word(self, word_address: int, data: int) -> None:
        """Write a single 32-bit word. 'word_address' must be 4-byte aligned."""
        raise NotImplementedError("_write_word must be implemented by subclasses of RocketCoreDebug")

    def _validate_safe_access(self, address: int, size_bytes: int) -> None:
        """Safety validations to be added. tt-exalens:#913"""
        pass

    def _read_memory(self, address: int, safe_mode: bool | None = None) -> int:
        buffer = bytearray(4)
        self.read_memory_bytes(address, buffer, safe_mode=safe_mode)
        return int.from_bytes(buffer, byteorder="little")

    def _write_memory(self, address: int, data: int, safe_mode: bool | None = None) -> None:
        self.write_memory_bytes(address, data.to_bytes(4, byteorder="little"), safe_mode=safe_mode)

    def read_memory_bytes(self, address: int, buffer: bytearray | memoryview, safe_mode: bool | None = None) -> None:
        size_bytes = len(buffer)
        safe_mode = safe_mode if safe_mode is not None else self.context.safe_mode
        if safe_mode:
            self._validate_safe_access(address, size_bytes)
        word_size = 4
        pos = 0
        while pos < size_bytes:
            addr = address + pos
            word_addr = addr - (addr % word_size)
            word = self._read_word(word_addr)
            word_bytes = word.to_bytes(word_size, byteorder="little")
            start_in_word = addr - word_addr
            n = min(word_size - start_in_word, size_bytes - pos)
            buffer[pos : pos + n] = word_bytes[start_in_word : start_in_word + n]
            pos += n

    def write_memory_bytes(
        self, address: int, data: bytes | bytearray | memoryview, safe_mode: bool | None = None
    ) -> None:
        safe_mode = safe_mode if safe_mode is not None else self.context.safe_mode
        if safe_mode:
            self._validate_safe_access(address, len(data))
        word_size = 4
        size_bytes = len(data)
        aligned_start = address - (address % word_size)
        aligned_end = ((address + size_bytes + word_size - 1) // word_size) * word_size

        new_data = bytearray()

        if aligned_start < address:
            prefix_size = address - aligned_start
            prefix_word = self._read_word(aligned_start)
            new_data.extend(prefix_word.to_bytes(word_size, byteorder="little")[:prefix_size])

        new_data.extend(data)

        if aligned_end > address + size_bytes:
            suffix_size = aligned_end - (address + size_bytes)
            suffix_word = self._read_word(aligned_end - word_size)
            new_data.extend(suffix_word.to_bytes(word_size, byteorder="little")[-suffix_size:])

        assert len(new_data) % word_size == 0, "Data length must be multiple of word size after alignment"

        for offset in range(0, len(new_data), word_size):
            new_addr = aligned_start + offset
            word = int.from_bytes(new_data[offset : offset + word_size], byteorder="little")
            self._write_word(new_addr, word)

    def read_status(self) -> RiscDebugStatus:
        raise NotImplementedError("read_status must be implemented by subclasses of RocketCoreDebug")

    def read_watchpoints_state(self) -> list[RiscDebugWatchpointState]:
        raise NotImplementedError("read_watchpoints_state must be implemented by subclasses of RocketCoreDebug")

    def read_watchpoint_address(self, watchpoint_index: int) -> int:
        raise NotImplementedError("read_watchpoint_address must be implemented by subclasses of RocketCoreDebug")

    def disable_watchpoint(self, watchpoint_index: int) -> None:
        raise NotImplementedError("disable_watchpoint must be implemented by subclasses of RocketCoreDebug")

    def set_watchpoint_on_pc_address(self, watchpoint_index: int, address: int) -> None:
        raise NotImplementedError("set_watchpoint_on_pc_address must be implemented by subclasses of RocketCoreDebug")

    def set_watchpoint_on_memory_read(self, watchpoint_index: int, address: int) -> None:
        raise NotImplementedError("set_watchpoint_on_memory_read must be implemented by subclasses of RocketCoreDebug")

    def set_watchpoint_on_memory_write(self, watchpoint_index: int, address: int) -> None:
        raise NotImplementedError("set_watchpoint_on_memory_write must be implemented by subclasses of RocketCoreDebug")

    def set_watchpoint_on_memory_access(self, watchpoint_index: int, address: int) -> None:
        raise NotImplementedError(
            "set_watchpoint_on_memory_access must be implemented by subclasses of RocketCoreDebug"
        )

    def set_branch_prediction(self, enable: bool) -> None:
        raise NotImplementedError("set_branch_prediction must be implemented by subclasses of RocketCoreDebug")

    def can_debug(self) -> bool:
        raise NotImplementedError("can_debug must be implemented by subclasses of RocketCoreDebug")

    def set_code_start_address(self, address: int | None) -> None:
        raise NotImplementedError("set_code_start_address must be implemented by subclasses of RocketCoreDebug")

    def get_l1(self) -> MemoryBlock:
        raise NotImplementedError("get_l1 must be implemented by subclasses of RocketCoreDebug")

    def get_data_private_memory(self) -> MemoryBlock | None:
        raise NotImplementedError("get_data_private_memory must be implemented by subclasses of RocketCoreDebug")

    def get_code_private_memory(self) -> MemoryBlock | None:
        raise NotImplementedError("get_code_private_memory must be implemented by subclasses of RocketCoreDebug")
