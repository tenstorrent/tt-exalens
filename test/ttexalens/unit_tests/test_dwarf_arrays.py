# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Device-free tests for array length, size, name and indexing in the ELF/DWARF reader."""
import unittest

from parameterized import parameterized_class

from test.ttexalens.unit_tests.compiled_elf import ElfImageMemoryAccess, compile_elf
from ttexalens.elf import ElfFile
from ttexalens.exceptions import TypeMismatchError

ARRAYS_SOURCE = """
#include <stdint.h>
struct ZeroLen {
    uint32_t n;
    uint32_t payload[0];
};
volatile ZeroLen g_zero_len = {7};
volatile int g_2d[3][4] = {{0, 1, 2, 3}, {4, 5, 6, 7}, {8, 9, 10, 11}};
volatile int g_3d[2][3][4] = {
    {{0, 1, 2, 3}, {4, 5, 6, 7}, {8, 9, 10, 11}},
    {{12, 13, 14, 15}, {16, 17, 18, 19}, {20, 21, 22, 23}},
};
volatile char g_names[3][8] = {"zero", "one", "two"};
int main() { return g_zero_len.n + g_2d[0][0] + g_3d[0][0][0] + g_names[0][0]; }
"""

# Built as C: GCC describes a C zero-length array with DW_AT_count 0 instead of an upper bound.
C_COUNT_SOURCE = """
struct CountZero {
    int n;
    int z[0];
};
volatile struct CountZero g_count_zero = {3};
int main(void) { return g_count_zero.n; }
"""


@parameterized_class(("opt",), [("-O0",), ("-O2",)])
class TestDwarfArrays(unittest.TestCase):
    opt: str

    def setUp(self):
        self.elf = ElfFile(compile_elf(ARRAYS_SOURCE, [self.opt, "-g"]))
        self.mem = ElfImageMemoryAccess(self.elf)

    def test_zero_length_array_upper_bound(self):
        # GCC on a 32-bit target encodes the zero-length array's upper bound -1 as a 4-byte 0xffffffff.
        payload = self.elf.get_global("g_zero_len", self.mem).payload
        self.assertEqual(len(payload), 0)
        self.assertEqual(payload.get_size(), 0)
        self.assertTrue(payload.get_type_die().get_readable_name().endswith("[0]"))
        self.assertEqual(payload.as_value_list(), [])

    def test_zero_length_array_count(self):
        elf = ElfFile(compile_elf(C_COUNT_SOURCE, ["-x", "c", self.opt, "-g"]))
        z = elf.get_global("g_count_zero", ElfImageMemoryAccess(elf)).z
        self.assertEqual(len(z), 0)
        self.assertEqual(z.get_size(), 0)
        self.assertTrue(z.get_type_die().get_readable_name().endswith("[0]"))

    def test_two_dimensional_array(self):
        g = self.elf.get_global("g_2d", self.mem)
        base = g.get_address()
        self.assertEqual(len(g), 3)
        self.assertEqual(g.get_size(), 48)
        self.assertEqual(g[1].get_address(), base + 16)
        self.assertEqual(len(g[1]), 4)
        self.assertEqual(g[1].get_size(), 16)
        self.assertEqual(g[1][2].read_value(), 6)
        self.assertEqual(g[2].as_value_list(), [8, 9, 10, 11])
        self.assertEqual([row.as_value_list() for row in g], [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]])
        self.assertEqual(g[2], [8, 9, 10, 11])

    def test_two_dimensional_array_write(self):
        g = self.elf.get_global("g_2d", self.mem)
        g[2][1].write_value(99)
        self.assertEqual(g[2].as_value_list(), [8, 99, 10, 11])
        self.assertEqual(g[1].as_value_list(), [4, 5, 6, 7])

    def test_three_dimensional_array(self):
        g = self.elf.get_global("g_3d", self.mem)
        self.assertEqual(len(g), 2)
        self.assertEqual(len(g[1]), 3)
        self.assertEqual(len(g[1][2]), 4)
        self.assertEqual(g[1].get_size(), 48)
        self.assertEqual(g[1][2].get_size(), 16)
        self.assertEqual(g[1][2][3].read_value(), 23)
        self.assertEqual(g[1][0][1].read_value(), 13)

    def test_snapshot_keeps_dimension(self):
        row = self.elf.get_global("g_2d", self.mem)[1].read()
        self.assertEqual(len(row), 4)
        self.assertEqual(row.as_value_list(), [4, 5, 6, 7])

    def test_two_dimensional_char_array(self):
        names = self.elf.get_global("g_names", self.mem)
        self.assertEqual(len(names), 3)
        self.assertEqual(names[1].read_value(), "one")
        self.assertEqual(names[2].read_value(), "two")
        # The outer dimension holds three strings, not one.
        with self.assertRaises(TypeMismatchError):
            names.read_value()


if __name__ == "__main__":
    unittest.main()
