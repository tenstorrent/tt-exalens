# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Device-free tests that objects obtained from an ElfFile keep it alive."""
import gc
import os
import subprocess
import sys
import textwrap
import unittest

from test.ttexalens.unit_tests.compiled_elf import compile_elf
from ttexalens.elf import ElfFile, ElfSection

SOURCE = """
struct Inner { int x; int y; };
struct Outer { Inner inner; unsigned value; };
volatile Outer g_outer = {{1, 2}, 0x12345678};
volatile int g_value = 0x12345678;
int main() { return g_value + g_outer.inner.x; }
"""

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Runs in a child process: a use of freed DWARF state can crash the interpreter.
# Every scenario drops the ElfFile right after the lookup, collects garbage and
# churns memory by parsing other ELFs before using what the lookup returned.
_SCENARIO_PRELUDE = """
import gc, sys
from ttexalens.elf import ElfFile
from ttexalens.memory_access import NoMemoryAccess
from test.ttexalens.unit_tests.compiled_elf import ElfImageMemoryAccess
path = sys.argv[1]
memory = ElfImageMemoryAccess(ElfFile(path))

def churn():
    gc.collect()
    others = [ElfFile(path) for _ in range(20)]
    for other in others:
        other.dwarf_info.get_die_by_name("g_outer")
    del others
    gc.collect()
"""


def text_section(elf: ElfFile) -> ElfSection:
    section = elf.get_section_by_name(".text")
    assert section is not None
    return section


class TestElfFileLifetime(unittest.TestCase):
    def run_scenario(self, body: str) -> str:
        script = _SCENARIO_PRELUDE + textwrap.dedent(body)
        env = dict(os.environ, PYTHONPATH=_REPO_ROOT)
        result = subprocess.run(
            [sys.executable, "-c", script, compile_elf(SOURCE)], capture_output=True, text=True, env=env, cwd=_REPO_ROOT
        )
        self.assertEqual(result.returncode, 0, f"stdout: {result.stdout}\nstderr: {result.stderr}")
        return result.stdout.strip()

    def test_global_variable_outlives_elf_file(self):
        out = self.run_scenario(
            """
            var = ElfFile(path).get_global("g_outer", memory)
            churn()
            print(var.inner.y.read_value(), hex(var.value.read_value()), var.get_type_die().get_readable_name())
            """
        )
        self.assertEqual(out, "2 0x12345678 Outer")

    def test_die_outlives_elf_file(self):
        out = self.run_scenario(
            """
            die = ElfFile(path).find_die_by_name("g_outer")
            churn()
            print(die.get_resolved_type().get_readable_name())
            """
        )
        self.assertEqual(out, "Outer")

    def test_dwarf_info_die_and_children_outlive_elf_file(self):
        out = self.run_scenario(
            """
            struct = ElfFile(path).dwarf_info.get_die_by_name("Outer")
            children = struct.iter_children()
            del struct
            churn()
            print(",".join(child.name for child in children))
            """
        )
        self.assertEqual(out, "inner,value")

    def test_type_die_outlives_variable(self):
        out = self.run_scenario(
            """
            type_die = ElfFile(path).get_global("g_outer", memory).inner.get_type_die()
            churn()
            print(type_die.get_readable_name(), type_die.get_size())
            """
        )
        self.assertEqual(out, "Inner 8")

    def test_frame_description_outlives_elf_file(self):
        out = self.run_scenario(
            """
            elf = ElfFile(path)
            pc = elf.find_symbol_by_name("main").value
            fde = elf.get_frame_description(pc, NoMemoryAccess.instance())
            del elf
            churn()
            print(fde.get_return_address_register())
            """
        )
        self.assertEqual(out, "1")

    def test_compile_unit_die_outlives_elf_file(self):
        out = self.run_scenario(
            """
            unit_die = ElfFile(path).find_die_by_name("g_outer").cu.die
            churn()
            print(unit_die.tag.name, unit_die.get_first_child() is not None)
            """
        )
        self.assertEqual(out, "compile_unit True")

    def test_section_data_outlives_elf_file(self):
        path = compile_elf(SOURCE)
        with open(path, "rb") as f:
            reference = ElfFile.from_bytes(f.read(), path)
        expected = bytes(text_section(reference).data)
        self.assertGreater(len(expected), 0)

        # Neither the ElfFile nor the ElfSection is referenced after this line.
        data = text_section(ElfFile(path)).data
        gc.collect()
        # Parse other ELFs and allocate buffers so that freed memory gets reused.
        others = [ElfFile(path) for _ in range(50)]
        filler = [bytearray(b"\xaa" * len(expected)) for _ in range(2000)]
        self.assertEqual(bytes(data), expected)
        self.assertIsNotNone(data.obj, "memoryview must own a reference that keeps the section bytes alive")
        del others, filler

    def test_section_data_is_read_only_and_matches_size(self):
        elf = ElfFile(compile_elf(SOURCE))
        section = text_section(elf)
        data = section.data
        self.assertIsInstance(data, memoryview)
        self.assertTrue(data.readonly)
        self.assertEqual(len(data), section.size)
        self.assertEqual(data.format, "B")
        bss = elf.get_section_by_name(".bss")
        if bss is not None:
            self.assertEqual(len(bss.data), 0)


if __name__ == "__main__":
    unittest.main()
