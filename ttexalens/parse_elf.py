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
from functools import cached_property
import os
import re
from typing import Dict, Optional

try:
    from elftools.elf.elffile import ELFFile
    from elftools.dwarf.callframe import CIE, FDE
    from elftools.dwarf.compileunit import CompileUnit as DWARF_CU
    from elftools.dwarf.dwarfinfo import DWARFInfo
    from elftools.dwarf.die import DIE as DWARF_DIE
    from elftools.elf.enums import ENUM_ST_INFO_TYPE
    from docopt import docopt
    from tabulate import tabulate
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


class MY_DWARF:
    def __init__(self, dwarf: DWARFInfo, loaded_offset=0):
        self.dwarf = dwarf
        self.loaded_offset = loaded_offset
        self._cus: Dict[int, MY_CU] = {}

    @cached_property
    def range_lists(self):
        return self.dwarf.range_lists()

    def get_cu(self, dwarf_cu: DWARF_CU):
        cu = self._cus.get(id(dwarf_cu))
        if cu == None:
            cu = MY_CU(self, dwarf_cu)
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
        address += self.loaded_offset
        # Try to find CU that contains this address
        for cu in self.iter_CUs():
            # Top DIE should contain the address
            top_die = cu.top_DIE
            for range in top_die.address_ranges:
                if range[0] <= address < range[1]:
                    # Try to recurse until we find last child that contains the address
                    result_die = top_die
                    found = True
                    while found:
                        found = False
                        for child in result_die.iter_children():
                            for range in child.address_ranges:
                                if range[0] <= address < range[1]:
                                    result_die = child
                                    found = True
                                    break
                    return result_die

        # We failed to find the function
        return None

    @cached_property
    def file_lines_ranges(self):
        result = dict()
        for cu in self.iter_CUs():
            lineprog = cu.line_program
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
        address += self.loaded_offset
        ranges = self.file_lines_ranges
        for (start, end), info in ranges.items():
            if start <= address < end:
                return info
        return None


class MY_CU:
    def __init__(self, dwarf: MY_DWARF, dwarf_cu: DWARF_CU):
        self.dwarf = dwarf
        self.dwarf_cu = dwarf_cu
        self.offsets: Dict[int, MY_DIE] = {}
        self._dies: Dict[int, MY_DIE] = {}

    def get_die(self, dwarf_die: DWARF_DIE):
        die = self._dies.get(id(dwarf_die))
        if die == None:
            die = MY_DIE(self, dwarf_die)
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

    def iter_DIEs(self):
        for die in self.dwarf_cu.iter_DIEs():
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

    def find_DIE_that_specifies(self, die: "MY_DIE"):
        """
        Given a DIE, find another DIE that specifies it. For example, if the DIE is a
        variable, find the DIE that defines the variable.

        IMPROVE: What if there are multiple dies to return?
        """
        for dwarf_cu in self.dwarf_cu.dwarfinfo.iter_CUs():
            for DIE in dwarf_cu.iter_DIEs():
                if "DW_AT_specification" in DIE.attributes:
                    if DIE.attributes["DW_AT_specification"].value == die.offset:
                        return self.dwarf.get_die(DIE)
                if "DW_AT_abstract_origin" in DIE.attributes:
                    dwarf_die = DIE.get_DIE_from_attribute("DW_AT_abstract_origin")
                    if dwarf_die == die.dwarf_die and len(DIE.attributes) > 1:
                        return self.dwarf.get_die(DIE)
        return None


# We only care about the stuff we can use for probing the memory
IGNORE_TAGS = set(
    [
        "DW_TAG_compile_unit",
        "DW_TAG_formal_parameter",
        "DW_TAG_unspecified_parameters",
    ]
)


