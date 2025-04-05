# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Union

from ttexalens import util
from ttexalens.baby_risc_info import BabyRiscInfo
from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.risc_debug import RiscLocation, RiscDebug
from ttexalens.register_store import RegisterDescription, RegisterStore
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device

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
        self.debug_hardware = BabyRiscDebugHardware(location, register_store, risc_info, verbose, enable_asserts)
        self.enable_asserts = enable_asserts
        self.verbose = verbose

        self.RISC_DBG_SOFT_RESET0 = register_store.get_register_noc_address("RISCV_DEBUG_REG_SOFT_RESET_0")

    @property
    def location(self) -> BabyRiscLocation:
        return self.debug_hardware.location

    @property
    def risc_info(self) -> BabyRiscInfo:
        return self.debug_hardware.risc_info

    @property
    def register_store(self) -> RegisterStore:
        return self.debug_hardware.register_store

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

    def read_register(self, register: Union[str | RegisterDescription]):
        if self.enable_asserts:
            self.assert_not_in_reset()
            self.debug_hardware.assert_halted()

        if isinstance(register, str):
            register = self.register_store.get_register_description(register)
        else:
            assert isinstance(register, RegisterDescription), f"Invalid register type {type(register)}"
        if register.noc_address is None:
            value = self.debug_hardware.read_memory(register.address)
        else:
            value = self.__read(register.noc_address)
        return (value & register.mask) >> register.shift

    def write_register(self, register: Union[str | RegisterDescription], value: int):
        if self.enable_asserts:
            self.assert_not_in_reset()
            self.debug_hardware.assert_halted()

        if isinstance(register, str):
            register = self.register_store.get_register_description(register)
        else:
            assert isinstance(register, RegisterDescription), f"Invalid register type {type(register)}"

        read = self.__read if register.noc_address is not None else self.debug_hardware.read_memory
        write = self.__write if register.noc_address is not None else self.debug_hardware.write_memory

        # If register mask is not 0xffffffff, we need to read other bits
        if register.mask != 0xFFFFFFFF:
            old_value = read(register.address)
            value = (old_value & ~register.mask) | ((value << register.shift) & register.mask)
        write(register.address, value)

    @contextmanager
    def ensure_private_memory_access(self):
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
        return self.debug_hardware.is_halted()

    def halt(self):
        if self.enable_asserts:
            self.assert_not_in_reset()
        return self.debug_hardware.halt()

    def step(self):
        if self.enable_asserts:
            self.assert_not_in_reset()
        return self.debug_hardware.step()

    def cont(self):
        if self.enable_asserts:
            self.assert_not_in_reset()
        return self.debug_hardware.cont(verify=False)

    @contextmanager
    def ensure_halted(self):
        if self.enable_asserts:
            self.assert_not_in_reset()
        with self.debug_hardware.ensure_halted():
            yield

    def read_gpr(self, register_index: int) -> int:
        if self.enable_asserts:
            self.assert_not_in_reset()
        return self.debug_hardware.read_gpr(register_index)

    def write_gpr(self, register_index: int, value: int):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.debug_hardware.write_gpr(register_index, value)

    def read_memory(self, address: int) -> int:
        if self.enable_asserts:
            self.assert_not_in_reset()
        return self.debug_hardware.read_memory(address)

    def write_memory(self, address: int, value: int):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.debug_hardware.write_memory(address, value)
