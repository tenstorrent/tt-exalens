# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from contextlib import contextmanager
from dataclasses import dataclass
from elftools.elf.elffile import ELFFile
import os
from typing import List, Union

from ttexalens import util
from ttexalens.baby_risc_info import BabyRiscInfo
from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.parse_elf import read_elf
from ttexalens.risc_debug import CallstackEntry, RiscLocation, RiscDebug
from ttexalens.register_store import RegisterDescription, RegisterStore
from ttexalens.tt_exalens_lib import read_from_device, read_word_from_device, write_to_device, write_words_to_device

# Register address
REG_STATUS = 0
REG_COMMAND = 1
REG_COMMAND_ARG_0 = 2
REG_COMMAND_ARG_1 = 3
REG_COMMAND_RETURN_VALUE = 4
REG_HW_WATCHPOINT_SETTINGS = 5
REG_HW_WATCHPOINT_0 = 10
REG_HW_WATCHPOINT_1 = 11
REG_HW_WATCHPOINT_2 = 12
REG_HW_WATCHPOINT_3 = 13
REG_HW_WATCHPOINT_4 = 14
REG_HW_WATCHPOINT_5 = 15
REG_HW_WATCHPOINT_6 = 16
REG_HW_WATCHPOINT_7 = 17

# Status register bits
STATUS_HALTED = 0x1
STATUS_PC_WATCHPOINT_HIT = 0x2
STATUS_MEMORY_WATCHPOINT_HIT = 0x4
STATUS_EBREAK_HIT = 0x8
STATUS_WATCHPOINT_0_HIT = 0x00000100

# Command register bits
COMMAND_HALT = 0x00000001
COMMAND_STEP = 0x00000002  # resume for one cycle
COMMAND_CONTINUE = 0x00000004
COMMAND_READ_REGISTER = 0x00000008
COMMAND_WRITE_REGISTER = 0x00000010
COMMAND_READ_MEMORY = 0x00000020
COMMAND_WRITE_MEMORY = 0x00000040
COMMAND_FLUSH_REGISTERS = 0x00000080
COMMAND_FLUSH = 0x00000100
COMMAND_DEBUG_MODE = 0x80000000

# Watchpoint - REG_HW_WATCHPOINT_SETTINGS
HW_WATCHPOINT_BREAKPOINT = 0x00000000
HW_WATCHPOINT_READ = 0x00000001
HW_WATCHPOINT_WRITE = 0x00000002
HW_WATCHPOINT_ACCESS = 0x00000003
HW_WATCHPOINT_ENABLED = 0x00000008
HW_WATCHPOINT_MASK = 0x0000000F

# Register names
RISCV_REGISTER_NAMES_BY_INDEX = {
    0: "zero",
    1: "ra",
    2: "sp",
    3: "gp",
    4: "tp",
    5: "t0",
    6: "t1",
    7: "t2",
    8: "s0 / fp",
    9: "s1",
    10: "a0",
    11: "a1",
    12: "a2",
    13: "a3",
    14: "a4",
    15: "a5",
    16: "a6",
    17: "a7",
    18: "s2",
    19: "s3",
    20: "s4",
    21: "s5",
    22: "s6",
    23: "s7",
    24: "s8",
    25: "s9",
    26: "s10",
    27: "s11",
    28: "t3",
    29: "t4",
    30: "t5",
    31: "t6",
    32: "pc",
}

