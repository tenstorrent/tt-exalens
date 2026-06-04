# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Generator
from ttexalens import util
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.elf import (
    DwarfDieTag,
    DwarfDie,
    DwarfFileLine,
    ElfFile,
    ElfVariable,
    FrameDescription,
    FrameInspection,
    FrameSnapshot,
)
from ttexalens.hardware.risc_info import RiscInfo
from ttexalens.memory_access import MemoryAccess, create_memory_access


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
    die: DwarfDie
    value: ElfVariable | None

    @cached_property
    def name(self):
        return self.die.name

    @cached_property
    def type(self):
        return self.die.get_resolved_type()

    @cached_property
    def declared_at(self):
        return self.die.get_decl_file_info()


@dataclass
class CallstackEntry:
    pc: int | None = None
    function_name: str | None = None
    file_info: DwarfFileLine | None = None
    cfa: int | None = None
    arguments: list[CallstackEntryVariable] = field(default_factory=list)
    locals: list[CallstackEntryVariable] = field(default_factory=list)
    template_parameters: list[CallstackEntryVariable] = field(default_factory=list)


class ExtendedFrameSnapshot(FrameSnapshot):
    """Snapshot of one frame on the callstack at the PC where execution was
    when we walked through it. Extends the native snapshot (which carries
    `pc`, `fde`, `cfa` — everything `FrameInspection` consumes) with one
    Python-only field, `reported_pc`: the PC value `CallstackEntry.pc`
    exposes to callers. For the live frame this is the live PC; for outer
    frames it is the return address (what GDB's backtrace prints), so our
    callstack lines up with GDB output for tests and tooling. The native
    `pc` itself is the call-instruction PC (return address minus one JAL),
    which is what DWARF lookups need.
    """

    def __init__(self, *, pc: int, fde: FrameDescription, cfa: int, reported_pc: int):
        super().__init__(fde=fde, cfa=cfa, pc=pc)
        self.reported_pc = reported_pc


