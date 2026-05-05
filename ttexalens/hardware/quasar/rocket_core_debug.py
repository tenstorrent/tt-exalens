# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from contextlib import contextmanager
from typing import Any, Generator

from ttexalens import util
from ttexalens.exceptions import RiscHaltError
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
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

    def get_pc(self) -> int:
        with self.ensure_debug_module_out_of_reset():
            with self.ensure_halted():
                hartsel = self.baby_risc_info.risc_id << 16
                dmcontrol = self.overlay_register_store.get_register_noc_address("TT_DEBUG_MODULE_APB_DMCONTROL")
                self.location.noc_write32(dmcontrol, DMACTIVE | hartsel, noc_id=1)

                command = self.overlay_register_store.get_register_noc_address("TT_DEBUG_MODULE_APB_COMMAND")
                self.location.noc_write32(command, CMD_READ_DPC, noc_id=1)

                abstractcs = self.overlay_register_store.get_register_noc_address("TT_DEBUG_MODULE_APB_ABSTRACTCS")
                while self.location.noc_read32(abstractcs, noc_id=1) & ABSTRACTS_BUSY:
                    pass

                data0 = self.overlay_register_store.get_register_noc_address("TT_DEBUG_MODULE_APB_DATA0")
                data1 = self.overlay_register_store.get_register_noc_address("TT_DEBUG_MODULE_APB_DATA1")
                lo = self.location.noc_read32(data0, noc_id=1)
                hi = self.location.noc_read32(data1, noc_id=1)
                return (hi << 32) | lo
