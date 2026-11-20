# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Device-free tests for DWARF attribute decoding and enum / constant lookups."""
import unittest

from test.ttexalens.unit_tests.compiled_elf import ElfImageMemoryAccess, compile_elf
from ttexalens.elf import DwarfAttribute, DwarfAttributeForm, DwarfAttributeTag, DwarfDie, DwarfDieTag, ElfFile

from parameterized import parameterized

ENUMS_SOURCE = """
#include <stdint.h>

// Several enumerators share the value -1, so GCC (DWARF 5) emits one abbreviation for them
// with DW_AT_const_value as DW_FORM_implicit_const -1.
enum class EnumA : int { A_ZERO = 0, A_INVALID = -1 };
enum class EnumB : int { B_ZERO = 0, B_INVALID = -1 };
enum class EnumC : int { C_ZERO = 0, C_INVALID = -1 };

// Large negative enumerator, emitted as DW_FORM_sdata.
enum signed_enum { NEG = -1000, POS = 1 };

// An enum and a constexpr scalar with the same name (like `enum noc_mode` and `noc_mode`).
enum shadowed_const : uint8_t { SHADOWED_A = 0, SHADOWED_B = 1, SHADOWED_C = 2 };
volatile enum shadowed_const g_shadowed_enum_user = SHADOWED_B;
constexpr uint8_t shadowed_const = 42;

volatile EnumA g_enum_a = EnumA::A_INVALID;
volatile EnumB g_enum_b = EnumB::B_INVALID;
volatile EnumC g_enum_c = EnumC::C_INVALID;
volatile signed_enum g_signed_enum = NEG;

// Unsigned one-byte attribute values above 127 (DW_AT_byte_size 200 as DW_FORM_data1).
struct Big { char bytes[200]; };
volatile Big g_big;

int main() { return shadowed_const + static_cast<int>(g_enum_a) + static_cast<int>(g_enum_b) +
                    static_cast<int>(g_enum_c) + g_signed_enum + g_shadowed_enum_user + g_big.bytes[0]; }
"""

TYPE_UNITS_SOURCE = """
struct InTypeUnit { int first; int second; };
InTypeUnit g_in_type_unit = {1, 2};
int main() { return g_in_type_unit.first; }
"""


def find_die(elf: ElfFile, name: str) -> DwarfDie:
    die = elf.dwarf_info.get_die_by_name(name)
    assert die is not None, name
    return die


def find_attribute(die: DwarfDie, tag: DwarfAttributeTag) -> DwarfAttribute:
    attribute = die.get_attribute(tag)
    assert attribute is not None, tag
    return attribute


