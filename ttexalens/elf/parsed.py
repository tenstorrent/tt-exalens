# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from dataclasses import dataclass
import struct
from elftools.dwarf.dwarfinfo import DWARFInfo
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from functools import cache, cached_property
import os
from ttexalens.server import FileAccessApi
import ttexalens.util as util
from ttexalens.exceptions import ElfLookupError, ElfTypeError
from ttexalens.elf.dwarf import ElfDwarf, ElfDwarfWithOffset
from ttexalens.elf.frame import FrameInfoProvider, FrameInfoProviderWithOffset
from ttexalens.elf.variable import ElfVariable
from ttexalens.memory_access import MemoryAccess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttexalens.elf.die import ElfDie


def process_die(die: ElfDie, recurse_dict, r_depth):
    """
    Processes a DIE, adds it to the recurse_dict if needed, and returns True if we
    should recurse into its children
    """

    def log(str):
        util.DEBUG(f"{'  ' * (r_depth+1)}{str}")

    category = die.category
    path = die.path

    # We add test for debug_enabled here, because we don't want string formatting to be executed without printint anything
    if util.Verbosity.supports(util.Verbosity.DEBUG):
        log(
            f"{util.CLR_BLUE}{path}{util.CLR_END} {category} {util.CLR_GREEN}{die.resolved_type.path}{util.CLR_END} {die.offset}/{hex(die.offset)} {die}"
        )

    if category:
        if category not in recurse_dict:
            recurse_dict[category] = dict()
        recurse_dict[category][path] = die

    recurse_down = category is not None
    return recurse_down


def recurse_die(DIE: ElfDie, recurse_dict, r_depth=0):
    """
    This function visits all children recursively and calls process_DIE() on each
    """
    for child in DIE.iter_children():
        recurse_down = process_die(child, recurse_dict, r_depth)
        if recurse_down:
            recurse_die(child, recurse_dict, r_depth + 1)


def recurse_dwarf(dwarf: ElfDwarf) -> dict[str, dict[str, ElfDie]]:
    """
    Itaretes recursively over all the DIEs in the DWARF info and returns a dictionary
    with the following keys:
        'variable' - all the variables (top level names)
        'type' - all the types
        'member' - all the members of structures etc
        'enumerator' - all the enumerators in the DWARF info
        'PC' - mappings between PC values and source code locations
    """
    recurse_dict: dict[str, dict[str, ElfDie]] = {
        "variable": dict(),
        "type": dict(),
        "member": dict(),
        "enumerator": dict(),
    }

    for cu in dwarf.iter_CUs():
        top_DIE = cu.top_DIE
        cu_name = "N/A"
        if "DW_AT_name" in top_DIE.attributes:
            cu_name = top_DIE.attributes["DW_AT_name"].value.decode("utf-8")
        util.DEBUG(f"CU: {cu_name}")

        # Process the names etc
        recurse_die(top_DIE, recurse_dict)

    return recurse_dict


# Class representing symbol from symbol table
@dataclass
class ElfDwarfSymbol:
    value: int | None
    size: int | None


def decode_symbols(elf_file: ELFFile) -> dict[str, ElfDwarfSymbol]:
    symbols = {}
    section = elf_file.get_section_by_name(".symtab")
    assert section is not None and isinstance(section, SymbolTableSection)
    for symbol in section.iter_symbols():
        if not symbol.name:
            continue
        type = symbol["st_info"]["type"]
        if type == "STT_NOTYPE" or type == "STT_FUNC" or type == "STT_OBJECT":
            symbols[symbol.name] = ElfDwarfSymbol(value=symbol["st_value"], size=symbol["st_size"])
    return symbols


def decode_file_line(dwarf: DWARFInfo) -> dict[int, tuple[str, int, int]]:
    PC_to_fileline_map = {}
    for CU in dwarf.iter_CUs():
        lineprog = dwarf.line_program_for_CU(CU)
        if lineprog is None:
            continue
        delta = 1 if lineprog.header.version < 5 else 0
        for entry in lineprog.get_entries():
            if entry.state is None:
                continue

            file_entry = lineprog["file_entry"][entry.state.file - delta]
            directory = lineprog["include_directory"][file_entry.dir_index].decode("utf-8")
            filename = file_entry.name.decode("utf-8")
            filename = os.path.join(directory, filename)
            line = entry.state.line
            column = entry.state.column
            PC_to_fileline_map[entry.state.address] = (filename, line, column)
    return PC_to_fileline_map


