#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Description:

    This program parses an ELF file and extracts the information from the DWARF
    section. By default, it prints all the information in a table.

    If access-path is specified, it prints the memory access path to read the
    variable pointed to by the access-path. For example, if the access-path is
    "s_ptr->an_int", it prints the memory access path to read the variable
    pointed to by s_ptr->an_int. In this case, it will print two memory accesses
    (one for reading s_ptr and one for reading s_ptr->an_int).

    Access-path supports structures, pointer dereferences, references, and arrays.
    For arrays, the indices must be integers. For example, this is allowed:
    "s_global_var.my_coordinate_matrix_ptr->matrix[2][3].x".

    Dereferending a pointer with * is supported only at the top level. For example,
    this is allowed: "*s_global_var.my_member".

Usage:
  parse_elf.py <elf-file> [ <access-path> ] [ -d | --debug ]

Options:
  -d --debug             Enable debug messages

Arguments:
  elf-file               ELF file to parse
  access-path            Access path to a variable in the ELF file

Examples:
  parse_elf.py ./build/riscv-src/wormhole/sample.brisc.elf

  Options:
  -h --help      Show this screen.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import cached_property
import os
import re
import struct
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ttexalens.hardware.risc_debug import RiscDebug

try:
    from elftools.elf.elffile import ELFFile
    from elftools.elf.sections import SymbolTableSection
    from elftools.dwarf.callframe import FDE
    from elftools.dwarf.compileunit import CompileUnit as DWARF_CU
    from elftools.dwarf.dwarf_expr import DWARFExprParser
    from elftools.dwarf.dwarfinfo import DWARFInfo
    from elftools.dwarf.ranges import RangeEntry
    from elftools.dwarf.die import DIE as DWARF_DIE
    from elftools.dwarf.locationlists import LocationParser, LocationExpr
    from docopt import docopt
    from tabulate import tabulate
    import cxxfilt
except:
    print(
        "ERROR: Please install dependencies with: pip install tt-pyelftools docopt fuzzywuzzy python-Levenshtein tabulate"
    )
    exit(1)

CLR_RED = "\033[31m"
CLR_GREEN = "\033[32m"
CLR_BLUE = "\033[34m"
CLR_GREY = "\033[37m"
CLR_ORANGE = "\033[38:2:205:106:0m"
CLR_WHITE = "\033[38:2:255:255:255m"
CLR_END = "\033[0m"

# Helpers
debug_enabled = False


def debug(msg):
    if debug_enabled:
        print(msg)


def strip_DW_(s):
    """
    Removes DW_AT_, DW_TAG_ and other DW_* prefixes from the string
    """
    return re.sub(r"^DW_[^_]*_", "", s)


# Class representing symbol from symbol table
@dataclass
class ElfDwarfSymbol:
    value: int | None
    size: int | None


class ElfDwarf:
    def __init__(self, dwarf: DWARFInfo, parsed_elf: ParsedElfFile | ParsedElfFileWithOffset):
        self.dwarf = dwarf
        self._cus: dict[int, ElfCompileUnit] = {}
        self.parsed_elf = parsed_elf

    @cached_property
    def range_lists(self):
        return self.dwarf.range_lists()

    @cached_property
    def location_lists(self):
        return self.dwarf.location_lists()

    @cached_property
    def location_parser(self):
        return LocationParser(self.location_lists)

    def get_cu(self, dwarf_cu: DWARF_CU):
        cu = self._cus.get(id(dwarf_cu))
        if cu == None:
            cu = ElfCompileUnit(self, dwarf_cu)
            self._cus[id(dwarf_cu)] = cu
        return cu

    def get_die(self, dwarf_die: DWARF_DIE):
        dwarf_cu = dwarf_die.cu
        cu = self.get_cu(dwarf_cu)
        return cu.get_die(dwarf_die)

    def iter_CUs(self):
        for cu in self.dwarf.iter_CUs():
            yield self.get_cu(cu)

    def find_function_by_address(self, address):
        """
        Given an address, find the function that contains that address. Goes through all CUs and all DIEs and all inlined functions.
        """
        # DWARF symbols may sometimes show overlapping address ranges. If this is the
        # case, we return the function with the narrowest address range as a heuristic.

        # We save the current best candidate here.
        best_die = None

        # Try to find the CU that contains this address.
        for cu in self.iter_CUs():
            # Top DIE should contain the address
            top_die = cu.top_DIE
            for range in top_die.address_ranges:
                if range[0] <= address < range[1]:
                    # Try to recurse until we find last child that contains the address
                    result_die = top_die
                    result_range = range  # Save the range for later comparison
                    found = True
                    while found:
                        found = False
                        for child in result_die.iter_children():
                            for range in child.address_ranges:
                                if range[0] <= address < range[1]:
                                    result_range = range
                                    result_die = child
                                    found = True
                                    break

                    # Update our best solution based on the heuristic
                    if best_die is None:
                        # This is our first solution
                        best_die = result_die
                        best_range = result_range
                    elif result_range[1] - result_range[0] < best_range[1] - best_range[0]:
                        # Tighter range than the previous, save this one
                        best_range = result_range
                        best_die = result_die
        return best_die

    @cached_property
    def file_lines_ranges(self):
        result = dict()
        for cu in self.iter_CUs():
            lineprog = cu.line_program
            if lineprog is None:
                continue
            delta = 1 if lineprog.header.version < 5 else 0
            previous_entry = None
            for entry in lineprog.get_entries():
                if entry.state is None:
                    continue

                file_entry = lineprog["file_entry"][entry.state.file - delta]
                directory = lineprog["include_directory"][file_entry.dir_index].decode("utf-8")
                filename = file_entry.name.decode("utf-8")
                filename = os.path.join(directory, filename)
                line = entry.state.line
                column = entry.state.column
                current_entry = (entry.state.address, filename, line, column)
                if previous_entry is not None:
                    result[(previous_entry[0], current_entry[0])] = (
                        previous_entry[1],
                        previous_entry[2],
                        previous_entry[3],
                    )
                previous_entry = current_entry
            if previous_entry is not None:
                result[(previous_entry[0], previous_entry[0] + 4)] = (
                    previous_entry[1],
                    previous_entry[2],
                    previous_entry[3],
                )
        return result

    def find_file_line_by_address(self, address):
        ranges = self.file_lines_ranges
        for (start, end), info in ranges.items():
            if start <= address < end:
                return info
        return None


