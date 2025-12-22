# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest

from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.context import Context
from ttexalens.elf import ElfVariable, MemoryAccess


class MemoryAccessWrapper(MemoryAccess):
    """
    Wrapper around ELF memory reader that collects basic statistics about memory access.
    Maintains the same interface as the original memory reader.
    """

    def __init__(self, mem_access: MemoryAccess):
        self._mem_access = mem_access
        self.read_count = 0
        self.total_bytes_read = 0
        self.write_count = 0
        self.total_bytes_written = 0

    def read(self, address: int, size_bytes: int) -> bytes:
        self.read_count += 1
        self.total_bytes_read += size_bytes
        return self._mem_access.read(address, size_bytes)

    def write(self, address: int, data: bytes) -> None:
        self.write_count += 1
        self.total_bytes_written += len(data)
        return self._mem_access.write(address, data)

    def reset_stats(self):
        """Reset all statistics counters."""
        self.read_count = 0
        self.total_bytes_read = 0
        self.write_count = 0
        self.total_bytes_written = 0


class TestDebugSymbols(unittest.TestCase):
    context: Context  # TTExaLens context
    core_sim: RiscvCoreSimulator  # RISC-V core simulator instance

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        risc_debug = cls.context.devices[0].get_blocks()[0].all_riscs[0]
        cls.core_sim = RiscvCoreSimulator(
            cls.context,
            risc_debug.risc_location.location.to_str(),
            risc_debug.risc_location.risc_name,
            risc_debug.risc_location.neo_id,
        )
        cls.core_sim.load_elf("globals_test.release")
        cls.parsed_elf = cls.core_sim.parse_elf("globals_test.release")

        # Create the memory access wrapper
        original_mem_access = MemoryAccess.get(risc_debug)
        cls.mem_access = MemoryAccessWrapper(original_mem_access)

        assert not cls.core_sim.is_in_reset()

    @classmethod
    def tearDownClass(cls):
        cls.core_sim.set_reset(True)

    def verify_global_struct_low_level(self, g_global_struct):
        self.assertEqual(0xAA, g_global_struct.base_field1.read_value())
        self.assertEqual(0xBBBB, g_global_struct.base_field2.read_value())
        self.assertEqual(0x04030201, g_global_struct.packed.read_value())
        self.assertEqual(0x01, g_global_struct.v1.read_value())
        self.assertEqual(0x02, g_global_struct.v2.read_value())
        self.assertEqual(0x03, g_global_struct.v3.read_value())
        self.assertEqual(0x04, g_global_struct.v4.read_value())

        self.assertEqual(0xCC, g_global_struct.bs2_base_field1.read_value())
        self.assertEqual(0xDDDD, g_global_struct.bs2_base_field2.read_value())
        self.assertEqual(0x08070605, g_global_struct.bs2_packed.read_value())
        self.assertEqual(0x05, g_global_struct.bs2_v1.read_value())
        self.assertEqual(0x06, g_global_struct.bs2_v2.read_value())
        self.assertEqual(0x07, g_global_struct.bs2_v3.read_value())
        self.assertEqual(0x08, g_global_struct.bs2_v4.read_value())

        self.assertEqual(0x11223344, g_global_struct.a.read_value())
        self.assertEqual(0x5566778899AABBCC, g_global_struct.b.read_value())
        self.assertEqual(16, len(g_global_struct.c))
        for i in range(16):
            self.assertEqual(i, g_global_struct.c[i].read_value())
        self.assertEqual(4, len(g_global_struct.d))
        for i in range(4):
            self.assertEqual(i * 2, g_global_struct.d[i].x.read_value())
            self.assertEqual(i * 2 + 1, g_global_struct.d[i].y.read_value())
        self.assertEqual(2, g_global_struct.f.read_value())
        self.assertEqual(2.718281828459, g_global_struct.g.read_value())
        self.assertEqual(8, len(g_global_struct.h))
        for i in range(8):
            self.assertEqual(i % 2 == 0, g_global_struct.h[i].read_value())
        self.assertEqual(2 * 2, g_global_struct.p.x.read_value())
        self.assertEqual(2 * 2 + 1, g_global_struct.p.y.read_value())
        self.assertEqual(1056964608, g_global_struct.u.u32.read_value())
        self.assertEqual(0.5, g_global_struct.u.f32.read_value())
        self.assertEqual(0, g_global_struct.u.bytes[0].read_value())
        self.assertEqual(0, g_global_struct.u.bytes[1].read_value())
        self.assertEqual(0, g_global_struct.u.bytes[2].read_value())
        self.assertEqual(63, g_global_struct.u.bytes[3].read_value())
        self.assertEqual(0, g_global_struct.u.words[0].read_value())
        self.assertEqual(16128, g_global_struct.u.words[1].read_value())
        self.assertEqual(0x12345678, g_global_struct.msg.test.read_value())
        self.assertEqual(0xAABBCCDD, g_global_struct.msg.packed.read_value())
        self.assertEqual(0xAA, g_global_struct.msg.signal.read_value())
        self.assertEqual(0x87654321, g_global_struct.msg.test2.read_value())
        self.assertEqual(4, len(g_global_struct.uint_array))
        self.assertEqual(0x11111111, g_global_struct.uint_array[0].read_value())
        self.assertEqual(0x22222222, g_global_struct.uint_array[1].read_value())
        self.assertEqual(0x33333333, g_global_struct.uint_array[2].read_value())
        self.assertEqual(0x44444444, g_global_struct.uint_array[3].read_value())
        self.assertNotEqual(0, g_global_struct.uint_pointer.read_value())
        self.assertEqual(0x11111111, g_global_struct.uint_pointer.dereference().read_value())
        self.assertEqual(0x11111111, g_global_struct.uint_pointer[0].read_value())
        self.assertEqual(0x22222222, g_global_struct.uint_pointer[1].read_value())
        self.assertEqual(2, g_global_struct.enum_class_field.read_value())
        self.assertEqual(20, g_global_struct.enum_type_field.read_value())

    def verify_global_struct(self, g_global_struct):
        self.assertEqual(0xAA, g_global_struct.base_field1)
        self.assertEqual(0xBBBB, g_global_struct.base_field2)
        self.assertEqual(0x04030201, g_global_struct.packed)
        self.assertEqual(0x01, g_global_struct.v1)
        self.assertEqual(0x02, g_global_struct.v2)
        self.assertEqual(0x03, g_global_struct.v3)
        self.assertEqual(0x04, g_global_struct.v4)

        self.assertEqual(0xCC, g_global_struct.bs2_base_field1)
        self.assertEqual(0xDDDD, g_global_struct.bs2_base_field2)
        self.assertEqual(0x08070605, g_global_struct.bs2_packed)
        self.assertEqual(0x05, g_global_struct.bs2_v1)
        self.assertEqual(0x06, g_global_struct.bs2_v2)
        self.assertEqual(0x07, g_global_struct.bs2_v3)
        self.assertEqual(0x08, g_global_struct.bs2_v4)

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
        self.assertEqual(4, len(g_global_struct.uint_array))
        self.assertEqual(0x11111111, g_global_struct.uint_array[0])
        self.assertEqual(0x22222222, g_global_struct.uint_array[1])
        self.assertEqual(0x33333333, g_global_struct.uint_array[2])
        self.assertEqual(0x44444444, g_global_struct.uint_array[3])
        self.assertNotEqual(0, g_global_struct.uint_pointer)
        self.assertEqual(0x11111111, g_global_struct.uint_pointer.dereference())
        self.assertEqual(0x11111111, g_global_struct.uint_pointer[0])
        self.assertEqual(0x22222222, g_global_struct.uint_pointer[1])
        self.assertEqual(2, g_global_struct.enum_class_field)
        self.assertEqual("EnumClass::VALUE_C", str(g_global_struct.enum_class_field))
        self.assertEqual(20, g_global_struct.enum_type_field)
        self.assertEqual("EnumType::TYPE_Y", str(g_global_struct.enum_type_field))

    def test_elf_variable_low_level(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        assert variable_die.address is not None
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_access)
        self.verify_global_struct_low_level(g_global_struct)

    def test_elf_variable(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        assert variable_die.address is not None
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_access)
        self.verify_global_struct(g_global_struct)

    def test_read_elf_variable(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        assert variable_die.address is not None
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_access)
        self.verify_global_struct(g_global_struct.read())

    def test_elf_global_variable(self):
        self.mem_access.reset_stats()
        g_global_struct = self.parsed_elf.get_global("g_global_struct", TestDebugSymbols.mem_access)
        self.verify_global_struct(g_global_struct)
        self.assertGreater(self.mem_access.read_count, 1)

    def test_read_elf_global_variable(self):
        self.mem_access.reset_stats()
        g_global_struct = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_access)
        self.verify_global_struct(g_global_struct)
        self.assertEqual(self.mem_access.read_count, 1)

    def test_elf_const_global_variable(self):
        g_global_struct = self.parsed_elf.get_global("g_global_const_struct_ptr", TestDebugSymbols.mem_access)
        self.verify_global_struct(g_global_struct)

    def test_read_elf_const_global_variable(self):
        self.mem_access.reset_stats()
        g_global_struct = self.parsed_elf.read_global("g_global_const_struct_ptr", TestDebugSymbols.mem_access)
        self.verify_global_struct(g_global_struct)
        self.assertEqual(self.mem_access.read_count, 1)

    def test_elf_variable_constants(self):
        self.assertEqual(0x11223344, self.parsed_elf.get_constant("c_uint32_t"))
        self.assertEqual(0x5566778899AABBCC, self.parsed_elf.get_constant("c_uint64_t"))
        self.assertEqual(0.5, self.parsed_elf.get_constant("c_float"))
        self.assertEqual(2.718281828459, self.parsed_elf.get_constant("c_double"))

    def test_elf_variable_array_iteration(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        assert variable_die.address is not None
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_access)
        c_values = [var.read_value() for var in g_global_struct.c]
        self.assertEqual(list(range(16)), c_values)
        d_x_values = [var.x.read_value() for var in g_global_struct.d]
        d_y_values = [var.y.read_value() for var in g_global_struct.d]
        self.assertEqual([i * 2 for i in range(4)], d_x_values)
        self.assertEqual([i * 2 + 1 for i in range(4)], d_y_values)
        h_values = [var.read_value() for var in g_global_struct.h]
        self.assertEqual([i % 2 == 0 for i in range(8)], h_values)

    def test_elf_variable_array_as_list(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        assert variable_die.address is not None
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_access)
        c_values = [var.read_value() for var in g_global_struct.c.as_list()]
        self.assertEqual(list(range(16)), c_values)
        d_x_values = [var.x.read_value() for var in g_global_struct.d.as_list()]
        d_y_values = [var.y.read_value() for var in g_global_struct.d.as_list()]
        self.assertEqual([i * 2 for i in range(4)], d_x_values)
        self.assertEqual([i * 2 + 1 for i in range(4)], d_y_values)
        h_values = [var.read_value() for var in g_global_struct.h.as_list()]
        self.assertEqual([i % 2 == 0 for i in range(8)], h_values)

    def test_elf_variable_array_as_value_list(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        assert variable_die.address is not None
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_access)
        c_values = g_global_struct.c.as_value_list()
        self.assertEqual(list(range(16)), c_values)
        d_x_values = [var.x.read_value() for var in g_global_struct.d.as_list()]
        d_y_values = [var.y.read_value() for var in g_global_struct.d.as_list()]
        self.assertEqual([i * 2 for i in range(4)], d_x_values)
        self.assertEqual([i * 2 + 1 for i in range(4)], d_y_values)
        h_values = g_global_struct.h.as_value_list()
        self.assertEqual([i % 2 == 0 for i in range(8)], h_values)

    def test_elf_variable_operators(self):
        """Test arithmetic, bitwise, and comparison operators"""
        self.mem_access.reset_stats()

        g_global_struct = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_access)

        # Test that we didn't do any additional memory reads
        self.assertEqual(self.mem_access.read_count, 1)

        # Reset memory reader stats
        self.mem_access.reset_stats()

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
        self.assertEqual(self.mem_access.read_count, 0)
        self.assertEqual(self.mem_access.total_bytes_read, 0)

    def test_elf_variable_hash(self):
        g_global_struct1 = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_access)
        g_global_struct2 = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_access)
        self.assertEqual(hash(g_global_struct1), hash(g_global_struct2))
        self.assertEqual(hash(g_global_struct1.a), hash(g_global_struct2.a))
        self.assertEqual(hash(g_global_struct1.b), hash(g_global_struct2.b))
        self.assertEqual(hash(g_global_struct1.c[5]), hash(g_global_struct2.c[5]))
        self.assertEqual(hash(g_global_struct1.f), hash(g_global_struct2.f))
        self.assertEqual(hash(g_global_struct1.g), hash(g_global_struct2.g))
        self.assertEqual(hash(g_global_struct1.h[3]), hash(g_global_struct2.h[3]))

    def test_elf_variable_format(self):
        g_global_struct = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_access)
        self.assertEqual(format(g_global_struct.a, "010x"), format(0x11223344, "010x"))
        self.assertEqual(format(g_global_struct.b, "X"), format(0x5566778899AABBCC, "X"))
        self.assertEqual(format(g_global_struct.c[10], "d"), format(10, "d"))
        self.assertEqual(format(g_global_struct.f, ".2f"), format(2.0, ".2f"))
        self.assertEqual(f"{g_global_struct.f:.2f}", format(2.0, ".2f"))
        self.assertEqual(format(g_global_struct.g, ".5f"), format(2.718281828459, ".5f"))
        self.assertEqual(format(g_global_struct.h[2], ""), format(True, ""))

    def test_elf_variable_write_value(self):
        g_global_struct = self.parsed_elf.get_global("g_global_struct", TestDebugSymbols.mem_access)
        g_global_struct.a.write_value(0xDEADBEEF)
        self.assertEqual(0xDEADBEEF, g_global_struct.a)
        g_global_struct.a.write_value(0x11223344)  # Restore original value
        self.assertRaises(Exception, g_global_struct.a.write_value, 2.5)  # Rounding with float
        self.assertRaises(Exception, g_global_struct.f.write_value, 0xFFFFFFFF)  # Overflow uint32 on float32
        self.assertRaises(Exception, g_global_struct.f.write_value, 3.4028235e38 * 2)  # Overflow float32
        self.assertRaises(Exception, g_global_struct.g.write_value, 0xFFFFFFFFFFFFFFFF)  # Overflow uint64 on float64
        enum_value = self.parsed_elf.get_enum_value("EnumClass::VALUE_D")
        assert enum_value is not None
        self.assertEqual(enum_value, 3)
        g_global_struct.enum_class_field.write_value(enum_value)
        self.assertEqual(3, g_global_struct.enum_class_field)
        self.assertEqual("EnumClass::VALUE_D", str(g_global_struct.enum_class_field))
        g_global_struct.enum_class_field.write_value(2)  # Restore original value
        self.assertRaises(
            Exception, g_global_struct.enum_class_field.write_value, 0xFFFFFFFFFFFFFFFF
        )  # Overflow uint64 on byte enum

    def test_elf_variable_memory_access_errors(self):
        """Test that all operators propagate memory access errors (Issue #782)"""
        g_global_struct = self.parsed_elf.get_global("g_global_struct", TestDebugSymbols.mem_access)

        # invalid_memory_ptr points to 0xFFFF0000 which is outside L1/Data Private Memory
        invalid_ptr = g_global_struct.invalid_memory_ptr

        # Dereferencing should raise memory access error
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference())

        # Test all comparison operators propagate memory errors
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() < 100)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 > invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() <= 100)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 >= invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() > 100)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 < invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() >= 100)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 <= invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() == 100)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 == invalid_ptr.dereference())

        # Test all arithmetic operators propagate memory errors
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() + 10)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 10 + invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() - 10)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 - invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() * 10)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 10 * invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() / 10)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 / invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() // 10)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 // invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() % 10)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 100 % invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() ** 2)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 2 ** invalid_ptr.dereference())

        # Test all bitwise operators propagate memory errors
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() & 0xFF)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 0xFF & invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() | 0xFF)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 0xFF | invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() ^ 0xFF)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 0xFF ^ invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() << 2)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 1 << invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: invalid_ptr.dereference() >> 2)
        self.assertRaisesRegex(Exception, "restricted access", lambda: 256 >> invalid_ptr.dereference())

        # Test all unary operators propagate memory errors
        self.assertRaisesRegex(Exception, "restricted access", lambda: -invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: +invalid_ptr.dereference())
        self.assertRaisesRegex(Exception, "restricted access", lambda: abs(invalid_ptr.dereference()))
        self.assertRaisesRegex(Exception, "restricted access", lambda: ~invalid_ptr.dereference())

    def test_elf_variable_type_errors(self):
        """Test that all operators handle type incompatibility correctly (Issue #782)"""
        g_global_struct = self.parsed_elf.get_global("g_global_struct", TestDebugSymbols.mem_access)

        # Test comparison operators with incompatible types
        # __eq__ should return False for type mismatch
        self.assertFalse(g_global_struct.a == [1, 2, 3])
        self.assertFalse(g_global_struct.a == {"key": "value"})
        self.assertFalse(g_global_struct.a == "string")

        # __lt__ and __gt__ should raise TypeError when both operands return NotImplemented
        self.assertRaises(TypeError, lambda: g_global_struct.a < [1, 2, 3])
        self.assertRaises(TypeError, lambda: [1, 2, 3] > g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a > [1, 2, 3])
        self.assertRaises(TypeError, lambda: [1, 2, 3] < g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a <= {"key": "value"})
        self.assertRaises(TypeError, lambda: {"key": "value"} >= g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a >= {"key": "value"})
        self.assertRaises(TypeError, lambda: {"key": "value"} <= g_global_struct.a)

        # Test arithmetic operators with incompatible types
        self.assertRaises(TypeError, lambda: g_global_struct.a + "string")
        self.assertRaises(TypeError, lambda: "string" + g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a - [1, 2])
        self.assertRaises(TypeError, lambda: [1, 2] - g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a * {"key": "value"})
        self.assertRaises(TypeError, lambda: {"key": "value"} * g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a / "string")
        self.assertRaises(TypeError, lambda: "string" / g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a // [1, 2])
        self.assertRaises(TypeError, lambda: [1, 2] // g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a % {"key": "value"})
        self.assertRaises(TypeError, lambda: {"key": "value"} % g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a ** "string")
        self.assertRaises(TypeError, lambda: "string" ** g_global_struct.a)

        # Test bitwise operators with incompatible types
        self.assertRaises(TypeError, lambda: g_global_struct.a & "string")
        self.assertRaises(TypeError, lambda: "string" & g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a | [1, 2])
        self.assertRaises(TypeError, lambda: [1, 2] | g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a ^ {"key": "value"})
        self.assertRaises(TypeError, lambda: {"key": "value"} ^ g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a << "string")
        self.assertRaises(TypeError, lambda: "string" << g_global_struct.a)
        self.assertRaises(TypeError, lambda: g_global_struct.a >> [1, 2])
        self.assertRaises(TypeError, lambda: [1, 2] >> g_global_struct.a)

        # Test bitwise operators with floats (should fail type check)
        self.assertRaises(TypeError, lambda: g_global_struct.f & 0xFF)
        self.assertRaises(TypeError, lambda: 0xFF & g_global_struct.f)
        self.assertRaises(TypeError, lambda: g_global_struct.g | 0xFF)
        self.assertRaises(TypeError, lambda: 0xFF | g_global_struct.g)
        self.assertRaises(TypeError, lambda: g_global_struct.f ^ 0xFF)
        self.assertRaises(TypeError, lambda: 0xFF ^ g_global_struct.f)
        self.assertRaises(TypeError, lambda: g_global_struct.g << 2)
        self.assertRaises(TypeError, lambda: 2 << g_global_struct.g)
        self.assertRaises(TypeError, lambda: g_global_struct.f >> 2)
        self.assertRaises(TypeError, lambda: 2 >> g_global_struct.f)

        # Test unary invert with float (should raise TypeError)
        self.assertRaises(TypeError, lambda: ~g_global_struct.f)
        self.assertRaises(TypeError, lambda: ~g_global_struct.g)

        # Test that wrong_type_ptr works with valid memory (type cast, not type error)
        # wrong_type_ptr is InnerStruct* but points to uint32_t array
        wrong_ptr = g_global_struct.wrong_type_ptr
        dereferenced = wrong_ptr.dereference()

        # Should be able to access (memory is valid), data is interpreted as InnerStruct
        # InnerStruct has x (uint16_t) and y (uint16_t)
        # uint_array[0] = 0x11111111, so x = 0x1111, y = 0x1111 (little-endian)
        self.assertEqual(dereferenced.x, 0x1111)
        self.assertEqual(dereferenced.y, 0x1111)

        # Verify operators work with wrong type interpretation but valid memory
        self.assertTrue(dereferenced.x < 0x2000)
        self.assertEqual(dereferenced.x + 0x1000, 0x2111)
        self.assertEqual(dereferenced.y & 0xFF00, 0x1100)