class MY_DIE:
    """
    A wrapper around DIE class from pyelftools that adds some helper functions.
    """

    def __init__(self, cu: MY_CU, dwarf_die: DWARF_DIE):
        self.cu = cu
        self.dwarf_die = dwarf_die

        self.tag: str = dwarf_die.tag
        self.attributes = dwarf_die.attributes
        self.offset = dwarf_die.offset
        self.children_by_name: Dict[str, MY_DIE] = {}

    def get_child_by_name(self, child_name: str):
        child = self.children_by_name.get(child_name)
        if child == None:
            for die in self.iter_children():
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
        ):
            return None
        else:
            print(f"{CLR_RED}Don't know how to categorize tag: {self.tag}{CLR_END}")
            return None

    @cached_property
    def path(self):
        """
        Returns full path of the DIE, including the parent DIEs
            e.g. <parent.get_path()...>::<self.get_name()>
        """
        parent = self.parent
        name = self.name

        if parent and parent.tag != "DW_TAG_compile_unit":
            parent_path = parent.path
            return f"{parent_path}::{name}"

        return name

    @cached_property
    def resolved_type(self):
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
            my_type_die = self.cu.find_DIE_at_local_offset(self.local_offset)
            if (
                my_type_die.tag == "DW_TAG_typedef"
                or my_type_die.tag == "DW_TAG_const_type"
                or my_type_die.tag == "DW_TAG_volatile_type"
            ):
                return my_type_die.resolved_type
            return my_type_die
        return self

    @cached_property
    def dereference_type(self):
        """
        Dereference a pointer type to get the type of what it points to
        """
        if self.tag == "DW_TAG_pointer_type" or self.tag == "DW_TAG_reference_type":
            if "DW_AT_type" not in self.attributes:
                return None
            return self.cu.find_DIE_at_local_offset(self.local_offset).resolved_type
        return None

    @cached_property
    def array_element_type(self):
        """
        Get the type of the elements of an array
        """
        if self.tag == "DW_TAG_array_type":
            return self.cu.find_DIE_at_local_offset(self.local_offset).resolved_type
        return None

    @cached_property
    def size(self):
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
            elem_size = elem_die.size
            return array_size * elem_size

        if "DW_AT_type" in self.attributes:
            type_die = self.cu.find_DIE_at_local_offset(self.local_offset)
            return type_die.size

        return None

    @cached_property
    def address(self):
        """
        Return the address of the DIE within the parent type
        """
        addr = None
        if "DW_AT_data_member_location" in self.attributes:
            addr = self.attributes["DW_AT_data_member_location"].value
        else:
            location = self.attributes.get("DW_AT_location")
            if location:
                # Assuming the location's form is a block
                block = location.value
                # Check if the first opcode is DW_OP_addr (0x03)
                if block[0] == 0x03:
                    addr = int.from_bytes(block[1:], byteorder="little")
            else:
                # Try to find another DIE that defines this variable
                other_die = self.cu.find_DIE_that_specifies(self)
                if other_die:
                    addr = other_die.address

        if addr is None:
            if (
                self.tag_is("enumerator")
                or self.tag_is("namespace")
                or self.tag.endswith("_type")
                or self.tag_is("typedef")
            ):
                # Then we are not expecting an address
                pass
            elif self.parent.tag == "DW_TAG_union_type":
                return 0  # All members of a union start at the same address
            else:
                if self.attributes.get("DW_AT_const_value"):
                    return self.attributes["DW_AT_const_value"].value
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
    def name(self):
        """
        Return the name of the DIE
        """
        if "DW_AT_name" in self.attributes:
            name = self.attributes["DW_AT_name"].value.decode("utf-8")
        elif "DW_AT_specification" in self.attributes:
            # This is a variable that is defined elsewhere. We'll skip it.
            # IMPROVE: We should probably find the DIE that defines it and use its name.
            name = None
        elif self.tag_is("pointer_type"):
            if self.dereference_type is None:
                name = "?"
            else:
                name = f"{self.dereference_type.name}*"
        elif self.tag_is("reference_type"):
            name = f"{self.dereference_type.name}&"
        elif "DW_AT_abstract_origin" in self.attributes:
            dwarf_die = self.dwarf_die.get_DIE_from_attribute("DW_AT_abstract_origin")
            die = self.cu.dwarf.get_die(dwarf_die)
            name = die.name
        else:
            # We can't figure out the name of this variable. Just give it a name based on the ELF offset.
            name = f"{self.tag}-{hex(self.offset)}"
        return name

    @cached_property
    def address_ranges(self):
        if "DW_AT_low_pc" in self.attributes and "DW_AT_high_pc" in self.attributes:
            return [
                (
                    self.attributes["DW_AT_low_pc"].value,
                    self.attributes["DW_AT_low_pc"].value + self.attributes["DW_AT_high_pc"].value,
                )
            ]
        elif "DW_AT_ranges" in self.attributes:
            ranges = self.cu.dwarf.range_lists.get_range_list_at_offset(self.attributes["DW_AT_ranges"].value)
            return [(r.begin_offset, r.end_offset) for r in ranges]
        return []

    @cached_property
    def call_file_info(self):
        file = None
        line = None
        column = None
        if "DW_AT_call_file" in self.attributes:
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


def process_DIE(die: MY_DIE, recurse_dict, r_depth):
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


def recurse_DIE(DIE: MY_DIE, recurse_dict, r_depth=0):
    """
    This function visits all children recursively and calls process_DIE() on each
    """
    for child in DIE.iter_children():
        recurse_down = process_DIE(child, recurse_dict, r_depth)
        if recurse_down:
            recurse_DIE(child, recurse_dict, r_depth + 1)