class ParsedElfFileSection:
    def __init__(self, section):
        self._section = section
        self.name = section.name
        self.address = int(section.header.sh_addr) if hasattr(section.header, "sh_addr") else None
        self.size = int(section.header.sh_size) if hasattr(section.header, "sh_size") else 0

    @cached_property
    def data(self):
        return self._section.data()


class ParsedElfFile:
    def __init__(self, elf: ELFFile, elf_file_path: str):
        self.elf = elf
        self.elf_file_path = elf_file_path
        self.loaded_offset = 0

    @cached_property
    def sections(self):
        return [ParsedElfFileSection(section) for section in self.elf.iter_sections()]

    @cached_property
    def _dwarf(self) -> ElfDwarf:
        dwarf = self.elf.get_dwarf_info(relocate_dwarf_sections=False)
        return ElfDwarf(dwarf, self)

    @cached_property
    def _recursed_dwarf(self):
        return recurse_dwarf(self._dwarf)

    @cached_property
    def variables(self):
        return self._recursed_dwarf["variable"]

    @cached_property
    def types(self):
        return self._recursed_dwarf["type"]

    @cached_property
    def members(self):
        return self._recursed_dwarf["member"]

    @cached_property
    def enumerators(self):
        return self._recursed_dwarf["enumerator"]

    @cached_property
    def subprograms(self):
        return self._recursed_dwarf["subprogram"]

    @cached_property
    def code_load_address(self) -> int:
        # TODO: Figure out how GDB knows the load address
        text_sh = self.elf.get_section_by_name(".text")
        if text_sh is None:
            text_sh = self.elf.get_section_by_name(".firmware_text")
        if text_sh is None:
            raise ValueError(f"Could not locate text section in {self.elf_file_path}.")
        return int(text_sh["sh_addr"])

    @cached_property
    def symbols(self):
        return decode_symbols(self.elf)

    @cached_property
    def file_line(self):
        return decode_file_line(self._dwarf.dwarf)

    @cached_property
    def frame_info(self) -> FrameInfoProvider:
        return FrameInfoProvider(self._dwarf.dwarf)

    @cache
    def find_die_by_name(self, name: str) -> ElfDie | None:
        names = name.split("::")
        if len(names) == 0:
            return None
        declaration_die = None
        for cu in self._dwarf.iter_CUs():
            index = 0
            die: ElfDie | None = cu.top_DIE
            while index < len(names) and die is not None:
                die = die.get_child_by_name(names[index])
                index += 1
            if die is not None:
                if "DW_AT_abstract_origin" in die.attributes:
                    die = die.get_DIE_from_attribute("DW_AT_abstract_origin")
                    if die is None:
                        return None
                elif "DW_AT_specification" in die.attributes:
                    die = die.get_DIE_from_attribute("DW_AT_specification")
                    if die is None:
                        return None
                if "DW_AT_declaration" in die.attributes and die.attributes["DW_AT_declaration"].value:
                    declaration_die = die
                    continue
                return die
        return declaration_die

    def get_enum_value(self, name: str, allow_fallback: bool = False) -> int | None:
        # Try to use fast lookup first
        die: ElfDie | None = self.find_die_by_name(name)
        if die is None or die.category != "enumerator":
            # Fallback to full lookup
            die = self.enumerators.get(name) if allow_fallback else None
        if die is not None:
            return int(die.value)
        return None

    def get_global(self, name: str, mem_access: MemoryAccess, allow_fallback: bool = False) -> ElfVariable:
        """
        Given a global variable name, return an ElfVariable object that can be used to access it
        """
        # Try to use fast lookup first
        die = self.find_die_by_name(name)
        if die is None or die.category != "variable":
            # Fallback to full lookup
            die = self.variables.get(name) if allow_fallback else None
        if die is None:
            raise ElfLookupError(f"Cannot find global variable {name} in ELF DWARF info")
        address = die.address
        if address is None:
            raise ElfLookupError(f"Cannot find address of global variable {name} in ELF DWARF info")
        if die.value is not None and die.resolved_type.tag_is("pointer_type"):
            assert die.resolved_type.dereference_type is not None
            return ElfVariable(die.resolved_type.dereference_type, address, mem_access)
        return ElfVariable(die.resolved_type, address, mem_access)

    def read_global(self, name: str, mem_access: MemoryAccess, allow_fallback: bool = False) -> ElfVariable:
        """
        Given a global variable name, return an ElfVariable object that has been read
        """
        return self.get_global(name, mem_access, allow_fallback).read()

    def get_constant(self, name: str, allow_fallback: bool = False):
        # Try to use fast lookup first
        die = self.find_die_by_name(name)
        if die is None or die.category != "variable":
            # Fallback to full lookup
            die = self.variables.get(name) if allow_fallback else None
        if die is None:
            raise ElfLookupError(f"Cannot find constant variable {name} in ELF DWARF info")
        if die.value is None:
            raise ElfTypeError(f"Variable {name} is not constant in ELF DWARF info")
        type_die = die.resolved_type
        value = die.value
        if not type_die.tag_is("base_type"):
            raise ElfTypeError(f"Constant {name} is not a base type")

        # If value is a list, convert to bytes
        if isinstance(value, list):
            value = bytes(value)

        # Convert the value to the appropriate type
        if type_die.name == "float":
            if not isinstance(value, bytes):
                value = struct.pack("I", value)
            return struct.unpack("f", value)[0]
        elif type_die.name == "double":
            if not isinstance(value, bytes):
                value = struct.pack("Q", value)
            return struct.unpack("d", value)[0]
        elif type_die.name == "bool":
            return bool(value)
        return value


