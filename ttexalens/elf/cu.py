# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from elftools.dwarf.compileunit import CompileUnit as DWARF_CU
from elftools.dwarf.die import DIE as DWARF_DIE
from elftools.dwarf.dwarf_expr import DWARFExprParser
from elftools.dwarf.lineprogram import LineProgram
from functools import cached_property
from ttexalens.elf.die import ElfDie
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttexalens.elf.dwarf import ElfDwarf


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
    def line_program(self) -> LineProgram:
        line_program = self.dwarf.dwarf.line_program_for_CU(self.dwarf_cu)
        assert line_program is not None
        return line_program

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

    def find_DIE_that_specifies(self, die: ElfDie):
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
