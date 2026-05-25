# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
from typing import Any, Generator
import time

from ttexalens import util
from ttexalens.exceptions import RiscHaltError
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.rocket_core_debug import RocketCoreDebug
from ttexalens.register_store import RegisterStore

# RISC-V Debug Spec 0.13 — DMCONTROL bit fields
DMACTIVE = 1 << 0
RESUMEREQ = 1 << 30
HALTREQ = 1 << 31

# SMN_RISC_RESET_REG bit 17: debug module out-of-reset (active-low, 0 = in reset)
DM_OUT_OF_RESET_BIT = 1 << 17

# Abstract command (COMMAND) — Access Register, 64-bit, transfer=1, write=0, regno=dpc (0x7B1)
ABSTRACTS_BUSY = 1 << 12
CMD_READ_DPC = (3 << 20) | (1 << 17) | 0x7B1


class QuasarRocketCoreDebug(RocketCoreDebug):
    def __init__(self, risc_info: BabyRiscInfo, register_store: RegisterStore, enable_asserts: bool = True):
        super().__init__(risc_info, enable_asserts)
        self.register_store = register_store

    def is_in_reset(self) -> bool:
        reset_bit = 1 << self.baby_risc_info.reset_flag_shift
        value = self.register_store.read_register("SMN_RISC_RESET_REG")
        return not bool(value & reset_bit)

    def set_reset_signal(self, value: bool) -> None:
        reset_bit = 1 << self.baby_risc_info.reset_flag_shift
        current = self.register_store.read_register("SMN_RISC_RESET_REG")
        new_value = (current & ~reset_bit) if value else (current | reset_bit)
        self.register_store.write_register("SMN_RISC_RESET_REG", new_value)

    def is_debug_module_in_reset(self, value: int | None) -> bool:
        if value is None:
            value = self.register_store.read_register("SMN_RISC_RESET_REG")
        return not bool(value & DM_OUT_OF_RESET_BIT)

    def _wait_for_debug_module_to_be_active(self, timeout=10) -> None:
        start_time = time.time()
        while self.register_store.read_register("TT_CLUSTER_CTRL_DEBUG_DMACTIVE") != 1:
            if time.time() - start_time > timeout:
                raise Exception("Timeout waiting for debug module to be active")
            time.sleep(0.01)
        # Acknowledge that debug module is active
        self.register_store.write_register("TT_CLUSTER_CTRL_DEBUG_DMACTIVEACK", 1)

    def take_debug_module_out_of_reset(self, value: int | None = None) -> None:
        if value is None:
            value = self.register_store.read_register("SMN_RISC_RESET_REG")
        self.register_store.write_register("SMN_RISC_RESET_REG", value | DM_OUT_OF_RESET_BIT)
        self.register_store.write_register("TT_DEBUG_MODULE_APB_DMCONTROL", 1)
        self._wait_for_debug_module_to_be_active()
        assert not self.is_debug_module_in_reset(), "Debug module should be out of reset"

    @contextmanager
    def ensure_debug_module_out_of_reset(self) -> Generator[None, Any, None]:
        value = self.register_store.read_register("SMN_RISC_RESET_REG")
        dm_was_in_reset = self.is_debug_module_in_reset(value)
        if dm_was_in_reset:
            self.take_debug_module_out_of_reset(value)
        try:
            yield
        finally:
            if dm_was_in_reset:
                # Put register in initial state
                self.register_store.write_register("SMN_RISC_RESET_REG", value)

    def is_halted(self) -> bool:
        with self.ensure_debug_module_out_of_reset():
            haltsummary = self.register_store.read_register("TT_DEBUG_MODULE_APB_HALTSUMMARY0")
            return bool(haltsummary & (1 << self.baby_risc_info.risc_id))

    def halt(self) -> None:
        with self.ensure_debug_module_out_of_reset():
            if self.is_halted():
                util.WARN(f"Halt: {self.risc_location.risc_name} at {self.risc_location.location} is already halted")
                return
            hartsel = self.baby_risc_info.risc_id << 16
            self.register_store.write_register("TT_DEBUG_MODULE_APB_DMCONTROL", DMACTIVE | hartsel | HALTREQ)
            self.register_store.write_register("TT_DEBUG_MODULE_APB_DMCONTROL", DMACTIVE | hartsel)

    def cont(self) -> None:
        with self.ensure_debug_module_out_of_reset():
            if not self.is_halted():
                util.WARN(
                    f"Continue: {self.risc_location.risc_name} at {self.risc_location.location} is already running"
                )
                return
            hartsel = self.baby_risc_info.risc_id << 16
            self.register_store.write_register("TT_DEBUG_MODULE_APB_DMCONTROL", DMACTIVE | hartsel | RESUMEREQ)
            self.register_store.write_register("TT_DEBUG_MODULE_APB_DMCONTROL", DMACTIVE | hartsel)

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

    def get_pc(self) -> int:
        with self.ensure_debug_module_out_of_reset():
            with self.ensure_halted():
                hartsel = self.baby_risc_info.risc_id << 16
                self.register_store.write_register("TT_DEBUG_MODULE_APB_DMCONTROL", DMACTIVE | hartsel)
                self.register_store.write_register("TT_DEBUG_MODULE_APB_COMMAND", CMD_READ_DPC)
                while self.register_store.read_register("TT_DEBUG_MODULE_APB_ABSTRACTCS") & ABSTRACTS_BUSY:
                    pass
                lo = self.register_store.read_register("TT_DEBUG_MODULE_APB_DATA0")
                hi = self.register_store.read_register("TT_DEBUG_MODULE_APB_DATA1")
                return (hi << 32) | lo

    def set_code_start_address(self, address: int | None) -> None:
        self.baby_risc_info.set_code_start_address(self.register_store, address if address is not None else 0)
