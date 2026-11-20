# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Device-free tests for reading compile-time constants from DWARF."""
import os
import unittest

from test.ttexalens.unit_tests.compiled_elf import ElfImageMemoryAccess, compile_elf
from ttexalens.elf import DwarfAttributeTag, DwarfDie, DwarfDieTag, ElfFile, FrameInspection
from ttexalens.exceptions import TypeMismatchError

from parameterized import parameterized

SOURCE = """
#include <stdint.h>

// Mirrors riscv-src/globals_test.cc: an enum and a constexpr with the same name.
enum shadowed_const : uint8_t { SHADOWED_A = 0, SHADOWED_B = 1, SHADOWED_C = 2 };
volatile enum shadowed_const g_shadowed_enum_user = SHADOWED_B;
constexpr uint8_t shadowed_const = 42;
constexpr int32_t used_constexpr = -7;
volatile int32_t g_sink;

struct K { static constexpr int member = 5; };
const int* g_member_ptr = &K::member;

int main() { g_sink = used_constexpr + shadowed_const; return 0; }
"""


def constant_die(elf: ElfFile, name: str) -> DwarfDie:
    die = elf.dwarf_info.get_die_by_name(name, lambda d: d.tag == DwarfDieTag.variable)
    assert die is not None, name
    return die


class TestDwarfConstants(unittest.TestCase):
    def test_constexpr_without_emitted_value_is_not_a_constant(self):
        # At -O0 GCC gives the constexprs storage (DW_AT_location) and only the DW_AT_const_expr flag.
        elf = ElfFile(compile_elf(SOURCE, ["-O0", "-g"]))
        for name in ("shadowed_const", "used_constexpr"):
            die = constant_die(elf, name)
            self.assertTrue(die.has_attribute(DwarfAttributeTag.const_expr))
            self.assertFalse(die.has_attribute(DwarfAttributeTag.const_value))
            with self.assertRaises(TypeMismatchError, msg=name):
                elf.get_constant(name)
            self.assertIsNone(elf.get_enum_value(name))
        # The value is still readable from the variable's storage.
        memory = ElfImageMemoryAccess(elf)
        self.assertEqual(elf.get_global("shadowed_const", memory).read_value(), 42)
        self.assertEqual(elf.get_global("used_constexpr", memory).read_value(), -7)

    def test_constexpr_read_value_uses_storage_when_no_value_emitted(self):
        elf = ElfFile(compile_elf(SOURCE, ["-O0", "-g"]))
        memory = ElfImageMemoryAccess(elf)
        variable = constant_die(elf, "shadowed_const").read_value(FrameInspection(memory))
        assert variable is not None
        self.assertEqual(variable.read_value(), 42)

    @parameterized.expand([("O0", ["-O0", "-g"]), ("O2", ["-O2", "-g"])])
    def test_emitted_constant_value(self, _name, flags):
        elf = ElfFile(compile_elf(SOURCE, flags))
        self.assertEqual(elf.get_constant("K::member"), 5)
        if constant_die(elf, "used_constexpr").has_attribute(DwarfAttributeTag.const_value):
            self.assertEqual(elf.get_constant("used_constexpr"), -7)
            self.assertEqual(elf.get_constant("shadowed_const"), 42)

    def test_globals_test_debug_build(self):
        # The firmware fixture built at -O0 has the same shadowed_const without an emitted value.
        path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "build",
            "riscv-src",
            "blackhole",
            "globals_test.debug.brisc.elf",
        )
        if not os.path.isfile(path):
            self.skipTest(f"{path} not built")
        elf = ElfFile(path)
        with self.assertRaises(TypeMismatchError):
            elf.get_constant("shadowed_const")
        self.assertIsNone(elf.get_enum_value("shadowed_const"))
        self.assertEqual(elf.get_enum_value("shadowed_const::SHADOWED_B"), 1)


if __name__ == "__main__":
    unittest.main()
