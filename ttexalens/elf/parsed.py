# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cached_property

from ttexalens._native_ttexalens import (
    NativeDwarfDie as DwarfDie,
    NativeDwarfInfo as DwarfInfo,
    NativeElfFile as ElfFile,
    NativeElfSection,
    NativeElfVariable as ElfVariable,
    NativeFrameDescription as FrameDescription,
)
from ttexalens.memory_access import MemoryAccess
from ttexalens.server import FileAccessApi


class ParsedElfFile:
    def __init__(self, native_elf: ElfFile, elf_file_path: str, load_address: int | None = None):
        self._native_elf = native_elf
        self.elf_file_path = elf_file_path
        self.loaded_offset = (self.code_load_address - load_address) if load_address is not None else 0
        # TODO: If we need thread safety, we need to add locks inside native code.

    @cached_property
    def _dwarf(self) -> DwarfInfo:
        return self._native_elf.dwarf_info

    @cached_property
    def code_load_address(self) -> int:
        # TODO: Figure out how GDB knows the load address
        text_sh = self._native_elf.get_section_by_name(".text")
        if text_sh is None:
            text_sh = self._native_elf.get_section_by_name(".firmware_text")
        if text_sh is None:
            raise ValueError(f"Could not locate text section in {self.elf_file_path}.")
        return text_sh.address

    @cached_property
    def sections(self) -> dict[str, NativeElfSection]:
        count = self._native_elf.get_sections_count()
        result: dict[str, NativeElfSection] = {}
        for i in range(count):
            section = self._native_elf.get_section(i)
            if section is not None:
                result[section.name] = section
        return result

    def get_section_by_name(self, name: str):
        return self._native_elf.get_section_by_name(name)

    def find_symbol_by_name(self, name: str):
        return self._dwarf.find_symbol_by_name(name)

    def get_frame_description(self, pc: int, memory_access: MemoryAccess) -> FrameDescription | None:
        pc = pc + self.loaded_offset
        return self._dwarf.get_frame_description(pc, memory_access)

    def find_die_by_name(self, name: str) -> DwarfDie | None:
        return self._dwarf.get_die_by_name(name)

    def get_enum_value(self, name: str) -> int | None:
        return self._dwarf.get_enum_value(name)

    def get_global(self, name: str, mem_access: MemoryAccess) -> ElfVariable:
        """
        Given a global variable name, return an ElfVariable object that can be used to access it
        """
        return self._dwarf.get_global(name, mem_access)

    def read_global(self, name: str, mem_access: MemoryAccess) -> ElfVariable:
        """
        Given a global variable name, return an ElfVariable object that has been read
        """
        return self._dwarf.read_global(name, mem_access)

    def get_constant(self, name: str):
        return self._dwarf.get_constant(name)


def read_elf(
    file_ifc: FileAccessApi, elf_file_path: str, load_address: int | None = None, require_debug_symbols: bool = True
) -> ParsedElfFile:
    """
    Reads the ELF file and returns a dictionary with the DWARF info
    """
    # This is redirected to read from tmp folder in case of remote runs.
    with file_ifc.get_binary(elf_file_path) as f:
        data = f.read()
        native_elf = ElfFile.from_bytes(data)
        if require_debug_symbols and not native_elf.has_dwarf_info():
            raise ValueError(f"{elf_file_path} does not have DWARF info. Source file must be compiled with -g")
        return ParsedElfFile(native_elf, elf_file_path, load_address)