def decode_file_line(dwarfinfo):
    PC_to_fileline_map = {}
    for CU in dwarfinfo.iter_CUs():
        lineprog = dwarfinfo.line_program_for_CU(CU)
        delta = 1 if lineprog.header.version < 5 else 0
        prevstate = None
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
    def __init__(self, pc: int, fde: FDE, risc_debug):
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

    def read_previous_cfa(self, current_cfa: Optional[int] = None):
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
        return 0


class FrameInfoProvider:
    def __init__(self, dwarf_info, loaded_offset):
        self.dwarf_info = dwarf_info
        self.loaded_offset = loaded_offset
        self.fdes = []

        # Check if we have dwarf_frame CFI section
        if dwarf_info.has_CFI():
            for entry in dwarf_info.CFI_entries():
                if not isinstance(entry, FDE):
                    continue
                start_address = entry.header["initial_location"]
                end_address = start_address + entry.header["address_range"]
                self.fdes.append((start_address, end_address, entry))

    def get_frame_description(self, pc, risc_debug) -> FrameDescription:
        pc = pc + self.loaded_offset
        for start_address, end_address, fde in self.fdes:
            if start_address <= pc < end_address:
                return FrameDescription(pc, fde, risc_debug)
        return None


def decode_symbols(elf_file):
    functions = {}
    for section in elf_file.iter_sections():
        # Check if it's a symbol table section
        if section.name == ".symtab":
            # Iterate through symbols
            for symbol in section.iter_symbols():
                # Check if it's a label symbol
                if symbol["st_info"]["type"] == "STT_NOTYPE" and symbol.name:
                    functions[symbol.name] = symbol["st_value"]
                if symbol["st_info"]["type"] == "STT_FUNC":
                    functions[symbol.name] = symbol["st_value"]
    return functions


def parse_dwarf(dwarf: DWARFInfo, loaded_offset=0):
    """
    Itaretes recursively over all the DIEs in the DWARF info and returns a dictionary
    with the following keys:
        'variable' - all the variables (top level names)
        'type' - all the types
        'member' - all the members of structures etc
        'enumerator' - all the enumerators in the DWARF info
        'PC' - mappings between PC values and source code locations
    """
    my_dwarf = MY_DWARF(dwarf)
    recurse_dict = {
        "variable": dict(),
        "type": dict(),
        "member": dict(),
        "enumerator": dict(),
        "dwarf": my_dwarf,
    }

    for cu in my_dwarf.iter_CUs():
        top_DIE = cu.top_DIE
        cu_name = "N/A"
        if "DW_AT_name" in top_DIE.attributes:
            cu_name = top_DIE.attributes["DW_AT_name"].value.decode("utf-8")
        debug(f"CU: {cu_name}")

        # Process the names etc
        recurse_DIE(top_DIE, recurse_dict)

    # Process the PC (program counter) values so we can map them to source code
    recurse_dict["file-line"] = decode_file_line(dwarf)

    # Process frame info
    recurse_dict["frame-info"] = FrameInfoProvider(dwarf, loaded_offset)

    return recurse_dict


def read_elf(file_ifc, elf_file_path, load_address=None):
    """
    Reads the ELF file and returns a dictionary with the DWARF info
    """
    # This is redirected to read from tmp folder in case of remote runs.
    f = file_ifc.get_binary(elf_file_path)

    elf = ELFFile(f)

    if not elf.has_dwarf_info():
        print(f"ERROR: {elf_file_path} does not have DWARF info. Source file must be compiled with -g")
        return
    text_sh_address = elf.get_section_by_name(".text")["sh_addr"]
    if load_address is None:
        load_address = text_sh_address

    dwarf = elf.get_dwarf_info()

    recurse_dict = parse_dwarf(dwarf, loaded_offset=text_sh_address - load_address)

    recurse_dict["symbols"] = decode_symbols(elf)

    recurse_dict["dwarf"].loaded_offset = text_sh_address - load_address

    return recurse_dict


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
        return access_path, None, None


def get_ptr_dereference_count(name):
    """
    Given a name, count the number of leading '*'s. Return the name without the leading '*'s, and the count.
    """
    ptr_dereference_count = 0
    while name.startswith("*"):
        name = name[1:]
        ptr_dereference_count += 1
    return name, ptr_dereference_count


