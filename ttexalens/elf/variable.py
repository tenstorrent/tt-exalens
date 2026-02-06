# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import struct
from typing import TYPE_CHECKING

from ttexalens.memory_access import (
    MemoryAccess,
    CachedReadMemoryAccess,
)

if TYPE_CHECKING:
    from ttexalens.elf.die import ElfDie


class ElfVariable:
    def __init__(self, type_die: ElfDie, address: int, mem_access: MemoryAccess):
        self.__type_die = type_die
        self.__address = address
        self.__mem_access = mem_access

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
            return self.dereference().get_member(member_name)
        offset: int | None = 0
        child_die = self.__type_die.get_child_by_name(member_name)
        if child_die is None:
            offset, child_die = ElfVariable._resolve_unnamed_struct_union_member(self.__type_die, member_name)
        if child_die is None:
            offset, child_die = ElfVariable._resolve_inheritance_member(self.__type_die, member_name)
        if child_die is None or offset is None:
            assert self.__type_die.path is not None
            member_path = self.__type_die.path + "::" + member_name
            raise Exception(f"ERROR: Cannot find {member_path}")
        assert self.__address is not None and child_die.address is not None
        return ElfVariable(child_die.resolved_type, self.__address + child_die.address + offset, self.__mem_access)

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
                if member is not None and address is not None:
                    assert child.address is not None
                    return address + child.address, member
        return None, None

    @staticmethod
    def _resolve_inheritance_member(
        type_die: ElfDie, member_name: str, offset: int = 0
    ) -> tuple[int | None, ElfDie | None]:
        for child in type_die.iter_children():
            if child.tag_is("inheritance"):
                assert child.address is not None
                data_member_location = offset + child.address
                child_type = child.resolved_type
                member = child_type.get_child_by_name(member_name)
                if member is not None:
                    assert member.address is not None
                    return data_member_location, member
                address, member = ElfVariable._resolve_inheritance_member(child_type, member_name, data_member_location)
                if member is not None and address is not None:
                    return address, member
                address, member = ElfVariable._resolve_unnamed_struct_union_member(child_type, member_name)
                if member is not None and address is not None:
                    return data_member_location + address, member
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
                address = self.dereference().get_address()
            else:
                array_element_type = self.__type_die.array_element_type
                address = self.__address

            assert array_element_type is not None
            assert array_element_type.size is not None
            new_address = address + key * array_element_type.size
            return ElfVariable(array_element_type, new_address, self.__mem_access)

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
                upper_bound: int = child.attributes["DW_AT_upper_bound"].value
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
        return [self[i].read_value() for i in range(len(self))]

    def dereference(self) -> "ElfVariable":
        """
        Dereference a pointer variable and return the pointed-to variable.
        """
        if not self.__type_die.tag_is("pointer_type"):
            raise Exception(f"ERROR: {self.__type_die.name} is not a pointer type")
        assert self.__type_die.size is not None
        assert self.__type_die.dereference_type is not None
        address_bytes = self.__mem_access.read(self.__address, self.__type_die.size)
        address = int.from_bytes(address_bytes, byteorder="little")
        return ElfVariable(self.__type_die.dereference_type, address, self.__mem_access)

    def read_value(self) -> int | float | bool:
        # Check that type_die is a basic type
        type = self.__type_die
        if not type.tag_is("base_type") and not type.tag_is("pointer_type") and not type.tag_is("enumeration_type"):
            raise Exception(f"ERROR: {type.name} is not a base type or pointer type")

        # If it is an enumeration type, treat it as its underlying base type
        while type.tag_is("enumeration_type") and type.resolved_type != type:
            type = type.resolved_type

        # Read the value from memory
        assert type.size is not None
        value_bytes = self.__mem_access.read(self.__address, type.size)

        # Convert the value to the appropriate type
        if type.tag_is("pointer_type"):
            return self.dereference().get_address()
        if type.name == "float":
            return float(struct.unpack("f", value_bytes)[0])
        elif type.name == "double":
            return float(struct.unpack("d", value_bytes)[0])
        elif type.name == "bool":
            return bool(int.from_bytes(value_bytes, byteorder="little"))
        else:
            return int.from_bytes(value_bytes, byteorder="little")

    def write_value(self, value: int | float | bool, check_data_loss: bool = True) -> None:
        # Check that type_die is a basic type
        type = self.__type_die
        if not type.tag_is("base_type") and not type.tag_is("enumeration_type"):
            raise Exception(f"ERROR: {type.name} is not a base type")

        # If it is an enumeration type, treat it as its underlying base type
        while type.tag_is("enumeration_type"):
            type = type.resolved_type

        # Convert the value to bytes
        assert type.size is not None
        if type.name == "float":
            value_bytes = struct.pack("f", value)
            if len(value_bytes) > type.size:
                value_bytes = value_bytes[: type.size]
            if check_data_loss:
                # Verify no data loss
                unpacked_value = struct.unpack("f", value_bytes)[0]
                if unpacked_value != value:
                    raise Exception(f"ERROR: Data loss when writing float value {value} to variable")
        elif type.name == "double":
            value_bytes = struct.pack("d", value)
            if len(value_bytes) > type.size:
                value_bytes = value_bytes[: type.size]
            if check_data_loss:
                # Verify no data loss
                unpacked_value = struct.unpack("d", value_bytes)[0]
                if unpacked_value != value:
                    raise Exception(f"ERROR: Data loss when writing double value {value} to variable")
        elif type.name == "bool":
            value_bytes = (1 if value else 0).to_bytes(type.size, byteorder="little")
        else:
            value_bytes = int(value).to_bytes(type.size, byteorder="little")
            if check_data_loss:
                # Verify no data loss
                unpacked_value = int.from_bytes(value_bytes, byteorder="little")
                if unpacked_value != value:
                    raise Exception(f"ERROR: Data loss when writing integer value {value} to variable")

        # Write the value to memory
        self.__mem_access.write(self.__address, value_bytes)

    def __eq__(self, other) -> bool:
        """
        Compare the ElfVariable's value with another value.
        For base types, compares the actual value.
        For arrays, compares element-by-element with the other sequence.
        """
        # For arrays, compare element-by-element
        if self.__type_die.tag_is("array_type"):
            if hasattr(other, "__len__") and hasattr(other, "__getitem__"):
                try:
                    if len(self) != len(other):
                        return False
                    # Compare each element
                    for i in range(len(self)):
                        if self[i] != other[i]:
                            return False
                    return True
                except TypeError:
                    return False  # Type incompatible during comparison
            return False

        # For base types, compare values
        try:
            return bool(self.read_value() == other)
        except TypeError:
            return False  # Type incompatible
        # Let memory access and other errors propagate

    def __lt__(self, other) -> bool:
        """
        Less than comparison. Works with base types only.
        """
        try:
            return bool(self.read_value() < other)
        except TypeError:
            return NotImplemented

    def __le__(self, other) -> bool:
        """Less than or equal comparison."""
        return bool(self < other) or self == other

    def __gt__(self, other) -> bool:
        """
        Greater than comparison. Works with base types only.
        """
        try:
            return bool(self.read_value() > other)
        except TypeError:
            return NotImplemented

    def __ge__(self, other) -> bool:
        """Greater than or equal comparison."""
        return bool(self > other) or self == other

    # Arithmetic operators
    def __add__(self, other):
        """Addition operator."""
        try:
            return self.read_value() + other
        except TypeError:
            return NotImplemented

    def __radd__(self, other):
        """Reverse addition operator."""
        try:
            return other + self.read_value()
        except TypeError:
            return NotImplemented

    def __sub__(self, other):
        """Subtraction operator."""
        try:
            return self.read_value() - other
        except TypeError:
            return NotImplemented

    def __rsub__(self, other):
        """Reverse subtraction operator."""
        try:
            return other - self.read_value()
        except TypeError:
            return NotImplemented

    def __mul__(self, other):
        """Multiplication operator."""
        try:
            return self.read_value() * other
        except TypeError:
            return NotImplemented

    def __rmul__(self, other):
        """Reverse multiplication operator."""
        try:
            return other * self.read_value()
        except TypeError:
            return NotImplemented

    def __truediv__(self, other):
        """Division operator."""
        try:
            return self.read_value() / other
        except TypeError:
            return NotImplemented

    def __rtruediv__(self, other):
        """Reverse division operator."""
        try:
            return other / self.read_value()
        except TypeError:
            return NotImplemented

    def __floordiv__(self, other):
        """Floor division operator."""
        try:
            return self.read_value() // other
        except TypeError:
            return NotImplemented

    def __rfloordiv__(self, other):
        """Reverse floor division operator."""
        try:
            return other // self.read_value()
        except TypeError:
            return NotImplemented

    def __mod__(self, other):
        """Modulo operator."""
        try:
            return self.read_value() % other
        except TypeError:
            return NotImplemented

    def __rmod__(self, other):
        """Reverse modulo operator."""
        try:
            return other % self.read_value()
        except TypeError:
            return NotImplemented

    def __pow__(self, other):
        """Power operator."""
        try:
            return self.read_value() ** other
        except TypeError:
            return NotImplemented

    def __rpow__(self, other):
        """Reverse power operator."""
        try:
            return other ** self.read_value()
        except TypeError:
            return NotImplemented

    # Bitwise operators (for integers and booleans)
    def __and__(self, other):
        """Bitwise AND operator."""
        try:
            value = self.read_value()
            if isinstance(value, (int, bool)):
                return value & other
        except TypeError:
            pass
        return NotImplemented

    def __rand__(self, other):
        """Reverse bitwise AND operator."""
        try:
            value = self.read_value()
            if isinstance(value, (int, bool)):
                return other & value
        except TypeError:
            pass
        return NotImplemented

    def __or__(self, other):
        """Bitwise OR operator."""
        try:
            value = self.read_value()
            if isinstance(value, (int, bool)):
                return value | other
        except TypeError:
            pass
        return NotImplemented

    def __ror__(self, other):
        """Reverse bitwise OR operator."""
        try:
            value = self.read_value()
            if isinstance(value, (int, bool)):
                return other | value
        except TypeError:
            pass
        return NotImplemented

    def __xor__(self, other):
        """Bitwise XOR operator."""
        try:
            value = self.read_value()
            if isinstance(value, (int, bool)):
                return value ^ other
        except TypeError:
            pass
        return NotImplemented

    def __rxor__(self, other):
        """Reverse bitwise XOR operator."""
        try:
            value = self.read_value()
            if isinstance(value, (int, bool)):
                return other ^ value
        except TypeError:
            pass
        return NotImplemented

    def __lshift__(self, other):
        """Left shift operator."""
        try:
            value = self.read_value()
            if isinstance(value, int):
                return value << other
        except TypeError:
            pass
        return NotImplemented

    def __rlshift__(self, other):
        """Reverse left shift operator."""
        try:
            value = self.read_value()
            if isinstance(value, int):
                return other << value
        except TypeError:
            pass
        return NotImplemented

    def __rshift__(self, other):
        """Right shift operator."""
        try:
            value = self.read_value()
            if isinstance(value, int):
                return value >> other
        except TypeError:
            pass
        return NotImplemented

    def __rrshift__(self, other):
        """Reverse right shift operator."""
        try:
            value = self.read_value()
            if isinstance(value, int):
                return other >> value
        except TypeError:
            pass
        return NotImplemented

    # Unary operators
    def __neg__(self):
        """Unary negation operator."""
        return -self.read_value()

    def __pos__(self):
        """Unary positive operator."""
        return +self.read_value()

    def __abs__(self):
        """Absolute value operator."""
        return abs(self.read_value())

    def __invert__(self):
        """Bitwise inversion operator."""
        value = self.read_value()
        if isinstance(value, (int, bool)):
            return ~value
        raise TypeError(f"bad operand type for unary ~: '{type(value).__name__}'")

    def __index__(self) -> int:
        """
        Allow ElfVariable to be used as an index in sequences (lists, tuples, etc.)
        This enables usage like: a[elf_var] instead of a[elf_var.value()]
        """
        value = self.read_value()
        if isinstance(value, int):
            return value
        elif isinstance(value, bool):
            return int(value)  # Convert bool to int (True -> 1, False -> 0)
        elif isinstance(value, float):
            if value.is_integer():
                return int(value)
        raise TypeError(f"ElfVariable '{self}' cannot be used as an index")

    def __str__(self) -> str:
        """
        String representation of the ElfVariable's value
        This enables usage like: str(elf_var) instead of str(elf_var.value())
        """
        try:
            value = self.read_value()
            if self.__type_die.tag_is("enumeration_type"):
                for entry in self.__type_die.iter_children():
                    if entry.value == value and entry.path is not None:
                        return str(entry.path)
            return str(value)
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
            value_info = f", value={self.read_value()!r}"
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
            return hash(self.read_value())
        except Exception:
            return hash((self.__type_die.offset, self.__address))

    def __format__(self, format_spec: str) -> str:
        """
        Enable formatted string representation of the ElfVariable's value.
        This allows usage like: format(elf_var, 'x') for hexadecimal formatting.
        """
        try:
            value = self.read_value()
            return format(value, format_spec)
        except Exception:
            # If get_value() fails, fall back to default string representation
            return str(self)

    def get_address(self) -> int:
        return self.__address

    def get_size(self) -> int:
        assert self.__type_die.size is not None
        return self.__type_die.size

    def read_bytes(self) -> bytes:
        return self.__mem_access.read(self.__address, self.get_size())

    def read(self) -> "ElfVariable":
        if self.__type_die.tag_is("pointer_type"):
            return self.dereference().read()
        data = self.read_bytes()
        address = self.__address
        return ElfVariable(self.__type_die, address, CachedReadMemoryAccess(address, data, self.__mem_access))
