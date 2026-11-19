# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Device-free tests for evaluating DWARF location expressions.

The variables below are described by a hand-written DWARF 5 compile unit, so each test pins down
one exact location expression. The registers and memory they read come from ElfImageMemoryAccess.
"""
import unittest

from test.ttexalens.unit_tests.compiled_elf import ElfImageMemoryAccess, compile_elf
from ttexalens.elf import DwarfDie, ElfFile, FrameInspection, FrameSnapshot, evaluate_die_location

# main() is five 4-byte instructions. Its DW_AT_frame_base is s0 (DW_OP_reg8).
# Each child of main below has the location expression named in its comment.
LOCATION_FIXTURE = r"""
    .option norvc
    .option norelax
    .cfi_sections .debug_frame
    .text
    .globl main
    .type main, @function
main:
    .cfi_startproc
    nop
    nop
    nop
    nop
    ret
    .cfi_endproc
.Lmain_end:
    .size main, .Lmain_end - main

    .data
    .p2align 2
    .globl g_target
    .type g_target, @object
g_target:
    .4byte 0x11223344
    .size g_target, 4
    .globl g_shadow
    .type g_shadow, @object
g_shadow:
    .4byte 0x55667788
    .size g_shadow, 4

    .section .debug_abbrev,"",@progbits
.Labbrev:
    /* 1: compile_unit with children: name, low_pc, high_pc, addr_base */
    .uleb128 1
    .uleb128 0x11
    .byte 1
    .uleb128 0x03
    .uleb128 0x08
    .uleb128 0x11
    .uleb128 0x01
    .uleb128 0x12
    .uleb128 0x06
    .uleb128 0x73
    .uleb128 0x17
    .byte 0, 0
    /* 2: base_type: name, byte_size, encoding */
    .uleb128 2
    .uleb128 0x24
    .byte 0
    .uleb128 0x03
    .uleb128 0x08
    .uleb128 0x0b
    .uleb128 0x0b
    .uleb128 0x3e
    .uleb128 0x0b
    .byte 0, 0
    /* 3: pointer_type: byte_size, type */
    .uleb128 3
    .uleb128 0x0f
    .byte 0
    .uleb128 0x0b
    .uleb128 0x0b
    .uleb128 0x49
    .uleb128 0x13
    .byte 0, 0
    /* 4: subprogram with children: name, low_pc, high_pc, frame_base */
    .uleb128 4
    .uleb128 0x2e
    .byte 1
    .uleb128 0x03
    .uleb128 0x08
    .uleb128 0x11
    .uleb128 0x01
    .uleb128 0x12
    .uleb128 0x06
    .uleb128 0x40
    .uleb128 0x18
    .byte 0, 0
    /* 5: variable: name, type, location (expression) */
    .uleb128 5
    .uleb128 0x34
    .byte 0
    .uleb128 0x03
    .uleb128 0x08
    .uleb128 0x49
    .uleb128 0x13
    .uleb128 0x02
    .uleb128 0x18
    .byte 0, 0
    /* 6: formal_parameter: name, type, location (expression) */
    .uleb128 6
    .uleb128 0x05
    .byte 0
    .uleb128 0x03
    .uleb128 0x08
    .uleb128 0x49
    .uleb128 0x13
    .uleb128 0x02
    .uleb128 0x18
    .byte 0, 0
    /* 7: variable without a location (optimized out): name, type */
    .uleb128 7
    .uleb128 0x34
    .byte 0
    .uleb128 0x03
    .uleb128 0x08
    .uleb128 0x49
    .uleb128 0x13
    .byte 0, 0
    /* 8: variable: name, type, location (location list) */
    .uleb128 8
    .uleb128 0x34
    .byte 0
    .uleb128 0x03
    .uleb128 0x08
    .uleb128 0x49
    .uleb128 0x13
    .uleb128 0x02
    .uleb128 0x17
    .byte 0, 0
    .byte 0

    .section .debug_info,"",@progbits
.Linfo:
    .4byte .Linfo_end - .Linfo_version
.Linfo_version:
    .2byte 5
    .byte 1 /* DW_UT_compile */
    .byte 4 /* address size */
    .4byte .Labbrev
    .uleb128 1
    .asciz "locations.S"
    .4byte main
    .4byte .Lmain_end - main
    .4byte .Laddr_base
.Lint = . - .Linfo
    .uleb128 2
    .asciz "int"
    .byte 4, 5