RISCV_REGISTER_INDEX_BY_NAME = {
    "zero": 0,
    "x0": 0,
    "ra": 1,
    "x1": 1,
    "sp": 2,
    "x2": 2,
    "gp": 3,
    "x3": 3,
    "tp": 4,
    "x4": 4,
    "t0": 5,
    "x5": 5,
    "t1": 6,
    "x6": 6,
    "t2": 7,
    "x7": 7,
    "s0": 8,
    "fp": 8,
    "x8": 8,
    "s1": 9,
    "x9": 9,
    "a0": 10,
    "x10": 10,
    "a1": 11,
    "x11": 11,
    "a2": 12,
    "x12": 12,
    "a3": 13,
    "x13": 13,
    "a4": 14,
    "x14": 14,
    "a5": 15,
    "x15": 15,
    "a6": 16,
    "x16": 16,
    "a7": 17,
    "x17": 17,
    "s2": 18,
    "x18": 18,
    "s3": 19,
    "x19": 19,
    "s4": 20,
    "x20": 20,
    "s5": 21,
    "x21": 21,
    "s6": 22,
    "x22": 22,
    "s7": 23,
    "x23": 23,
    "s8": 24,
    "x24": 24,
    "s9": 25,
    "x25": 25,
    "s10": 26,
    "x26": 26,
    "s11": 27,
    "x27": 27,
    "t3": 28,
    "x28": 28,
    "t4": 29,
    "x29": 29,
    "t5": 30,
    "x30": 30,
    "t6": 31,
    "x31": 31,
    "pc": 32,
    "x32": 32,
}


def get_register_index(reg_index_or_name):
    if reg_index_or_name in RISCV_REGISTER_NAMES_BY_INDEX:
        return reg_index_or_name
    if reg_index_or_name in RISCV_REGISTER_INDEX_BY_NAME:
        return RISCV_REGISTER_INDEX_BY_NAME[reg_index_or_name]
    raise ValueError(f"Unknown register {reg_index_or_name}")


def get_register_name(reg_index_or_name):
    index = get_register_index(reg_index_or_name)
    return RISCV_REGISTER_NAMES_BY_INDEX[index]


@dataclass
class BabyRiscLocation(RiscLocation):
    risc_id: int = 0
    neo_id: Union[int, None] = None

    def __hash__(self) -> int:
        return hash((self.coord, self.noc_id, self.neo_id, self.risc_id, self.risc_name))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BabyRiscLocation):
            return False
        return (
            self.coord == other.coord
            and self.noc_id == other.noc_id
            and self.neo_id == other.neo_id
            and self.risc_id == other.risc_id
            and self.risc_name == other.risc_name
        )


@dataclass
class BabyRiscDebugStatus:
    is_halted: bool
    is_pc_watchpoint_hit: bool
    is_memory_watchpoint_hit: bool
    is_ebreak_hit: bool
    watchpoints_hit: List[bool]

    @staticmethod
    def from_register(value: int, max_watchpoints: int):
        return BabyRiscDebugStatus(
            is_halted=value & STATUS_HALTED != 0,
            is_pc_watchpoint_hit=value & STATUS_PC_WATCHPOINT_HIT != 0,
            is_memory_watchpoint_hit=value & STATUS_MEMORY_WATCHPOINT_HIT != 0,
            is_ebreak_hit=value & STATUS_EBREAK_HIT != 0,
            watchpoints_hit=[(value & (STATUS_WATCHPOINT_0_HIT << i)) != 0 for i in range(max_watchpoints)],
        )


@dataclass
class BabyRiscDebugWatchpointState:
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

    @staticmethod
    def from_value(value: int):
        assert value & HW_WATCHPOINT_MASK == value, f"Invalid watchpoint value {value:08x}"

        return BabyRiscDebugWatchpointState(
            value & HW_WATCHPOINT_ENABLED != 0,
            value & HW_WATCHPOINT_ACCESS != 0,
            value & HW_WATCHPOINT_READ != 0,
            value & HW_WATCHPOINT_WRITE != 0,
        )


