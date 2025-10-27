# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import struct
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ttexalens.elf.die import ElfDie


class ElfVariable:
    def __init__(self, type_die: ElfDie, address: int, mem_access_function: Callable[[int, int, int], list[int]]):
        self.__type_die = type_die
        self.__address = address
        self.__mem_access_function = mem_access_function

    def __getattr__(self, member_name) -> "ElfVariable":
        # __getattr__ is only called when the attribute is not found through normal lookup
        # This means if we get here, the member_name is not a method/attribute of this class
        return self.get_member(member_name)

    def get_member(self, member_name: str) -> "ElfVariable":
        """
        Explicitly get a struct/union member by name, bypassing method name collisions.
        Use this when you have a struct field with the same name as a class method.

        Example: var.get_member('bytes') instead of var.bytes
        """
        if self.__type_die.tag_is("pointer_type"):
            assert self.__type_die.size is not None
            address = self.__mem_access_function(self.__address, self.__type_die.size, 1)[0]
            dereferenced_pointer = ElfVariable(self.__type_die.dereference_type, address, self.__mem_access_function)
            return dereferenced_pointer.get_member(member_name)
        offset = 0
        child_die = self.__type_die.get_child_by_name(member_name)
        if child_die is None:
            offset, child_die = ElfVariable._resolve_unnamed_struct_union_member(self.__type_die, member_name)
        if child_die is None or offset is None:
            assert self.__type_die.path is not None
            member_path = self.__type_die.path + "::" + member_name
            raise Exception(f"ERROR: Cannot find {member_path}")
        assert self.__address is not None and child_die.address is not None
        return ElfVariable(
            child_die.resolved_type, self.__address + child_die.address + offset, self.__mem_access_function
        )

    @staticmethod
    def _resolve_unnamed_struct_union_member(type_die: ElfDie, member_name: str) -> tuple[int | None, ElfDie | None]:
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

    def __getitem__(self, key: str | int) -> "ElfVariable":
        # Handle string keys for struct/union member access
        if isinstance(key, str):
            return self.get_member(key)

        # Handle integer keys for array/pointer indexing
        if isinstance(key, int):
            if not self.__type_die.tag_is("array_type") and not self.__type_die.tag_is("pointer_type"):
                raise Exception(f"ERROR: {self.__type_die.name} is not an array or pointer")

            if self.__type_die.tag_is("pointer_type"):
                array_element_type = self.__type_die.dereference_type
            else:
                array_element_type = self.__type_die.array_element_type

            new_address = self.__address + key * array_element_type.size
            return ElfVariable(array_element_type, new_address, self.__mem_access_function)

        # Handle other types that might be used as indices (like ElfVariable with __index__)
        try:
            index = int(key)
            return self[index]  # Recursive call with the converted integer
        except (TypeError, ValueError):
            raise TypeError(f"ElfVariable indices must be integers or strings, not {type(key).__name__}")

    def __len__(self) -> int:
        """
        Return the number of elements in the array
        """
        if not self.__type_die.tag_is("array_type"):
            raise Exception(f"ERROR: {self.__type_die.name} is not an array")

        # For arrays, calculate total number of elements in the first dimension
        for child in self.__type_die.iter_children():
            if "DW_AT_upper_bound" in child.attributes:
                upper_bound = child.attributes["DW_AT_upper_bound"].value
                return upper_bound + 1  # Return first dimension size

        # If no upper bound found, this might be a flexible array member
        raise Exception(f"ERROR: Cannot determine length of array {self.__type_die.name}")

    def __iter__(self):
        """
        Enable iteration over array elements
        """
        length = len(self)
        for i in range(length):
            yield self[i]

    def as_list(self) -> list["ElfVariable"]:
        """
        Return the array elements as a list
        """
        return [self[i] for i in range(len(self))]

    def as_value_list(self) -> list[int | float | bool]:
        """
        Return the array elements as a list of values
        """
        return [self[i].get_value() for i in range(len(self))]

    def get_value(self) -> int | float | bool:
        # Check that type_die is a basic type
        if not self.__type_die.tag_is("base_type"):
            raise Exception(f"ERROR: {self.__type_die.name} is not a base type")

        # Read the value from memory
        assert self.__type_die.size is not None
        value = self.__mem_access_function(self.__address, self.__type_die.size, 1)[0]

        # Convert the value to the appropriate type
        if self.__type_die.name == "float":
            return struct.unpack("f", struct.pack("I", value))[0]
        elif self.__type_die.name == "double":
            return struct.unpack("d", struct.pack("Q", value))[0]
        elif self.__type_die.name == "bool":
            return bool(value)
        else:
            return value

    def __eq__(self, other) -> bool:
        """
        Compare the ElfVariable's value with another value.
        For base types, compares the actual value.
        For arrays, compares element-by-element with the other sequence.
        """
        try:
            # Try to get the value for base types
            return self.get_value() == other
        except Exception:
            # If get_value() fails, check if this is an array and other is a sequence
            try:
                if self.__type_die.tag_is("array_type"):
                    # Check if other is a sequence (list, tuple, etc.)
                    if hasattr(other, "__len__") and hasattr(other, "__getitem__"):
                        # Compare lengths first for efficiency
                        if len(self) != len(other):
                            return False
                        # Compare each element
                        for i in range(len(self)):
                            if self[i] != other[i]:
                                return False
                        return True
            except Exception:
                pass
            # If neither value comparison nor array comparison worked, return False
            return False

    def __lt__(self, other) -> bool:
        """
        Less than comparison. Works with base types only.
        """
        try:
            return self.get_value() < other
        except Exception:
            return NotImplemented

    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return self < other or self == other

    def __gt__(self, other) -> bool:
        """
        Greater than comparison. Works with base types only.
        """
        try:
            return self.get_value() > other
        except Exception:
            return NotImplemented

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return self > other or self == other

    # Arithmetic operators
    def __add__(self, other):
        """Addition operator."""
        try:
            return self.get_value() + other
        except Exception:
            return NotImplemented

    def __radd__(self, other):
        """Reverse addition operator."""
        try:
            return other + self.get_value()
        except Exception:
            return NotImplemented

    def __sub__(self, other):
        """Subtraction operator."""
        try:
            return self.get_value() - other
        except Exception:
            return NotImplemented

    def __rsub__(self, other):
        """Reverse subtraction operator."""
        try:
            return other - self.get_value()
        except Exception:
            return NotImplemented

    def __mul__(self, other):
        """Multiplication operator."""
        try:
            return self.get_value() * other
        except Exception:
            return NotImplemented

    def __rmul__(self, other):
        """Reverse multiplication operator."""
        try:
            return other * self.get_value()
        except Exception:
            return NotImplemented

    def __truediv__(self, other):
        """Division operator."""
        try:
            return self.get_value() / other
        except Exception:
            return NotImplemented

    def __rtruediv__(self, other):
        """Reverse division operator."""
        try:
            return other / self.get_value()
        except Exception:
            return NotImplemented

    def __floordiv__(self, other):
        """Floor division operator."""
        try:
            return self.get_value() // other
        except Exception:
            return NotImplemented

    def __rfloordiv__(self, other):
        """Reverse floor division operator."""
        try:
            return other // self.get_value()
        except Exception:
            return NotImplemented

    def __mod__(self, other):
        """Modulo operator."""
        try:
            return self.get_value() % other
        except Exception:
            return NotImplemented

    def __rmod__(self, other):
        """Reverse modulo operator."""
        try:
            return other % self.get_value()
        except Exception:
            return NotImplemented

    def __pow__(self, other):
        """Power operator."""
        try:
            return self.get_value() ** other
        except Exception:
            return NotImplemented

    def __rpow__(self, other):
        """Reverse power operator."""
        try:
            return other ** self.get_value()
        except Exception:
            return NotImplemented

    # Bitwise operators (for integers and booleans)
    def __and__(self, other):
        """Bitwise AND operator."""
        try:
            value = self.get_value()
            if isinstance(value, (int, bool)):
                return value & other
        except Exception:
            pass
        return NotImplemented

    def __rand__(self, other):
        """Reverse bitwise AND operator."""
        try:
            value = self.get_value()
            if isinstance(value, (int, bool)):
                return other & value
        except Exception:
            pass
        return NotImplemented

    def __or__(self, other):
        """Bitwise OR operator."""
        try:
            value = self.get_value()
            if isinstance(value, (int, bool)):
                return value | other
        except Exception:
            pass
        return NotImplemented

    def __ror__(self, other):
        """Reverse bitwise OR operator."""
        try:
            value = self.get_value()
            if isinstance(value, (int, bool)):
                return other | value
        except Exception:
            pass
        return NotImplemented

    def __xor__(self, other):
        """Bitwise XOR operator."""
        try:
            value = self.get_value()
            if isinstance(value, (int, bool)):
                return value ^ other
        except Exception:
            pass
        return NotImplemented

    def __rxor__(self, other):
        """Reverse bitwise XOR operator."""
        try:
            value = self.get_value()
            if isinstance(value, (int, bool)):
                return other ^ value
        except Exception:
            pass
        return NotImplemented

    def __lshift__(self, other):
        """Left shift operator."""
        try:
            value = self.get_value()
            if isinstance(value, int):
                return value << other
        except Exception:
            pass
        return NotImplemented

    def __rlshift__(self, other):
        """Reverse left shift operator."""
        try:
            value = self.get_value()
            if isinstance(value, int):
                return other << value
        except Exception:
            pass
        return NotImplemented

    def __rshift__(self, other):
        """Right shift operator."""
        try:
            value = self.get_value()
            if isinstance(value, int):
                return value >> other
        except Exception:
            pass
        return NotImplemented

    def __rrshift__(self, other):
        """Reverse right shift operator."""
        try:
            value = self.get_value()
            if isinstance(value, int):
                return other >> value
        except Exception:
            pass
        return NotImplemented

    # Unary operators
    def __neg__(self):
        """Unary negation operator."""
        try:
            return -self.get_value()
        except Exception:
            return NotImplemented

    def __pos__(self):
        """Unary positive operator."""
        try:
            return +self.get_value()
        except Exception:
            return NotImplemented

    def __abs__(self):
        """Absolute value operator."""
        try:
            return abs(self.get_value())
        except Exception:
            return NotImplemented

    def __invert__(self):
        """Bitwise inversion operator."""
        try:
            value = self.get_value()
            if isinstance(value, (int, bool)):
                return ~value
        except Exception:
            pass
        return NotImplemented

    def __index__(self) -> int:
        """
        Allow ElfVariable to be used as an index in sequences (lists, tuples, etc.)
        This enables usage like: a[elf_var] instead of a[elf_var.value()]
        """
        try:
            value = self.get_value()
            if isinstance(value, int):
                return value
            elif isinstance(value, bool):
                return int(value)  # Convert bool to int (True -> 1, False -> 0)
            elif isinstance(value, float):
                if value.is_integer():
                    return int(value)
        except:
            pass
        raise TypeError(f"ElfVariable '{self}' cannot be used as an index")

    def __str__(self) -> str:
        """
        String representation of the ElfVariable's value
        This enables usage like: str(elf_var) instead of str(elf_var.value())
        """
        try:
            return str(self.get_value())
        except Exception:
            # If get_value() fails (e.g., not a base type), fall back to __repr__
            return self.__repr__()

    def __repr__(self) -> str:
        """
        Detailed string representation for debugging purposes
        Shows internal state including type, address, and other relevant information
        """
        type_name = getattr(self.__type_die, "name", "Unknown")
        type_tag = getattr(self.__type_die, "tag", "Unknown")
        type_size = getattr(self.__type_die, "size", "Unknown")

        # Try to get the value for additional context
        try:
            value_info = f", value={self.get_value()!r}"
        except Exception:
            value_info = ""

        # Try to get the length for arrays
        try:
            length_info = f", length={len(self)}"
        except Exception:
            length_info = ""

        return (
            f"ElfVariable(type_name='{type_name}', type_tag='{type_tag}', "
            f"size={type_size}, address=0x{self.__address:x}{value_info}{length_info})"
        )

    def __hash__(self):
        try:
            return hash(self.get_value())
        except Exception:
            return hash((self.__type_die.offset, self.__address))

    def get_address(self) -> int:
        return self.__address

    def read_bytes(self) -> bytes:
        size = self.__type_die.size
        assert size is not None
        int_bytes = self.__mem_access_function(self.__address, size, size)
        return bytes(int_bytes)

    def read(self) -> "ElfVariable":
        if self.__type_die.tag_is("pointer_type"):
            assert self.__type_die.size is not None
            address = self.__mem_access_function(self.__address, self.__type_die.size, 1)[0]
            dereferenced_pointer = ElfVariable(self.__type_die.dereference_type, address, self.__mem_access_function)
            return dereferenced_pointer.read()
        data = self.read_bytes()
        address = self.__address

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
            return self.__mem_access_function(addr, size_bytes, elements_to_read)

        return ElfVariable(self.__type_die, self.__address, mem_access)