class ElfDwarfWithOffset(ElfDwarf):
    def __init__(self, my_dwarf: ElfDwarf, loaded_offset: int):
        super().__init__(my_dwarf.dwarf, my_dwarf.parsed_elf)
        self._my_dwarf = my_dwarf
        self.loaded_offset = loaded_offset

    @cached_property
    def range_lists(self):
        return self._my_dwarf.range_lists

    @cached_property
    def location_lists(self):
        return self._my_dwarf.location_lists

    @cached_property
    def location_parser(self):
        return self._my_dwarf.location_parser

    def get_cu(self, dwarf_cu: DWARF_CU):
        return self._my_dwarf.get_cu(dwarf_cu)

    def get_die(self, dwarf_die: DWARF_DIE):
        return self._my_dwarf.get_die(dwarf_die)

    def iter_CUs(self):
        return self._my_dwarf.iter_CUs()

    def find_function_by_address(self, address):
        address += self.loaded_offset
        return self._my_dwarf.find_function_by_address(address)

    @cached_property
    def file_lines_ranges(self):
        return self._my_dwarf.file_lines_ranges

    def find_file_line_by_address(self, address):
        address += self.loaded_offset
        return self._my_dwarf.find_file_line_by_address(address)


class ElfCompileUnit:
    def __init__(self, dwarf: ElfDwarf, dwarf_cu: DWARF_CU):
        self.dwarf = dwarf
        self.dwarf_cu = dwarf_cu
        self.offsets: dict[int, ElfDie] = {}
        self._dies: dict[int, ElfDie] = {}

    def get_die(self, dwarf_die: DWARF_DIE):
        die = self._dies.get(id(dwarf_die))
        if die == None:
            die = ElfDie(self, dwarf_die)
            self._dies[id(dwarf_die)] = die
            assert die.offset not in self.offsets
            self.offsets[die.offset] = die
        return die

    @cached_property
    def top_DIE(self):
        return self.get_die(self.dwarf_cu.get_top_DIE())

    @cached_property
    def line_program(self):
        return self.dwarf.dwarf.line_program_for_CU(self.dwarf_cu)

    @cached_property
    def version(self):
        return self.dwarf_cu["version"]

    @cached_property
    def expression_parser(self):
        return DWARFExprParser(self.dwarf_cu.structs)

    def iter_DIEs(self):
        for die in self.dwarf_cu.iter_DIEs():
            if die.tag is not None:
                yield self.get_die(die)

    def find_DIE_at_local_offset(self, local_offset):
        """
        Given a local offset, find the DIE that has that offset
        """
        die = self.offsets.get(local_offset + self.dwarf_cu.cu_offset)
        if die != None:
            return die
        for die in self.iter_DIEs():
            if die.offset == local_offset + self.dwarf_cu.cu_offset:
                assert local_offset + self.dwarf_cu.cu_offset in self.offsets
                return die
        return None

    def find_DIE_that_specifies(self, die: "ElfDie"):
        """
        Given a DIE, find another DIE that specifies it. For example, if the DIE is a
        variable, find the DIE that defines the variable.

        IMPROVE: What if there are multiple dies to return?
        """
        for cu in self.dwarf.iter_CUs():
            for iter_die in cu.iter_DIEs():
                if len(iter_die.attributes) > 1:
                    if "DW_AT_specification" in iter_die.attributes:
                        if iter_die.get_DIE_from_attribute("DW_AT_specification") == die:
                            return iter_die
                    if "DW_AT_abstract_origin" in iter_die.attributes:
                        if iter_die.get_DIE_from_attribute("DW_AT_abstract_origin") == die:
                            return iter_die
        return None


# We only care about the stuff we can use for probing the memory
IGNORE_TAGS = set(
    [
        "DW_TAG_compile_unit",
        "DW_TAG_formal_parameter",
        "DW_TAG_unspecified_parameters",
    ]
)


