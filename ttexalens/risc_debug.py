# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from abc import abstractmethod
from collections import namedtuple
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator, List, Union
from ttexalens.coordinate import OnChipCoordinate


@dataclass
class RiscLocation:
    coord: OnChipCoordinate
    risc_name: str = ""
    noc_id: int = 0


@dataclass
class CallstackEntry:
    pc: Union[int, None] = None
    function_name: Union[str, None] = None
    file: Union[str, None] = None
    line: Union[int, None] = None
    column: Union[int, None] = None
    cfa: int = 0


class RiscDebug:
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

    # TODO: Implement the following methods in BabyRiscDebug
    @abstractmethod
    def get_callstack(self, elf_path: str, limit: int = 100, stop_on_main: bool = True) -> List[CallstackEntry]:
        """
        Get the callstack from the RISC core.

        Args:
            elf_path (str): Path to the ELF file.
            limit (int): Maximum number of frames to return.
            stop_on_main (bool): If True, stop when reaching the main function.

        Returns:
            List[CallstackEntry]: List of callstack entries.
        """
        pass