class RiscDebug:
    """
    Abstract base class for RISC debug interface.
    This class defines the interface for interacting with a RISC core for debugging purposes.
    """

    def __init__(self, risc_location: RiscLocation, risc_info: RiscInfo):
        self.risc_location = risc_location
        self.risc_info = risc_info

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
    def read_memory(self, address: int, safe_mode: bool | None = None) -> int:
        """
        Read a memory address.
        Args:
            address (int): Memory address to read.
            safe_mode (bool | None): If True, apply additional safety checks to prevent access to known unsafe memory regions.
        Returns:
            int: Value at the memory address.
        """
        pass

    @abstractmethod
    def read_memory_bytes(self, address: int, buffer: bytearray | memoryview, safe_mode: bool | None = None) -> None:
        """
        Read len(buffer) bytes from a memory address into 'buffer'.
        Args:
            address (int): Memory address to read.
            buffer (bytearray | memoryview): Destination buffer; exactly len(buffer) bytes are read into it.
            safe_mode (bool | None): If True, apply additional safety checks to prevent access to known unsafe memory regions.
        """
        pass

    @abstractmethod
    def write_memory(self, address: int, data: int, safe_mode: bool | None = None) -> None:
        """
        Write data to a memory address.
        Args:
            address (int): Memory address to write.
            data (int): Data to write to the memory address.
            safe_mode (bool | None): If True, apply additional safety checks to prevent access to known unsafe memory regions.
        """
        pass

    @abstractmethod
    def write_memory_bytes(
        self, address: int, data: bytes | bytearray | memoryview, safe_mode: bool | None = None
    ) -> None:
        """
        Write len(data) bytes to a memory address.
        Args:
            address (int): Memory address to write.
            data (bytes | bytearray | memoryview): Bytes to write to the memory address.
            safe_mode (bool | None): If True, apply additional safety checks to prevent access to known unsafe memory regions.
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
    def _read_elfs(parsed_elfs: list[ElfFile] | ElfFile, offsets: list[int | None] | None) -> list[ElfFile]:
        if not isinstance(parsed_elfs, list):
            parsed_elfs = [parsed_elfs]
        if offsets is None:
            offsets = [None for _ in range(len(parsed_elfs))]

        elfs: list[ElfFile] = []
        for parsed_elf, offset in zip(parsed_elfs, offsets):
            offset = None if offset == 0 else offset
            if offset is not None:
                elfs.append(parsed_elf.with_load_address(offset))
            else:
                elfs.append(parsed_elf)
        return elfs

    @staticmethod
    def _find_elf_and_frame_description(elfs: list[ElfFile], pc: int, mem_access: MemoryAccess):
        for elf in elfs:
            frame_description = elf.get_frame_description(pc, mem_access)
            # If we get frame description from elf we return that elf and frame description
            if frame_description is not None:
                return elf, frame_description

        return None, None

    @staticmethod
    def _get_elf_and_frame_snapshot(
        elf: ElfFile | None,
        elfs: list[ElfFile],
        pc: int,
        reported_pc: int,
        mem_access: MemoryAccess,
        inner_cfa: int | None = None,
    ) -> tuple[ExtendedFrameSnapshot | None, ElfFile | None]:
        fde = elf.get_frame_description(pc, mem_access) if elf is not None else None
        if fde is None:
            new_elf, fde = RiscDebug._find_elf_and_frame_description(elfs, pc, mem_access)
            if fde is not None and new_elf is not None:
                elf = new_elf
        if fde is None:
            util.WARN("We don't have information on frame and we don't know how to proceed")
            return None, None
        cfa = fde.compute_cfa(inner_cfa)
        if cfa is None:
            return None, None
        return ExtendedFrameSnapshot(pc=pc, fde=fde, cfa=cfa, reported_pc=reported_pc), elf

    @staticmethod
    def get_frame_callstack(
        elf: ElfFile,
        frame: ExtendedFrameSnapshot,
        callstack: list[CallstackEntry] | None = None,
        mem_access: MemoryAccess | None = None,
        inner_frames: list[ExtendedFrameSnapshot] | None = None,
    ) -> tuple[list[CallstackEntry], DwarfDie | None]:
        dwarf_pc = frame.pc + elf.loaded_offset
        dwarf = elf.dwarf_info
        assert dwarf is not None, "ELF has no DWARF info; cannot inspect callstack"
        file_info = dwarf.find_file_line_by_address(dwarf_pc)
        function_die = dwarf.find_function_by_address(dwarf_pc)
        callstack = callstack if callstack is not None else []
        arguments: list[CallstackEntryVariable] = []
        locals: list[CallstackEntryVariable] = []
        template_parameters: list[CallstackEntryVariable] = []

        frame_inspection: FrameInspection | None = None
        if mem_access is not None:
            # Empty inner_frames means this IS the top frame; the chain
            # walker's reverse loop then runs zero iterations and falls
            # through to a live register read. No special case needed.
            frame_inspection = FrameInspection(
                mem_access,
                FrameSnapshot(fde=frame.fde, cfa=frame.cfa, pc=dwarf_pc),
                inner_frames or [],
            )

        def extract_variables(
            function_die: DwarfDie,
            arguments: list[CallstackEntryVariable],
            locals: list[CallstackEntryVariable],
            template_parameters: list[CallstackEntryVariable],
        ):
            for child in function_die.iter_children():
                value = child.read_value(frame_inspection) if frame_inspection is not None else None
                if child.tag == DwarfDieTag.formal_parameter:
                    arguments.append(CallstackEntryVariable(child, value))
                elif child.tag == DwarfDieTag.variable:
                    locals.append(CallstackEntryVariable(child, value))
            for template_value_param in function_die.get_template_value_parameters():
                value = template_value_param.read_value(frame_inspection) if frame_inspection is not None else None
                template_parameters.append(CallstackEntryVariable(template_value_param, value))

        # Skipping lexical blocks since we do not print them
        if function_die is not None and (
            function_die.tag == DwarfDieTag.inlined_subroutine or function_die.tag == DwarfDieTag.lexical_block
        ):
            # Returning inlined functions (virtual frames)

            # Skipping lexical blocks since we do not print them
            while function_die.tag == DwarfDieTag.lexical_block:
                parent = function_die.get_parent()
                if parent is None:
                    break
                extract_variables(function_die, arguments, locals, template_parameters)
                function_die = parent

            extract_variables(function_die, arguments, locals, template_parameters)
            callstack.append(
                CallstackEntry(
                    frame.reported_pc,
                    function_die.get_path(),
                    file_info,
                    frame.cfa,
                    arguments,
                    locals,
                    template_parameters,
                )
            )
            arguments = []
            locals = []
            template_parameters = []
            file_info = function_die.get_call_file_info()
            while function_die.tag == DwarfDieTag.inlined_subroutine:
                parent = function_die.get_parent()
                assert parent is not None
                function_die = parent
                # Skipping lexical blocks since we do not print them
                while function_die.tag == DwarfDieTag.lexical_block:
                    inner_parent = function_die.get_parent()
                    if inner_parent is None:
                        break
                    extract_variables(function_die, arguments, locals, template_parameters)
                    function_die = inner_parent

                extract_variables(function_die, arguments, locals, template_parameters)
                callstack.append(
                    CallstackEntry(
                        None, function_die.get_path(), file_info, frame.cfa, arguments, locals, template_parameters
                    )
                )
                arguments = []
                locals = []
                template_parameters = []
                file_info = function_die.get_call_file_info()
        elif function_die is not None and function_die.tag == DwarfDieTag.subprogram:
            extract_variables(function_die, arguments, locals, template_parameters)
            callstack.append(
                CallstackEntry(
                    frame.reported_pc,
                    function_die.get_path(),
                    file_info,
                    frame.cfa,
                    arguments,
                    locals,
                    template_parameters,
                )
            )
        else:
            callstack.append(
                CallstackEntry(frame.reported_pc, None, file_info, frame.cfa, arguments, locals, template_parameters)
            )
        return callstack, function_die

    def get_callstack(
        self,
        parsed_elfs: list[ElfFile],
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

            mem_access: MemoryAccess = create_memory_access(self)

            # Chain of frames inner to the one being inspected
            inner_frames: list[ExtendedFrameSnapshot] = []

            # Find top frame
            current_frame, elf = RiscDebug._get_elf_and_frame_snapshot(None, elfs, pc, pc, mem_access)

            while current_frame is not None and len(callstack) < limit:
                assert elf is not None
                callstack, function_die = RiscDebug.get_frame_callstack(
                    elf, current_frame, callstack, mem_access, inner_frames
                )

                # We want to stop when we print main as frame descriptor might not be correct afterwards
                if stop_on_main and function_die is not None and function_die.get_path() == "main":
                    break

                # We want to stop when we are at the end of frames list
                if current_frame.cfa == 0:
                    break

                # Step one frame outward by reading the return-address register (index 1).
                return_address = current_frame.fde.read_register(1, current_frame.cfa)
                if return_address is None:
                    break
                pc = return_address - 4  # Move back from return address to call instruction
                inner_frames.append(current_frame)
                current_frame, elf = RiscDebug._get_elf_and_frame_snapshot(
                    elf, elfs, pc, return_address, mem_access, current_frame.cfa
                )

        return callstack