class BabyRiscDebugHardware:
    def __init__(
        self,
        location: BabyRiscLocation,
        register_store: RegisterStore,
        risc_info: BabyRiscInfo,
        verbose: bool = False,
        enable_asserts: bool = True,
    ):
        self.location = location
        self.register_store = register_store
        self.risc_info = risc_info
        self.enable_asserts = enable_asserts
        self.verbose = verbose

        self.CONTROL0_WRITE = 0x80010000 + (self.location.risc_id << 17)
        self.CONTROL0_READ = 0x80000000 + (self.location.risc_id << 17)
        self.RISC_DBG_CNTL0 = register_store.get_register_noc_address("RISCV_DEBUG_REG_RISC_DBG_CNTL_0")
        self.RISC_DBG_CNTL1 = register_store.get_register_noc_address("RISCV_DEBUG_REG_RISC_DBG_CNTL_1")
        self.RISC_DBG_STATUS0 = register_store.get_register_noc_address("RISCV_DEBUG_REG_RISC_DBG_STATUS_0")
        self.RISC_DBG_STATUS1 = register_store.get_register_noc_address("RISCV_DEBUG_REG_RISC_DBG_STATUS_1")

    @property
    def device(self) -> Device:
        return self.location.coord._device

    @property
    def context(self) -> Context:
        return self.device._context

    def _get_reg_name_for_address(self, address: int):
        if address == self.RISC_DBG_CNTL0:
            return "CNTL0"
        elif address == self.RISC_DBG_CNTL1:
            return "CNTL1"
        elif address == self.RISC_DBG_STATUS0:
            return "STATUS0"
        elif address == self.RISC_DBG_STATUS1:
            return "STATUS1"
        else:
            return f"Unknown register {address}"

    def __write(self, addr, data):
        if self.verbose:
            util.DEBUG(f"{self._get_reg_name_for_address(addr)} <- WR   0x{data:08x}")
        write_words_to_device(self.location.coord, addr, data, self.device._id, self.context)

    def __read(self, addr):
        data = read_word_from_device(self.location.coord, addr, self.device._id, self.context)
        if self.verbose:
            util.DEBUG(f"{self._get_reg_name_for_address(addr)} -> RD == 0x{data:08x}")
        return data

    def __trigger_write(self, reg_addr):
        if self.verbose:
            util.INFO(f"      __trigger_write({reg_addr})")
        self.__write(self.RISC_DBG_CNTL0, self.CONTROL0_WRITE + reg_addr)
        self.__write(self.RISC_DBG_CNTL0, 0)

    def __trigger_read(self, reg_addr):
        if self.verbose:
            util.INFO(f"      __trigger_read({reg_addr})")
        self.__write(self.RISC_DBG_CNTL0, self.CONTROL0_READ + reg_addr)
        self.__write(self.RISC_DBG_CNTL0, 0)

    def __riscv_write(self, reg_addr, value):
        if self.verbose:
            util.INFO(f"    __riscv_write({reg_addr}, 0x{value:08x})")
        # set wrdata
        self.__write(self.RISC_DBG_CNTL1, value)
        self.__trigger_write(reg_addr)

    def __is_read_valid(self):
        if self.verbose:
            util.INFO("  __is_read_valid()")
        status0 = self.__read(self.RISC_DBG_STATUS0)
        return (status0 & self.risc_info.status_read_valid_mask) == self.risc_info.status_read_valid_mask

    def __riscv_read(self, reg_addr):
        if self.verbose:
            util.INFO(f"  __riscv_read({reg_addr})")
        self.__trigger_read(reg_addr)

        if self.enable_asserts:
            if not self.__is_read_valid():
                util.WARN(f"Reading from RiscV debug registers failed (debug read valid bit is set to 0).")
        return self.__read(self.RISC_DBG_STATUS1)

    def enable_debug(self):
        if self.verbose:
            util.INFO("  enable_debug()")
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE)

    def _halt_command(self):
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_HALT)

    def halt(self):
        if self.is_halted():
            util.WARN(f"Halt: {self.location.risc_name} core at {self.location.coord} is already halted")
            return
        if self.verbose:
            util.INFO("  halt()")
        self._halt_command()
        assert self.is_halted(), f"Failed to halt {self.location.risc_name} core at {self.location.coord}"

    @contextmanager
    def ensure_halted(self):
        """
        Ensures that an operation is performed while the RISC-V core is halted, and then resumes it.
        """
        was_halted = self.is_halted()
        if not was_halted:
            self.halt()
        try:
            yield
        finally:
            if not was_halted:
                self.cont()

    def step(self):
        if self.verbose:
            util.INFO("  step()")
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_STEP)
        # There is bug in hardware and for blackhole step should be executed twice
        if self.device._arch == "blackhole":
            self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_STEP)

    def cont(self, verify=True):
        if not self.is_halted():
            util.WARN(f"Continue: {self.location.risc_name} core at {self.location.coord} is alredy running")
            return
        if self.verbose:
            util.INFO("  cont()")
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_CONTINUE)
        assert (
            not verify or not self.is_halted()
        ), f"Failed to continue {self.location.risc_name} core at {self.location.coord}"

    def continue_without_debug(self):
        if not self.is_halted():
            util.WARN(f"Continue: {self.location.risc_name} core at {self.location.coord} is alredy running")
            return
        if self.verbose:
            util.INFO("  cont()")
        self.__riscv_write(REG_COMMAND, COMMAND_CONTINUE)

    def read_status(self) -> BabyRiscDebugStatus:
        if self.verbose:
            util.INFO("  read_status()")
        status = self.__riscv_read(REG_STATUS)
        return BabyRiscDebugStatus.from_register(status, self.risc_info.max_watchpoints)

    def is_halted(self):
        if self.verbose:
            util.INFO("  is_halted()")
        return self.read_status().is_halted

    def is_pc_watchpoint_hit(self):
        if self.verbose:
            util.INFO("  is_pc_watchpoint_hit()")
        return self.read_status().is_pc_watchpoint_hit

    def assert_halted(self, message=""):
        """
        Make sure that the RISC-V core is halted.
        """
        if not self.is_halted():
            exception_message = f"{self.location.risc_name} is not halted"
            if message:
                exception_message += f": {message}"
            raise ValueError(exception_message)

    def is_memory_watchpoint_hit(self):
        if self.verbose:
            util.INFO("  is_pc_watchpoint_hit()")
        return self.read_status().is_memory_watchpoint_hit

    def read_gpr(self, reg_index):
        if self.verbose:
            util.INFO(f"  read_gpr({reg_index})")
        self.__riscv_write(REG_COMMAND_ARG_0, reg_index)
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_READ_REGISTER)
        return self.__riscv_read(REG_COMMAND_RETURN_VALUE)

    def write_gpr(self, reg_index, value):
        if self.verbose:
            util.INFO(f"  write_gpr({reg_index}, 0x{value:08x})")
        self.__riscv_write(REG_COMMAND_ARG_1, value)
        self.__riscv_write(REG_COMMAND_ARG_0, reg_index)
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_WRITE_REGISTER)

    def read_memory(self, addr):
        if self.enable_asserts:
            self.assert_halted()
        if self.verbose:
            util.INFO(f"  read_memory(0x{addr:08x})")
        self.__riscv_write(REG_COMMAND_ARG_0, addr)
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_READ_MEMORY)
        data = self.__riscv_read(REG_COMMAND_RETURN_VALUE)
        if self.verbose:
            util.INFO(f"                             read -> 0x{data:08x}")
        return data

    def write_memory(self, addr, value):
        if self.enable_asserts:
            self.assert_halted()
        if self.verbose:
            util.INFO(f"  write_memory(0x{addr:08x}, 0x{value:08x})")
        self.__riscv_write(REG_COMMAND_ARG_1, value)
        self.__riscv_write(REG_COMMAND_ARG_0, addr)
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_WRITE_MEMORY)

    def __update_watchpoint_setting(self, id, value):
        assert 0 <= value <= 15
        with self.ensure_halted():
            old_wp_settings = self.__riscv_read(REG_HW_WATCHPOINT_SETTINGS)
            mask = HW_WATCHPOINT_MASK << (id * 4)
            new_wp_settings = (old_wp_settings & (~mask)) + (value << (id * 4))
            self.__riscv_write(REG_HW_WATCHPOINT_SETTINGS, new_wp_settings)

    def __set_watchpoint(self, id, address, setting):
        with self.ensure_halted():
            self.__riscv_write(REG_HW_WATCHPOINT_0 + id, address)
            self.__update_watchpoint_setting(id, setting)

    def set_watchpoint_on_pc_address(self, id, address):
        self.__set_watchpoint(id, address, HW_WATCHPOINT_ENABLED + HW_WATCHPOINT_BREAKPOINT)

    def set_watchpoint_on_memory_read(self, id, address):
        self.__set_watchpoint(id, address, HW_WATCHPOINT_ENABLED + HW_WATCHPOINT_READ)

    def set_watchpoint_on_memory_write(self, id, address):
        self.__set_watchpoint(id, address, HW_WATCHPOINT_ENABLED + HW_WATCHPOINT_WRITE)

    def set_watchpoint_on_memory_access(self, id, address):
        self.__set_watchpoint(id, address, HW_WATCHPOINT_ENABLED + HW_WATCHPOINT_ACCESS)

    def read_watchpoints_state(self):
        settings = self.__riscv_read(REG_HW_WATCHPOINT_SETTINGS)
        watchpoints = []
        for i in range(self.risc_info.max_watchpoints):
            watchpoints.append(BabyRiscDebugWatchpointState.from_value((settings >> (i * 4)) & HW_WATCHPOINT_MASK))
        return watchpoints

    def read_watchpoint_address(self, id):
        return self.__riscv_read(REG_HW_WATCHPOINT_0 + id)

    def disable_watchpoint(self, id):
        self.__update_watchpoint_setting(id, 0)