class TestDwarfAttributes(unittest.TestCase):
    @parameterized.expand([("O0", ["-O0", "-g"]), ("O2", ["-O2", "-g"])])
    def test_negative_shared_enumerator_value(self, _name, flags):
        elf = ElfFile(compile_elf(ENUMS_SOURCE, flags))
        attribute = find_attribute(find_die(elf, "EnumA::A_INVALID"), DwarfAttributeTag.const_value)
        self.assertEqual(attribute.value, -1)
        self.assertEqual(elf.get_enum_value("EnumA::A_INVALID"), -1)
        self.assertEqual(elf.get_enum_value("EnumC::C_INVALID"), -1)
        self.assertEqual(elf.get_enum_value("EnumA::A_ZERO"), 0)

    @parameterized.expand([("O0", ["-O0", "-g"]), ("O2", ["-O2", "-g"])])
    def test_enum_variable_holding_negative_value_prints_enumerator(self, _name, flags):
        elf = ElfFile(compile_elf(ENUMS_SOURCE, flags))
        memory = ElfImageMemoryAccess(elf)
        self.assertEqual(str(elf.get_global("g_enum_a", memory)), "EnumA::A_INVALID")
        self.assertEqual(str(elf.get_global("g_enum_c", memory)), "EnumC::C_INVALID")
        self.assertEqual(str(elf.get_global("g_signed_enum", memory)), "signed_enum::NEG")

    def test_negative_enum_value_keeps_sign(self):
        elf = ElfFile(compile_elf(ENUMS_SOURCE))
        self.assertEqual(elf.get_enum_value("signed_enum::NEG"), -1000)
        self.assertEqual(elf.dwarf_info.get_enum_value("signed_enum::POS"), 1)

    def test_enum_value_skips_same_named_type(self):
        # At -O2 the constant carries DW_AT_const_value; the enum type with the same name comes first in DWARF.
        elf = ElfFile(compile_elf(ENUMS_SOURCE, ["-O2", "-g"]))
        self.assertEqual(elf.get_enum_value("shadowed_const"), 42)
        self.assertEqual(elf.get_enum_value("shadowed_const::SHADOWED_B"), 1)

    @parameterized.expand([("O0", ["-O0", "-g"]), ("O2", ["-O2", "-g"])])
    def test_unsigned_data_forms_stay_unsigned(self, _name, flags):
        elf = ElfFile(compile_elf(ENUMS_SOURCE, flags))
        byte_size = find_attribute(find_die(elf, "Big"), DwarfAttributeTag.byte_size)
        self.assertEqual(byte_size.form, DwarfAttributeForm.data1)
        self.assertEqual(byte_size.value, 200)
        self.assertEqual(elf.get_global("g_big", ElfImageMemoryAccess(elf)).get_size(), 200)

    def test_section_offset_attribute_has_value(self):
        elf = ElfFile(compile_elf(ENUMS_SOURCE))
        unit = find_die(elf, "g_enum_a").cu
        assert unit is not None
        compile_unit = unit.die
        assert compile_unit is not None
        stmt_list = find_attribute(compile_unit, DwarfAttributeTag.stmt_list)
        self.assertEqual(stmt_list.form, DwarfAttributeForm.sec_offset)
        offset = stmt_list.value
        assert isinstance(offset, int)
        line_section = elf.get_section_by_name(".debug_line")
        assert line_section is not None
        self.assertLess(offset, line_section.size)

    def test_type_reference_into_other_section_is_not_a_debug_info_offset(self):
        # DWARF 4 type units live in .debug_types; a DW_FORM_ref_sig8 reference resolves to an offset in that
        # section, which must not be looked up as a .debug_info DIE.
        elf = ElfFile(compile_elf(TYPE_UNITS_SOURCE, ["-O2", "-gdwarf-4", "-fdebug-types-section"]))
        variable = find_die(elf, "g_in_type_unit")
        type_attribute = find_attribute(variable, DwarfAttributeTag.type)
        self.assertEqual(type_attribute.form, DwarfAttributeForm.ref_sig8)
        self.assertIsNone(type_attribute.value)
        type_die = variable.get_die_from_attribute(DwarfAttributeTag.type)
        if type_die is not None:
            self.assertEqual(type_die.get_readable_name(), "InTypeUnit")

    def test_die_tags_sharing_a_value_are_one_member(self):
        self.assertIs(DwarfDieTag.TI_near_type, DwarfDieTag.MIPS_loop)
        self.assertEqual(DwarfDieTag(0x4081), DwarfDieTag.TI_near_type)
        self.assertEqual(DwarfDieTag(0x4081), DwarfDieTag.MIPS_loop)

    def test_attribute_tags_sharing_a_value_are_one_member(self):
        self.assertIs(DwarfAttributeTag.MIPS_linkage_name, DwarfAttributeTag.ghs_mangled)
        self.assertIs(DwarfAttributeTag.stride, DwarfAttributeTag.byte_stride)
        self.assertIs(DwarfAttributeTag.stride_size, DwarfAttributeTag.bit_stride)
        self.assertEqual(DwarfAttributeTag(0x2007), DwarfAttributeTag.MIPS_linkage_name)

    @parameterized.expand([(DwarfDieTag,), (DwarfAttributeTag,), (DwarfAttributeForm,)])
    def test_every_shared_value_is_one_member(self, enum_type):
        for name, member in vars(enum_type).items():
            if isinstance(member, enum_type):
                self.assertIs(member, enum_type(member.value), f"{enum_type.__name__}.{name}")
                self.assertIs(enum_type[name], member, f"{enum_type.__name__}.{name}")

    def test_linkage_name_attribute_from_dwarf_3(self):
        # GCC writes DW_AT_MIPS_linkage_name before DWARF 4; it must compare equal to that name.
        source = "namespace ns { int f(int x) { return x + 1; } }\nint main() { return ns::f(1); }\n"
        elf = ElfFile(compile_elf(source, ["-O0", "-gdwarf-3"]))
        found = False
        unit = find_die(elf, "ns::f").cu
        assert unit is not None
        root = unit.die
        assert root is not None
        pending = [root]
        while pending and not found:
            die = pending.pop()
            found = any(a.tag == DwarfAttributeTag.MIPS_linkage_name for a in die.attributes)
            pending.extend(die.iter_children())
        self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