.Lint_pointer = . - .Linfo
    .uleb128 3
    .byte 4
    .4byte .Lint
    .uleb128 4
    .asciz "main"
    .4byte main
    .4byte .Lmain_end - main
    .uleb128 1
    .byte 0x58 /* DW_OP_reg8 */

    /* DW_OP_breg8 0; DW_OP_lit16; DW_OP_plus */
    .uleb128 5
    .asciz "v_breg_lit_plus"
    .4byte .Lint
    .uleb128 4
    .byte 0x78, 0x00, 0x40, 0x22

    /* DW_OP_const4u &g_target */
    .uleb128 5
    .asciz "v_const_address"
    .4byte .Lint
    .uleb128 5
    .byte 0x0c
    .4byte g_target

    /* DW_OP_fbreg -8; DW_OP_deref */
    .uleb128 5
    .asciz "v_fbreg_deref"
    .4byte .Lint
    .uleb128 3
    .byte 0x91, 0x78, 0x06

    /* DW_OP_addr &g_target; DW_OP_stack_value */
    .uleb128 5
    .asciz "v_addr_stack_value"
    .4byte .Lint_pointer
    .uleb128 6
    .byte 0x03
    .4byte g_target
    .byte 0x9f

    /* DW_OP_reg10: a pointer held in a register */
    .uleb128 5
    .asciz "v_register_pointer"
    .4byte .Lint_pointer
    .uleb128 1
    .byte 0x5a

    /* Parameter that shares its name with a global symbol: DW_OP_fbreg -12 */
    .uleb128 6
    .asciz "g_target"
    .4byte .Lint
    .uleb128 2
    .byte 0x91, 0x74

    /* Optimized-out local that shares its name with a global symbol */
    .uleb128 7
    .asciz "g_shadow"
    .4byte .Lint

    /* Location list: DW_LLE_base_addressx, then [main+8, main+16): DW_OP_breg8 4 */
    .uleb128 8
    .asciz "v_location_list"
    .4byte .Lint
    .4byte .Llocation_list

    .byte 0 /* end of main's children */
    .byte 0 /* end of the compile unit's children */
.Linfo_end:

    .section .debug_addr,"",@progbits
    .4byte .Laddr_end - .Laddr_version
.Laddr_version:
    .2byte 5
    .byte 4, 0
.Laddr_base:
    .4byte main
.Laddr_end:

    .section .debug_loclists,"",@progbits
    .4byte .Lloclists_end - .Lloclists_version
.Lloclists_version:
    .2byte 5
    .byte 4, 0
    .4byte 0
.Llocation_list:
    .byte 1 /* DW_LLE_base_addressx */
    .uleb128 0
    .byte 4 /* DW_LLE_offset_pair */
    .uleb128 8
    .uleb128 16
    .uleb128 2
    .byte 0x78, 0x04 /* DW_OP_breg8 4 */
    .byte 0 /* DW_LLE_end_of_list */