class BabyRiscDebug(RiscDebug):
    def __init__(
        self, location: BabyRiscLocation, risc_info: BabyRiscInfo, verbose: bool = False, enable_asserts: bool = True
    ):
        register_store = location.coord._device.get_register_store(
            location.coord, noc_id=location.noc_id, neo_id=location.neo_id
        )
        self.location = location
        self.risc_info = risc_info
        self.register_store = register_store
        self.debug_hardware = (
            BabyRiscDebugHardware(location, register_store, risc_info, verbose, enable_asserts)
            if risc_info.has_debug_hardware
            else None
        )
        self.enable_asserts = enable_asserts
        self.verbose = verbose

        self.RISC_DBG_SOFT_RESET0 = register_store.get_register_noc_address("RISCV_DEBUG_REG_SOFT_RESET_0")

    @property
    def device(self) -> Device:
        return self.location.coord._device

    @property
    def context(self) -> Context:
        return self.device._context

    def __write(self, addr, data):
        write_words_to_device(self.location.coord, addr, data, self.device._id, self.context)

    def __read(self, addr):
        return read_word_from_device(self.location.coord, addr, self.device._id, self.context)

    def is_in_reset(self):
        reset_reg = self.__read(self.RISC_DBG_SOFT_RESET0)
        return (reset_reg >> self.risc_info.reset_flag_shift) & 1

    def set_reset_signal(self, value: bool):
        """
        Assert (1) or deassert (0) the reset signal of the RISC-V core.
        """
        assert value in [0, 1]
        reset_reg = self.__read(self.RISC_DBG_SOFT_RESET0)
        reset_reg = (reset_reg & ~(1 << self.risc_info.reset_flag_shift)) | (value << self.risc_info.reset_flag_shift)
        self.__write(self.RISC_DBG_SOFT_RESET0, reset_reg)
        new_reset_reg = self.__read(self.RISC_DBG_SOFT_RESET0)
        if new_reset_reg != reset_reg:
            util.ERROR(f"Error writing reset signal. Expected 0x{reset_reg:08x}, got 0x{new_reset_reg:08x}")
        return reset_reg

    def assert_not_in_reset(self, message=""):
        """
        Make sure that the RISC-V core is not in reset.
        """
        if self.is_in_reset():
            exception_message = f"{self.location.risc_name} is in reset"
            if message:
                exception_message += f": {message}"
            raise ValueError(exception_message)

    def invalidate_instruction_cache(self):
        """
        Invalidates the instruction cache of the RISC-V core.
        """
        self.write_register("RISCV_IC_INVALIDATE_InvalidateAll", 1 << self.location.risc_id)

    def assert_debug_hardware(self):
        """
        Make sure that the debug hardware is present.
        """
        if self.debug_hardware is None:
            raise ValueError(f"{self.location.risc_name} does not have debug hardware")

    def read_register(self, register: Union[str | RegisterDescription]):
        if self.enable_asserts:
            self.assert_not_in_reset()

        if isinstance(register, str):
            register = self.register_store.get_register_description(register)
        else:
            assert isinstance(register, RegisterDescription), f"Invalid register type {type(register)}"
        if register.noc_address is None:
            self.assert_debug_hardware()
            if self.enable_asserts:
                self.debug_hardware.assert_halted()
            value = self.debug_hardware.read_memory(register.address)
        else:
            value = self.__read(register.noc_address)
        return (value & register.mask) >> register.shift

    def write_register(self, register: Union[str | RegisterDescription], value: int):
        if isinstance(register, str):
            register = self.register_store.get_register_description(register)
        else:
            assert isinstance(register, RegisterDescription), f"Invalid register type {type(register)}"

        if register.noc_address is None:
            self.assert_debug_hardware()
            if self.enable_asserts:
                self.assert_not_in_reset()
                self.debug_hardware.assert_halted()
            read = self.debug_hardware.read_memory
            write = self.debug_hardware.write_memory
        else:
            read = self.__read
            write = self.__write

        # If register mask is not 0xffffffff, we need to read other bits
        if register.mask != 0xFFFFFFFF:
            old_value = read(register.address)
            value = (old_value & ~register.mask) | ((value << register.shift) & register.mask)
        write(register.address, value)

    @contextmanager
    def ensure_private_memory_access(self):
        self.assert_debug_hardware()
        if not self.is_in_reset():
            with self.debug_hardware.ensure_halted():
                yield
        else:
            start_address = self.risc_info.get_code_start_address(self.register_store)

            # Save 4 bytes from the start address (we need to return it to previous state)
            saved_bytes = self.__read(start_address)
            try:
                # Write endless loop to the start address
                self.__write(start_address, 0x6F)  # JAL x0, 0

                # Take core out of reset
                self.set_reset_signal(0)

                # Ensure it is halted and yield
                with self.debug_hardware.ensure_halted():
                    yield

                # Take core back to reset
                self.set_reset_signal(1)
            finally:
                # Write back the 4 bytes to the start address
                self.__write(start_address, saved_bytes)

    def set_branch_prediction(self, enable: bool):
        assert enable in [0, 1]
        value = 0 if enable else 1
        register_name = self.risc_info.branch_prediction_register
        bp_mask = self.risc_info.branch_prediction_mask
        previous_value = self.register_store.read_register(register_name)
        new_value = (previous_value & ~bp_mask) | (value * bp_mask)
        self.register_store.write_register(register_name, new_value)

    def is_halted(self) -> bool:
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        return self.debug_hardware.is_halted()

    def halt(self):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        return self.debug_hardware.halt()

    def step(self):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        return self.debug_hardware.step()

    def cont(self):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        return self.debug_hardware.cont(verify=False)

    @contextmanager
    def ensure_halted(self):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        with self.debug_hardware.ensure_halted():
            yield

    def read_gpr(self, register_index: int) -> int:
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        return self.debug_hardware.read_gpr(register_index)

    def write_gpr(self, register_index: int, value: int):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        self.debug_hardware.write_gpr(register_index, value)

    def read_memory(self, address: int) -> int:
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        return self.debug_hardware.read_memory(address)

    def write_memory(self, address: int, value: int):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        self.debug_hardware.write_memory(address, value)

    def get_callstack(self, elf_path: str, limit: int = 100, stop_on_main: bool = True):
        callstack = []
        with self.ensure_halted():
            elf = read_elf(self.context.server_ifc, elf_path)
            pc = self.read_gpr(32)
            frame_description = elf["frame-info"].get_frame_description(pc, self)
            frame_pointer = frame_description.read_previous_cfa()
            i = 0
            while i < limit:
                file_line = elf["dwarf"].find_file_line_by_address(pc)
                function_die = elf["dwarf"].find_function_by_address(pc)
                if function_die is not None and function_die.category == "inlined_function":
                    # Returning inlined functions (virtual frames)
                    callstack.append(
                        CallstackEntry(pc, function_die.name, file_line[0], file_line[1], file_line[2], frame_pointer)
                    )
                    file_line = function_die.call_file_info
                    while function_die.category == "inlined_function":
                        i = i + 1
                        function_die = function_die.parent
                        callstack.append(
                            CallstackEntry(
                                None, function_die.name, file_line[0], file_line[1], file_line[2], frame_pointer
                            )
                        )
                        file_line = function_die.call_file_info
                elif function_die is not None and function_die.category == "subprogram":
                    callstack.append(
                        CallstackEntry(pc, function_die.name, file_line[0], file_line[1], file_line[2], frame_pointer)
                    )
                else:
                    if file_line is not None:
                        callstack.append(
                            CallstackEntry(pc, None, file_line[0], file_line[1], file_line[2], frame_pointer)
                        )
                    else:
                        callstack.append(CallstackEntry(pc, None, None, None, None, frame_pointer))

                # We want to stop when we print main as frame descriptor might not be correct afterwards
                if stop_on_main and function_die is not None and function_die.name == "main":
                    break

                # We want to stop when we are at the end of frames list
                if frame_pointer == 0:
                    break

                frame_description = elf["frame-info"].get_frame_description(pc, self)
                if frame_description is None:
                    util.WARN("We don't have information on frame and we don't know how to proceed")
                    break

                cfa = frame_pointer
                return_address = frame_description.read_register(1, cfa)
                frame_pointer = frame_description.read_previous_cfa(cfa)
                pc = return_address
                i = i + 1
        return callstack

    # TODO: Move load methods to RiscLoader
    def _write_block_through_debug(self, address, data):
        """
        Writes a block of data to a given address through the debug interface.
        """
        with self.ensure_halted():
            for i in range(0, len(data), 4):
                word = data[i : i + 4]
                word = word.ljust(4, b"\x00")
                word = int.from_bytes(word, byteorder="little")
                self.write_memory(address + i, word)

    def _read_block_through_debug(self, address, byte_count):
        """
        Reads a block of data from a given address through the debug interface.
        """
        with self.ensure_halted():
            data = bytearray()
            for i in range(0, byte_count, 4):
                word = self.read_memory(address + i)
                data.extend(word.to_bytes(4, byteorder="little"))

        return data

    def _write_block(self, address, data: bytes):
        """
        Writes a block of bytes to a given address. Knows about the sections not accessible through NOC (0xFFB00000 or 0xFFC00000), and uses
        the debug interface to write them.
        """
        if address & self.risc_info.private_memory_base == self.risc_info.private_memory_base or (
            self.risc_info.private_code_base is not None
            and address & self.risc_info.private_code_base == self.risc_info.private_code_base
        ):
            # Use debug interface
            self._write_block_through_debug(address, data)
        else:
            write_to_device(self.location.coord, address, data, self.location.coord._device._id, self.context)

    def _read_block(self, address, byte_count):
        """
        Reads a block of bytes from a given address. Knows about the sections not accessible through NOC (0xFFB00000 or 0xFFC00000), and uses
        the debug interface to read them.
        """
        if address & self.risc_info.private_memory_base == self.risc_info.private_memory_base or (
            self.risc_info.private_code_base is not None
            and address & self.risc_info.private_code_base == self.risc_info.private_code_base
        ):
            # Use debug interface
            return self._read_block_through_debug(address, byte_count)
        else:
            return read_from_device(
                self.location.coord,
                address,
                self.location.coord._device._id,
                byte_count,
                self.context,
            )

    SECTIONS_TO_LOAD = [".init", ".text", ".ldm_data", ".stack"]

    def _remap_address(self, address: int, loader_data: int, loader_code: int):
        if address & self.risc_info.private_memory_base == self.risc_info.private_memory_base:
            if loader_data is not None and isinstance(loader_data, int):
                return address - self.risc_info.private_memory_base + loader_data
            return address
        if (
            self.risc_info.private_code_base is not None
            and address & self.risc_info.private_code_base == self.risc_info.private_code_base
        ):
            if loader_code is not None and isinstance(loader_code, int):
                return address - self.risc_info.private_code_base + loader_code
            return address
        return address

    def _load_elf_sections(self, elf_path, loader_data: Union[str, int], loader_code: Union[str, int]):
        """
        Given an ELF file, this function loads the sections specified in SECTIONS_TO_LOAD to the
        memory of the RISC-V core. It also loads (into location 0) the jump instruction to the
        address of the .init section.
        """
        if not os.path.exists(elf_path):
            raise FileNotFoundError(f"File {elf_path} not found")

        # Remember the .init section address to jump to after loading
        init_section_address = None

        try:
            elf_file = self.context.server_ifc.get_binary(elf_path)
            elf_file = ELFFile(elf_file)

            # Try to find address mapping for loader_data and loader_code
            for section in elf_file.iter_sections():
                if section.data() and hasattr(section.header, "sh_addr"):
                    name = section.name
                    address = section.header.sh_addr
                    if name == loader_data:
                        loader_data = address
                    elif name == loader_code:
                        loader_code = address

            # Load section into memory
            for section in elf_file.iter_sections():
                if section.data() and hasattr(section.header, "sh_addr"):
                    name = section.name
                    if name in self.SECTIONS_TO_LOAD:
                        address = section.header.sh_addr
                        if address % 4 != 0:
                            raise ValueError(f"Section address 0x{address:08x} is not 32-bit aligned")

                        address = self._remap_address(address, loader_data, loader_code)
                        data = section.data()

                        if name == ".init":
                            init_section_address = address

                        util.VERBOSE(f"Writing section {name} to address 0x{address:08x}. Size: {len(data)} bytes")
                        self._write_block(address, data)

            # Check that what we have written is correct
            if self.enable_asserts:
                for section in elf_file.iter_sections():
                    if section.data() and hasattr(section.header, "sh_addr"):
                        name = section.name
                        if name in self.SECTIONS_TO_LOAD:
                            address = section.header.sh_addr
                            data = section.data()
                            address = self._remap_address(address, loader_data, loader_code)
                            read_data = self._read_block(address, len(data))
                            if read_data != data:
                                util.ERROR(f"Error writing section {name} to address 0x{address:08x}.")
                                continue
                            else:
                                util.VERBOSE(
                                    f"Section {name} loaded successfully to address 0x{address:08x}. Size: {len(data)} bytes"
                                )
        except Exception as e:
            util.ERROR(e)
            raise util.TTException(f"Error loading elf file {elf_path}")

        # TODO: Update risc_id
        self.context.elf_loaded(self.location.coord, self.location.risc_id, elf_path)
        return init_section_address

    def load_elf(self, elf_path: str):
        # Risc must be in reset
        assert self.is_in_reset(), f"RISC at location {self.location} is not in reset."

        # Load elf file to the L1 memory; avoid writing to private sections
        init_section_address = self._load_elf_sections(elf_path, loader_data=".loader_init", loader_code=".loader_code")
        assert init_section_address is not None, "No .init section found in the ELF file"

        # Change core start address to the start of the .init section
        # if it is BRISC or ERISC, we should just add jump to start address instead, since we cannot change start address
        if not self.risc_info.can_change_code_start_address:
            if init_section_address != 0:
                jump_instruction = BabyRiscInfo.get_jump_to_offset_instruction(init_section_address)
                self.__write(0, jump_instruction)
        else:
            # Change core start address
            self.risc_info.set_code_start_address(self.register_store, init_section_address)

    def run_elf(self, elf_path: str):
        # Make sure risc is in reset
        if not self.is_in_reset():
            self.set_reset_signal(True)

        self.load_elf(elf_path)

        # Take risc out of reset
        self.set_reset_signal(False)
        assert not self.is_in_reset(), f"RISC at location {self.location} is still in reset."
        if self.debug_hardware is not None:
            assert (
                not self.is_halted() or self.debug_hardware.read_status().is_ebreak_hit
            ), f"RISC at location {self.location} is still halted, but not because of ebreak."
