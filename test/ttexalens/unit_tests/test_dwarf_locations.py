# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import struct
import unittest

from parameterized import parameterized

from ttexalens.elf import ElfFile, ElfVariable, FrameInspection
from ttexalens.memory_access import MemoryAccess

SHT_PROGBITS = 1
SHT_SYMTAB = 2
SHT_STRTAB = 3
SHT_NOBITS = 8
SHF_WRITE_ALLOC = 0x3
SHF_TLS = 0x400
PT_TLS = 7
STB_GLOBAL = 1
STT_OBJECT = 1
STT_TLS = 6

DW_TAG_formal_parameter = 0x05
DW_TAG_member = 0x0D
DW_TAG_pointer_type = 0x0F
DW_TAG_compile_unit = 0x11
DW_TAG_structure_type = 0x13
DW_TAG_base_type = 0x24
DW_TAG_subprogram = 0x2E
DW_TAG_variable = 0x34

DW_AT_location = 0x02
DW_AT_name = 0x03
DW_AT_byte_size = 0x0B
DW_AT_data_member_location = 0x38
DW_AT_encoding = 0x3E
DW_AT_frame_base = 0x40
DW_AT_type = 0x49
DW_AT_addr_base = 0x73

DW_FORM_string = 0x08
DW_FORM_data1 = 0x0B
DW_FORM_ref4 = 0x13
DW_FORM_sec_offset = 0x17
DW_FORM_exprloc = 0x18

DW_UT_compile = 0x01
DW_ATE_signed_char = 0x06
DW_ATE_unsigned = 0x07

DW_OP_addr = 0x03
DW_OP_deref = 0x06
DW_OP_const4u = 0x0C
DW_OP_plus = 0x22
DW_OP_lit16 = 0x40
DW_OP_reg10 = 0x5A
DW_OP_breg2 = 0x72
DW_OP_breg8 = 0x78
DW_OP_fbreg = 0x91
DW_OP_stack_value = 0x9F

DW_LLE_end_of_list = 0x00
DW_LLE_base_addressx = 0x01
DW_LLE_offset_pair = 0x04

MEMORY = {
    0x0: 0x55555555,
    0x0FE0: 0x77777777,
    0x0FF0: 0x6000,
    0x2010: 0x11111111,
    0x3000: 0x66666666,
    0x5000: 0x22222222,
    0x6000: 0x33333333,
    0x6004: 0x44444444,
}

REGISTERS = {2: 0x1000, 8: 0x2000, 10: 0}

Attribute = tuple[int, int, bytes]


def at_name(name: str) -> Attribute:
    return DW_AT_name, DW_FORM_string, name.encode() + b"\0"


def at_type(offset: int) -> Attribute:
    return DW_AT_type, DW_FORM_ref4, struct.pack("<I", offset)


def at_data1(attribute: int, value: int) -> Attribute:
    return attribute, DW_FORM_data1, bytes([value])


def at_expr(attribute: int, expression: bytes) -> Attribute:
    return attribute, DW_FORM_exprloc, bytes([len(expression)]) + expression


def at_sec_offset(attribute: int, offset: int) -> Attribute:
    return attribute, DW_FORM_sec_offset, struct.pack("<I", offset)


class DwarfUnit:
    def __init__(self) -> None:
        self.info = bytearray(struct.pack("<IHBBI", 0, 5, DW_UT_compile, 4, 0))
        self.abbrev = bytearray()
        self.code = 0

    def die(self, tag: int, attributes: list[Attribute], children: bool = False) -> int:
        offset = len(self.info)
        self.code += 1
        forms = [number for attribute, form, _ in attributes for number in (attribute, form)]
        self.abbrev += bytes([self.code, tag, children, *forms, 0, 0])
        self.info += bytes([self.code]) + b"".join(value for _, _, value in attributes)
        return offset

    def end_children(self) -> None:
        self.info += b"\0"


