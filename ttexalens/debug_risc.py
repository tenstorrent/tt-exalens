# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from collections import namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.parse_elf import ParsedElfFile, ParsedElfFileWithOffset
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device, read_from_device, write_to_device
from ttexalens import util as util
import os

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
STATUS_WATCHPOINT_1_HIT = 0x00000200
STATUS_WATCHPOINT_2_HIT = 0x00000400
STATUS_WATCHPOINT_3_HIT = 0x00000800
STATUS_WATCHPOINT_4_HIT = 0x00001000
STATUS_WATCHPOINT_5_HIT = 0x00002000
STATUS_WATCHPOINT_6_HIT = 0x00004000
STATUS_WATCHPOINT_7_HIT = 0x00008000

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

RISCV_REGS = {
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


def get_register_index(reg_index_or_name):
    if reg_index_or_name in RISCV_REGS:
        return reg_index_or_name
    else:  # try to find register by name
        for i, name in RISCV_REGS.items():
            if reg_index_or_name.lower() in name:
                return i
    raise ValueError(f"Unknown register {reg_index_or_name}")


RISC_NAMES = ["BRISC", "TRISC0", "TRISC1", "TRISC2", "NCRISC"]


def get_risc_name(id):
    if 0 <= id < len(RISC_NAMES):
        return RISC_NAMES[id]
    else:
        return f"Unknown RISC id {id}"


def get_risc_id(name):
    for i, n in enumerate(RISC_NAMES):
        if name.lower() in n.lower():
            return i
    raise ValueError(f"Unknown RISC name {name}")


def get_risc_reset_shift(id):
    """
    Return the reset register bit position for a given RISC.
    """
    if id == 0:
        return 11
    elif id == 1:
        return 12
    elif id == 2:
        return 13
    elif id == 3:
        return 14
    elif id == 4:
        return 18
    else:
        return f"Unknown RISC id {id}"


@dataclass
class RiscLoc:
    loc: OnChipCoordinate
    noc_id: int = 0
    risc_id: int = 0

    def __hash__(self) -> int:
        return hash((self.loc, self.noc_id, self.risc_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RiscLoc):
            return False
        return self.loc == other.loc and self.noc_id == other.noc_id and self.risc_id == other.risc_id


@dataclass
class RiscDebugStatus:
    is_halted: bool
    is_pc_watchpoint_hit: bool
    is_memory_watchpoint_hit: bool
    is_ebreak_hit: bool
    is_watchpoint0_hit: bool
    is_watchpoint1_hit: bool
    is_watchpoint2_hit: bool
    is_watchpoint3_hit: bool
    is_watchpoint4_hit: bool
    is_watchpoint5_hit: bool
    is_watchpoint6_hit: bool
    is_watchpoint7_hit: bool

    @property
    def watchpoints_hit(self):
        return [
            self.is_watchpoint0_hit,
            self.is_watchpoint1_hit,
            self.is_watchpoint2_hit,
            self.is_watchpoint3_hit,
            self.is_watchpoint4_hit,
            self.is_watchpoint5_hit,
            self.is_watchpoint6_hit,
            self.is_watchpoint7_hit,
        ]

    @staticmethod
    def from_register(value: int):
        return RiscDebugStatus(
            value & STATUS_HALTED != 0,
            value & STATUS_PC_WATCHPOINT_HIT != 0,
            value & STATUS_MEMORY_WATCHPOINT_HIT != 0,
            value & STATUS_EBREAK_HIT != 0,
            value & STATUS_WATCHPOINT_0_HIT != 0,
            value & STATUS_WATCHPOINT_1_HIT != 0,
            value & STATUS_WATCHPOINT_2_HIT != 0,
            value & STATUS_WATCHPOINT_3_HIT != 0,
            value & STATUS_WATCHPOINT_4_HIT != 0,
            value & STATUS_WATCHPOINT_5_HIT != 0,
            value & STATUS_WATCHPOINT_6_HIT != 0,
            value & STATUS_WATCHPOINT_7_HIT != 0,
        )


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

    @staticmethod
    def from_value(value: int):
        assert value & HW_WATCHPOINT_MASK == value, f"Invalid watchpoint value {value:08x}"

        return RiscDebugWatchpointState(
            value & HW_WATCHPOINT_ENABLED != 0,
            value & HW_WATCHPOINT_ACCESS != 0,
            value & HW_WATCHPOINT_READ != 0,
            value & HW_WATCHPOINT_WRITE != 0,
        )


class RiscDebug:
    def __init__(self, location: RiscLoc, context, verbose=False, enable_asserts=True):
        assert 0 <= location.risc_id <= 4, f"Invalid risc id({location.risc_id})"
        self.location = location
        self.enable_asserts = enable_asserts
        self.CONTROL0_WRITE = 0x80010000 + (self.location.risc_id << 17)
        self.CONTROL0_READ = 0x80000000 + (self.location.risc_id << 17)
        self.verbose = verbose
        self.context = context
        self.max_watchpoints = 8
        device = location.loc._device
        self.RISC_DBG_CNTL0 = device.get_tensix_register_address("RISCV_DEBUG_REG_RISC_DBG_CNTL_0")
        self.RISC_DBG_CNTL1 = device.get_tensix_register_address("RISCV_DEBUG_REG_RISC_DBG_CNTL_1")
        self.RISC_DBG_STATUS0 = device.get_tensix_register_address("RISCV_DEBUG_REG_RISC_DBG_STATUS_0")
        self.RISC_DBG_STATUS1 = device.get_tensix_register_address("RISCV_DEBUG_REG_RISC_DBG_STATUS_1")
        self.RISC_DBG_SOFT_RESET0 = device.get_tensix_register_address("RISCV_DEBUG_REG_SOFT_RESET_0")
        self.DEBUG_READ_VALID_BIT = 1 << 30

    def get_reg_name_for_address(self, addr):
        if addr == self.RISC_DBG_CNTL0:
            return "CNTL0"
        elif addr == self.RISC_DBG_CNTL1:
            return "CNTL1"
        elif addr == self.RISC_DBG_STATUS0:
            return "STATUS0"
        elif addr == self.RISC_DBG_STATUS1:
            return "STATUS1"
        else:
            return f"Unknown register {addr}"

    def __write(self, addr, data):
        if self.enable_asserts:
            self.assert_not_in_reset()
        if self.verbose:
            util.DEBUG(f"{self.get_reg_name_for_address(addr)} <- WR   0x{data:08x}")
        write_words_to_device(self.location.loc, addr, data, self.location.loc._device._id, self.context)

    def __read(self, addr):
        if self.enable_asserts:
            self.assert_not_in_reset()
        data = read_word_from_device(self.location.loc, addr, self.location.loc._device._id, self.context)
        if self.verbose:
            util.DEBUG(f"{self.get_reg_name_for_address(addr)} -> RD == 0x{data:08x}")
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
        return (status0 & self.DEBUG_READ_VALID_BIT) == self.DEBUG_READ_VALID_BIT

    def __riscv_read(self, reg_addr):
        if self.verbose:
            util.INFO(f"  __riscv_read({reg_addr})")
        self.__trigger_read(reg_addr)

        if self.enable_asserts:
            if not self.__is_read_valid():
                util.WARN(
                    f"Reading from RiscV debug registers failed (debug read valid bit is set to 0). Run `srs 0` to check if core is active."
                )
        return self.__read(self.RISC_DBG_STATUS1)

    def enable_debug(self):
        if self.verbose:
            util.INFO("  enable_debug()")
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE)

    def _halt_command(self):
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_HALT)

    def halt(self):
        if self.is_halted():
            util.WARN(f"Halt: {get_risc_name(self.location.risc_id)} core at {self.location.loc} is already halted")
            return
        if self.verbose:
            util.INFO("  halt()")
        self._halt_command()
        assert self.is_halted(), f"Failed to halt {get_risc_name(self.location.risc_id)} core at {self.location.loc}"

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
        if self.location.loc._device._arch == "blackhole":
            self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_STEP)

    def cont(self, verify=True):
        if not self.is_halted():
            util.WARN(
                f"Continue: {get_risc_name(self.location.risc_id)} core at {self.location.loc} is already running"
            )
            return
        if self.verbose:
            util.INFO("  cont()")
        self.__riscv_write(REG_COMMAND, COMMAND_DEBUG_MODE + COMMAND_CONTINUE)
        assert (
            not verify or not self.is_halted()
        ), f"Failed to continue {get_risc_name(self.location.risc_id)} core at {self.location.loc}"

    def continue_without_debug(self):
        """
        Continues RISC-V core execution without debugging functionality.
        This method triggers core execution to continue by writing COMMAND_CONTINUE to the command register.
        Note: This function might trigger core lockup - use cont() method instead.
        Returns:
            None
        Warns:
            If the core is already running when method is called
        Side Effects:
            - Writes to RISC-V command register
            - May log debug information if verbose mode is enabled
        """
        if not self.is_halted():
            util.WARN(
                f"Continue: {get_risc_name(self.location.risc_id)} core at {self.location.loc} is already running"
            )
            return
        if self.verbose:
            util.INFO("  cont()")
        self.__riscv_write(REG_COMMAND, COMMAND_CONTINUE)

    def read_status(self) -> RiscDebugStatus:
        if self.verbose:
            util.INFO("  read_status()")
        status = self.__riscv_read(REG_STATUS)
        return RiscDebugStatus.from_register(status)

    def is_halted(self):
        if self.verbose:
            util.INFO("  is_halted()")
        return self.read_status().is_halted

    def is_pc_watchpoint_hit(self):
        if self.verbose:
            util.INFO("  is_pc_watchpoint_hit()")
        return self.read_status().is_pc_watchpoint_hit

    def is_in_reset(self):
        reset_reg = read_word_from_device(
            self.location.loc, self.RISC_DBG_SOFT_RESET0, self.location.loc._device.id(), self.context
        )
        shift = get_risc_reset_shift(self.location.risc_id)
        return (reset_reg >> shift) & 1

    def set_reset_signal(self, value):
        """
        Assert (1) or deassert (0) the reset signal of the RISC-V core.
        """
        assert value in [0, 1]
        shift = get_risc_reset_shift(self.location.risc_id)
        reset_reg = read_word_from_device(
            self.location.loc, self.RISC_DBG_SOFT_RESET0, self.location.loc._device.id(), self.context
        )
        reset_reg = (reset_reg & ~(1 << shift)) | (value << shift)
        write_words_to_device(
            self.location.loc, self.RISC_DBG_SOFT_RESET0, reset_reg, self.location.loc._device.id(), self.context
        )
        new_reset_reg = read_word_from_device(
            self.location.loc, self.RISC_DBG_SOFT_RESET0, self.location.loc._device.id(), self.context
        )
        if new_reset_reg != reset_reg:
            util.ERROR(f"Error writing reset signal. Expected 0x{reset_reg:08x}, got 0x{new_reset_reg:08x}")
        return reset_reg

    def assert_not_in_reset(self, message=""):
        """
        Make sure that the RISC-V core is not in reset.
        """
        if self.is_in_reset():
            exception_message = f"{get_risc_name(self.location.risc_id)} is in reset"
            if message:
                exception_message += f": {message}"
            raise ValueError(exception_message)

    def assert_halted(self, message=""):
        """
        Make sure that the RISC-V core is halted.
        """
        if not self.is_halted():
            exception_message = f"{get_risc_name(self.location.risc_id)} is not halted"
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
        if reg_index == 32 and self.location.loc._device._arch == "blackhole":
            # Fall back to debug signals when reading pc on blackhole
            return blackhole_read_pc(self.location)

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
        for i in range(self.max_watchpoints):
            watchpoints.append(RiscDebugWatchpointState.from_value((settings >> (i * 4)) & HW_WATCHPOINT_MASK))
        return watchpoints

    def read_watchpoint_address(self, id):
        return self.__riscv_read(REG_HW_WATCHPOINT_0 + id)

    def disable_watchpoint(self, id):
        self.__update_watchpoint_setting(id, 0)

    def invalidate_instruction_cache(self):
        """
        Invalidates the instruction cache of the RISC-V core.
        """
        self.write_configuration_register("RISCV_IC_INVALIDATE_InvalidateAll", 1 << self.location.risc_id)

    def read_configuration_register(self, register_name: str):
        if self.enable_asserts:
            self.assert_halted()
        register = self.location.loc._device.get_tensix_register_description(register_name)
        return (self.read_memory(register.address) & register.mask) >> register.shift

    def write_configuration_register(self, register, value: int):
        if self.enable_asserts:
            self.assert_halted()

        if isinstance(register, str):
            register = self.location.loc._device.get_tensix_register_description(register)

        # Speed optimization: if register mask is 0xffffffff, we can write directly to memory
        if register.mask == 0xFFFFFFFF:
            self.write_memory(register.address, value)
        else:
            old_value = self.read_memory(register.address)
            new_value = (old_value & ~register.mask) | ((value << register.shift) & register.mask)
            self.write_memory(register.address, new_value)


def blackhole_read_pc(location: RiscLoc) -> int:
    loc = location.loc
    device = loc._device
    debug_bus_signal_store = device.get_block(loc).debug_bus
    if not debug_bus_signal_store:
        util.ERROR(f"Device {device._id} at location {loc.to_user_str()} does not have a debug bus.")
        return 0

    value: int = 0
    if location.risc_id == 0:
        value = debug_bus_signal_store.read_signal("brisc_pc")
    elif location.risc_id == 1:
        value = debug_bus_signal_store.read_signal("trisc0_pc")
    elif location.risc_id == 2:
        value = debug_bus_signal_store.read_signal("trisc1_pc")
    elif location.risc_id == 3:
        value = debug_bus_signal_store.read_signal("trisc2_pc")
    elif location.risc_id == 4:
        value = debug_bus_signal_store.read_signal("ncrisc_pc")
    else:
        util.ERROR(f"Could not read PC for RISC ID {location.risc_id}")
    return value
