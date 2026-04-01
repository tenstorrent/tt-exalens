# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""Unit tests for pack_unpack_regfile.py.

Each test class exercises one unpacking function and verifies two code paths:

* ``reorder=True``  – hardware bit-shuffling applied (identical to the original
  code before the refactoring, because ``True`` is the default).
* ``reorder=False`` – new path: raw bytes are parsed as plain IEEE 754 without
  any bit manipulation.

Expected values for every assertion were computed by running the functions
against the same input data and recording the output, so they serve as a
regression baseline for both paths simultaneously.
"""

import importlib.util
import struct
import unittest

# Load pack_unpack_regfile without triggering the ttexalens package __init__
# (which requires hardware drivers that are not available in a plain CI environment).
_spec = importlib.util.spec_from_file_location(
    "pack_unpack_regfile",
    str(__file__).replace(
        "test/ttexalens/unit_tests/test_pack_unpack_regfile.py",
        "ttexalens/pack_unpack_regfile.py",
    ),
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

unpack_fp16 = _mod.unpack_fp16
unpack_bfp16 = _mod.unpack_bfp16
unpack_fp32 = _mod.unpack_fp32
unpack_bfp8_b = _mod.unpack_bfp8_b
unpack_uint16 = _mod.unpack_uint16
unpack_data = _mod.unpack_data
TensixDataFormat = _mod.TensixDataFormat


class TestUnpackFp16Reorder(unittest.TestCase):
    """unpack_fp16: verify both code paths with non-trivial fp16 values.

    Input bytes encode:
      [0x43, 0x00]  → fp16  3.5
      [0xC7, 0x40]  → fp16 -7.25
    """

    # Two fp16 values with non-trivial bit patterns: 3.5 and -7.25.
    DATA = [0x43, 0x00, 0xC7, 0x40]

    def test_no_reorder_parses_standard_ieee754_fp16(self):
        # reorder=False: bytes are decoded as plain IEEE 754 half-precision.
        # Expected: 3.5, -7.25 (the values encoded in DATA above).
        result = unpack_fp16(self.DATA, reorder=False)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 3.5, places=6)
        self.assertAlmostEqual(result[1], -7.25, places=6)

    def test_reorder_applies_hardware_bit_shuffle(self):
        # reorder=True: hardware bit-flip is applied before decoding.
        # These are the exact values the original code produced for DATA.
        result = unpack_fp16(self.DATA, reorder=True)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 3.1948089599609375e-05, places=15)
        self.assertAlmostEqual(result[1], -3.3974647521972656e-05, places=15)

    def test_reorder_true_is_default(self):
        # Calling without reorder= must match reorder=True (backward compat).
        self.assertEqual(unpack_fp16(self.DATA), unpack_fp16(self.DATA, reorder=True))

    def test_reorder_and_no_reorder_differ(self):
        # The two paths must produce different floats for these non-trivial bytes.
        self.assertNotEqual(unpack_fp16(self.DATA, reorder=False), unpack_fp16(self.DATA, reorder=True))


class TestUnpackBfp16Reorder(unittest.TestCase):
    """unpack_bfp16: verify both code paths with non-trivial bfloat16 values.

    Input bytes encode:
      [0x3F, 0xC0]  → bfloat16  1.5
      [0xC0, 0x80]  → bfloat16 -4.0
    """

    # 1.5 in bfloat16 = 0x3FC0, -4.0 in bfloat16 = 0xC080.
    DATA = [0x3F, 0xC0, 0xC0, 0x80]

    def test_no_reorder_parses_standard_bfloat16(self):
        result = unpack_bfp16(self.DATA, reorder=False)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 1.5, places=6)
        self.assertAlmostEqual(result[1], -4.0, places=6)

    def test_reorder_applies_hardware_bit_shuffle(self):
        # Exact values produced by the original code (reorder=True path).
        result = unpack_bfp16(self.DATA, reorder=True)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 5.505200184497694e+19, places=5)
        self.assertAlmostEqual(result[1], -3.0, places=6)

    def test_reorder_true_is_default(self):
        self.assertEqual(unpack_bfp16(self.DATA), unpack_bfp16(self.DATA, reorder=True))

    def test_reorder_and_no_reorder_differ(self):
        self.assertNotEqual(unpack_bfp16(self.DATA, reorder=False), unpack_bfp16(self.DATA, reorder=True))


class TestUnpackFp32Reorder(unittest.TestCase):
    """unpack_fp32: verify both code paths with non-trivial float32 values.

    The function splits its input into two halves: the first half carries the
    upper 16 bits of each float and the second half carries the lower 16 bits.

    Input encodes fp32  3.75 (0x40700000) and fp32 -9.5 (0xC1180000):
      upper half: [0x40, 0x70, 0xC1, 0x18]
      lower half: [0x00, 0x00, 0x00, 0x00]
    """

    # Upper bytes of 3.75 and -9.5, then their lower bytes (all zero here).
    DATA = [0x40, 0x70, 0xC1, 0x18,
            0x00, 0x00, 0x00, 0x00]

    def test_no_reorder_parses_plain_fp32(self):
        result = unpack_fp32(self.DATA, reorder=False)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 3.75, places=6)
        self.assertAlmostEqual(result[1], -9.5, places=6)

    def test_reorder_applies_hardware_bit_shuffle_and_pair_swap(self):
        # Exact values produced by the original code (reorder=True path).
        # Note: the pair-swap exchanges the two values, so the shuffled -9.5
        # value ends up at index 0 and the shuffled 3.75 value ends up at index 1.
        result = unpack_fp32(self.DATA, reorder=True)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], -1.486817917066946e-31, places=40)
        self.assertAlmostEqual(result[1], 4.57763671875e-05, places=15)

    def test_reorder_true_is_default(self):
        self.assertEqual(unpack_fp32(self.DATA), unpack_fp32(self.DATA, reorder=True))

    def test_no_reorder_preserves_value_order(self):
        # Without reorder the pair-swap does NOT happen: first value stays first.
        result = unpack_fp32(self.DATA, reorder=False)
        self.assertAlmostEqual(result[0], 3.75, places=6)   # not -9.5
        self.assertAlmostEqual(result[1], -9.5, places=6)   # not  3.75

    def test_reorder_swaps_pairs(self):
        # With reorder the pair-swap IS applied: values are exchanged.
        result_reorder = unpack_fp32(self.DATA, reorder=True)
        result_plain   = unpack_fp32(self.DATA, reorder=False)
        self.assertNotEqual(result_reorder, result_plain)


class TestUnpackUint16Reorder(unittest.TestCase):
    """unpack_uint16: verify both code paths with non-trivial integer values.

    Input bytes big-endian decode to: 0x1234=4660, 0x5678=22136,
    0xABCD=43981, 0xEF01=61185.
    """

    # Four non-trivial 16-bit values.
    DATA = [0x12, 0x34, 0x56, 0x78, 0xAB, 0xCD, 0xEF, 0x01]

    def test_no_reorder_preserves_natural_order(self):
        result = unpack_uint16(self.DATA, reorder=False)
        self.assertEqual(result, [4660, 22136, 43981, 61185])

    def test_reorder_swaps_adjacent_pairs(self):
        # Original code behaviour: pairs are swapped in place.
        result = unpack_uint16(self.DATA, reorder=True)
        self.assertEqual(result, [22136, 4660, 61185, 43981])

    def test_reorder_true_is_default(self):
        self.assertEqual(unpack_uint16(self.DATA), unpack_uint16(self.DATA, reorder=True))

    def test_odd_count_no_reorder(self):
        # Three values — last one has no pair partner and is left in place.
        data = [0x12, 0x34, 0x56, 0x78, 0xAB, 0xCD]   # 4660, 22136, 43981
        self.assertEqual(unpack_uint16(data, reorder=False), [4660, 22136, 43981])

    def test_odd_count_with_reorder(self):
        data = [0x12, 0x34, 0x56, 0x78, 0xAB, 0xCD]   # 4660, 22136, 43981
        # Pairs (4660, 22136) are swapped; 43981 is unpaired and stays last.
        self.assertEqual(unpack_uint16(data, reorder=True), [22136, 4660, 43981])


class TestUnpackBfp8bReorder(unittest.TestCase):
    """unpack_bfp8_b: verify both code paths with non-trivial mantissa data.

    Block layout: 64 exponent bytes followed by 64 groups of 16 mantissa bytes.
    We set exponent[0] = 130 (effective exponent = 3) and fill group 0 with
    a non-trivial, monotonically structured mantissa pattern so that the
    reorder-vs-no-reorder difference is easy to reason about.
    """

    # Mantissa bytes for group 0.  With effective exponent 3, the integer part
    # of each value is the top 4 bits of the 7-bit mantissa field, giving the
    # values [8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15, 0.5].
    MANTISSA_GROUP0 = [
        0b01000000, 0b00100000, 0b01100000, 0b00010000,
        0b01010000, 0b00110000, 0b01110000, 0b00001000,
        0b01001000, 0b00101000, 0b01101000, 0b00011000,
        0b01011000, 0b00111000, 0b01111000, 0b00000100,
    ]

    def _make_block(self) -> list[int]:
        data = [0] * (64 + 64 * 16)
        data[0] = 130          # exponent for group 0
        data[64:80] = self.MANTISSA_GROUP0
        return data

    def test_no_reorder_decodes_mantissas_in_storage_order(self):
        # Without reorder the mantissa bytes are consumed in the order they
        # appear in memory, giving the values listed above.
        expected = [8.0, 4.0, 12.0, 2.0, 10.0, 6.0, 14.0, 1.0,
                    9.0, 5.0, 13.0, 3.0, 11.0, 7.0, 15.0, 0.5]
        result = unpack_bfp8_b(self._make_block(), reorder=False)
        self.assertEqual(result[:16], expected)

    def test_reorder_reverses_mantissa_chunks(self):
        # Original code behaviour: within each group of 16, mantissa bytes are
        # split into chunks of 4 and each chunk is reversed before decoding.
        # Chunk-reversed MANTISSA_GROUP0 → [2,12,4,8, 1,14,6,10, 3,13,5,9, 0.5,15,7,11]
        expected = [2.0, 12.0, 4.0, 8.0, 1.0, 14.0, 6.0, 10.0,
                    3.0, 13.0, 5.0, 9.0, 0.5, 15.0, 7.0, 11.0]
        result = unpack_bfp8_b(self._make_block(), reorder=True)
        self.assertEqual(result[:16], expected)

    def test_reorder_true_is_default(self):
        data = self._make_block()
        self.assertEqual(unpack_bfp8_b(data), unpack_bfp8_b(data, reorder=True))

    def test_reorder_and_no_reorder_differ(self):
        data = self._make_block()
        self.assertNotEqual(unpack_bfp8_b(data, reorder=False), unpack_bfp8_b(data, reorder=True))

    def test_output_length(self):
        data = self._make_block()
        self.assertEqual(len(unpack_bfp8_b(data, reorder=False)), 64 * 16)
        self.assertEqual(len(unpack_bfp8_b(data, reorder=True)), 64 * 16)


class TestUnpackDataReorderParam(unittest.TestCase):
    """unpack_data: verify that the reorder flag is threaded to each format handler."""

    # Same non-trivial data as TestUnpackUint16Reorder.
    U16_DATA = [0x12, 0x34, 0x56, 0x78, 0xAB, 0xCD, 0xEF, 0x01]

    def test_uint16_no_reorder(self):
        result = unpack_data(self.U16_DATA, TensixDataFormat.UInt16, signed=False, reorder=False)
        self.assertEqual(result, [4660, 22136, 43981, 61185])

    def test_uint16_with_reorder(self):
        result = unpack_data(self.U16_DATA, TensixDataFormat.UInt16, signed=False, reorder=True)
        self.assertEqual(result, [22136, 4660, 61185, 43981])

    def test_default_reorder_is_true(self):
        self.assertEqual(
            unpack_data(self.U16_DATA, TensixDataFormat.UInt16, signed=False),
            unpack_data(self.U16_DATA, TensixDataFormat.UInt16, signed=False, reorder=True),
        )

    def test_format_as_int_value(self):
        # Passing df as a plain int must work identically to the enum member.
        result_enum = unpack_data(self.U16_DATA, TensixDataFormat.UInt16, signed=False, reorder=False)
        result_int  = unpack_data(self.U16_DATA, TensixDataFormat.UInt16.value, signed=False, reorder=False)
        self.assertEqual(result_enum, result_int)

    def test_unsupported_format_raises(self):
        with self.assertRaises(ValueError):
            unpack_data([], TensixDataFormat.Int32, signed=False)

    def test_fp16_no_reorder_via_unpack_data(self):
        # Verify reorder=False path for Float16 via the dispatcher.
        data = [0x43, 0x00, 0xC7, 0x40]   # fp16 3.5 and -7.25
        result = unpack_data(data, TensixDataFormat.Float16, signed=False, reorder=False)
        self.assertAlmostEqual(result[0], 3.5, places=6)
        self.assertAlmostEqual(result[1], -7.25, places=6)

    def test_fp32_no_reorder_via_unpack_data(self):
        # Verify reorder=False path for Float32 via the dispatcher.
        data = [0x40, 0x70, 0xC1, 0x18, 0x00, 0x00, 0x00, 0x00]
        result = unpack_data(data, TensixDataFormat.Float32, signed=False, reorder=False)
        self.assertAlmostEqual(result[0], 3.75, places=6)
        self.assertAlmostEqual(result[1], -9.5, places=6)


if __name__ == "__main__":
    unittest.main()