.Lloclists_end:
"""

# GCC places __thread variables in separate .tdata and .tbss output sections with its default
# linker script. A TLS symbol's value is an offset from the start of the whole TLS block.
TLS_FIXTURE = """
__thread int tls_initialized = 5;
__thread int tls_zeroed;
int main() { return tls_initialized + tls_zeroed; }
"""

S0 = 8
A0 = 10
FRAME_POINTER = 0x8000


class TestDwarfLocations(unittest.TestCase):
    elf: ElfFile
    main: DwarfDie

    @classmethod
    def setUpClass(cls):
        cls.elf = ElfFile(compile_elf(LOCATION_FIXTURE, flags=[], suffix=".S"))
        main_symbol = cls.elf.find_symbol_by_name("main")
        assert main_symbol is not None
        main = cls.elf.dwarf_info.find_function_by_address(main_symbol.value)
        assert main is not None
        cls.main = main

    def setUp(self):
        self.memory = ElfImageMemoryAccess(self.elf, {S0: FRAME_POINTER, A0: 0})
        self.frame = FrameInspection(self.memory)

    def child(self, name: str) -> DwarfDie:
        die = self.main.get_first_child()
        while die is not None:
            if die.name == name:
                return die
            die = die.get_next_sibling()
        raise KeyError(name)

    def symbol_address(self, name: str) -> int:
        symbol = self.elf.find_symbol_by_name(name)
        assert symbol is not None
        return symbol.value

    def test_constant_operand_keeps_address(self):
        # A constant added to a register-relative address is still an address.
        location = evaluate_die_location(self.child("v_breg_lit_plus"), self.frame)
        assert location is not None
        self.assertTrue(location.is_address)
        self.assertEqual(location.value, FRAME_POINTER + 16)

    def test_constant_address_is_address(self):
        # A bare constant without DW_OP_stack_value is the address of the variable.
        g_target = self.symbol_address("g_target")
        location = evaluate_die_location(self.child("v_const_address"), self.frame)
        assert location is not None
        self.assertTrue(location.is_address)
        self.assertEqual(location.value, g_target)
        variable = self.child("v_const_address").read_value(self.frame)
        assert variable is not None
        self.assertEqual(variable.read_value(), 0x11223344)

    def test_deref_result_is_address(self):
        # fbreg -8 holds a pointer to the variable (for example a struct passed by invisible
        # reference); the variable's bytes live where that pointer points.
        g_target = self.symbol_address("g_target")
        self.memory.write_word(FRAME_POINTER - 8, g_target)
        location = evaluate_die_location(self.child("v_fbreg_deref"), self.frame)
        assert location is not None
        self.assertTrue(location.is_address)
        self.assertEqual(location.value, g_target)
        variable = self.child("v_fbreg_deref").read_value(self.frame)
        assert variable is not None
        self.assertEqual(variable.read_value(), 0x11223344)

    def test_address_with_stack_value_is_the_value(self):
        # DW_OP_addr X; DW_OP_stack_value: the pointer's value is X, it is not stored at X.
        g_target = self.symbol_address("g_target")
        die = self.child("v_addr_stack_value")
        self.assertIsNone(die.get_address())
        variable = die.read_value(self.frame)
        assert variable is not None
        self.assertEqual(variable.read_value(), g_target)
        self.assertEqual(variable.dereference().read_value(), 0x11223344)

    def test_parameter_named_like_global_uses_frame_location(self):
        self.memory.write_word(FRAME_POINTER - 12, 1234)
        variable = self.child("g_target").read_value(self.frame)
        assert variable is not None
        self.assertEqual(variable.get_address(), FRAME_POINTER - 12)
        self.assertEqual(variable.read_value(), 1234)

    def test_optimized_out_local_named_like_global_has_no_value(self):
        self.assertIsNone(self.child("g_shadow").read_value(self.frame))

    def test_register_pointer_dereferences_into_memory(self):
        # a0 holds a null pointer. Dereferencing it must read memory at 0, not the register's own bytes.
        self.memory.write_word(0, 0x12345678)
        variable = self.child("v_register_pointer").read_value(self.frame)
        assert variable is not None
        self.assertEqual(variable.read_value(), 0)
        self.assertEqual(variable.dereference().read_value(), 0x12345678)

    def test_location_list_after_base_address_entry(self):
        main_address = self.symbol_address("main")
        fde = self.elf.get_frame_description(main_address + 8, self.memory)
        assert fde is not None
        frame = FrameInspection(self.memory, FrameSnapshot(fde, FRAME_POINTER, main_address + 8))
        self.memory.write_word(FRAME_POINTER + 4, 77)
        location = evaluate_die_location(self.child("v_location_list"), frame)
        assert location is not None
        self.assertTrue(location.is_address)
        self.assertEqual(location.value, FRAME_POINTER + 4)

        # Outside the only bounded entry the variable has no location.
        fde = self.elf.get_frame_description(main_address, self.memory)
        assert fde is not None
        frame = FrameInspection(self.memory, FrameSnapshot(fde, FRAME_POINTER, main_address))
        self.assertIsNone(evaluate_die_location(self.child("v_location_list"), frame))


class TestThreadLocalAddress(unittest.TestCase):
    def test_tbss_variable_address_is_relative_to_tls_block(self):
        elf = ElfFile(compile_elf(TLS_FIXTURE, flags=["-O0", "-g"]))
        tdata = elf.get_section_by_name(".tdata")
        tbss = elf.get_section_by_name(".tbss")
        assert tdata is not None and tbss is not None
        self.assertNotEqual(tdata.address, tbss.address)
        # The TLS block starts at .tdata, which comes first in the TLS segment.
        for name in ("tls_initialized", "tls_zeroed"):
            symbol = elf.find_symbol_by_name(name)
            die = elf.find_die_by_name(name)
            assert symbol is not None and die is not None
            self.assertEqual(die.get_address(), tdata.address + symbol.value, name)


if __name__ == "__main__":
    unittest.main()
