# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from collections import namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Union
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.parse_elf import read_elf
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
            util.WARN(f"Continue: {get_risc_name(self.location.risc_id)} core at {self.location.loc} is alredy running")
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
            util.WARN(f"Continue: {get_risc_name(self.location.risc_id)} core at {self.location.loc} is alredy running")
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


from elftools.elf.elffile import ELFFile


class RiscLoader:
    """
    This class is used to load elf file to a RISC-V core.
    """

    def __init__(self, risc_debug: RiscDebug, context: Context, verbose=False):
        self.verbose = verbose
        self.risc_debug = risc_debug
        self.context = context

    SECTIONS_TO_LOAD = [".init", ".text", ".ldm_data", ".stack"]
    PRIVATE_MEMORY_BASE = 0xFFB00000
    PRIVATE_CODE_BASE = 0xFFC00000

    @contextmanager
    def ensure_reading_configuration_register(self):
        """
        Ensures that an reading configuration register operation is performed in correct state.
        """

        # If core is not in reset, we can use it to read configuration.
        if not self.risc_debug.is_in_reset():
            # Read the configuration register using the core itself
            with self.risc_debug.ensure_halted():
                yield self.risc_debug
        else:
            # Since we cannot access configuration registers except through debug interface, we need to have a core that is started.
            # Use BRISC since we know that its start address is always 0.
            brisc_debug = RiscDebug(RiscLoc(self.risc_debug.location.loc, 0, 0), self.context, self.verbose)
            brisc_loader = RiscLoader(brisc_debug, self.context, self.verbose)
            brisc_debug = brisc_loader.risc_debug
            if not brisc_debug.is_in_reset():
                with brisc_debug.ensure_halted():
                    yield brisc_debug
            else:
                # Start BRISC in infinite loop and read the configuration register
                brisc_loader.start_risc_in_infinite_loop(0)

                try:
                    with brisc_debug.ensure_halted():
                        yield brisc_debug
                finally:
                    # Return BRISC in reset
                    brisc_debug.set_reset_signal(1)
                    assert brisc_debug.is_in_reset(), f"RISC at location {brisc_debug.location} is not in reset."

    def set_branch_prediction(self, value: bool):
        """
        Set the branch prediction configuration register to enable/disable for selected core.
        """
        assert value in [0, 1]
        value = 0 if value else 1
        risc_id = self.risc_debug.location.risc_id
        risc_name = get_risc_name(risc_id)

        with self.ensure_reading_configuration_register() as rdbg:
            if risc_name == "BRISC":
                rdbg.write_configuration_register("DISABLE_RISC_BP_Disable_main", value)
            elif risc_name == "TRISC0":
                previous_value = rdbg.read_configuration_register("DISABLE_RISC_BP_Disable_trisc")
                if value:
                    rdbg.write_configuration_register("DISABLE_RISC_BP_Disable_trisc", previous_value | 0b001)
                else:
                    rdbg.write_configuration_register("DISABLE_RISC_BP_Disable_trisc", previous_value & ~0b001)
            elif risc_name == "TRISC1":
                previous_value = rdbg.read_configuration_register("DISABLE_RISC_BP_Disable_trisc")
                if value:
                    rdbg.write_configuration_register("DISABLE_RISC_BP_Disable_trisc", previous_value | 0b010)
                else:
                    rdbg.write_configuration_register("DISABLE_RISC_BP_Disable_trisc", previous_value & ~0b010)
            elif risc_name == "TRISC2":
                previous_value = rdbg.read_configuration_register("DISABLE_RISC_BP_Disable_trisc")
                if value:
                    rdbg.write_configuration_register("DISABLE_RISC_BP_Disable_trisc", previous_value | 0b100)
                else:
                    rdbg.write_configuration_register("DISABLE_RISC_BP_Disable_trisc", previous_value & ~0b100)
            elif risc_name == "NCRISC":
                rdbg.write_configuration_register("DISABLE_RISC_BP_Disable_ncrisc", value)
            else:
                raise ValueError(f"Unknown RISC name {risc_name}")

    def _get_risc_start_address_register_configuration(self):
        """
        Returns namedtuple that has names of two configuration registers: address register and enable register, and the bit that enables this core.
        """
        risc_id = self.risc_debug.location.risc_id
        risc_name = get_risc_name(risc_id)

        # BRISC is always at 0 and it doesn't have register name, so we return None
        if risc_name == "BRISC":
            return None

        from collections import namedtuple

        RegisterConfiguration = namedtuple(
            "RegisterConfiguration", ["address_register", "enable_register", "enable_bit"]
        )

        # For other cores, there is configuration register that specifies the start address
        if risc_name == "TRISC0":
            return RegisterConfiguration(
                "TRISC_RESET_PC_SEC0_PC", "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en", 0b001
            )
        elif risc_name == "TRISC1":
            return RegisterConfiguration(
                "TRISC_RESET_PC_SEC1_PC", "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en", 0b010
            )
        elif risc_name == "TRISC2":
            return RegisterConfiguration(
                "TRISC_RESET_PC_SEC2_PC", "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en", 0b100
            )
        elif risc_name == "NCRISC":
            return RegisterConfiguration("NCRISC_RESET_PC_PC", "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en", 0b1)
        else:
            raise ValueError(f"Unknown RISC name {risc_name}")

    def get_risc_start_address(self):
        """
        Get the address of first instruction that will be executed when RISC-V core is taken out of reset.
        Returns None if configuration register is not enabled for specific core. You can use set_risc_start_address to set the start address which will enable configuration register.
        """
        register_configuration = self._get_risc_start_address_register_configuration()
        # BRISC is always at 0 and it doesn't have register name, so we return 0
        if register_configuration is None:
            return 0

        with self.ensure_reading_configuration_register() as rdbg:
            # Check if configuration register is enabled for this core
            enabled_register_value = rdbg.read_configuration_register(register_configuration.enable_register)
            if enabled_register_value & register_configuration.enable_bit == 0:
                # Since configuration register is not enabled, we don't know how to get start address, hence we return None
                return None

            # Return value that is read from configuration register
            return rdbg.read_configuration_register(register_configuration.address_register)

    def set_risc_start_address(self, address):
        """
        Set the address of first instruction that will be executed when RISC-V core is taken out of reset.
        """
        register_configuration = self._get_risc_start_address_register_configuration()
        if register_configuration is None:
            raise ValueError(f"Cannot change start address of BRISC register")

        with self.ensure_reading_configuration_register() as rdbg:
            # Read previous value of enable register
            enabled_register_value = rdbg.read_configuration_register(register_configuration.enable_register)

            # Update enable register to enable this core
            rdbg.write_configuration_register(
                register_configuration.enable_register, enabled_register_value | register_configuration.enable_bit
            )

            # Update start address register
            rdbg.write_configuration_register(register_configuration.address_register, address)

    def start_risc_in_infinite_loop(self, address):
        # Make sure risc is in reset
        if not self.risc_debug.is_in_reset():
            self.risc_debug.set_reset_signal(1)
        assert self.risc_debug.is_in_reset(), f"RISC at location {self.risc_debug.location} is not in reset."

        # Generate infinite loop instruction (JAL 0)
        jal_instruction = RiscLoader.get_jump_to_offset_instruction(
            0
        )  # Since JAL uses offset and we need to return to current address, we specify 0
        write_words_to_device(
            self.risc_debug.location.loc,
            address,
            jal_instruction,
            self.risc_debug.location.loc._device.id(),
            self.context,
        )

        # Take risc out of reset
        self.risc_debug.set_reset_signal(0)
        assert not self.risc_debug.is_in_reset(), f"RISC at location {self.risc_debug.location} is still in reset."
        assert not self.risc_debug.is_halted(), f"RISC at location {self.risc_debug.location} is still halted."

    @staticmethod
    def get_jump_to_offset_instruction(offset, rd=0):
        """
        Generate a JAL instruction code based on the given offset.

        :param offset: The offset to jump to, can be positive or negative.
        :param rd: The destination register (default is x1 for the return address).
        :return: The 32-bit JAL instruction code.
        """
        if rd < 0 or rd > 31:
            raise ValueError("Invalid register number. rd must be between 0 and 31.")

        if offset < -(2**20) or offset >= 2**20:
            raise ValueError("Offset out of range. Must be between -2^20 and 2^20-1.")

        # Make sure the offset is within the range for a 20-bit signed integer
        offset &= 0x1FFFFF

        # Extracting the bit fields from the offset
        jal_offset_bit_20 = (offset >> 20) & 0x1
        jal_offset_bits_10_to_1 = (offset >> 1) & 0x3FF
        jal_offset_bit_11 = (offset >> 11) & 0x1
        jal_offset_bits_19_to_12 = (offset >> 12) & 0xFF

        # Reconstruct the 20-bit immediate in the JAL instruction format
        jal_offset = (
            (jal_offset_bit_20 << 31)
            | (jal_offset_bits_19_to_12 << 12)
            | (jal_offset_bit_11 << 20)
            | (jal_offset_bits_10_to_1 << 21)
        )

        # Construct the instruction
        return jal_offset | (rd << 7) | 0x6F

    def write_block_through_debug(self, address, data):
        """
        Writes a block of data to a given address through the debug interface.
        """
        rd = self.risc_debug
        rd.enable_debug()
        with rd.ensure_halted():
            for i in range(0, len(data), 4):
                word = data[i : i + 4]
                word = word.ljust(4, b"\x00")
                word = int.from_bytes(word, byteorder="little")
                rd.write_memory(address + i, word)
                # ww = rd.read_memory(address + i)
                # if ww != word:
                #     util.ERROR(f"Error writing word at address 0x{address + i:08x}. Expected 0x{word:08x}, got 0x{ww:08x}")

    def read_block_through_debug(self, address, byte_count):
        """
        Reads a block of data from a given address through the debug interface.
        """
        rd = self.risc_debug
        rd.enable_debug()
        with rd.ensure_halted():
            data = bytearray()
            for i in range(0, byte_count, 4):
                word = rd.read_memory(address + i)
                data.extend(word.to_bytes(4, byteorder="little"))

        return data

    def write_block(self, address, data: bytes):
        """
        Writes a block of bytes to a given address. Knows about the sections not accessible through NOC (0xFFB00000 or 0xFFC00000), and uses
        the debug interface to write them.
        """
        if (
            address & self.PRIVATE_MEMORY_BASE == self.PRIVATE_MEMORY_BASE
            or address & self.PRIVATE_CODE_BASE == self.PRIVATE_CODE_BASE
        ):
            # Use debug interface
            self.write_block_through_debug(address, data)
        else:
            write_to_device(
                self.risc_debug.location.loc, address, data, self.risc_debug.location.loc._device.id(), self.context
            )

    def read_block(self, address, byte_count):
        """
        Reads a block of bytes from a given address. Knows about the sections not accessible through NOC (0xFFB00000 or 0xFFC00000), and uses
        the debug interface to read them.
        """
        if (
            address & self.PRIVATE_MEMORY_BASE == self.PRIVATE_MEMORY_BASE
            or address & self.PRIVATE_CODE_BASE == self.PRIVATE_CODE_BASE
        ):
            # Use debug interface
            return self.read_block_through_debug(address, byte_count)
        else:
            return read_from_device(
                self.risc_debug.location.loc,
                address,
                self.risc_debug.location.loc._device.id(),
                byte_count,
                self.context,
            )

    def remap_address(self, address: int, loader_data: int, loader_code: int):
        if address & self.PRIVATE_MEMORY_BASE == self.PRIVATE_MEMORY_BASE:
            if loader_data is not None and isinstance(loader_data, int):
                return address - self.PRIVATE_MEMORY_BASE + loader_data
            return address
        if address & self.PRIVATE_CODE_BASE == self.PRIVATE_CODE_BASE:
            if loader_code is not None and isinstance(loader_code, int):
                return address - self.PRIVATE_CODE_BASE + loader_code
            return address
        return address

    def load_elf_sections(self, elf_path, loader_data: Union[str, int], loader_code: Union[str, int]):
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
            elf_file_io = self.context.server_ifc.get_binary(elf_path)
            elf_file = ELFFile(elf_file_io)
            address: int
            loader_data_address: int = loader_data if isinstance(loader_data, int) else None
            loader_code_address: int = loader_code if isinstance(loader_code, int) else None

            # Try to find address mapping for loader_data and loader_code
            for section in elf_file.iter_sections():
                if section.data() and hasattr(section.header, "sh_addr"):
                    name = section.name
                    address = section.header.sh_addr
                    if name == loader_data:
                        loader_data_address = address
                    elif name == loader_code:
                        loader_code_address = address

            # Load section into memory
            for section in elf_file.iter_sections():
                if section.data() and hasattr(section.header, "sh_addr"):
                    name = section.name
                    if name in self.SECTIONS_TO_LOAD:
                        address = section.header.sh_addr
                        if address % 4 != 0:
                            raise ValueError(f"Section address 0x{address:08x} is not 32-bit aligned")

                        address = self.remap_address(address, loader_data_address, loader_code_address)
                        data = section.data()

                        if name == ".init":
                            init_section_address = address

                        util.VERBOSE(f"Writing section {name} to address 0x{address:08x}. Size: {len(data)} bytes")
                        self.write_block(address, data)

            # Check that what we have written is correct
            for section in elf_file.iter_sections():
                if section.data() and hasattr(section.header, "sh_addr"):
                    name = section.name
                    if name in self.SECTIONS_TO_LOAD:
                        address = section.header.sh_addr
                        data = section.data()
                        address = self.remap_address(address, loader_data_address, loader_code_address)
                        read_data = self.read_block(address, len(data))
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

        self.context.elf_loaded(self.risc_debug.location.loc, self.risc_debug.location.risc_id, elf_path)
        return init_section_address

    def load_elf(self, elf_path: str):
        # Risc must be in reset
        assert self.risc_debug.is_in_reset(), f"RISC at location {self.risc_debug.location} is not in reset."

        # Load elf file to the L1 memory; avoid writing to private sections
        init_section_address = self.load_elf_sections(elf_path, loader_data=".loader_init", loader_code=".loader_code")
        assert init_section_address is not None, "No .init section found in the ELF file"

        # Change core start address to the start of the .init section
        # if it is BRISC, we should just add jump to start address instead, since we cannot change start address
        risc_id = self.risc_debug.location.risc_id
        risc_name = get_risc_name(risc_id)
        if risc_name == "BRISC":
            if init_section_address != 0:
                jump_instruction = RiscLoader.get_jump_to_offset_instruction(init_section_address)
                write_words_to_device(
                    self.risc_debug.location.loc,
                    0,
                    jump_instruction,
                    self.risc_debug.location.loc._device.id(),
                    self.context,
                )
        else:
            # Change core start address
            self.set_risc_start_address(init_section_address)

    def run_elf(self, elf_path: str):
        # Make sure risc is in reset
        if not self.risc_debug.is_in_reset():
            self.risc_debug.set_reset_signal(1)

        self.load_elf(elf_path)

        # Take risc out of reset
        self.risc_debug.set_reset_signal(0)
        assert not self.risc_debug.is_in_reset(), f"RISC at location {self.risc_debug.location} is still in reset."
        assert (
            not self.risc_debug.is_halted() or self.risc_debug.read_status().is_ebreak_hit
        ), f"RISC at location {self.risc_debug.location} is still halted, but not because of ebreak."

    def _read_elfs(self, elf_paths: List[str], offsets: List[int | None]) -> List[dict]:
        if not isinstance(elf_paths, list):
            elf_paths = [elf_paths]
        offsets = [None] * len(elf_paths) if offsets is None else offsets

        elfs = []
        for elf_path, offset in zip(elf_paths, offsets):
            offset = None if offset == 0 else offset
            elfs.append(read_elf(self.context.server_ifc, elf_path, offset))

        return elfs

    def _find_elf_and_frame_description(self, elfs: List[dict], pc: int):
        for elf in elfs:
            frame_description = elf["frame-info"].get_frame_description(pc, self.risc_debug)
            # If we get frame description from elf we return that elf and frame description
            if frame_description is not None:
                return elf, frame_description

        return None, None

    def get_callstack(
        self, elf_paths: List[str], offsets: List[int | None] = None, limit: int = 100, stop_on_main: bool = True
    ):
        callstack = []
        with self.risc_debug.ensure_halted():

            # Reading the elf files for given paths and offsets
            elfs = self._read_elfs(elf_paths, offsets)

            # Reading the program counter from risc register
            pc = self.risc_debug.read_gpr(32)

            # Choose the elf which is referenced by the program counter
            elf, frame_description = self._find_elf_and_frame_description(elfs, pc)

            # If we do not get frame description from any elf, we cannot proceed
            if frame_description is None:
                util.WARN("We don't have information on frame and we don't know how to proceed.")
                return []

            frame_pointer = frame_description.read_previous_cfa()
            i = 0
            while i < limit:
                file_line = elf["dwarf"].find_file_line_by_address(pc)
                function_die = elf["dwarf"].find_function_by_address(pc)

                # Skipping lexical blocks since we do not print them
                if function_die is not None and (
                    function_die.category == "inlined_function" or function_die.category == "lexical_block"
                ):
                    # Returning inlined functions (virtual frames)

                    # Skipping lexical blocks since we do not print them
                    while function_die.category == "lexical_block":
                        function_die = function_die.parent    

                    origin_dwarf_die = function_die.dwarf_die.get_DIE_from_attribute("DW_AT_abstract_origin")
                    origin_die = function_die.cu.dwarf.get_die(origin_dwarf_die)

                    callstack.append(
                        CallstackEntry(pc, origin_die.path, file_line[0], file_line[1], file_line[2], frame_pointer)
                    )
                    file_line = function_die.call_file_info
                    while function_die.category == "inlined_function":
                        i = i + 1
                        function_die = function_die.parent
                        # Skipping lexical blocks since we do not print them
                        while function_die.category == "lexical_block":
                            function_die = function_die.parent

                        origin_dwarf_die = function_die.dwarf_die.get_DIE_from_attribute("DW_AT_abstract_origin")
                        origin_die = function_die.cu.dwarf.get_die(origin_dwarf_die)

                        callstack.append(
                            CallstackEntry(
                                None, origin_die.path, file_line[0], file_line[1], file_line[2], frame_pointer
                            )
                        )
                        file_line = function_die.call_file_info
                elif function_die is not None and function_die.category == "subprogram":
                    callstack.append(
                        CallstackEntry(pc, function_die.path, file_line[0], file_line[1], file_line[2], frame_pointer)
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

                # If we do not get frame description from any elf, we cannot proceed
                if frame_description is None:
                    util.WARN("We don't have information on frame and we don't know how to proceed")
                    break

                # Prepare for next iteration
                cfa = frame_pointer
                return_address = frame_description.read_register(1, cfa)
                frame_pointer = frame_description.read_previous_cfa(cfa)
                pc = return_address
                i = i + 1

                frame_description = elf["frame-info"].get_frame_description(pc, self.risc_debug)
                # If we do not get frame description from current elf check in others
                if frame_description is None:
                    new_elf, frame_description = self._find_elf_and_frame_description(elfs, pc)
                    if frame_description is not None:
                        elf = new_elf

        return callstack


CallstackEntry = namedtuple("CallstackEntry", ["pc", "function_name", "file", "line", "column", "cfa"])
