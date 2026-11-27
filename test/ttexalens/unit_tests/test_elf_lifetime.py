# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import ast
import gc
import os
import subprocess
import sys
import unittest

from parameterized import parameterized

from ttexalens.elf import ElfFile, get_frame_callstack
from ttexalens.memory_access import NO_MEMORY_ACCESS, MemoryAccess

GLOBALS_ELF = "build/riscv-src/blackhole/globals_test.release.brisc.elf"
CALLSTACK_ELF = "build/riscv-src/blackhole/callstack.debug.brisc.elf"


class PatternMemoryAccess(MemoryAccess):
    def read(self, address: int, buffer: memoryview | bytearray) -> None:
        buffer[:] = bytes((address + i) & 0xFF for i in range(len(buffer)))


def die_key(die):
    return die.name, die.tag.name, die.offset


def filter_arguments(die, name):
    arguments = []

    def collect(child):
        arguments.append(child)
        return True

    die.find_child_by_name(name, collect)
    return arguments


CASES = {
    "variable": (
        GLOBALS_ELF,
        lambda elf: elf.get_global("g_global_struct", PatternMemoryAccess()),
        lambda variable: [
            variable.d[1].x.read_value(),
            variable.get_type_die().name,
            variable.d[1].get_type_die().name,
        ],
    ),
    "die": (
        GLOBALS_ELF,
        lambda elf: elf.find_die_by_name("g_global_struct"),
        lambda die: [
            die_key(die.get_resolved_type()),
            die_key(die.cu.die),
            [die_key(child) for child in die.get_resolved_type().iter_children()],
        ],
    ),
    "dwarf_info_die": (
        GLOBALS_ELF,
        lambda elf: elf.dwarf_info.get_die_by_name("g_global_struct"),
        die_key,
    ),
    "function_die": (
        GLOBALS_ELF,
        lambda elf: elf.dwarf_info.find_function_by_address(elf.find_symbol_by_name("main").value),
        die_key,
    ),
    "children_iterator": (
        GLOBALS_ELF,
        lambda elf: elf.find_die_by_name("g_global_struct").get_resolved_type().iter_children(),
        lambda children: [die_key(child) for child in children],
    ),
    "filter_argument": (
        GLOBALS_ELF,
        lambda elf: filter_arguments(elf.find_die_by_name("g_global_struct").get_resolved_type(), "d"),
        lambda dies: [die_key(die) for die in dies],
    ),
    "compile_unit": (
        GLOBALS_ELF,
        lambda elf: elf.find_die_by_name("g_global_struct").cu,
        lambda unit: die_key(unit.die),
    ),
    "compile_unit_iterator": (
        GLOBALS_ELF,
        lambda elf: elf.dwarf_info.iter_compile_units(),
        lambda units: [die_key(unit.die) for unit in units],
    ),
    "section_data": (
        GLOBALS_ELF,
        lambda elf: elf.get_section_by_name(".text").data,
        lambda data: bytes(data),
    ),
    "section_data_slice": (
        GLOBALS_ELF,
        lambda elf: elf.get_section_by_name(".text").data[4:20],
        lambda data: bytes(data),
    ),
    "section_iterator": (
        GLOBALS_ELF,
        lambda elf: elf.iter_sections(),
        lambda sections: [section.name for section in sections],
    ),
    "frame_description": (
        CALLSTACK_ELF,
        lambda elf: elf.get_frame_description(elf.find_symbol_by_name("main").value, NO_MEMORY_ACCESS),
        lambda frame: frame.get_return_address_register(),
    ),
    "callstack": (
        CALLSTACK_ELF,
        lambda elf: get_frame_callstack(
            [elf], elf.dwarf_info.find_symbol_by_demangled_name("tail_multi_test::leaf_pos(int)").value
        ),
        lambda entries: [
            (entry.function_name, [(argument.name, argument.type.name) for argument in entry.arguments])
            for entry in entries
        ],
    ),
}


def open_file_count(path):
    target = os.path.realpath(path)
    return sum(os.path.realpath(f"/proc/self/fd/{fd}") == target for fd in os.listdir("/proc/self/fd"))


def held_and_released(case):
    path, get, read = CASES[case]
    elf = ElfFile(path)
    held = read(get(elf))
    del elf
    objects = get(ElfFile(path))
    released = read(objects)
    del objects
    gc.collect()
    return held, released, open_file_count(path)


class TestElfObjectLifetime(unittest.TestCase):
    @parameterized.expand(CASES)
    def test_object_after_elf_release(self, case):
        result = subprocess.run(
            [sys.executable, "-c", f"from {__name__} import held_and_released; print(held_and_released({case!r}))"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        held, released, open_files = ast.literal_eval(result.stdout)
        self.assertTrue(held)
        self.assertEqual(held, released)
        self.assertEqual(0, open_files)
