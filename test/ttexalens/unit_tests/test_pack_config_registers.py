# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest

from parameterized import parameterized
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.wormhole import functional_worker_registers as wormhole_registers
from ttexalens.register_store import ConfigurationRegisterDescription

# Fields of the third word of each Wormhole packer configuration: (name, mask) per bank,
# for the banks at config words 58 and 98 (with the zero-compress override) and at 86 and 126.
_COMMON_FIELDS = [
    ("uncompress", 0x1),
    ("add_l1_dest_addr_offset", 0x2),
    ("addr_cnt_context", 0xC),
    ("out_data_format", 0xF0),
    ("in_data_format", 0xF00),
    ("dis_shared_exp_assembler", 0x1000),
    ("force_pack_per_max_xy_plane", 0x2000),
    ("enable_out_fifo", 0x4000),
    ("sub_l1_tile_header_size", 0x8000),
    ("src_if_sel", 0x10000),
    ("l1_src_addr", 0xFF000000),
]
WORMHOLE_PACK_CONFIG_WORD_2_FIELDS = {
    ("01", 58): _COMMON_FIELDS
    + [
        ("all_pack_disable_zero_compress", 0x1E0000),
        ("all_pack_disable_zero_compress_ovrd", 0x200000),
        ("add_tile_header_size", 0x400000),
    ],
    ("11", 98): _COMMON_FIELDS
    + [
        ("all_pack_disable_zero_compress", 0x1E0000),
        ("all_pack_disable_zero_compress_ovrd", 0x200000),
        ("add_tile_header_size", 0x400000),
    ],
    ("08", 86): _COMMON_FIELDS + [("add_tile_header_size", 0x20000)],
    ("18", 126): _COMMON_FIELDS + [("add_tile_header_size", 0x20000)],
}


class TestWormholePackConfigRegisters(unittest.TestCase):
    @parameterized.expand(list(WORMHOLE_PACK_CONFIG_WORD_2_FIELDS.items()))
    def test_pack_config_word_2_fields(self, bank: tuple[str, int], expected_fields: list[tuple[str, int]]):
        """Every field of the word has its name, mask and shift, and no other name covers its bits."""
        bank_name, index = bank
        prefix = f"PACK_CONFIG{bank_name}_"
        actual_fields = {
            name[len(prefix) :]: (description.mask, description.shift)
            for name, description in wormhole_registers.register_map.items()
            if name.startswith(prefix)
            and isinstance(description, ConfigurationRegisterDescription)
            and description.index == index
        }
        expected = {name: (mask, (mask & -mask).bit_length() - 1) for name, mask in expected_fields}
        self.assertEqual(actual_fields, expected)

    def test_pack_config_table_fields(self):
        """dump-tensix-state shows the fields of each bank under their own names."""
        for config in wormhole_registers.get_pack_config():
            for field, register_name in config.items():
                self.assertIn(register_name, wormhole_registers.register_map)
                self.assertTrue(register_name.endswith("_" + field))
        names = set(wormhole_registers.get_pack_config()[0])
        self.assertNotIn("reserved_0", names)
        self.assertNotIn("reserved_1", names)
        self.assertNotIn("pack_per_xy_plane", names)

    @parameterized.expand(list(WORMHOLE_PACK_CONFIG_WORD_2_FIELDS.items()))
    def test_pack_config_word_2_fields_on_device(self, bank: tuple[str, int], expected_fields: list[tuple[str, int]]):
        """Each field reads its own bits of the config word on the device."""
        device = init_cached_test_context().devices[0]
        if not device.is_wormhole():
            self.skipTest("Checks the Wormhole register map.")
        bank_name, index = bank
        location = OnChipCoordinate.create("0,0", device=device)
        register_store = location.noc_block.get_register_store()
        word = ConfigurationRegisterDescription(index=index)
        self.addCleanup(register_store.write_register, word, register_store.read_register(word))
        for name, mask in expected_fields:
            # Set only the field's top bit, so that a field read from other bits reads 0
            value = 1 << (mask.bit_length() - 1)
            register_store.write_register(word, value)
            field_value = register_store.read_register(f"PACK_CONFIG{bank_name}_{name}")
            self.assertEqual(field_value, 1 << (mask.bit_length() - 1 - ((mask & -mask).bit_length() - 1)), name)
