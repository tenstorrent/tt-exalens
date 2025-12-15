# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator
from ttexalens import util
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.elf import ParsedElfFile, ParsedElfFileWithOffset, ElfVariable, ElfDie, FrameInspection


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


@dataclass
class CallstackEntryVariable:
    die: ElfDie
    value: ElfVariable | None

    @property
    def name(self):
        return self.die.name

    @property
    def type(self):
        return self.die.resolved_type

    @property
    def declared_at(self):
        return self.die.decl_file_info


@dataclass
class CallstackEntry:
    pc: int | None = None
    function_name: str | None = None
    file: str | None = None
    line: int | None = None
    column: int | None = None
    cfa: int | None = None
    arguments: list[CallstackEntryVariable] = field(default_factory=list)
    locals: list[CallstackEntryVariable] = field(default_factory=list)


class RiscDebug:
    """
    Abstract base class for RISC debug interface.
    This class defines the interface for interacting with a RISC core for debugging purposes.
    """

    def __init__(self, risc_location: RiscLocation):
        self.risc_location = risc_location

    @staticmethod
    def get_instance(risc_location: RiscLocation) -> "RiscDebug":
        noc_block = risc_location.location._device.get_block(risc_location.location)
        return noc_block.get_risc_debug(risc_location.risc_name, risc_location.neo_id)

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

    @abstractmethod
    def read_memory(self, address: int) -> int:
        """
        Read a memory address.
        Args:
            address (int): Memory address to read.
        Returns:
            int: Value at the memory address.
        """
        pass

    @abstractmethod
    def read_memory_bytes(self, address: int, size_bytes: int) -> bytes:
        """
        Read size_bytes bytes from a memory address.
        Args:
            address (int): Memory address to read.
            size_bytes (int): Number of bytes to read.
        Returns:
            bytes: Size_bytes bytes at the memory address.
        """
        pass

    @abstractmethod
    def write_memory(self, address: int, data: int) -> None:
        """
        Write data to a memory address.
        Args:
            address (int): Memory address to write.
            data (int): Data to write to the memory address.
        """
        pass

    @abstractmethod
    def write_memory_bytes(self, address: int, data: bytes) -> None:
        """
        Write size_bytes bytes to a memory address.
        Args:
            address (int): Memory address to write.
            data (bytes): Bytes to write to the memory address.
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

    @staticmethod
    def _read_elfs(
        parsed_elfs: list[ParsedElfFile] | ParsedElfFile, offsets: list[int | None] | None
    ) -> list[ParsedElfFile]:
        if not isinstance(parsed_elfs, list):
            parsed_elfs = [parsed_elfs]
        if offsets is None:
            offsets = [None for _ in range(len(parsed_elfs))]

        elfs: list[ParsedElfFile] = []
        for parsed_elf, offset in zip(parsed_elfs, offsets):
            offset = None if offset == 0 else offset
            if offset is not None:
                elfs.append(ParsedElfFileWithOffset(parsed_elf, offset))
            else:
                elfs.append(parsed_elf)
        return elfs

    @staticmethod
    def _find_elf_and_frame_description(elfs: list[ParsedElfFile], pc: int, risc_debug: "RiscDebug | None"):
        for elf in elfs:
            frame_description = elf.frame_info.get_frame_description(pc, risc_debug)
            # If we get frame description from elf we return that elf and frame description
            if frame_description is not None:
                return elf, frame_description

        return None, None

    @staticmethod
    def get_frame_callstack(
        elf: ParsedElfFile,
        pc: int,
        frame_pointer: int | None = None,
        callstack: list[CallstackEntry] | None = None,
        top_frame: bool = True,
        frame_inspection: FrameInspection | None = None,
    ) -> tuple[list[CallstackEntry], ElfDie | None]:
        # If we are at the top frame, pc is correct.
        # If we are not at the top frame, pc points to the instruction after the call instruction.
        # We need to adjust pc by -4 to get the correct call instruction address.
        adjusted_pc = pc if top_frame else pc - 4
        file_line = elf._dwarf.find_file_line_by_address(adjusted_pc)
        function_die = elf._dwarf.find_function_by_address(adjusted_pc)
        file = file_line[0] if file_line is not None else None
        line = file_line[1] if file_line is not None else None
        column = file_line[2] if file_line is not None else None
        callstack = callstack if callstack is not None else []
        arguments: list[CallstackEntryVariable] = []
        locals: list[CallstackEntryVariable] = []

        if frame_inspection is not None:
            frame_inspection.pc = adjusted_pc

        def extract_variables(
            function_die: ElfDie, arguments: list[CallstackEntryVariable], locals: list[CallstackEntryVariable]
        ):
            for child in function_die.iter_children():
                if child.tag_is("formal_parameter"):
                    arguments.append(CallstackEntryVariable(child, child.read_value(frame_inspection)))
                elif child.tag_is("variable"):
                    locals.append(CallstackEntryVariable(child, child.read_value(frame_inspection)))

        # Skipping lexical blocks since we do not print them
        if function_die is not None and (
            function_die.category == "inlined_function" or function_die.category == "lexical_block"
        ):
            # Returning inlined functions (virtual frames)

            # Skipping lexical blocks since we do not print them
            while function_die.category == "lexical_block" and function_die.parent is not None:
                extract_variables(function_die, arguments, locals)
                function_die = function_die.parent

            extract_variables(function_die, arguments, locals)
            callstack.append(
                CallstackEntry(pc, function_die.name, file, line, column, frame_pointer, arguments, locals)
            )
            arguments = []
            locals = []
            file, line, column = function_die.call_file_info
            while function_die.category == "inlined_function":
                assert function_die.parent is not None
                function_die = function_die.parent
                # Skipping lexical blocks since we do not print them
                while function_die.category == "lexical_block" and function_die.parent is not None:
                    extract_variables(function_die, arguments, locals)
                    function_die = function_die.parent

                extract_variables(function_die, arguments, locals)
                callstack.append(
                    CallstackEntry(None, function_die.name, file, line, column, frame_pointer, arguments, locals)
                )
                arguments = []
                locals = []
                file, line, column = function_die.call_file_info
        elif function_die is not None and function_die.category == "subprogram":
            extract_variables(function_die, arguments, locals)
            callstack.append(
                CallstackEntry(pc, function_die.path, file, line, column, frame_pointer, arguments, locals)
            )
        else:
            callstack.append(CallstackEntry(pc, None, file, line, column, frame_pointer, arguments, locals))
        return callstack, function_die

    def get_callstack(
        self,
        parsed_elfs: list[ParsedElfFile],
        offsets: list[int | None] | None = None,
        limit: int = 100,
        stop_on_main: bool = True,
    ) -> list[CallstackEntry]:
        callstack: list[CallstackEntry] = []
        with self.ensure_halted():

            # Load elfs at specified offsets
            elfs = RiscDebug._read_elfs(parsed_elfs, offsets)

            # Reading the program counter from risc register
            pc = self.read_gpr(32)

            # If ebreak was hit, pc will point to the instruction after it
            if self.is_ebreak_hit():
                # Rewind pc to unwind callstack from the ebreak instruction
                pc -= 4

            # Choose the elf which is referenced by the program counter
            elf, frame_description = RiscDebug._find_elf_and_frame_description(elfs, pc, self)

            # If we do not get frame description from any elf, we cannot proceed
            if frame_description is None or elf is None:
                util.WARN("We don't have information on frame and we don't know how to proceed.")
                return []

            frame_inspection = FrameInspection(self, elf.loaded_offset)
            frame_pointer = frame_description.read_previous_cfa()
            while len(callstack) < limit:
                callstack, function_die = RiscDebug.get_frame_callstack(
                    elf, pc, frame_pointer, callstack, top_frame=len(callstack) == 0, frame_inspection=frame_inspection
                )

                # We want to stop when we print main as frame descriptor might not be correct afterwards
                if stop_on_main and function_die is not None and function_die.name == "main":
                    break

                # We want to stop when we are at the end of frames list
                if frame_pointer == 0 or frame_pointer is None:
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
                frame_inspection = FrameInspection(self, elf.loaded_offset, frame_description, cfa)
                frame_description = elf.frame_info.get_frame_description(pc, self)

                # If we do not get frame description from current elf check in others
                if frame_description is None:
                    new_elf, frame_description = RiscDebug._find_elf_and_frame_description(elfs, pc, self)
                    if frame_description is not None and new_elf is not None:
                        elf = new_elf

        return callstack
