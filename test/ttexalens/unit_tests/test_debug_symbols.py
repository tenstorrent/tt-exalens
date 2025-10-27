# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest

from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.test_base import init_default_test_context
from ttexalens.context import Context
from ttexalens.elf import ElfVariable
from ttexalens.firmware import ELF
from ttexalens.parse_elf import mem_access


class MemoryReaderWrapper:
    """
    Wrapper around ELF memory reader that collects basic statistics about memory access.
    Maintains the same interface as the original memory reader.
    """

    def __init__(self, mem_reader):
        self._mem_reader = mem_reader
        self.call_count = 0
        self.total_bytes_transferred = 0

    def __call__(self, address: int, size_bytes: int, elements_to_read: int) -> list[int]:
        """
        Call the underlying memory reader and collect statistics.

        Args:
            address: Memory address to read from
            size_bytes: Total number of bytes to read
            elements_to_read: Number of elements to read

        Returns:
            List of integers read from memory
        """
        # Update statistics
        self.call_count += 1
        self.total_bytes_transferred += size_bytes

        # Call the actual memory reader
        return self._mem_reader(address, size_bytes, elements_to_read)

    def reset_stats(self):
        """Reset all statistics counters."""
        self.call_count = 0
        self.total_bytes_transferred = 0


class TestDebugSymbols(unittest.TestCase):
    context: Context  # TTExaLens context
    core_sim: RiscvCoreSimulator  # RISC-V core simulator instance

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()
        risc_debug = cls.context.devices[0].get_blocks()[0].all_riscs[0]
        cls.core_sim = RiscvCoreSimulator(
            cls.context,
            risc_debug.risc_location.location.to_str(),
            risc_debug.risc_location.risc_name,
            risc_debug.risc_location.neo_id,
        )
        cls.core_sim.load_elf("globals_test.release")
        cls.parsed_elf = cls.core_sim.parse_elf("globals_test.release")

        # Create the memory reader wrapper
        original_mem_reader = ELF.get_mem_reader(
            risc_debug.risc_location.location, risc_debug.risc_location.risc_name, risc_debug.risc_location.neo_id
        )
        cls.mem_reader = MemoryReaderWrapper(original_mem_reader)

        assert not cls.core_sim.is_in_reset()

    @classmethod
    def tearDownClass(cls):
        cls.core_sim.set_reset(True)

    def mem_access(self, symbol_name: str):
        return mem_access(self.parsed_elf, symbol_name, TestDebugSymbols.mem_reader)[0][0]

    def mem_access_constant(self, const_name: str):
        return mem_access(self.parsed_elf, const_name, lambda x, y, z: [0])[3]

    def test_mem_access(self):
        self.assertEqual(0x11223344, self.mem_access_constant("c_uint32_t"))
        self.assertEqual(0x5566778899AABBCC, self.mem_access_constant("c_uint64_t"))
        self.assertEqual([0, 0, 0, 63], self.mem_access_constant("c_float"))
        self.assertEqual([3, 87, 20, 139, 10, 191, 5, 64], self.mem_access_constant("c_double"))
        self.assertEqual(0x5566778899AABBCC, self.mem_access("g_global_struct.b"))
        self.assertEqual(0x11223344, self.mem_access("g_global_struct.a"))
        self.assertEqual(0x5566778899AABBCC, self.mem_access("g_global_struct.b"))
        for i in range(16):
            self.assertEqual(i, self.mem_access(f"g_global_struct.c[{i}]"))
        for i in range(4):
            self.assertEqual(i * 2, self.mem_access(f"g_global_struct.d[{i}].x"))
            self.assertEqual(i * 2 + 1, self.mem_access(f"g_global_struct.d[{i}].y"))
        self.assertEqual(1073741824, self.mem_access("g_global_struct.f"))
        self.assertEqual(4613303445314885379, self.mem_access("g_global_struct.g"))
        for i in range(8):
            self.assertEqual(i % 2 == 0, self.mem_access(f"g_global_struct.h[{i}]"))
        self.assertEqual(2 * 2, self.mem_access("g_global_struct.p->x"))
        self.assertEqual(2 * 2 + 1, self.mem_access("g_global_struct.p->y"))
        self.assertEqual(1056964608, self.mem_access("g_global_struct.u.u32"))
        self.assertEqual(1056964608, self.mem_access("g_global_struct.u.f32"))
        self.assertEqual(0, self.mem_access("g_global_struct.u.bytes[0]"))
        self.assertEqual(0, self.mem_access("g_global_struct.u.bytes[1]"))
        self.assertEqual(0, self.mem_access("g_global_struct.u.bytes[2]"))
        self.assertEqual(63, self.mem_access("g_global_struct.u.bytes[3]"))
        self.assertEqual(0, self.mem_access("g_global_struct.u.words[0]"))
        self.assertEqual(16128, self.mem_access("g_global_struct.u.words[1]"))

    def verify_global_struct_low_level(self, g_global_struct):
        self.assertEqual(0x11223344, g_global_struct.a.get_value())
        self.assertEqual(0x5566778899AABBCC, g_global_struct.b.get_value())
        self.assertEqual(16, len(g_global_struct.c))
        for i in range(16):
            self.assertEqual(i, g_global_struct.c[i].get_value())
        self.assertEqual(4, len(g_global_struct.d))
        for i in range(4):
            self.assertEqual(i * 2, g_global_struct.d[i].x.get_value())
            self.assertEqual(i * 2 + 1, g_global_struct.d[i].y.get_value())
        self.assertEqual(2, g_global_struct.f.get_value())
        self.assertEqual(2.718281828459, g_global_struct.g.get_value())
        self.assertEqual(8, len(g_global_struct.h))
        for i in range(8):
            self.assertEqual(i % 2 == 0, g_global_struct.h[i].get_value())
        self.assertEqual(2 * 2, g_global_struct.p.x.get_value())
        self.assertEqual(2 * 2 + 1, g_global_struct.p.y.get_value())
        self.assertEqual(1056964608, g_global_struct.u.u32.get_value())
        self.assertEqual(0.5, g_global_struct.u.f32.get_value())
        self.assertEqual(0, g_global_struct.u.bytes[0].get_value())
        self.assertEqual(0, g_global_struct.u.bytes[1].get_value())
        self.assertEqual(0, g_global_struct.u.bytes[2].get_value())
        self.assertEqual(63, g_global_struct.u.bytes[3].get_value())
        self.assertEqual(0, g_global_struct.u.words[0].get_value())
        self.assertEqual(16128, g_global_struct.u.words[1].get_value())
        self.assertEqual(0x12345678, g_global_struct.msg.test.get_value())
        self.assertEqual(0xAABBCCDD, g_global_struct.msg.packed.get_value())
        self.assertEqual(0xAA, g_global_struct.msg.signal.get_value())
        self.assertEqual(0x87654321, g_global_struct.msg.test2.get_value())

    def verify_global_struct(self, g_global_struct):
        self.assertEqual(0x11223344, g_global_struct.a)
        self.assertEqual(0x5566778899AABBCC, g_global_struct.b)
        self.assertEqual([i for i in range(16)], g_global_struct.c)
        self.assertEqual(4, len(g_global_struct.d))
        for i in range(4):
            self.assertEqual(i * 2, g_global_struct.d[i].x)
            self.assertEqual(i * 2 + 1, g_global_struct.d[i].y)
        self.assertEqual(2, g_global_struct.f)
        self.assertEqual(2.718281828459, g_global_struct.g)
        self.assertEqual([i % 2 == 0 for i in range(8)], g_global_struct.h)
        self.assertEqual(2 * 2, g_global_struct.p.x)
        self.assertEqual(2 * 2 + 1, g_global_struct.p.y)
        self.assertEqual(1056964608, g_global_struct.u.u32)
        self.assertEqual(0.5, g_global_struct.u.f32)
        self.assertEqual([0, 0, 0, 63], g_global_struct.u.bytes)
        self.assertEqual([0, 16128], g_global_struct.u.words)
        self.assertEqual(0x12345678, g_global_struct.msg.test)
        self.assertEqual(0xAABBCCDD, g_global_struct.msg.packed)
        self.assertEqual(0xAA, g_global_struct.msg.signal)
        self.assertEqual(0x87654321, g_global_struct.msg.test2)

    def test_elf_variable_low_level(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_reader)
        self.verify_global_struct_low_level(g_global_struct)

    def test_elf_variable(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct)

    def test_read_elf_variable(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct.read())

    def test_elf_global_variable(self):
        self.mem_reader.reset_stats()
        g_global_struct = self.parsed_elf.get_global("g_global_struct", TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct)
        self.assertGreater(self.mem_reader.call_count, 1)

    def test_read_elf_global_variable(self):
        self.mem_reader.reset_stats()
        g_global_struct = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct)
        self.assertEqual(self.mem_reader.call_count, 1)

    def test_elf_const_global_variable(self):
        g_global_struct = self.parsed_elf.get_global("g_global_const_struct_ptr", TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct)

    def test_read_elf_const_global_variable(self):
        self.mem_reader.reset_stats()
        g_global_struct = self.parsed_elf.read_global("g_global_const_struct_ptr", TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct)
        self.assertEqual(self.mem_reader.call_count, 1)

    def test_elf_variable_constants(self):
        self.assertEqual(0x11223344, self.parsed_elf.get_constant("c_uint32_t"))
        self.assertEqual(0x5566778899AABBCC, self.parsed_elf.get_constant("c_uint64_t"))
        self.assertEqual(0.5, self.parsed_elf.get_constant("c_float"))
        self.assertEqual(2.718281828459, self.parsed_elf.get_constant("c_double"))

    def test_elf_variable_array_iteration(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_reader)
        c_values = [var.get_value() for var in g_global_struct.c]
        self.assertEqual(list(range(16)), c_values)
        d_x_values = [var.x.get_value() for var in g_global_struct.d]
        d_y_values = [var.y.get_value() for var in g_global_struct.d]
        self.assertEqual([i * 2 for i in range(4)], d_x_values)
        self.assertEqual([i * 2 + 1 for i in range(4)], d_y_values)
        h_values = [var.get_value() for var in g_global_struct.h]
        self.assertEqual([i % 2 == 0 for i in range(8)], h_values)

    def test_elf_variable_array_as_list(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_reader)
        c_values = [var.get_value() for var in g_global_struct.c.as_list()]
        self.assertEqual(list(range(16)), c_values)
        d_x_values = [var.x.get_value() for var in g_global_struct.d.as_list()]
        d_y_values = [var.y.get_value() for var in g_global_struct.d.as_list()]
        self.assertEqual([i * 2 for i in range(4)], d_x_values)
        self.assertEqual([i * 2 + 1 for i in range(4)], d_y_values)
        h_values = [var.get_value() for var in g_global_struct.h.as_list()]
        self.assertEqual([i % 2 == 0 for i in range(8)], h_values)

    def test_elf_variable_array_as_value_list(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_reader)
        c_values = g_global_struct.c.as_value_list()
        self.assertEqual(list(range(16)), c_values)
        d_x_values = [var.x.get_value() for var in g_global_struct.d.as_list()]
        d_y_values = [var.y.get_value() for var in g_global_struct.d.as_list()]
        self.assertEqual([i * 2 for i in range(4)], d_x_values)
        self.assertEqual([i * 2 + 1 for i in range(4)], d_y_values)
        h_values = g_global_struct.h.as_value_list()
        self.assertEqual([i % 2 == 0 for i in range(8)], h_values)

    def test_elf_variable_operators(self):
        """Test arithmetic, bitwise, and comparison operators"""
        self.mem_reader.reset_stats()

        g_global_struct = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_reader)

        # Test that we didn't do any additional memory reads
        self.assertEqual(self.mem_reader.call_count, 1)

        # Reset memory reader stats
        self.mem_reader.reset_stats()

        # Test comparison operators with integers
        self.assertTrue(g_global_struct.a == g_global_struct.a)
        self.assertTrue(0x11223344 == g_global_struct.a)
        self.assertTrue(0x12345678 != g_global_struct.a)
        self.assertTrue(g_global_struct.a == 0x11223344)
        self.assertTrue(g_global_struct.a != 0x12345678)
        self.assertTrue(g_global_struct.c[5] < 10)
        self.assertTrue(g_global_struct.c[5] <= 5)
        self.assertTrue(g_global_struct.c[10] > 5)
        self.assertTrue(g_global_struct.c[10] >= 10)

        # Test comparison operators with floats
        self.assertTrue(g_global_struct.f < 3.0)
        self.assertTrue(g_global_struct.f >= 2.0)
        self.assertTrue(g_global_struct.g > 2.7)
        self.assertTrue(g_global_struct.g <= 2.8)

        # Test arithmetic operators
        self.assertEqual(g_global_struct.c[5] + 10, 15)  # 5 + 10
        self.assertEqual(g_global_struct.c[8] - 3, 5)  # 8 - 3
        self.assertEqual(g_global_struct.c[4] * 3, 12)  # 4 * 3
        self.assertEqual(g_global_struct.c[6] / 2, 3.0)  # 6 / 2
        self.assertEqual(g_global_struct.c[7] // 2, 3)  # 7 // 2
        self.assertEqual(g_global_struct.c[9] % 4, 1)  # 9 % 4
        self.assertEqual(g_global_struct.c[2] ** 3, 8)  # 2 ** 3

        # Test reverse arithmetic operators
        self.assertEqual(20 - g_global_struct.c[3], 17)  # 20 - 3
        self.assertEqual(2 * g_global_struct.c[6], 12)  # 2 * 6
        self.assertEqual(100 / g_global_struct.c[4], 25.0)  # 100 / 4

        # Test bitwise operators with integers
        self.assertEqual(g_global_struct.a & 0xFF, 0x44)  # 0x11223344 & 0xFF
        self.assertEqual(g_global_struct.c[1] | 0xF0, 0xF1)  # 1 | 0xF0
        self.assertEqual(g_global_struct.c[5] ^ 0x0F, 0x0A)  # 5 ^ 0x0F
        self.assertEqual(g_global_struct.c[2] << 2, 8)  # 2 << 2
        self.assertEqual(g_global_struct.c[8] >> 1, 4)  # 8 >> 1

        # Test reverse bitwise operators
        self.assertEqual(0xFF & g_global_struct.a, 0x44)  # 0xFF & 0x11223344
        self.assertEqual(0xF0 | g_global_struct.c[1], 0xF1)  # 0xF0 | 1
        self.assertEqual(0x0F ^ g_global_struct.c[5], 0x0A)  # 0x0F ^ 5

        # Test bitwise operators with booleans
        self.assertTrue(g_global_struct.h[0] & True)  # True & True
        self.assertFalse(g_global_struct.h[1] & True)  # False & True
        self.assertTrue(g_global_struct.h[1] | True)  # False | True
        self.assertTrue(g_global_struct.h[0] ^ False)  # True ^ False

        # Test unary operators
        self.assertEqual(-g_global_struct.c[5], -5)  # -5
        self.assertEqual(+g_global_struct.c[7], 7)  # +7
        self.assertEqual(abs(-g_global_struct.c[3]), 3)  # abs(-3) = 3
        self.assertEqual(~g_global_struct.c[0], -1)  # ~0 = -1
        self.assertEqual(~g_global_struct.h[0], -2)  # ~True = ~1 = -2

        # Test __index__ operator (ElfVariable as index)
        test_list = [10, 20, 30, 40, 50]
        self.assertEqual(test_list[g_global_struct.c[2]], 30)  # test_list[2]
        self.assertEqual(test_list[g_global_struct.c[4]], 50)  # test_list[4]

        # Test string representation
        self.assertEqual(str(g_global_struct.c[5]), "5")
        self.assertEqual(str(g_global_struct.f), "2.0")
        self.assertEqual(str(g_global_struct.h[0]), "True")
        self.assertEqual(str(g_global_struct.h[1]), "False")

        # Test array equality
        self.assertEqual(g_global_struct.c, list(range(16)))
        self.assertEqual(g_global_struct.h, [i % 2 == 0 for i in range(8)])
        self.assertEqual(g_global_struct.u.get_member("bytes"), [0, 0, 0, 63])
        self.assertEqual(g_global_struct.u.words, [0, 16128])

        # Test dictionary-style access
        self.assertEqual(g_global_struct["a"], 0x11223344)
        self.assertEqual(g_global_struct["c"][5], 5)
        self.assertEqual(g_global_struct["u"]["u32"], 1056964608)
        self.assertEqual(g_global_struct["u"].get_member("bytes")[3], 63)

        # Test that we didn't do any additional memory reads
        self.assertEqual(self.mem_reader.call_count, 0)
        self.assertEqual(self.mem_reader.total_bytes_transferred, 0)

    def test_elf_variable_hash(self):
        g_global_struct1 = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_reader)
        g_global_struct2 = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_reader)
        self.assertEqual(hash(g_global_struct1), hash(g_global_struct2))
        self.assertEqual(hash(g_global_struct1.a), hash(g_global_struct2.a))
        self.assertEqual(hash(g_global_struct1.b), hash(g_global_struct2.b))
        self.assertEqual(hash(g_global_struct1.c[5]), hash(g_global_struct2.c[5]))
        self.assertEqual(hash(g_global_struct1.f), hash(g_global_struct2.f))
        self.assertEqual(hash(g_global_struct1.g), hash(g_global_struct2.g))
        self.assertEqual(hash(g_global_struct1.h[3]), hash(g_global_struct2.h[3]))

    def test_elf_variable_format(self):
        g_global_struct = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_reader)
        self.assertEqual(format(g_global_struct.a, "010x"), format(0x11223344, "010x"))
        self.assertEqual(format(g_global_struct.b, "X"), format(0x5566778899AABBCC, "X"))
        self.assertEqual(format(g_global_struct.c[10], "d"), format(10, "d"))
        self.assertEqual(format(g_global_struct.f, ".2f"), format(2.0, ".2f"))
        self.assertEqual(f"{g_global_struct.f:.2f}", format(2.0, ".2f"))
        self.assertEqual(format(g_global_struct.g, ".5f"), format(2.718281828459, ".5f"))
        self.assertEqual(format(g_global_struct.h[2], ""), format(True, ""))
