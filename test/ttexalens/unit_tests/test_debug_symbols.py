# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest

from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.test_base import init_default_test_context
from ttexalens.context import Context
from ttexalens.firmware import ELF
from ttexalens.parse_elf import ElfVariable, mem_access


class TestDebugSymbols(unittest.TestCase):
    context: Context  # TTExaLens context
    core_sim: RiscvCoreSimulator  # RISC-V core simulator instance

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()
        risc_debug = cls.context.devices[0].get_blocks()[0].all_riscs[0]
        cls.core_sim = RiscvCoreSimulator(cls.context, risc_debug.risc_location.location.to_str(), risc_debug.risc_location.risc_name, risc_debug.risc_location.neo_id)
        cls.core_sim.load_elf("globals_test.debug")
        cls.parsed_elf = cls.core_sim.parse_elf("globals_test.debug")
        cls.mem_reader = ELF.get_mem_reader(risc_debug.risc_location.location, risc_debug.risc_location.risc_name, risc_debug.risc_location.neo_id)
        assert(not cls.core_sim.is_in_reset())

    @classmethod
    def tearDownClass(cls):
        cls.core_sim.set_reset(True)

    def mem_access(self, symbol_name: str):
        return mem_access(self.parsed_elf, symbol_name, TestDebugSymbols.mem_reader)[0][0]

    def test_mem_access(self):
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

    def verify_global_struct(self, g_global_struct):
        self.assertEqual(0x11223344, g_global_struct.a.value())
        self.assertEqual(0x5566778899AABBCC, g_global_struct.b.value())
        self.assertEqual(16, len(g_global_struct.c))
        for i in range(16):
            self.assertEqual(i, g_global_struct.c[i].value())
        self.assertEqual(4, len(g_global_struct.d))
        for i in range(4):
            self.assertEqual(i * 2, g_global_struct.d[i].x.value())
            self.assertEqual(i * 2 + 1, g_global_struct.d[i].y.value())
        self.assertEqual(2, g_global_struct.f.value())
        self.assertEqual(2.718281828459, g_global_struct.g.value())
        self.assertEqual(8, len(g_global_struct.h))
        for i in range(8):
            self.assertEqual(i % 2 == 0, g_global_struct.h[i].value())
        self.assertEqual(2 * 2, g_global_struct.p.x.value())
        self.assertEqual(2 * 2 + 1, g_global_struct.p.y.value())
        self.assertEqual(1056964608, g_global_struct.u.u32.value())
        self.assertEqual(0.5, g_global_struct.u.f32.value())
        self.assertEqual(0, g_global_struct.u.bytes[0].value())
        self.assertEqual(0, g_global_struct.u.bytes[1].value())
        self.assertEqual(0, g_global_struct.u.bytes[2].value())
        self.assertEqual(63, g_global_struct.u.bytes[3].value())
        self.assertEqual(0, g_global_struct.u.words[0].value())
        self.assertEqual(16128, g_global_struct.u.words[1].value())

    def test_elf_variable(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct)

    def test_read_elf_variable(self):
        variable_die = self.parsed_elf.variables["g_global_struct"]
        g_global_struct = ElfVariable(variable_die.resolved_type, variable_die.address, TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct.read())

    def test_elf_global_variable(self):
        g_global_struct = self.parsed_elf.get_global("g_global_struct", TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct)

    def test_read_elf_global_variable(self):
        g_global_struct = self.parsed_elf.read_global("g_global_struct", TestDebugSymbols.mem_reader)
        self.verify_global_struct(g_global_struct)
