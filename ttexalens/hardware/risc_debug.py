# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator
from ttexalens import util
from ttexalens.parse_elf import ParsedElfFile, ParsedElfFileWithOffset


@dataclass
class CallstackEntry:
    pc: int | None = None
    function_name: str | None = None
    file: str | None = None
    line: int | None = None
    column: int | None = None
    cfa: int | None = None


class RiscDebug:
    """
    Abstract base class for RISC debug interface.
    This class defines the interface for interacting with a RISC core for debugging purposes.
    """

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
    def write_memory(self, address: int, value: int) -> None:
        """
        Read a memory address.
        Args:
            address (int): Memory address to read.
        Returns:
            int: Value at the memory address.
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
    def _find_elf_and_frame_description(elfs: list[ParsedElfFile], pc: int, risc_debug: "RiscDebug" | None):
        for elf in elfs:
            frame_description = elf.frame_info.get_frame_description(pc, risc_debug)
            # If we get frame description from elf we return that elf and frame description
            if frame_description is not None:
                return elf, frame_description

        return None, None

    @staticmethod
    def get_frame_callstack(
        elf: ParsedElfFile, pc: int, frame_pointer: int | None = None, callstack: list["CallstackEntry"] | None = None
    ):
        file_line = elf._dwarf.find_file_line_by_address(pc)
        function_die = elf._dwarf.find_function_by_address(pc)
        file = file_line[0] if file_line is not None else None
        line = file_line[1] if file_line is not None else None
        column = file_line[2] if file_line is not None else None
        callstack = callstack if callstack is not None else []

        # Skipping lexical blocks since we do not print them
        if function_die is not None and (
            function_die.category == "inlined_function" or function_die.category == "lexical_block"
        ):
            # Returning inlined functions (virtual frames)

            # Skipping lexical blocks since we do not print them
            while function_die.category == "lexical_block" and function_die.parent is not None:
                function_die = function_die.parent

            callstack.append(CallstackEntry(pc, function_die.name, file, line, column, frame_pointer))
            file, line, column = function_die.call_file_info
            while function_die.category == "inlined_function":
                assert function_die.parent is not None
                function_die = function_die.parent
                # Skipping lexical blocks since we do not print them
                while function_die.category == "lexical_block" and function_die.parent is not None:
                    function_die = function_die.parent

                callstack.append(CallstackEntry(None, function_die.name, file, line, column, frame_pointer))
                file, line, column = function_die.call_file_info
        elif function_die is not None and function_die.category == "subprogram":
            callstack.append(CallstackEntry(pc, function_die.path, file, line, column, frame_pointer))
        else:
            callstack.append(CallstackEntry(pc, None, file, line, column, frame_pointer))
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

            # Choose the elf which is referenced by the program counter
            elf, frame_description = RiscDebug._find_elf_and_frame_description(elfs, pc, self)

            # If we do not get frame description from any elf, we cannot proceed
            if frame_description is None or elf is None:
                util.WARN("We don't have information on frame and we don't know how to proceed.")
                return []

            frame_pointer = frame_description.read_previous_cfa()
            while len(callstack) < limit:
                callstack, function_die = RiscDebug.get_frame_callstack(elf, pc, frame_pointer, callstack)

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

                frame_description = elf.frame_info.get_frame_description(pc, self)
                # If we do not get frame description from current elf check in others
                if frame_description is None:
                    new_elf, frame_description = RiscDebug._find_elf_and_frame_description(elfs, pc, self)
                    if frame_description is not None and new_elf is not None:
                        elf = new_elf

        return callstack
