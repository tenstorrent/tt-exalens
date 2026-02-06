# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import cxxfilt
from elftools.dwarf.die import DIE as DWARF_DIE
from elftools.dwarf.dwarf_expr import DWARFExprOp
from elftools.dwarf.locationlists import (
    LocationExpr,
    LocationEntry as ListLocationEntry,
    BaseAddressEntry as ListBaseAddressEntry,
)
from elftools.dwarf.ranges import BaseAddressEntry, RangeEntry
from functools import cached_property
import os
import re
import ttexalens.util as util
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ttexalens.elf.cu import ElfCompileUnit
    from ttexalens.elf.frame import FrameInspection
    from ttexalens.elf.variable import ElfVariable


# We only care about the stuff we can use for probing the memory
IGNORE_TAGS = set(
    [
        "DW_TAG_compile_unit",
        "DW_TAG_formal_parameter",
        "DW_TAG_unspecified_parameters",
    ]
)


def strip_DW_(s):
    """
    Removes DW_AT_, DW_TAG_ and other DW_* prefixes from the string
    """
    return re.sub(r"^DW_[^_]*_", "", s)


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
            util.DEBUG(f"Don't know how to categorize tag: {self.tag}")
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
                return die.path  # type: ignore

        if parent and parent.tag != "DW_TAG_compile_unit":
            parent_path = parent.path
            return f"{parent_path}::{name}"

        return name

    @cached_property
    def resolved_type(self) -> "ElfDie":
        """
        Resolve to underlying type
        """
        # TODO: test typedefs, this looks overly complicated
        if self.tag == "DW_TAG_typedef" and self.local_offset != None:
            typedef_DIE = self.cu.find_DIE_at_local_offset(self.local_offset)
            if typedef_DIE:  # If typedef, recursivelly do it
                return typedef_DIE.resolved_type  # type: ignore
        elif self.tag == "DW_TAG_const_type" and self.local_offset != None:
            typedef_DIE = self.cu.find_DIE_at_local_offset(self.local_offset)
            if typedef_DIE:  # If typedef, recursivelly do it
                return typedef_DIE.resolved_type  # type: ignore
        elif self.tag == "DW_TAG_volatile_type" and self.local_offset != None:
            typedef_DIE = self.cu.find_DIE_at_local_offset(self.local_offset)
            if typedef_DIE:  # If typedef, recursivelly do it
                return typedef_DIE.resolved_type  # type: ignore
        elif self.category != "type" and "DW_AT_type" in self.attributes and self.local_offset != None:
            type_die = self.cu.find_DIE_at_local_offset(self.local_offset)
            if type_die is not None:
                if (
                    type_die.tag == "DW_TAG_typedef"
                    or type_die.tag == "DW_TAG_const_type"
                    or type_die.tag == "DW_TAG_volatile_type"
                ):
                    return type_die.resolved_type  # type: ignore
                return type_die  # type: ignore
        elif "DW_AT_specification" in self.attributes:
            dwarf_die = self.dwarf_die.get_DIE_from_attribute("DW_AT_specification")
            die = self.cu.dwarf.get_die(dwarf_die)
            if die is not None:
                return die.resolved_type  # type: ignore
        elif "DW_AT_abstract_origin" in self.attributes:
            dwarf_die = self.dwarf_die.get_DIE_from_attribute("DW_AT_abstract_origin")
            die = self.cu.dwarf.get_die(dwarf_die)
            if die is not None:
                return die.resolved_type  # type: ignore
        elif self.tag_is("enumeration_type"):
            if "DW_AT_type" in self.attributes and self.local_offset is not None:
                type_die = self.cu.find_DIE_at_local_offset(self.local_offset)
                if type_die is not None:
                    return type_die.resolved_type  # type: ignore
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
            return self.attributes["DW_AT_byte_size"].value  # type: ignore

        if self.tag == "DW_TAG_pointer_type":
            return 4  # Assuming 32-bit pointer

        if self.tag == "DW_TAG_array_type":
            array_size: int = 1
            for child in self.iter_children():
                if "DW_AT_upper_bound" in child.attributes:
                    upper_bound = child.attributes["DW_AT_upper_bound"].value
                    array_size *= upper_bound + 1
            elem_die = self.cu.find_DIE_at_local_offset(self.local_offset)
            if elem_die is not None:
                elem_size: int | None = elem_die.size
                if elem_size is not None:
                    return array_size * elem_size

        if "DW_AT_type" in self.attributes:
            type_die = self.cu.find_DIE_at_local_offset(self.local_offset)
            if type_die is not None:
                return type_die.size  # type: ignore

        # Try to find size from symbol table
        if self.name in self.cu.dwarf.parsed_elf.symbols:
            return self.cu.dwarf.parsed_elf.symbols[self.name].size  # type: ignore

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
        elif "DW_AT_low_pc" in self.attributes:
            addr = self.attributes["DW_AT_low_pc"].value
        else:
            location_attribute = self.attributes.get("DW_AT_location")
            location_parser = self.cu.dwarf.location_parser
            if location_attribute:
                location = location_parser.parse_from_attribute(location_attribute, self.cu.version, self.dwarf_die)
                if isinstance(location, LocationExpr):
                    parsed = self.cu.expression_parser.parse_expr(location.loc_expr)
                    _, addr = self._evaluate_location_expression(parsed, frame_inspection=None)
                elif isinstance(location, list):
                    # We have list of expressions. All need to be evaluated and applied in order to get to location value.
                    # This list is usually used for location ranges, so we need to have PC in order to evaluate them properly.
                    # We don't have it here, so we don't attempt to evaluate location lists.
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
                    return self.attributes["DW_AT_const_value"].value  # type: ignore
                else:
                    # Try to find address from symbol table
                    if self.name in self.cu.dwarf.parsed_elf.symbols:
                        return self.cu.dwarf.parsed_elf.symbols[self.name].value  # type: ignore
                    else:
                        util.DEBUG(f"ERROR: Cannot find address for {self}")
        return addr

    @cached_property
    def value(self):
        """
        Return the value of the DIE
        """
        if "DW_AT_const_value" in self.attributes:
            return self.attributes["DW_AT_const_value"].value
        if "DW_AT_const_expr" in self.attributes:
            return self.attributes["DW_AT_const_expr"].value
        if "DW_AT_abstract_origin" in self.attributes:
            die = self.get_DIE_from_attribute("DW_AT_abstract_origin")
            if die is not None:
                return die.value
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
        name: str | None
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
    def address_ranges(self) -> list[tuple[int, int, bool]]:
        if "DW_AT_low_pc" in self.attributes and "DW_AT_high_pc" in self.attributes:
            return [
                (
                    self.attributes["DW_AT_low_pc"].value,
                    self.attributes["DW_AT_low_pc"].value + self.attributes["DW_AT_high_pc"].value,
                    True,
                )
            ]
        elif "DW_AT_ranges" in self.attributes:
            assert self.cu.dwarf.range_lists is not None
            ranges = self.cu.dwarf.range_lists.get_range_list_at_offset(self.attributes["DW_AT_ranges"].value)
            address_ranges = []
            base_address = None
            parent = self
            while parent is not None:
                if "DW_AT_low_pc" in parent.attributes:
                    base_address = parent.attributes["DW_AT_low_pc"].value
                    break
                parent = parent.parent
            if base_address is None:
                base_address = self.cu.top_DIE.address
            for r in ranges:
                if isinstance(r, BaseAddressEntry):
                    base_address = r.base_address
                elif isinstance(r, RangeEntry):
                    if r.is_absolute:
                        address_ranges.append((r.begin_offset, r.end_offset, True))
                    elif base_address is None:
                        address_ranges.append((r.begin_offset, r.end_offset, False))
                    else:
                        address_ranges.append((r.begin_offset + base_address, r.end_offset + base_address, True))
            return address_ranges
        else:
            child_ranges = []
            for child in self.iter_children():
                child_ranges.extend(child.address_ranges)
            return child_ranges

    @cached_property
    def decl_file_info(self):
        file = None
        line = None
        column = None
        if "DW_AT_decl_file" in self.attributes:
            if self.cu.line_program is not None:
                file_entry = self.cu.line_program["file_entry"][self.attributes["DW_AT_decl_file"].value]
                directory = self.cu.line_program["include_directory"][file_entry.dir_index].decode("utf-8")
                file = file_entry.name.decode("utf-8")
                file = os.path.join(directory, file)
        if "DW_AT_decl_line" in self.attributes:
            line = self.attributes["DW_AT_decl_line"].value
        if "DW_AT_decl_column" in self.attributes:
            column = self.attributes["DW_AT_decl_column"].value
        if file is None and line is None and column is None and "DW_AT_abstract_origin" in self.attributes:
            die = self.get_DIE_from_attribute("DW_AT_abstract_origin")
            if die is not None:
                return die.decl_file_info
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

    ###########################################
    # Propertied for debugging and inspection #
    ###########################################

    @cached_property
    def _children(self):
        return list(self.iter_children())

    @cached_property
    def _location(self):
        """
        Return the location expression of the DIE
        """
        if "DW_AT_location" in self.attributes:
            location_attribute = self.attributes["DW_AT_location"]
            location_parser = self.cu.dwarf.location_parser
            location = location_parser.parse_from_attribute(location_attribute, self.cu.version, self.dwarf_die)
            return location
        return None

    @cached_property
    def _parsed_attributes(self):
        parsed_attributes = {}
        for attr_name, attr in self.attributes.items():
            value = attr
            if attr_name == "DW_AT_abstract_origin":
                value = self.get_DIE_from_attribute(attr_name)
                if value is None:
                    value = "[unresolvable]"
            elif attr_name == "DW_AT_artificial":
                value = attr.value
            elif attr_name == "DW_AT_byte_size":
                value = attr.value
            elif attr_name == "DW_AT_call_column":
                value = attr.value
            elif attr_name == "DW_AT_call_file":
                assert self.cu.line_program is not None
                file_entry = self.cu.line_program["file_entry"][attr.value]
                directory = self.cu.line_program["include_directory"][file_entry.dir_index].decode("utf-8")
                value = file_entry.name.decode("utf-8")
                value = os.path.join(directory, value)
            elif attr_name == "DW_AT_call_line":
                value = attr.value
            elif attr_name == "DW_AT_const_value":
                value = attr.value
            elif attr_name == "DW_AT_data_member_location":
                value = attr.value
            elif attr_name == "DW_AT_decl_column":
                value = attr.value
            elif attr_name == "DW_AT_decl_file":
                assert self.cu is not None and self.cu.line_program is not None
                file_entry = self.cu.line_program["file_entry"][attr.value]
                directory = self.cu.line_program["include_directory"][file_entry.dir_index].decode("utf-8")
                value = file_entry.name.decode("utf-8")
                value = os.path.join(directory, value)
            elif attr_name == "DW_AT_decl_line":
                value = attr.value
            elif attr_name == "DW_AT_high_pc":
                value = attr.value
            elif attr_name == "DW_AT_linkage_name":
                value = attr.value
                try:
                    value = cxxfilt.demangle(value.decode("utf-8"))
                except:
                    pass
            elif attr_name == "DW_AT_location":
                value = self.cu.dwarf.location_parser.parse_from_attribute(attr, self.cu.version, self.dwarf_die)
            elif attr_name == "DW_AT_low_pc":
                value = attr.value
            elif attr_name == "DW_AT_name":
                value = self.attributes["DW_AT_name"].value
                if value is not None:
                    value = value.decode("utf-8")
                else:
                    value = None
            elif attr_name == "DW_AT_ranges":
                assert self.cu.dwarf.range_lists is not None
                value = self.cu.dwarf.range_lists.get_range_list_at_offset(attr.value)
            elif attr_name == "DW_AT_specification":
                value = self.get_DIE_from_attribute(attr_name)
                if value is None:
                    value = "[unresolvable]"
            elif attr_name == "DW_AT_type":
                value = self.cu.find_DIE_at_local_offset(attr.value)
                if value is None:
                    value = "[unresolvable]"
            elif attr_name == "DW_AT_upper_bound":
                value = attr.value
            parsed_attributes[attr_name] = value
        return parsed_attributes

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

    def read_value(self, frame_inspection: FrameInspection | None) -> ElfVariable | None:
        """
        Read the value of the variable represented by this DIE using the provided frame inspection context.
        """
        from ttexalens.elf.variable import ElfVariable
        from ttexalens.memory_access import FixedMemoryAccess

        # TODO: Check if it is variable (global, local, member, argument)
        if not self.tag_is("formal_parameter") and not self.tag_is("variable"):
            return None

        util.DEBUG(f"Evaluating location expression for variable: {self.name}")

        # Get the type of the variable
        variable_type = self.resolved_type
        if variable_type is None or variable_type is self:
            util.DEBUG("    Could not resolve type for variable")
            # We failed to resolve type
            return None

        # Check if we have constant value
        const_value = self.value
        if const_value is not None:
            util.DEBUG(f"  Trying to read constant value: {const_value}")
            if isinstance(const_value, bytes):
                memory = const_value
            else:
                try:
                    const_value = int(const_value)
                    size = variable_type.size if variable_type.size is not None else 4
                    memory = const_value.to_bytes(size, byteorder="little")
                except Exception:
                    util.DEBUG("    Failed to convert constant value to integer")
                    return None

            # We explicitly set address to 0 to indicate that this is not an addressable variable
            return ElfVariable(variable_type, 0, FixedMemoryAccess(memory))

        # If we don't have frame inspection, we can't read the value
        if frame_inspection is None:
            util.DEBUG("    No frame inspection provided")
            return None

        # Check if we have address
        if self.address is not None:
            util.DEBUG(f"    Reading variable from address: {hex(self.address)}")
            return ElfVariable(variable_type, self.address, frame_inspection.mem_access)

        # Check if we have location
        location = self._location
        if location is None:
            util.DEBUG("    No location information available for variable")
            return None

        # Get parsed location expression
        if isinstance(location, LocationExpr):
            parsed_expression = self.cu.expression_parser.parse_expr(location.loc_expr)
            util.DEBUG(f"    {parsed_expression}")
        elif isinstance(location, list):
            base_address = 0
            pc = frame_inspection.pc + frame_inspection.loaded_offset
            parsed_expression = None
            for loc in location:
                util.DEBUG(f"  Looking at location entry: {loc}")
                if isinstance(loc, ListBaseAddressEntry):
                    base_address = loc.base_address
                elif isinstance(loc, ListLocationEntry):
                    if loc.is_absolute:
                        begin_offset = loc.begin_offset
                        end_offset = loc.end_offset
                    else:
                        begin_offset = loc.begin_offset + base_address
                        end_offset = loc.end_offset + base_address
                    if begin_offset <= pc < end_offset:
                        util.DEBUG(f"  Found matching location entry for PC: {hex(pc)}")
                        parsed_expression = self.cu.expression_parser.parse_expr(loc.loc_expr)
            if parsed_expression is None:
                util.DEBUG(f"    No matching location entry found for current PC: {hex(pc)}")
                return None
        else:
            # Unknown location type
            util.DEBUG("    Unknown location type for variable")
            return None

        # Evaluate expression to get value
        is_address, value = self._evaluate_location_expression(parsed_expression, frame_inspection)
        if value is None:
            return None
        if is_address:
            assert isinstance(value, int)
            return ElfVariable(variable_type, value, frame_inspection.mem_access)
        else:
            if isinstance(value, bytes):
                memory = value
            else:
                try:
                    value = int(value)
                    size = variable_type.size if variable_type.size is not None else 4
                    memory = value.to_bytes(size, byteorder="little")
                except Exception:
                    return None

            # We explicitly set address to 0 to indicate that this is not an addressable variable
            return ElfVariable(variable_type, 0, FixedMemoryAccess(memory))

    def _evaluate_location_expression(
        self, parsed_expression: list[DWARFExprOp], frame_inspection: FrameInspection | None = None
    ) -> tuple[bool, Any | None]:
        """
        Evaluate a DWARF location expression in the context of this DIE.

        This method delegates to the shared expression evaluator but handles
        DIE-specific operations like DW_OP_fbreg that need function DIE lookups.
        """
        from ttexalens.elf.variable import ElfVariable
        from ttexalens.memory_access import FixedMemoryAccess
        from ttexalens.elf.expression_evaluator import evaluate_dwarf_expression

        util.DEBUG(f"   {parsed_expression}")

        # Check if expression contains DW_OP_fbreg which needs special handling
        has_fbreg = any(op.op_name == "DW_OP_fbreg" for op in parsed_expression)

        if has_fbreg:
            # DW_OP_fbreg requires looking up the function's frame_base attribute
            # We need to handle this before delegating to the shared evaluator
            return self._evaluate_location_expression_with_fbreg(parsed_expression, frame_inspection)

        # Delegate to shared evaluator
        cfa = frame_inspection.cfa if frame_inspection else None
        return evaluate_dwarf_expression(parsed_expression, frame_inspection, cfa, self.cu)

    def _evaluate_location_expression_with_fbreg(
        self, parsed_expression: list[DWARFExprOp], frame_inspection: FrameInspection | None = None
    ) -> tuple[bool, Any | None]:
        """
        Evaluate location expression with DW_OP_fbreg support (requires DIE context).

        This method computes the frame_base by walking the parent DIE tree to find
        the containing function, then delegates to the shared expression evaluator.
        """
        from ttexalens.elf.expression_evaluator import evaluate_dwarf_expression

        # Find the parent function DIE that contains the frame_base attribute
        function_die = self.parent
        while (
            function_die is not None
            and not function_die.tag_is("subprogram")
            and not function_die.tag_is("inlined_function")
        ):
            function_die = function_die.parent

        if function_die is None or "DW_AT_frame_base" not in function_die.attributes:
            # No function DIE with frame_base found - can't evaluate DW_OP_fbreg
            util.DEBUG(f"DW_OP_fbreg: Could not find parent function with frame_base")
            return False, None

        # Get and evaluate the frame_base expression
        location_parser = self.cu.dwarf.location_parser
        frame_base_attribute = function_die.attributes["DW_AT_frame_base"]
        frame_base_location = location_parser.parse_from_attribute(
            frame_base_attribute, self.cu.version, self.dwarf_die
        )

        if not isinstance(frame_base_location, LocationExpr):
            # Frame base is not a simple expression
            util.DEBUG(f"DW_OP_fbreg: frame_base is not a LocationExpr")
            return False, None

        # Parse and evaluate the frame_base expression recursively
        parsed_frame_base_expression = self.cu.expression_parser.parse_expr(frame_base_location.loc_expr)
        _, frame_base = function_die._evaluate_location_expression(parsed_frame_base_expression, frame_inspection)

        if frame_base is None:
            util.DEBUG(f"DW_OP_fbreg: Failed to evaluate frame_base expression")
            return False, None

        # Now delegate to shared evaluator with the computed frame_base
        cfa = frame_inspection.cfa if frame_inspection else None
        return evaluate_dwarf_expression(parsed_expression, frame_inspection, cfa, self.cu, frame_base)