def get_array_indices(rest_of_path):
    """
    Given a string that starts with '[', parse the array indices and return them as a list.
    Supports integer indices only. Supports multidimensional arrays (e.g. [1][2] in which
    case it returns [1, 2]).
    """
    array_indices = []
    while rest_of_path.startswith("["):
        closing_bracket_pos = rest_of_path.find("]")
        if closing_bracket_pos == -1:
            raise Exception(f"ERROR: Expected ] in {rest_of_path}")
        array_index = rest_of_path[1:closing_bracket_pos]
        array_indices.append(int(array_index))
        rest_of_path = rest_of_path[closing_bracket_pos + 1 :]
    return array_indices, rest_of_path


def resolve_unnamed_union_member(type_die, member_name):
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


def mem_access(name_dict, access_path, mem_access_function):
    """
    Given an access path such as "s_ptr->an_int", "s_ptr->an_int[2]", or "s_ptr->an_int[2][3]",
    calls the mem_access_function to read the memory, and returns the value array.
    """
    debug(f"Accessing {CLR_GREEN}{access_path}{CLR_END}")

    # At the top level, the next name should be found in the 'variable'
    # section of the name dict: name_dict["variable"]
    # We also check for pointer dereferences here
    access_path, ptr_dereference_count = get_ptr_dereference_count(access_path)
    name, path_divider, rest_of_path = split_access_path(access_path)
    die: MY_DIE = name_dict["variable"][name]
    current_address = die.address
    type_die = die.resolved_type

    num_members_to_read = 1
    while True:
        if path_divider is None:
            # We reached the end of the path. Call the mem_access_functions, and return the value array.

            # If we have leading *s, dereference the pointer
            while ptr_dereference_count > 0:
                ptr_dereference_count -= 1
                type_die = type_die.dereference_type
                current_address = mem_access_function(current_address, 4)[0]  # Assuming 4 byte pointers

            # Check if it is a reference
            if type_die.tag_is("reference_type"):
                type_die = type_die.dereference_type
                current_address = mem_access_function(current_address, 4)[0]  # Dereference the reference

            bytes_to_read = type_die.size * num_members_to_read
            return (
                mem_access_function(current_address, bytes_to_read),
                current_address,
                bytes_to_read,
                die.value,
                type_die,
            )
        elif path_divider == ".":
            if num_members_to_read > 1:
                raise Exception(f"ERROR: Cannot access {name} as a single value")
            member_name, path_divider, rest_of_path = split_access_path(rest_of_path)
            die = type_die.get_child_by_name(member_name)
            if not die:
                die = resolve_unnamed_union_member(type_die, member_name)
            if not die:
                member_path = type_die.path + "::" + member_name
                raise Exception(f"ERROR: Cannot find {member_path}")
            type_die = die.resolved_type
            current_address += die.address

        elif path_divider == "->":
            if num_members_to_read > 1:
                raise Exception(f"ERROR: Cannot access {name} as a single value")
            member_name, path_divider, rest_of_path = split_access_path(rest_of_path)
            if not type_die.tag_is("pointer_type"):
                raise Exception(f"ERROR: {type_die.path} is not a pointer")
            type_die = type_die.dereference_type.resolved_type
            pointer_address = mem_access_function(current_address, 4)[0] if die.value is None else die.value
            die = type_die.get_child_by_name(member_name)
            if not die:
                die = resolve_unnamed_union_member(type_die, member_name)
            if not die:
                member_path = type_die.path + "::" + member_name
                raise Exception(f"ERROR: Cannot find {member_path}")
            type_die = die.resolved_type
            current_address = pointer_address + die.address  # Assuming 4 byte pointers

        elif path_divider == "[":
            if num_members_to_read > 1:
                raise Exception(f"INTERNAL ERROR: An array of arrays should be processed in a single call")
            array_indices, rest_of_path = get_array_indices("[" + rest_of_path)
            element_type_die, array_member_offset, num_members_to_read = get_array_member_offset(
                type_die, array_indices
            )
            element_size = element_type_die.size
            current_address += element_size * array_member_offset
            rest_of_path = "ARRAY" + rest_of_path
            member_name, path_divider, rest_of_path = split_access_path(rest_of_path)
            type_die = element_type_die
        else:
            raise Exception(f"ERROR: Unknown divider {path_divider}")


def get_array_member_offset(array_type, array_indices):
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


def access_logger(addr, size_bytes):
    """
    A simple memory reader emulator that prints all memory accesses
    """
    print(f"RD {hex(addr)} - {size_bytes} bytes")
    # We must return what we read to support dereferencing
    words_read = [i for i in range((size_bytes - 1) // 4 + 1)]
    return words_read


# TODO:
# 2. Integration into TTExaLens:
#   - Fuzzy search for autocomplete
#   - Real memory reader function
#   - Test
