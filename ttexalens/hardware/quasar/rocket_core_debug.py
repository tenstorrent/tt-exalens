# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
from typing import Any, Generator

from ttexalens import util
from ttexalens.exceptions import RiscHaltError
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.risc_debug import RiscDebugStatus, RiscDebugWatchpointState
from ttexalens.register_store import RegisterStore

# RISC-V Debug Spec 0.13 — DMCONTROL bit fields
DMACTIVE = 1 << 0
RESUMEREQ = 1 << 30
HALTREQ = 1 << 31

# SMN_RISC_RESET_REG bit 17: debug module out-of-reset (active-low, 0 = in reset)
DM_OUT_OF_RESET_BIT = 1 << 17


class QuasarRocketCoreDebug(BabyRiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, overlay_register_store: RegisterStore, enable_asserts: bool = True):
        super().__init__(risc_info, enable_asserts)
        self.overlay_register_store = overlay_register_store

    def is_in_reset(self) -> bool:
        reset_bit = 1 << (8 + self.baby_risc_info.risc_id)
        address = self.overlay_register_store.get_register_noc_address("SMN_RISC_RESET_REG")
        value = self.location.noc_read32(address, noc_id=1)
        return not bool(value & reset_bit)

    def set_reset_signal(self, value: bool) -> None:
        reset_bit = 1 << (8 + self.baby_risc_info.risc_id)
        address = self.overlay_register_store.get_register_noc_address("SMN_RISC_RESET_REG")
        current = self.location.noc_read32(address, noc_id=1)
        new_value = (current & ~reset_bit) if value else (current | reset_bit)
        self.location.noc_write32(address, new_value, noc_id=1)

    @contextmanager
    def ensure_debug_module_out_of_reset(self) -> Generator[None, Any, None]:
        address = self.overlay_register_store.get_register_noc_address("SMN_RISC_RESET_REG")
        value = self.location.noc_read32(address, noc_id=1)
        dm_was_in_reset = not bool(value & DM_OUT_OF_RESET_BIT)
        if dm_was_in_reset:
            self.location.noc_write32(address, value | DM_OUT_OF_RESET_BIT, noc_id=1)
        try:
            yield
        finally:
            if dm_was_in_reset:
                self.location.noc_write32(address, value, noc_id=1)

    def is_halted(self) -> bool:
        with self.ensure_debug_module_out_of_reset():
            address = self.overlay_register_store.get_register_noc_address("TT_DEBUG_MODULE_APB_HALTSUMMARY0")
            haltsummary = self.location.noc_read32(address, noc_id=1)
            return bool(haltsummary & (1 << self.baby_risc_info.risc_id))

    def halt(self) -> None:
        with self.ensure_debug_module_out_of_reset():
            if self.is_halted():
                util.WARN(f"Halt: {self.risc_location.risc_name} at {self.location} is already halted")
                return
            address = self.overlay_register_store.get_register_noc_address("TT_DEBUG_MODULE_APB_DMCONTROL")
            hartsel = self.baby_risc_info.risc_id << 16
            self.location.noc_write32(address, DMACTIVE | hartsel | HALTREQ, noc_id=1)
            self.location.noc_write32(address, DMACTIVE | hartsel, noc_id=1)  # clear haltreq
            if not self.is_halted():
                raise RiscHaltError(self.risc_location.risc_name, self.location)

    def cont(self) -> None:
        with self.ensure_debug_module_out_of_reset():
            if not self.is_halted():
                util.WARN(f"Continue: {self.risc_location.risc_name} at {self.location} is already running")
                return
            address = self.overlay_register_store.get_register_noc_address("TT_DEBUG_MODULE_APB_DMCONTROL")
            hartsel = self.baby_risc_info.risc_id << 16
            self.location.noc_write32(address, DMACTIVE | hartsel | RESUMEREQ, noc_id=1)
            self.location.noc_write32(address, DMACTIVE | hartsel, noc_id=1)  # clear resumereq

    @contextmanager
    def ensure_halted(self) -> Generator[None, Any, None]:
        was_halted = self.is_halted()
        if not was_halted:
            self.halt()
        try:
            yield
        finally:
            if not was_halted:
                self.cont()

    def is_ebreak_hit(self) -> bool:
        raise NotImplementedError(
            f"Rocket core ebreak detection not yet implemented for {self.risc_location.risc_name}"
        )

    def step(self) -> None:
        raise NotImplementedError(f"Rocket core step not yet implemented for {self.risc_location.risc_name}")

    @contextmanager
    def ensure_private_memory_access(self) -> Generator[None, Any, None]:
        raise NotImplementedError(
            f"Rocket core ensure_private_memory_access not yet implemented for {self.risc_location.risc_name}"
        )

    def read_gpr(self, register_index: int) -> int:
        raise NotImplementedError(f"Rocket core GPR read not yet implemented for {self.risc_location.risc_name}")

    def write_gpr(self, register_index: int, value: int) -> None:
        raise NotImplementedError(f"Rocket core GPR write not yet implemented for {self.risc_location.risc_name}")

    def get_pc(self) -> int:
        raise NotImplementedError(f"Rocket core PC read not yet implemented for {self.risc_location.risc_name}")

    def read_memory(self, address: int, safe_mode: bool | None = None) -> int:
        raise NotImplementedError(f"Rocket core memory read not yet implemented for {self.risc_location.risc_name}")

    def write_memory(self, address: int, data: int, safe_mode: bool | None = None) -> None:
        raise NotImplementedError(f"Rocket core memory write not yet implemented for {self.risc_location.risc_name}")

    def read_memory_bytes(self, address: int, size_bytes: int, safe_mode: bool | None = None) -> bytes:
        raise NotImplementedError(f"Rocket core memory read not yet implemented for {self.risc_location.risc_name}")

    def write_memory_bytes(self, address: int, data: bytes, safe_mode: bool | None = None) -> None:
        raise NotImplementedError(f"Rocket core memory write not yet implemented for {self.risc_location.risc_name}")

    def read_status(self) -> RiscDebugStatus:
        raise NotImplementedError(f"Rocket core status read not yet implemented for {self.risc_location.risc_name}")

    def read_watchpoints_state(self) -> list[RiscDebugWatchpointState]:
        raise NotImplementedError(f"Rocket core watchpoints not yet implemented for {self.risc_location.risc_name}")

    def read_watchpoint_address(self, watchpoint_index: int) -> int:
        raise NotImplementedError(f"Rocket core watchpoints not yet implemented for {self.risc_location.risc_name}")

    def disable_watchpoint(self, watchpoint_index: int) -> None:
        raise NotImplementedError(f"Rocket core watchpoints not yet implemented for {self.risc_location.risc_name}")

    def set_watchpoint_on_pc_address(self, watchpoint_index: int, address: int) -> None:
        raise NotImplementedError(f"Rocket core watchpoints not yet implemented for {self.risc_location.risc_name}")

    def set_watchpoint_on_memory_read(self, watchpoint_index: int, address: int) -> None:
        raise NotImplementedError(f"Rocket core watchpoints not yet implemented for {self.risc_location.risc_name}")

    def set_watchpoint_on_memory_write(self, watchpoint_index: int, address: int) -> None:
        raise NotImplementedError(f"Rocket core watchpoints not yet implemented for {self.risc_location.risc_name}")

    def set_watchpoint_on_memory_access(self, watchpoint_index: int, address: int) -> None:
        raise NotImplementedError(f"Rocket core watchpoints not yet implemented for {self.risc_location.risc_name}")

    def can_debug(self) -> bool:
        raise NotImplementedError(f"Rocket core can_debug not yet implemented for {self.risc_location.risc_name}")

    def set_branch_prediction(self, enable: bool) -> None:
        raise NotImplementedError(
            f"Rocket core branch prediction not yet implemented for {self.risc_location.risc_name}"
        )

    def set_code_start_address(self, address: int | None) -> None:
        raise NotImplementedError(
            f"Rocket core code start address not yet implemented for {self.risc_location.risc_name}"
        )

    def get_l1(self) -> MemoryBlock:
        raise NotImplementedError(f"Rocket core L1 not yet implemented for {self.risc_location.risc_name}")

    def get_data_private_memory(self) -> MemoryBlock | None:
        raise NotImplementedError(
            f"Rocket core data private memory not yet implemented for {self.risc_location.risc_name}"
        )

    def get_code_private_memory(self) -> MemoryBlock | None:
        raise NotImplementedError(
            f"Rocket core code private memory not yet implemented for {self.risc_location.risc_name}"
        )