class ElfDie:
    """
    A wrapper around DIE class from pyelftools that adds some helper functions.
    """

    def __init__(self, cu: ElfCompileUnit, dwarf_die: DWARF_DIE):
        self.cu = cu
        self.dwarf_die = dwarf_die

        assert type(dwarf_die.tag) == str
        self.tag: str = dwarf_die.tag
        self.attributes = dwarf_die.attributes
        self.offset = dwarf_die.offset
        self.children_by_name: dict[str, ElfDie] = {}

    def get_child_by_name(self, child_name: str):
        child = self.children_by_name.get(child_name)
        if child == None:
            for die in self.iter_children():
                if die.name is None:
                    continue
                assert die.name not in self.children_by_name or self.children_by_name[die.name] == die
                self.children_by_name[die.name] = die
                if die.name == child_name:
                    return die
        return child

    @cached_property
    def local_offset(self):
        if "DW_AT_type" in self.attributes:
            return self.attributes["DW_AT_type"].value
        return None

    @cached_property
    def category(self):
        """
        We lump all the DIEs into the following categories
        """
        if self.tag.endswith("_type") or self.tag == "DW_TAG_typedef":
            return "type"
        elif self.tag == "DW_TAG_enumerator":
            return "enumerator"
        elif self.tag == "DW_TAG_variable":
            return "variable"
        elif self.tag == "DW_TAG_member":
            return "member"
        elif self.tag == "DW_TAG_subprogram":
            return "subprogram"
        elif self.tag in IGNORE_TAGS:
            pass  # Just skip these tags
        elif self.tag == "DW_TAG_namespace":
            return "type"
        elif self.tag == "DW_TAG_inlined_subroutine":
            return "inlined_function"
        elif self.tag == "DW_TAG_lexical_block":
            return "lexical_block"
        elif (
            self.tag == "DW_TAG_imported_declaration"
            or self.tag == "DW_TAG_imported_module"
            or self.tag == "DW_TAG_template_type_param"
            or self.tag == "DW_TAG_template_value_param"
            or self.tag == "DW_TAG_call_site"
            or self.tag == "DW_TAG_GNU_call_site"
            or self.tag == "DW_TAG_GNU_template_parameter_pack"
            or self.tag == "DW_TAG_GNU_formal_parameter_pack"
            or self.tag == "DW_TAG_inheritance"
            or self.tag == "DW_TAG_label"
        ):
            return None
        else:
            print(f"{CLR_RED}Don't know how to categorize tag: {self.tag}{CLR_END}")
            return None

    @cached_property
    def path(self) -> str | None:
        """
        Returns full path of the DIE, including the parent DIEs
            e.g. <parent.get_path()...>::<self.get_name()>
        """
        parent = self.parent
        name = self.name

        if self.category == "subprogram" and "DW_AT_specification" in self.attributes:
            dwarf_die = self.dwarf_die.get_DIE_from_attribute("DW_AT_specification")
            die = self.cu.dwarf.get_die(dwarf_die)
            if die is not None:
                return die.path

        if parent and parent.tag != "DW_TAG_compile_unit":
            parent_path = parent.path
            return f"{parent_path}::{name}"

        return name

    @cached_property
    def resolved_type(self) -> "ElfDie":
        """
        Resolve to underlying type
        TODO: test typedefs, this looks overly complicated
        """
        if self.tag == "DW_TAG_typedef" and self.local_offset != None:
            typedef_DIE = self.cu.find_DIE_at_local_offset(self.local_offset)
            if typedef_DIE:  # If typedef, recursivelly do it
                return typedef_DIE.resolved_type
        elif self.tag == "DW_TAG_const_type" and self.local_offset != None:
            typedef_DIE = self.cu.find_DIE_at_local_offset(self.local_offset)
            if typedef_DIE:  # If typedef, recursivelly do it
                return typedef_DIE.resolved_type
        elif self.tag == "DW_TAG_volatile_type" and self.local_offset != None:
            typedef_DIE = self.cu.find_DIE_at_local_offset(self.local_offset)
            if typedef_DIE:  # If typedef, recursivelly do it
                return typedef_DIE.resolved_type
        elif self.category != "type" and "DW_AT_type" in self.attributes and self.local_offset != None:
            type_die = self.cu.find_DIE_at_local_offset(self.local_offset)
            if type_die is not None:
                if (
                    type_die.tag == "DW_TAG_typedef"
                    or type_die.tag == "DW_TAG_const_type"
                    or type_die.tag == "DW_TAG_volatile_type"
                ):
                    return type_die.resolved_type
                return type_die
        elif "DW_AT_specification" in self.attributes:
            dwarf_die = self.dwarf_die.get_DIE_from_attribute("DW_AT_specification")
            die = self.cu.dwarf.get_die(dwarf_die)
            if die is not None:
                return die.resolved_type
        return self

    @cached_property
    def dereference_type(self):
        """
        Dereference a pointer type to get the type of what it points to
        """
        if self.tag == "DW_TAG_pointer_type" or self.tag == "DW_TAG_reference_type":
            if "DW_AT_type" not in self.attributes:
                return None
            dereference_Type = self.cu.find_DIE_at_local_offset(self.local_offset)
            if dereference_Type is not None:
                return dereference_Type.resolved_type
        return None

    @cached_property
    def array_element_type(self):
        """
        Get the type of the elements of an array
        """
        if self.tag == "DW_TAG_array_type":
            element_type = self.cu.find_DIE_at_local_offset(self.local_offset)
            if element_type is not None:
                return element_type.resolved_type
        return None

    @cached_property
    def size(self) -> int | None:
        """
        Return the size in bytes of the DIE
        """
        if "DW_AT_byte_size" in self.attributes:
            return self.attributes["DW_AT_byte_size"].value

        if self.tag == "DW_TAG_pointer_type":
            return 4  # Assuming 32-bit pointer

        if self.tag == "DW_TAG_array_type":
            array_size = 1
            for child in self.iter_children():
                if "DW_AT_upper_bound" in child.attributes:
                    upper_bound = child.attributes["DW_AT_upper_bound"].value
                    array_size *= upper_bound + 1
            elem_die = self.cu.find_DIE_at_local_offset(self.local_offset)
            if elem_die is not None:
                elem_size = elem_die.size
                if elem_size is not None:
                    return array_size * elem_size

        if "DW_AT_type" in self.attributes:
            type_die = self.cu.find_DIE_at_local_offset(self.local_offset)
            if type_die is not None:
                return type_die.size

        # Try to find size from symbol table
        if self.name in self.cu.dwarf.parsed_elf.symbols:
            return self.cu.dwarf.parsed_elf.symbols[self.name].size

        return None

    @cached_property
    def address(self) -> int | None:
        """
        Return the address of the DIE within the parent type
        """
        return self.__get_address_recursed(allow_recursion=True)

    def __get_address_recursed(self, allow_recursion: bool) -> int | None:
        addr = None
        if "DW_AT_data_member_location" in self.attributes:
            addr = self.attributes["DW_AT_data_member_location"].value
        else:
            location_attribute = self.attributes.get("DW_AT_location")
            location_parser = self.cu.dwarf.location_parser
            if location_attribute:
                location = location_parser.parse_from_attribute(location_attribute, self.cu.version, self.dwarf_die)
                if isinstance(location, LocationExpr):
                    parsed = self.cu.expression_parser.parse_expr(location.loc_expr)
                    if len(parsed) == 1 and parsed[0].op_name == "DW_OP_addr":
                        assert len(parsed[0].args) == 1
                        addr = parsed[0].args[0]
                    elif len(parsed) == 1 and parsed[0].op_name == "DW_OP_addrx":
                        assert len(parsed[0].args) == 1
                        index = parsed[0].args[0]
                        addr = self.cu.dwarf.dwarf.get_addr(self.cu.dwarf_cu, index)
                    else:
                        # We have expression that needs to be evaluated and applied in order to get to location value.
                        # In order for this to work, we need to return expression that needs to be evaluated in mem_access method.
                        pass
                elif isinstance(location, list):
                    # We have list of expressions. All need to be evaluated and applied in order to get to location value.
                    # In order for this to work, we need to return expression that needs to be evaluated in mem_access method.
                    # for loc in location:
                    #     parsed = self.cu.expression_parser.parse_expr(loc.loc_expr)
                    pass
            else:
                if allow_recursion and (
                    not "DW_AT_artificial" in self.attributes or not self.attributes["DW_AT_artificial"].value
                ):
                    if "DW_AT_specification" in self.attributes:
                        other_die = self.get_DIE_from_attribute("DW_AT_specification")
                    elif "DW_AT_abstract_origin" in self.attributes:
                        other_die = self.get_DIE_from_attribute("DW_AT_abstract_origin")
                    else:
                        other_die = self.cu.find_DIE_that_specifies(self)
                    if other_die:
                        addr = other_die.__get_address_recursed(allow_recursion=False)

        if addr is None:
            if (
                self.tag_is("enumerator")
                or self.tag_is("namespace")
                or self.tag.endswith("_type")
                or self.tag_is("typedef")
            ):
                # Then we are not expecting an address
                pass
            elif self.parent is not None and self.parent.tag == "DW_TAG_union_type":
                return 0  # All members of a union start at the same address
            else:
                if self.attributes.get("DW_AT_const_value"):
                    return self.attributes["DW_AT_const_value"].value
                else:
                    # Try to find address from symbol table
                    if self.name in self.cu.dwarf.parsed_elf.symbols:
                        return self.cu.dwarf.parsed_elf.symbols[self.name].value
                    else:
                        print(f"{CLR_RED}ERROR: Cannot find address for {self}{CLR_END}")
        return addr

    @cached_property
    def value(self):
        """
        Return the value of the DIE
        """
        if "DW_AT_const_value" in self.attributes:
            return self.attributes["DW_AT_const_value"].value
        return None

    @cached_property
    def linkage_name(self):
        if "DW_AT_linkage_name" in self.attributes:
            value = self.attributes["DW_AT_linkage_name"].value
            try:
                return cxxfilt.demangle(value.decode("utf-8"))
            except:
                pass

        return None

    @cached_property
    def name(self) -> str | None:
        """
        Return the name of the DIE
        """

        if "DW_AT_name" in self.attributes:
            name_value = self.attributes["DW_AT_name"].value
            if name_value is not None:
                name = name_value.decode("utf-8")
            else:
                name = None
        elif "DW_AT_specification" in self.attributes:
            dwarf_die = self.dwarf_die.get_DIE_from_attribute("DW_AT_specification")
            die = self.cu.dwarf.get_die(dwarf_die)
            if die is not None:
                name = die.name
            else:
                name = None
        elif self.tag_is("pointer_type"):
            if self.dereference_type is None:
                name = "?"
            else:
                name = f"{self.dereference_type.name}*"
        elif self.tag_is("reference_type"):
            if self.dereference_type is not None:
                name = f"{self.dereference_type.name}&"
            else:
                name = "?Unknown?&"
        elif "DW_AT_abstract_origin" in self.attributes:
            die = self.get_DIE_from_attribute("DW_AT_abstract_origin")
            if die is not None:
                name = die.path if self.category == "inlined_function" else die.name
            else:
                name = None
        else:
            # We can't figure out the name of this variable. Just give it a name based on the ELF offset.
            name = f"{self.tag}-{hex(self.offset)}"

        return name

    @cached_property
    def address_ranges(self) -> list[tuple]:
        if "DW_AT_low_pc" in self.attributes and "DW_AT_high_pc" in self.attributes:
            return [
                (
                    self.attributes["DW_AT_low_pc"].value,
                    self.attributes["DW_AT_low_pc"].value + self.attributes["DW_AT_high_pc"].value,
                )
            ]
        elif "DW_AT_ranges" in self.attributes:
            assert self.cu.dwarf.range_lists is not None
            ranges = self.cu.dwarf.range_lists.get_range_list_at_offset(self.attributes["DW_AT_ranges"].value)
            return [(r.begin_offset, r.end_offset) for r in ranges if isinstance(r, RangeEntry)]
        else:
            child_ranges = []
            for child in self.iter_children():
                child_ranges.extend(child.address_ranges)

            if child_ranges:
                # Compute the overall range
                min_address = min(r[0] for r in child_ranges)
                max_address = max(r[1] for r in child_ranges)
                return [(min_address, max_address)]

        return []

    @cached_property
    def decl_file_info(self):
        file = None
        line = None
        column = None
        if "DW_AT_decl_file" in self.attributes:
            file_entry = self.cu.line_program["file_entry"][self.attributes["DW_AT_decl_file"].value]
            directory = self.cu.line_program["include_directory"][file_entry.dir_index].decode("utf-8")
            file = file_entry.name.decode("utf-8")
            file = os.path.join(directory, file)
        if "DW_AT_decl_line" in self.attributes:
            line = self.attributes["DW_AT_decl_line"].value
        if "DW_AT_decl_column" in self.attributes:
            column = self.attributes["DW_AT_decl_column"].value
        return (file, line, column)

    @cached_property
    def call_file_info(self):
        file = None
        line = None
        column = None
        if "DW_AT_call_file" in self.attributes and self.cu.line_program is not None:
            file_entry = self.cu.line_program["file_entry"][self.attributes["DW_AT_call_file"].value]
            directory = self.cu.line_program["include_directory"][file_entry.dir_index].decode("utf-8")
            file = file_entry.name.decode("utf-8")
            file = os.path.join(directory, file)
        if "DW_AT_call_line" in self.attributes:
            line = self.attributes["DW_AT_call_line"].value
        if "DW_AT_call_column" in self.attributes:
            column = self.attributes["DW_AT_call_column"].value
        return (file, line, column)

    def iter_children(self):
        """
        Iterate over all children of this DIE
        """
        for child in self.dwarf_die.iter_children():
            yield self.cu.get_die(child)

    def get_DIE_from_attribute(self, attribute_name: str):
        if attribute_name in self.attributes:
            dwarf_die = self.dwarf_die.get_DIE_from_attribute(attribute_name)
            return self.cu.dwarf.get_die(dwarf_die)
        return None

    @cached_property
    def parent(self):
        """
        A parent of a variable is the struct it is defined in. It is a type.
        """
        parent = self.dwarf_die.get_parent()
        if parent:
            return self.cu.get_die(parent)
        return None

    def __repr__(self):
        """
        Return a string representation of the DIE for debugging
        """
        attrs = []
        for attr_name in self.attributes.keys():
            attr_value = self.attributes[attr_name].value
            if isinstance(attr_value, bytes):
                attr_value = attr_value.decode("utf-8")
            attrs.append(f"{strip_DW_(attr_name)}={attr_value}")
        return f"{strip_DW_(self.tag)}({', '.join(attrs)}) offset={hex(self.offset)}"

    def tag_is(self, tag):
        return self.tag == f"DW_TAG_{tag}"


