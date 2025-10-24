# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from dataclasses import dataclass
import struct
from elftools.dwarf.dwarfinfo import DWARFInfo
from elftools.elf.elffile import ELFFile
from elftools.elf.sections import SymbolTableSection
from functools import cached_property
import os
from ttexalens import Verbosity
import ttexalens.util as util
from ttexalens.elf.dwarf import ElfDwarf, ElfDwarfWithOffset
from ttexalens.elf.frame import FrameInfoProvider, FrameInfoProviderWithOffset
from ttexalens.elf.variable import ElfVariable
from typing import TYPE_CHECKING, Callable

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
    if Verbosity.supports(Verbosity.DEBUG):
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
    for section in elf_file.iter_sections():
        # Check if it's a symbol table section
        if section.name == ".symtab":
            # Iterate through symbols
            assert isinstance(section, SymbolTableSection)
            for symbol in section.iter_symbols():
                # Check if it's a label symbol
                if symbol["st_info"]["type"] == "STT_NOTYPE" and symbol.name:
                    symbols[symbol.name] = ElfDwarfSymbol(value=symbol["st_value"], size=symbol["st_size"])
                elif symbol["st_info"]["type"] == "STT_FUNC":
                    symbols[symbol.name] = ElfDwarfSymbol(value=symbol["st_value"], size=symbol["st_size"])
                elif symbol["st_info"]["type"] == "STT_OBJECT":
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


class ParsedElfFile:
    def __init__(self, elf: ELFFile, elf_file_path: str):
        self.elf = elf
        self.elf_file_path = elf_file_path

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
        return text_sh["sh_addr"]

    @cached_property
    def symbols(self):
        return decode_symbols(self.elf)

    @cached_property
    def file_line(self):
        return decode_file_line(self._dwarf.dwarf)

    @cached_property
    def frame_info(self) -> FrameInfoProvider:
        return FrameInfoProvider(self._dwarf.dwarf)

    def get_global(self, name: str, mem_access_function: Callable[[int, int, int], list[int]]) -> ElfVariable:
        """
        Given a global variable name, return an ElfVariable object that can be used to access it
        """
        die = self.variables.get(name)
        if die is None:
            raise Exception(f"ERROR: Cannot find global variable {name} in ELF DWARF info")
        address = die.address
        if address is None:
            raise Exception(f"ERROR: Cannot find address of global variable {name} in ELF DWARF info")
        if die.value is not None and die.resolved_type.tag_is("pointer_type"):
            return ElfVariable(die.resolved_type.dereference_type, address, mem_access_function)
        return ElfVariable(die.resolved_type, address, mem_access_function)

    def read_global(self, name: str, mem_access_function: Callable[[int, int, int], list[int]]) -> ElfVariable:
        """
        Given a global variable name, return an ElfVariable object that has been read
        """
        return self.get_global(name, mem_access_function).read()

    def get_constant(self, name: str):
        die = self.variables.get(name)
        if die is None:
            raise Exception(f"ERROR: Cannot find constant variable {name} in ELF DWARF info")
        if die.value is None:
            raise Exception(f"ERROR: Cannot find variable {name} is not constant in ELF DWARF info")
        type_die = die.resolved_type
        value = die.value
        if not type_die.tag_is("base_type"):
            raise Exception(f"ERROR: Constant {name} is not a base type")

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


def read_elf(file_ifc, elf_file_path: str, load_address: int | None = None) -> ParsedElfFile:
    """
    Reads the ELF file and returns a dictionary with the DWARF info
    """
    # This is redirected to read from tmp folder in case of remote runs.
    f = file_ifc.get_binary(elf_file_path)
    elf = ELFFile(f)

    if not elf.has_dwarf_info():
        raise ValueError(f"{elf_file_path} does not have DWARF info. Source file must be compiled with -g")
    parsed_elf = ParsedElfFile(elf, elf_file_path)
    if load_address is None:
        return parsed_elf
    return ParsedElfFileWithOffset(parsed_elf, load_address)
