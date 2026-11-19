# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Device-free tests for reading and writing bitfield struct members through the ELF/DWARF reader."""
import unittest

from parameterized import parameterized_class

from test.ttexalens.unit_tests.compiled_elf import ElfImageMemoryAccess, compile_elf
from ttexalens.elf import ElfFile
from ttexalens.exceptions import DataLossError, TypeMismatchError

BITFIELDS_SOURCE = """
#include <stdint.h>
enum class Mode : uint8_t { M0, M1, M2, M3 };
struct BitFields {
    unsigned a : 3;
    unsigned b : 5;
    int c : 4;
    bool flag : 1;
    Mode mode : 2;
    uint16_t e : 9;
    int8_t f : 2;
    uint32_t d;
};
volatile BitFields g_bf = {5, 17, -3, true, Mode::M2, 300, -1, 0x12345678};
int main() { return g_bf.d; }
"""

FIELDS = {"a": 5, "b": 17, "c": -3, "flag": True, "e": 300, "f": -1, "d": 0x12345678}


# DWARF 5 places a bitfield with DW_AT_data_bit_offset; DWARF 4 uses DW_AT_bit_offset counted from the
# most significant bit of the storage unit.
@parameterized_class(
    ("flags",),
    [
        (["-O0", "-g", "-gdwarf-5"],),
        (["-O2", "-g", "-gdwarf-5"],),
        (["-O0", "-g", "-gdwarf-4"],),
        (["-O2", "-g", "-gdwarf-4"],),
    ],
)
class TestDwarfBitfields(unittest.TestCase):
    flags: list[str]

    def setUp(self):
        self.elf = ElfFile(compile_elf(BITFIELDS_SOURCE, self.flags))
        self.mem = ElfImageMemoryAccess(self.elf)
        self.var = self.elf.get_global("g_bf", self.mem)

    def read_all(self) -> dict:
        return {name: self.var.get_member(name).read_value() for name in FIELDS}

    def test_read(self):
        self.assertEqual(self.read_all(), FIELDS)
        self.assertEqual(self.var.mode.read_value(), 2)
        self.assertEqual(self.var.read().c.read_value(), -3)

    def test_write_leaves_neighbours_unchanged(self):
        expected = dict(FIELDS)
        for name, value in (("b", 9), ("c", 7), ("c", -8), ("a", 0), ("e", 511), ("f", 1), ("flag", False)):
            self.var.get_member(name).write_value(value)
            expected[name] = value
            self.assertEqual(self.read_all(), expected, f"after writing {name}={value}")
        self.var.mode.write_value(3)
        self.assertEqual(self.var.mode.read_value(), 3)
        self.assertEqual(self.read_all(), expected)

    def test_write_out_of_range_raises(self):
        for name, value in (("a", 8), ("a", -1), ("c", 8), ("c", -9), ("e", 512), ("f", 2)):
            with self.assertRaises(DataLossError, msg=f"{name}={value}"):
                self.var.get_member(name).write_value(value)
        self.assertEqual(self.read_all(), FIELDS)

    def test_size_of_bitfield_raises(self):
        with self.assertRaises(TypeMismatchError):
            self.var.b.get_size()


if __name__ == "__main__":
    unittest.main()