def build_elf() -> bytes:
    const_address = struct.pack("<BI", DW_OP_const4u, 0x5000)
    stack_value = struct.pack("<BIB", DW_OP_addr, 0x5000, DW_OP_stack_value)
    frame_slot = bytes([DW_OP_fbreg, -32 & 0x7F])

    unit = DwarfUnit()
    unit.die(DW_TAG_compile_unit, [at_sec_offset(DW_AT_addr_base, 8)], children=True)
    uint = unit.die(
        DW_TAG_base_type,
        [at_name("unsigned int"), at_data1(DW_AT_byte_size, 4), at_data1(DW_AT_encoding, DW_ATE_unsigned)],
    )
    uint_ptr = unit.die(DW_TAG_pointer_type, [at_data1(DW_AT_byte_size, 4), at_type(uint)])
    char = unit.die(
        DW_TAG_base_type, [at_name("char"), at_data1(DW_AT_byte_size, 1), at_data1(DW_AT_encoding, DW_ATE_signed_char)]
    )
    char_ptr = unit.die(DW_TAG_pointer_type, [at_data1(DW_AT_byte_size, 4), at_type(char)])
    pair = unit.die(DW_TAG_structure_type, [at_name("Pair"), at_data1(DW_AT_byte_size, 8)], children=True)
    unit.die(DW_TAG_member, [at_name("a"), at_type(uint), at_data1(DW_AT_data_member_location, 0)])
    unit.die(DW_TAG_member, [at_name("b"), at_type(uint), at_data1(DW_AT_data_member_location, 4)])
    unit.end_children()
    unit.die(DW_TAG_variable, [at_name("tls_bss_var"), at_type(uint)])
    unit.die(DW_TAG_variable, [at_name("g_value"), at_type(uint), at_expr(DW_AT_location, stack_value)])
    unit.die(DW_TAG_subprogram, [at_name("fn"), at_expr(DW_AT_frame_base, bytes([DW_OP_breg2, 0]))], children=True)
    for tag, name, type_offset, location in [
        (DW_TAG_formal_parameter, "p_breg", uint, bytes([DW_OP_breg8, 0, DW_OP_lit16, DW_OP_plus])),
        (DW_TAG_formal_parameter, "p_const", uint, const_address),
        (DW_TAG_formal_parameter, "p_ref", pair, bytes([DW_OP_fbreg, -16 & 0x7F, DW_OP_deref])),
        (DW_TAG_formal_parameter, "p_regptr", uint_ptr, bytes([DW_OP_reg10])),
        (DW_TAG_formal_parameter, "p_regstr", char_ptr, bytes([DW_OP_reg10])),
        (DW_TAG_formal_parameter, "shadow", uint, frame_slot),
        (DW_TAG_variable, "v_stack", uint, stack_value),
    ]:
        unit.die(tag, [at_name(name), at_type(type_offset), at_expr(DW_AT_location, location)])
    unit.die(DW_TAG_variable, [at_name("v_list"), at_type(uint), at_sec_offset(DW_AT_location, 12)])
    unit.end_children()
    unit.die(DW_TAG_subprogram, [at_name("fn2")], children=True)
    unit.die(DW_TAG_variable, [at_name("shadow"), at_type(uint)])
    unit.end_children()
    unit.end_children()
    struct.pack_into("<I", unit.info, 0, len(unit.info) - 4)

    loclist = (
        bytes([DW_LLE_base_addressx, 0, DW_LLE_offset_pair, 0, 0x10, len(const_address)])
        + const_address
        + bytes([DW_LLE_base_addressx, 1, DW_LLE_offset_pair, 0, 0x10, len(frame_slot)])
        + frame_slot
        + bytes([DW_LLE_end_of_list])
    )
    tls = SHF_WRITE_ALLOC | SHF_TLS
    sections = [
        (".tdata", SHT_PROGBITS, tls, 0x2000, bytes(8)),
        (".tbss", SHT_NOBITS, tls, 0x2008, bytes(4)),
        (".bss", SHT_NOBITS, SHF_WRITE_ALLOC, 0x3000, bytes(4)),
        (".debug_info", SHT_PROGBITS, 0, 0, bytes(unit.info)),
        (".debug_abbrev", SHT_PROGBITS, 0, 0, bytes(unit.abbrev) + b"\0"),
        (".debug_loclists", SHT_PROGBITS, 0, 0, struct.pack("<IHBBI", 8 + len(loclist), 5, 4, 0, 0) + loclist),
        (".debug_addr", SHT_PROGBITS, 0, 0, struct.pack("<IHBBII", 12, 5, 4, 0, 0x1000, 0)),
    ]
    names = [name for name, *_ in sections] + [".symtab", ".strtab", ".shstrtab"]
    strtab = bytearray(b"\0")
    symtab = bytearray(16)
    for name, value, symbol_type, section in [
        ("shadow", 0x3000, STT_OBJECT, ".bss"),
        ("g_value", 0x3000, STT_OBJECT, ".bss"),
        ("tls_bss_var", 8, STT_TLS, ".tbss"),
    ]:
        symtab += struct.pack(
            "<IIIBBH", len(strtab), value, 4, STB_GLOBAL << 4 | symbol_type, 0, names.index(section) + 1
        )
        strtab += name.encode() + b"\0"
    sections += [
        (".symtab", SHT_SYMTAB, 0, 0, bytes(symtab)),
        (".strtab", SHT_STRTAB, 0, 0, bytes(strtab)),
        (".shstrtab", SHT_STRTAB, 0, 0, b"\0" + b"".join(name.encode() + b"\0" for name in names)),
    ]

    image = bytearray(84)
    headers = bytearray(40)
    offsets: dict[str, int] = {}
    name_offset = 1
    for name, section_type, flags, address, contents in sections:
        image += bytes(-len(image) % 4)
        offsets[name] = len(image)
        link, info, entsize = (names.index(".strtab") + 1, 1, 16) if section_type == SHT_SYMTAB else (0, 0, 0)
        headers += struct.pack(
            "<10I", name_offset, section_type, flags, address, len(image), len(contents), link, info, 4, entsize
        )
        if section_type != SHT_NOBITS:
            image += contents
        name_offset += len(name) + 1
    image += bytes(-len(image) % 4)
    shoff, shnum = len(image), len(names) + 1
    image[0:52] = struct.pack(
        "<16sHHIIIIIHHHHHH", b"\x7fELF\x01\x01\x01", 2, 0xF3, 1, 0, 52, shoff, 0, 52, 32, 1, 40, shnum, shnum - 1
    )
    image[52:84] = struct.pack("<8I", PT_TLS, offsets[".tdata"], 0x2000, 0x2000, 8, 12, 4, 4)
    return bytes(image + headers)


