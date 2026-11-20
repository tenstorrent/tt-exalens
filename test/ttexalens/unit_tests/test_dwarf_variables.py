# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Device-free tests for reading and writing ELF variables through their DWARF types."""
import unittest

from test.ttexalens.unit_tests.compiled_elf import ElfImageMemoryAccess, compile_elf
from ttexalens.elf import DwarfDieTag, ElfFile
from ttexalens.exceptions import DataLossError, TypeMismatchError

from parameterized import parameterized

SOURCE = """
#include <stdint.h>

// Enums whose DW_AT_type points straight at a base type (no typedef in between).
enum class SignedEnum { NEG = -1, POS = 1 };
enum PlainEnum { PLAIN_NEG = -2, PLAIN_POS = 2 };

// A nested type with the same name as a data member, emitted before the member.
struct named_clash {
    enum class mode : unsigned char { M0, M1 };
    mode mode;
    int y;
};

struct Holder {
    SignedEnum signed_enum;
    PlainEnum plain_enum;
    named_clash clash;
    uint8_t bytes[4];
    int8_t signed_bytes[4];
    uint8_t* byte_ptr;
    char text[8];
    const char* text_ptr;
    uint64_t u64;
    int64_t i64;
    uint32_t u32;
    int32_t i32;
};

volatile Holder g_holder = {SignedEnum::NEG, PLAIN_NEG, {named_clash::mode::M1, 9}, {1, 2, 3, 4}, {-1, 2, -3, 4},
                            nullptr, "abc", nullptr, 1, -1, 1, -1};

int main() {
    g_holder.byte_ptr = const_cast<uint8_t*>(&g_holder.bytes[0]);
    g_holder.text_ptr = const_cast<const char*>(&g_holder.text[0]);
    return 0;
}
"""

FLAGS = [("O0", ["-O0", "-g"]), ("O2", ["-O2", "-g"]), ("strict_dwarf", ["-O2", "-g", "-gstrict-dwarf", "-gdwarf-4"])]


class TestDwarfVariables(unittest.TestCase):
    def load(self, flags: list[str]):
        elf = ElfFile(compile_elf(SOURCE, flags))
        # Variables do not keep their ElfFile alive; hold it for the whole test.
        self.elf = elf
        memory = ElfImageMemoryAccess(elf)
        holder = elf.get_global("g_holder", memory)
        # main() sets the pointers at run time; do the same here.
        memory.write_word(holder.byte_ptr.get_address(), holder.bytes.get_address())
        memory.write_word(holder.text_ptr.get_address(), holder.text.get_address())
        return elf, memory, holder

    @parameterized.expand(FLAGS)
    def test_enum_resolves_to_underlying_base_type(self, _name, flags):
        _, _, holder = self.load(flags)
        for member in ("signed_enum", "plain_enum"):
            enum_die = holder.get_member(member).get_type_die()
            self.assertEqual(enum_die.tag, DwarfDieTag.enumeration_type)
            resolved = enum_die.get_resolved_type()
            assert resolved is not None
            self.assertEqual(resolved.tag, DwarfDieTag.base_type)
            self.assertTrue(resolved.is_signed_type)

    @parameterized.expand(FLAGS)
    def test_signed_enum_read_and_write(self, _name, flags):
        _, _, holder = self.load(flags)
        self.assertEqual(holder.signed_enum.read_value(), -1)
        self.assertEqual(holder.plain_enum.read_value(), -2)
        holder.plain_enum.write_value(2)
        self.assertEqual(holder.plain_enum.read_value(), 2)
        holder.plain_enum.write_value(-2)
        self.assertEqual(holder.plain_enum.read_value(), -2)

    @parameterized.expand(FLAGS)
    def test_member_named_like_nested_type(self, _name, flags):
        _, _, holder = self.load(flags)
        self.assertEqual(holder.clash.mode.read_value(), 1)
        self.assertEqual(holder.clash.get_member("mode").get_address(), holder.clash.get_address())
        self.assertEqual(holder.clash.y.read_value(), 9)

    @parameterized.expand(FLAGS)
    def test_byte_arrays_and_pointers_are_not_strings(self, _name, flags):
        _, _, holder = self.load(flags)
        self.assertEqual(holder.byte_ptr.read_value(), holder.bytes.get_address())
        self.assertEqual(holder.bytes.as_value_list(), [1, 2, 3, 4])
        self.assertEqual(holder.signed_bytes.as_value_list(), [-1, 2, -3, 4])
        with self.assertRaises(TypeMismatchError):
            holder.bytes.read_value()
        with self.assertRaises(TypeMismatchError):
            holder.bytes.write_value("x")
        # Plain char arrays and pointers stay strings.
        self.assertEqual(holder.text.read_value(), "abc")
        self.assertEqual(holder.text_ptr.read_value(), "abc")

    @parameterized.expand(FLAGS)
    def test_string_with_invalid_utf8(self, _name, flags):
        _, memory, holder = self.load(flags)
        memory.write(holder.text.get_address(), b"\xffAB\x00")
        self.assertEqual(holder.text.read_value(), "�AB")
        self.assertEqual(holder.text_ptr.read_value(), "�AB")
        self.assertEqual(str(holder.text), "�AB")
        self.assertIn("\\ufffdAB", repr(holder.text).encode("unicode_escape").decode())
        # Plain char is unsigned on RISC-V.
        self.assertEqual(holder.text.as_value_list()[:3], [0xFF, ord("A"), ord("B")])

    @parameterized.expand(FLAGS)
    def test_write_out_of_range_integer_raises(self, _name, flags):
        _, _, holder = self.load(flags)
        cases = [
            (holder.u64, -1),
            (holder.u64, -1.0),
            (holder.i64, 2**64 - 1),
            (holder.i64, 2**63),
            (holder.u32, -1),
            (holder.i32, 2**64 - 1),
            (holder.i32, 2**32 - 1),
            (holder.i64, float(2**63)),
            (holder.u64, float(2**64)),
        ]
        for variable, value in cases:
            before = variable.read_value()
            with self.assertRaises(DataLossError, msg=f"{variable.get_type_die().name} <- {value}"):
                variable.write_value(value)
            self.assertEqual(variable.read_value(), before)
        # In-range values still go through.
        holder.u64.write_value(2**64 - 1)
        self.assertEqual(holder.u64.read_value(), 2**64 - 1)
        holder.i64.write_value(-(2**63))
        self.assertEqual(holder.i64.read_value(), -(2**63))
        holder.i32.write_value(-5)
        self.assertEqual(holder.i32.read_value(), -5)
        holder.u64.write_value(float(2**63))
        self.assertEqual(holder.u64.read_value(), 2**63)
        holder.u32.write_value(7.0)
        self.assertEqual(holder.u32.read_value(), 7)


if __name__ == "__main__":
    unittest.main()
