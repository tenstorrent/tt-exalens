# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from elftools.dwarf.compileunit import CompileUnit as DWARF_CU
from elftools.dwarf.die import DIE as DWARF_DIE
from elftools.dwarf.dwarfinfo import DWARFInfo
from elftools.dwarf.locationlists import LocationParser
from functools import cache, cached_property
import os
from ttexalens.elf.cu import ElfCompileUnit
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttexalens.elf.parsed import ParsedElfFile
    from ttexalens.elf.die import ElfDie


class ElfLocationParser:
    def __init__(self, dwarf: ElfDwarf):
        self.dwarf = dwarf
        self._location_parser = LocationParser(dwarf.location_lists)

    def parse_from_attribute(self, location_attribute, die: ElfDie):
        with self.dwarf.parsed_elf._lock:
            return self._location_parser.parse_from_attribute(location_attribute, die.cu.version, die.dwarf_die)


class ElfDwarf:
    def __init__(self, dwarf: DWARFInfo, parsed_elf: ParsedElfFile):
        self.dwarf = dwarf
        self.parsed_elf = parsed_elf
        self._cus: dict[int, ElfCompileUnit] = {}

    @cached_property
    def range_lists(self):
        with self.parsed_elf._lock:
            return self.dwarf.range_lists()

    @cached_property
    def location_lists(self):
        with self.parsed_elf._lock:
            return self.dwarf.location_lists()

    @cached_property
    def location_parser(self):
        return ElfLocationParser(self)

    @cached_property
    def cfi_entries(self):
        with self.parsed_elf._lock:
            if self.dwarf.has_CFI():
                return self.dwarf.CFI_entries()
            else:
                return []

    def get_cu(self, dwarf_cu: DWARF_CU):
        with self.parsed_elf._lock:
            cu = self._cus.get(id(dwarf_cu))
        if cu is None:
            with self.parsed_elf._lock:
                cu = ElfCompileUnit(self, dwarf_cu)
                self._cus[id(dwarf_cu)] = cu
        return cu

    def get_die(self, dwarf_die: DWARF_DIE):
        dwarf_cu = dwarf_die.cu
        cu = self.get_cu(dwarf_cu)
        return cu.get_die(dwarf_die)

    def iter_CUs(self):
        with self.parsed_elf._lock:
            for cu in self.dwarf.iter_CUs():
                yield self.get_cu(cu)

    @cache
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
        with self.parsed_elf._lock:
            result: list[tuple[int, int, str, int, int]] = []
            for cu in self.iter_CUs():
                lineprog = cu.line_program
                if lineprog is None:
                    continue
                delta = 1 if lineprog.header.version < 5 else 0
                previous_entry: tuple[int, str, int, int] | None = None
                for entry in lineprog.get_entries():
                    if entry.state is None:
                        continue

                    file_entry = lineprog["file_entry"][entry.state.file - delta]
                    directory = lineprog["include_directory"][file_entry.dir_index].decode("utf-8")
                    filename = file_entry.name.decode("utf-8")
                    filename = os.path.join(directory, filename)
                    line = entry.state.line
                    column = entry.state.column
                    current_entry: tuple[int, str, int, int] = (entry.state.address, filename, line, column)
                    if previous_entry is not None and previous_entry[0] != current_entry[0]:
                        result.append(
                            (
                                previous_entry[0],
                                current_entry[0],
                                previous_entry[1],
                                previous_entry[2],
                                previous_entry[3],
                            )
                        )
                    previous_entry = current_entry
                if previous_entry is not None:
                    result.append(
                        (
                            previous_entry[0],
                            previous_entry[0] + 4,
                            previous_entry[1],
                            previous_entry[2],
                            previous_entry[3],
                        )
                    )
            result.sort(key=lambda x: x[0])  # Sort by address
            return result

    def find_file_line_by_address(self, address):
        # Binary search for the address in file_lines_ranges
        file_lines_ranges = self.file_lines_ranges
        left = 0
        right = len(file_lines_ranges) - 1
        while left <= right:
            mid = (left + right) // 2
            if file_lines_ranges[mid][0] <= address < file_lines_ranges[mid][1]:
                return file_lines_ranges[mid][2], file_lines_ranges[mid][3], file_lines_ranges[mid][4]
            elif address < file_lines_ranges[mid][0]:
                right = mid - 1
            else:
                left = mid + 1
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