# end class MY_DIE


def process_die(die: ElfDie, recurse_dict, r_depth):
    """
    Processes a DIE, adds it to the recurse_dict if needed, and returns True if we
    should recurse into its children
    """

    def log(str):
        debug(f"{'  ' * (r_depth+1)}{str}")

    category = die.category
    path = die.path

    # We add test for debug_enabled here, because we don't want string formatting to be executed without printint anything
    global debug_enabled
    if debug_enabled:
        log(
            f"{CLR_BLUE}{path}{CLR_END} {category} {CLR_GREEN}{die.resolved_type.path}{CLR_END} {die.offset}/{hex(die.offset)} {die}"
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


class FrameDescription:
    def __init__(self, pc: int, fde: FDE, risc_debug: RiscDebug):
        self.pc = pc
        self.fde = fde
        self.risc_debug = risc_debug

        # Go through fde and try to find one that fits the pc
        decoded = self.fde.get_decoded()
        for entry in decoded.table:
            if entry["pc"] > self.pc:
                break
            self.current_fde_entry = entry

    def read_register(self, register_index: int, cfa: int):
        if self.current_fde_entry is not None and register_index in self.current_fde_entry:
            register_rule = self.current_fde_entry[register_index]
            if register_rule.type == "OFFSET":
                address = cfa + register_rule.arg
            else:
                address = None
            if address is not None:
                return self.risc_debug.read_memory(address)
        return self.risc_debug.read_gpr(register_index)

    def read_previous_cfa(self, current_cfa: int | None = None) -> int | None:
        if self.current_fde_entry is not None and self.fde.cie is not None:
            cfa_location = self.current_fde_entry["cfa"]
            register_index = cfa_location.reg

            # Check if it is first CFA
            if current_cfa is None:
                # We have rule on how to calculate CFA (register_value + offset)
                return self.risc_debug.read_gpr(register_index) + cfa_location.offset
            else:
                # If register is not stored in the current frame, we can calculate it from the previous CFA
                if not register_index in self.current_fde_entry:
                    return current_cfa + cfa_location.offset

                # Just read stored value of the register in current frame
                return self.read_register(register_index, current_cfa)

        # We don't know how to calculate CFA, return 0 which will stop callstack evaluation
        return None


class FrameInfoProvider:
    def __init__(self, dwarf_info):
        self.dwarf_info = dwarf_info
        self.fdes = []

        # Check if we have dwarf_frame CFI section
        if dwarf_info.has_CFI():
            for entry in dwarf_info.CFI_entries():
                if not isinstance(entry, FDE):
                    continue
                start_address = entry.header["initial_location"]
                end_address = start_address + entry.header["address_range"]
                self.fdes.append((start_address, end_address, entry))

    def get_frame_description(self, pc, risc_debug) -> FrameDescription | None:
        for start_address, end_address, fde in self.fdes:
            if start_address <= pc < end_address:
                return FrameDescription(pc, fde, risc_debug)
        return None


class FrameInfoProviderWithOffset(FrameInfoProvider):
    def __init__(self, frame_info: FrameInfoProvider, loaded_offset: int):
        self.dwarf_info = frame_info.dwarf_info
        self.fdes = frame_info.fdes
        self._frame_info = frame_info
        self.loaded_offset = loaded_offset

    def get_frame_description(self, pc, risc_debug) -> FrameDescription | None:
        pc = pc + self.loaded_offset
        return self._frame_info.get_frame_description(pc, risc_debug)


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
        debug(f"CU: {cu_name}")

        # Process the names etc
        recurse_die(top_DIE, recurse_dict)

    return recurse_dict


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
        return ElfVariable(die.resolved_type, address, mem_access_function)

    def read_global(self, name: str, mem_access_function: Callable[[int, int, int], list[int]]) -> ElfVariable:
        """
        Given a global variable name, return an ElfVariable object that has been read
        """
        return self.get_global(name, mem_access_function).read()

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


class ElfVariable:
    def __init__(self, type_die: ElfDie, address: int, mem_access_function: Callable[[int, int, int], list[int]]):
        self.type_die = type_die
        self.address = address
        self.mem_access_function = mem_access_function

    def __getattr__(self, member_name) -> "ElfVariable":
        if self.type_die.tag_is("pointer_type"):
            address = self.mem_access_function(self.address, self.type_die.size, 1)[0]
            dereferenced_pointer = ElfVariable(self.type_die.dereference_type, address, self.mem_access_function)
            return getattr(dereferenced_pointer, member_name)
        child_die = self.type_die.get_child_by_name(member_name)
        if not child_die:
            child_die = resolve_unnamed_union_member(self.type_die, member_name)
        if not child_die:
            assert self.type_die.path is not None
            member_path = self.type_die.path + "::" + member_name
            raise Exception(f"ERROR: Cannot find {member_path}")
        assert self.address is not None and child_die.address is not None
        return ElfVariable(child_die.resolved_type, self.address + child_die.address, self.mem_access_function)

    def __getitem__(self, index: int) -> "ElfVariable":
        if not self.type_die.tag_is("array_type") and not self.type_die.tag_is("pointer_type"):
            raise Exception(f"ERROR: {self.type_die.name} is not an array or pointer")

        if self.type_die.tag_is("pointer_type"):
            array_element_type = self.type_die.dereference_type
        else:
            array_element_type = self.type_die.array_element_type

        new_address = self.address + index * array_element_type.size
        return ElfVariable(array_element_type, new_address, self.mem_access_function)

    def __len__(self):
        """
        Return the number of elements in the array
        """
        if not self.type_die.tag_is("array_type"):
            raise Exception(f"ERROR: {self.type_die.name} is not an array")

        # For arrays, calculate total number of elements in the first dimension
        for child in self.type_die.iter_children():
            if "DW_AT_upper_bound" in child.attributes:
                upper_bound = child.attributes["DW_AT_upper_bound"].value
                return upper_bound + 1  # Return first dimension size

        # If no upper bound found, this might be a flexible array member
        raise Exception(f"ERROR: Cannot determine length of array {self.type_die.name}")

    def value(self):
        # Check that type_die is a basic type
        if not self.type_die.tag_is("base_type"):
            raise Exception(f"ERROR: {self.type_die.name} is not a base type")

        # Read the value from memory
        value = self.mem_access_function(self.address, self.type_die.size, 1)[0]

        # Convert the value to the appropriate type
        if self.type_die.name == "float":
            return struct.unpack("f", struct.pack("I", value))[0]
        elif self.type_die.name == "double":
            return struct.unpack("d", struct.pack("Q", value))[0]
        elif self.type_die.name == "bool":
            return bool(value)
        else:
            return value

    def read(self):
        int_bytes = self.mem_access_function(self.address, self.type_die.size, self.type_die.size)
        data = bytes(int_bytes)
        address = self.address
        def mem_access(addr: int, size_bytes: int, elements_to_read: int) -> list[int]:
            if elements_to_read == 0:
                return []
            element_size = size_bytes // elements_to_read
            assert element_size * elements_to_read == size_bytes, "Size must be divisible by number of elements"

            if addr >= address and addr + size_bytes * elements_to_read <= address + len(data):
                bytes_data = data[addr - address : addr - address + size_bytes * elements_to_read]
                return [
                    int.from_bytes(bytes_data[i * element_size : (i + 1) * element_size], byteorder="little")
                    for i in range(elements_to_read)
                ]
            return self.mem_access_function(addr, size_bytes, elements_to_read)
        return ElfVariable(self.type_die, self.address, mem_access)

#
# Access path parsing / processing
#
def split_access_path(access_path):
    """
    Splits a C language access path into three parts:
    1. The first element of the path.
    2. The dividing element (one of '.', '->', '[').
    3. The rest of the path.
    """
    # Regex pattern to capture the first element, the dividing element, and the rest of the path
    # pattern = r'^([\*]*\w+)(\.|->|\[|\])(.*)$'
    pattern = r"^([\*]*[\w:]+)(\.|->|\[)(.*)$"

    match = re.match(pattern, access_path)

    if match:
        return match.group(1), match.group(2), match.group(3)
    else:
        return access_path, "", ""


def get_ptr_dereference_count(name):
    """
    Given a name, count the number of leading '*'s. Return the name without the leading '*'s, and the count.
    """
    ptr_dereference_count = 0
    while name.startswith("*"):
        name = name[1:]
        ptr_dereference_count += 1
    return name, ptr_dereference_count


def get_array_indices(rest_of_path: str):
    """
    Given a string that starts with '[', parse the array indices and return them as a list.
    Supports integer indices only. Supports multidimensional arrays (e.g. [1][2] in which
    case it returns [1, 2]).
    """
    array_indices: list[int] = []
    while rest_of_path.startswith("["):
        closing_bracket_pos = rest_of_path.find("]")
        if closing_bracket_pos == -1:
            raise Exception(f"ERROR: Expected ] in {rest_of_path}")
        array_index = rest_of_path[1:closing_bracket_pos]
        array_indices.append(int(array_index))
        rest_of_path = rest_of_path[closing_bracket_pos + 1 :]
    return array_indices, rest_of_path


def resolve_unnamed_union_member(type_die: ElfDie, member_name: str):
    """
    Given a die that contains an unnamed union of type type_die, and a member path
    represening a member of the unnamed union, return the die of the unnamed union.
    """
    for child in type_die.iter_children():
        if "DW_AT_name" not in child.attributes and child.tag == "DW_TAG_member":
            union_type = child.resolved_type
            for union_member_child in union_type.iter_children():
                if union_member_child.name == member_name:
                    return child
    return None


def mem_access(elf: ParsedElfFile, access_path: str, mem_access_function: Callable[[int, int, int], list[int]]):
    """
    Given an access path such as "s_ptr->an_int", "s_ptr->an_int[2]", or "s_ptr->an_int[2][3]",
    calls the mem_access_function to read the memory, and returns the value array.
    mem_access_function should be:
        def mem_access(address: int, bytes_to_read: int, elements_to_read: int) -> list[int]:
    """
    debug(f"Accessing {CLR_GREEN}{access_path}{CLR_END}")

    # At the top level, the next name should be found in the elf.variables
    # We also check for pointer dereferences here
    access_path, ptr_dereference_count = get_ptr_dereference_count(access_path)
    name, path_divider, rest_of_path = split_access_path(access_path)
    die: ElfDie = elf.variables[name]
    current_address = die.address
    type_die = die.resolved_type

    num_members_to_read = 1
    while True:
        if path_divider is None or path_divider == "":
            # We reached the end of the path. Call the mem_access_functions, and return the value array.

            # If we have leading *s, dereference the pointer
            while ptr_dereference_count > 0:
                ptr_dereference_count -= 1
                assert type_die is not None
                type_die = type_die.dereference_type
                assert current_address is not None
                current_address = mem_access_function(current_address, 4, 1)[0]  # Assuming 4 byte pointers

            # Check if it is a reference
            assert type_die is not None
            if type_die.tag_is("reference_type"):
                type_die = type_die.dereference_type
                assert current_address is not None
                current_address = mem_access_function(current_address, 4, 1)[0]  # Dereference the reference

            assert current_address is not None and type_die is not None and type_die.size is not None
            bytes_to_read = type_die.size * num_members_to_read
            if type_die.array_element_type is not None and type_die.array_element_type.size is not None:
                return (
                    mem_access_function(
                        current_address,
                        bytes_to_read,
                        num_members_to_read * type_die.size // type_die.array_element_type.size,
                    ),
                    current_address,
                    bytes_to_read,
                    die.value,
                    type_die,
                )
            return (
                mem_access_function(current_address, bytes_to_read, num_members_to_read),
                current_address,
                bytes_to_read,
                die.value,
                type_die,
            )
        elif path_divider == ".":
            if num_members_to_read > 1:
                raise Exception(f"ERROR: Cannot access {name} as a single value")
            member_name, path_divider, rest_of_path = split_access_path(rest_of_path)
            assert type_die is not None and member_name is not None
            child_die = type_die.get_child_by_name(member_name)
            if not child_die:
                child_die = resolve_unnamed_union_member(type_die, member_name)
            if not child_die:
                assert type_die.path is not None
                member_path = type_die.path + "::" + member_name
                raise Exception(f"ERROR: Cannot find {member_path}")
            die = child_die
            type_die = die.resolved_type
            assert current_address is not None and die.address is not None
            current_address += die.address

        elif path_divider == "->":
            if num_members_to_read > 1:
                raise Exception(f"ERROR: Cannot access {name} as a single value")
            member_name, path_divider, rest_of_path = split_access_path(rest_of_path)
            assert type_die is not None
            if not type_die.tag_is("pointer_type"):
                raise Exception(f"ERROR: {type_die.path} is not a pointer")
            assert type_die.dereference_type is not None
            type_die = type_die.dereference_type.resolved_type
            assert current_address is not None
            pointer_address = mem_access_function(current_address, 4, 1)[0] if die.value is None else die.value
            assert type_die is not None and member_name is not None
            child_die = type_die.get_child_by_name(member_name)
            if not child_die:
                child_die = resolve_unnamed_union_member(type_die, member_name)
            if not child_die:
                assert type_die.path is not None
                member_path = type_die.path + "::" + member_name
                raise Exception(f"ERROR: Cannot find {member_path}")
            die = child_die
            type_die = die.resolved_type
            assert die.address is not None
            current_address = pointer_address + die.address  # Assuming 4 byte pointers

        elif path_divider == "[":
            if num_members_to_read > 1:
                raise Exception(f"INTERNAL ERROR: An array of arrays should be processed in a single call")
            array_indices, rest_of_path = get_array_indices("[" + rest_of_path)
            assert type_die is not None
            element_type_die, array_member_offset, num_members_to_read = get_array_member_offset(
                type_die, array_indices
            )
            element_size = element_type_die.size
            assert element_size is not None and current_address is not None
            current_address += element_size * array_member_offset
            rest_of_path = "ARRAY" + rest_of_path
            member_name, path_divider, rest_of_path = split_access_path(rest_of_path)
            type_die = element_type_die
        else:
            raise Exception(f"ERROR: Unknown divider {path_divider}")


def get_array_member_offset(array_type: ElfDie, array_indices: list[int]):
    """
    Given a list of array_indices of a multidimensional array:
     - Return element type with the offset in bytes.
     - Also, return the number of elements to read to get to the all the subarray elements, in
       case of multidimensional arrays with only a portion of the indices specified.

    For example, for int A[2][3]:
    - if array_indices is [0][0], we return (int, 0, 1): a single element of at offset 0
    - if array_indices is [0][1], we return (int, 1, 1): a single element of at offset 1
    - if array_indices is [1][0], we return (int, 3, 1)): a single element of at offset 3
    - if array_indices is [1],    we return (int, 3, 3): 3 elements at offset 3
    """
    if not array_type.tag_is("pointer_type") and not array_type.tag_is("array_type"):
        raise Exception(f"ERROR: {array_type.name} is not a pointer or an array")
    else:
        if array_type.tag_is("pointer_type"):
            array_element_type = array_type.dereference_type
        else:
            array_element_type = array_type.array_element_type
        assert array_element_type is not None

        # 1. Find array dimensions
        array_dimensions = []
        for child in array_type.iter_children():
            if "DW_AT_upper_bound" in child.attributes:
                upper_bound = child.attributes["DW_AT_upper_bound"].value
                array_dimensions.append(upper_bound + 1)

        # 2. Compute subarray sizes in elements. Each element of subarray_sizes stores the number
        # of elements per value in array_indices for the corresponding dimension. For example,
        # if we have a 2D array of integers A[2][3], the subarray_sizes will be [3, 1] because we
        # move 3 elements for each value in array_indices[0] and 1 element for each value
        # in array_indices[1].
        subarray_sizes = [1]  # In elements
        for i in reversed(range(len(array_dimensions) - 1)):
            subarray_size = array_dimensions[i + 1] * subarray_sizes[0]
            subarray_sizes.insert(0, subarray_size)

        # 3. Compute offset in bytes
        offset = 0
        for i in range(len(array_indices)):
            if array_indices[i] >= array_dimensions[i]:
                raise Exception(f"ERROR: Array index {array_indices[i]} is out of bounds")
            else:
                offset += array_indices[i] * subarray_sizes[i]
        num_elements_to_read = subarray_sizes[len(array_indices) - 1]
        return array_element_type, offset, num_elements_to_read


def access_logger(addr, size_bytes, num_elements):
    """
    A simple memory reader emulator that prints all memory accesses
    """
    print(f"RD {hex(addr)} - {size_bytes} bytes")
    # We must return what we read to support dereferencing
    words_read = [i for i in range((size_bytes - 1) // 4 + 1)]
    return words_read


class FileInterface:
    def __init__(self):
        pass

    def get_binary(self, file_path):
        return open(file_path, "rb")

    def get_file(self, file_path: str) -> str:
        with open(file_path, "r") as f:
            return f.read()


if __name__ == "__main__":
    args = docopt(__doc__)
    elf_file_path = args["<elf-file>"]
    access_path = args["<access-path>"]
    debug_enabled = args["--debug"]

    file_ifc = FileInterface()
    elf = read_elf(file_ifc, elf_file_path)
    if access_path:
        mem_access(elf, access_path, access_logger)
    else:
        # Debugging display
        header = [
            "Category",
            "Path",
            "Resolved Type Path",
            "Size",
            "Addr",
            "Hex Addr",
            "Value",
            "Hex Value",
        ]
        header.append("DIE offset")
        if debug_enabled:
            header.append("DIE")

        rows = []
        for cat, cat_dict in elf._recursed_dwarf.items():
            for key, die in cat_dict.items():
                if not hasattr(die, "path"):  # Skip if not a DIE object
                    continue
                if key != die.path:
                    print(f"{CLR_RED}ERROR: key {key} != die.get_path() {die.path}{CLR_END}")
                resolved_type_path = die.resolved_type.path
                if resolved_type_path:  # Some DIEs are just refences to other DIEs. We skip them.
                    # Safely handle address display
                    addr = die.address
                    addr_hex = ""
                    if addr is not None:
                        try:
                            addr_hex = hex(addr)
                        except TypeError:
                            addr_hex = str(addr)  # Fallback to string representation for non-integer addresses

                    # Safely handle value display
                    val = die.value
                    val_hex = ""
                    if val is not None:
                        try:
                            val_hex = hex(val)
                        except TypeError:
                            val_hex = str(val)  # Fallback to string representation for non-integer values

                    row = [
                        cat,
                        die.path,
                        resolved_type_path,
                        die.size,
                        addr,
                        addr_hex,
                        val,
                        val_hex,
                    ]
                    row.append(hex(die.offset))
                    if debug_enabled:
                        row.append(str(die))
                    rows.append(row)

        print(tabulate(rows, headers=header, showindex=False, disable_numparse=True))


# TODO:
# 2. Integration into TTExaLens:
#   - Fuzzy search for autocomplete
#   - Real memory reader function
#   - Test
