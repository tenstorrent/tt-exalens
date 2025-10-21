# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import struct
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ttexalens.elf.die import ElfDie


class ElfVariable:
    def __init__(self, type_die: ElfDie, address: int, mem_access_function: Callable[[int, int, int], list[int]]):
        self.type_die = type_die
        self.address = address
        self.mem_access_function = mem_access_function

    def __getattr__(self, member_name) -> "ElfVariable":
        if self.type_die.tag_is("pointer_type"):
            assert self.type_die.size is not None
            address = self.mem_access_function(self.address, self.type_die.size, 1)[0]
            dereferenced_pointer = ElfVariable(self.type_die.dereference_type, address, self.mem_access_function)
            return getattr(dereferenced_pointer, member_name)
        offset = 0
        child_die = self.type_die.get_child_by_name(member_name)
        if not child_die:
            offset, child_die = ElfVariable._resolve_unnamed_struct_union_member(self.type_die, member_name)
        if not child_die:
            assert self.type_die.path is not None
            member_path = self.type_die.path + "::" + member_name
            raise Exception(f"ERROR: Cannot find {member_path}")
        assert self.address is not None and child_die.address is not None
        return ElfVariable(child_die.resolved_type, self.address + child_die.address + offset, self.mem_access_function)

    @staticmethod
    def _resolve_unnamed_struct_union_member(type_die: ElfDie, member_name: str):
        """
        Given a die that contains an unnamed union of type type_die, and a member path
        represening a member of the unnamed union, return the die of the unnamed union.
        """
        for child in type_die.iter_children():
            if "DW_AT_name" not in child.attributes and child.tag == "DW_TAG_member":
                struct_union_type = child.resolved_type
                member = struct_union_type.get_child_by_name(member_name)
                if member is not None:
                    return child.address, member
                address, member = ElfVariable._resolve_unnamed_struct_union_member(struct_union_type, member_name)
                if member is not None:
                    return address + child.address, member
        return None, None

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
        assert self.type_die.size is not None
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
        if self.type_die.tag_is("pointer_type"):
            assert self.type_die.size is not None
            address = self.mem_access_function(self.address, self.type_die.size, 1)[0]
            dereferenced_pointer = ElfVariable(self.type_die.dereference_type, address, self.mem_access_function)
            return dereferenced_pointer.read()
        assert self.type_die.size is not None
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