class ParsedElfFileWithOffset(ParsedElfFile):
    def __init__(self, parsed_elf: ParsedElfFile, load_address: int):
        super().__init__(parsed_elf.elf, parsed_elf.elf_file_path)
        self.parsed_elf = parsed_elf
        self.load_address = load_address
        self.loaded_offset = parsed_elf.code_load_address - load_address

    @cached_property
    def _dwarf(self) -> ElfDwarf:
        return ElfDwarfWithOffset(self.parsed_elf._dwarf, self.loaded_offset)

    @cached_property
    def _recursed_dwarf(self):
        return self.parsed_elf._recursed_dwarf

    @cached_property
    def variables(self):
        return self.parsed_elf.variables

    @cached_property
    def types(self):
        return self.parsed_elf.types

    @cached_property
    def members(self):
        return self.parsed_elf.members

    @cached_property
    def enumerators(self):
        return self.parsed_elf.enumerators

    @cached_property
    def subprograms(self):
        return self.parsed_elf.subprograms

    @cached_property
    def code_load_address(self) -> int:
        return self.loaded_offset

    @cached_property
    def symbols(self):
        return self.parsed_elf.symbols

    @cached_property
    def file_line(self):
        return self.parsed_elf.file_line

    @cached_property
    def frame_info(self) -> FrameInfoProviderWithOffset:
        return FrameInfoProviderWithOffset(self.parsed_elf.frame_info, self.code_load_address)


def read_elf(
    file_ifc: FileAccessApi, elf_file_path: str, load_address: int | None = None, require_debug_symbols: bool = True
) -> ParsedElfFile:
    """
    Reads the ELF file and returns a dictionary with the DWARF info
    """
    # This is redirected to read from tmp folder in case of remote runs.
    f = file_ifc.get_binary(elf_file_path)
    elf = ELFFile(f)

    if require_debug_symbols and not elf.has_dwarf_info():
        raise ValueError(f"{elf_file_path} does not have DWARF info. Source file must be compiled with -g")
    parsed_elf = ParsedElfFile(elf, elf_file_path)
    if load_address is None:
        return parsed_elf
    return ParsedElfFileWithOffset(parsed_elf, load_address)