class StubMemoryAccess(MemoryAccess):
    def __init__(self) -> None:
        super().__init__()
        self.bytes = {
            address + i: byte for address, word in MEMORY.items() for i, byte in enumerate(struct.pack("<I", word))
        }

    def read(self, address: int, buffer: memoryview | bytearray) -> None:
        buffer[:] = bytes(self.bytes.get(address + offset, 0) for offset in range(len(buffer)))

    def read_register(self, register_index: int) -> int:
        return REGISTERS.get(register_index, 0)


class TestDwarfLocations(unittest.TestCase):
    elf: ElfFile

    @classmethod
    def setUpClass(cls) -> None:
        cls.elf = ElfFile.from_bytes(build_elf(), "fixture.elf")

    def setUp(self) -> None:
        self.frame = FrameInspection(StubMemoryAccess())

    def read_variable(self, name: str) -> ElfVariable:
        variable = self.elf.find_die_by_name(name).read_value(self.frame)
        assert variable is not None
        return variable

    @parameterized.expand(
        [
            ("fn::p_breg", 0x11111111),
            ("fn::p_const", 0x22222222),
            ("fn::v_stack", 0x5000),
            ("g_value", 0x5000),
            ("fn::shadow", 0x77777777),
            ("fn::v_list", 0x77777777),
        ]
    )
    def test_read_value_from_location(self, name: str, expected: int):
        self.assertEqual(expected, self.read_variable(name).read_value())

    def test_fbreg_deref_location_reads_struct_at_loaded_address(self):
        variable = self.read_variable("fn::p_ref")
        self.assertEqual(0x33333333, variable.a.read_value())
        self.assertEqual(0x44444444, variable.b.read_value())

    def test_register_pointer_reads_device_memory(self):
        pointer = self.read_variable("fn::p_regptr")
        self.assertEqual(0x55555555, pointer.dereference().read_value())
        self.assertEqual(0x55555555, pointer[0].read_value())
        self.assertEqual("UUUU", self.read_variable("fn::p_regstr").read_value())

    def test_value_without_address_is_read_only(self):
        variable = self.read_variable("fn::v_stack")
        with self.assertRaisesRegex(RuntimeError, "no memory address"):
            variable.write_value(1)

    def test_optimized_out_local_named_like_global_has_no_value(self):
        self.assertIsNone(self.elf.find_die_by_name("fn2::shadow").read_value(self.frame))

    def test_tbss_variable_address_is_tls_segment_relative(self):
        self.assertEqual(0x2008, self.elf.find_die_by_name("tls_bss_var").get_address())


if __name__ == "__main__":
    unittest.main()
