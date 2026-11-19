# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Device-free fixtures for ELF/DWARF reader tests.

`compile_elf` builds a small C++ or assembly source with the RISC-V toolchain that `make`
downloads into build/riscv-src/sfpi, so a test can pin down exactly which DWARF construct it
exercises. `ElfImageMemoryAccess` serves the loaded sections of that ELF as memory, so
variables can be read and written without a device.
"""
import hashlib
import os
import subprocess
import tempfile
import unittest

from ttexalens.elf import ElfFile
from ttexalens.memory_access import MemoryAccess

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_TOOLCHAIN_BIN = os.path.join(_REPO_ROOT, "build", "riscv-src", "sfpi", "compiler", "bin")
_GXX = os.path.join(_TOOLCHAIN_BIN, "riscv-tt-elf-g++")

# Flags shared by every fixture: a bare-metal rv32 executable with main as its entry point.
_BASE_FLAGS = ["-mabi=ilp32", "-std=c++17", "-fno-exceptions", "-fno-rtti", "-nostartfiles", "-Wl,-e,main"]

_output_dir: str | None = None


def compile_elf(source: str, flags: list[str] | None = None, suffix: str = ".cc") -> str:
    """Compiles and links `source` and returns the path of the ELF. Identical requests reuse one build.

    Args:
        source (str): C++ source, or assembly when `suffix` is ".S".
        flags (list[str] | None): Extra compiler flags, for example ["-O2", "-g"].
        suffix (str): Source file extension, which selects the language.

    Returns:
        str: Path of the linked ELF.
    """
    global _output_dir
    if not os.path.isfile(_GXX):
        raise unittest.SkipTest(f"RISC-V toolchain not found at {_GXX}; run make first")
    if _output_dir is None:
        _output_dir = tempfile.mkdtemp(prefix="ttexalens-elf-fixture-")
    flags = list(flags) if flags is not None else ["-O2", "-g"]
    key = hashlib.sha256((source + "\0" + suffix + "\0" + "\0".join(flags)).encode()).hexdigest()[:16]
    elf_path = os.path.join(_output_dir, f"{key}.elf")
    if not os.path.isfile(elf_path):
        source_path = os.path.join(_output_dir, f"{key}{suffix}")
        with open(source_path, "w") as f:
            f.write(source)
        subprocess.run([_GXX, *_BASE_FLAGS, *flags, source_path, "-o", elf_path], check=True, capture_output=True)
    return elf_path


class ElfImageMemoryAccess(MemoryAccess):
    """Memory holding the loaded sections of an ELF (.bss reads as zeros) and a register file set by the test."""

    def __init__(self, elf: ElfFile, registers: dict[int, int] | None = None):
        super().__init__()
        self.memory: dict[int, int] = {}
        self.registers: dict[int, int] = dict(registers or {})
        for index in range(elf.get_sections_count()):
            section = elf.get_section(index)
            if section is None or not section.address:
                continue
            data = section.data
            content = bytes(data) if len(data) == section.size else bytes(section.size)
            for offset, byte in enumerate(content):
                self.memory[section.address + offset] = byte

    def read(self, address: int, buffer: memoryview | bytearray) -> None:
        for i in range(len(buffer)):
            buffer[i] = self.memory.get(address + i, 0)

    def write(self, address: int, data: bytes | bytearray | memoryview) -> None:
        for i, byte in enumerate(bytes(data)):
            self.memory[address + i] = byte

    def read_register(self, register_index: int) -> int:
        return self.registers[register_index]

    def write_register(self, register_index: int, value: int) -> None:
        self.registers[register_index] = value

    def write_word(self, address: int, value: int) -> None:
        self.write(address, value.to_bytes(4, "little"))
