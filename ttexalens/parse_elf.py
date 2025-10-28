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
from docopt import docopt
import re
from tabulate import tabulate
from ttexalens.elf import ElfDie, ParsedElfFile, read_elf
from typing import Callable

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
