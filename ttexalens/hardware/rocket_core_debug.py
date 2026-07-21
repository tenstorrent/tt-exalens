# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
from typing import Any, Generator

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

    def is_in_reset(self) -> bool:
        raise NotImplementedError("is_in_reset must be implemented by subclasses of RocketCoreDebug")

    def set_reset_signal(self, value: bool) -> None:
        raise NotImplementedError("set_reset_signal must be implemented by subclasses of RocketCoreDebug")

    def ensure_debug_module_is_active(self) -> None:
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

    def _read_word(self, address: int) -> int:
        """Read a single 32-bit word. Address must be 4-byte aligned."""
        raise NotImplementedError("_read_word must be implemented by subclasses of RocketCoreDebug")

    def _write_word(self, address: int, data: int) -> None:
        """Write a single 32-bit word. Address must be 4-byte aligned."""
        raise NotImplementedError("_write_word must be implemented by subclasses of RocketCoreDebug")

    def _read_memory(self, address: int, safe_mode: bool | None = None) -> int:
        buffer = bytearray(4)
        self.read_memory_bytes(address, buffer, safe_mode=safe_mode)
        return int.from_bytes(buffer, byteorder="little")

    def _write_memory(self, address: int, data: int, safe_mode: bool | None = None) -> None:
        self.write_memory_bytes(address, data.to_bytes(4, byteorder="little"), safe_mode=safe_mode)

    def read_memory_bytes(self, address: int, buffer: bytearray | memoryview, safe_mode: bool | None = None) -> None:
        self._read_memory_bytes(address, buffer, self._read_word, safe_mode=safe_mode)

    def write_memory_bytes(
        self, address: int, data: bytes | bytearray | memoryview, safe_mode: bool | None = None
    ) -> None:
        self._write_memory_bytes(address, data, self._read_word, self._write_word, safe_mode=safe_mode)

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
