# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import importlib.util
import math
import struct
import sys
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

flip_bfp16_bits = _mod.flip_bfp16_bits
flip_fp16_bits = _mod.flip_fp16_bits
reorder_fp32 = _mod.reorder_fp32
unpack_fp16 = _mod.unpack_fp16
unpack_bfp16 = _mod.unpack_bfp16
unpack_fp32 = _mod.unpack_fp32
unpack_bfp8_b = _mod.unpack_bfp8_b
unpack_uint16 = _mod.unpack_uint16
unpack_data = _mod.unpack_data
TensixDataFormat = _mod.TensixDataFormat


def _fp16_bytes(f: float) -> bytes:
    """Pack a Python float as a big-endian IEEE 754 half-precision value."""
    return struct.pack(">e", f)


def _bfp16_bytes(f: float) -> bytes:
    """Pack the upper 2 bytes of a big-endian float32 (= BFloat16)."""
    return struct.pack(">f", f)[:2]


class TestUnpackFp16Reorder(unittest.TestCase):
    """unpack_fp16: verify that reorder=False skips bit-flipping."""

    def test_no_reorder_preserves_standard_fp16(self):
        # 0x3C00 is exactly 1.0 in standard IEEE 754 fp16.
        data = list(b"\x3c\x00")
        result = unpack_fp16(data, reorder=False)
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0], 1.0, places=5)

    def test_reorder_true_is_default(self):
        data = list(b"\x3c\x00")
        self.assertEqual(unpack_fp16(data, reorder=True), unpack_fp16(data))

    def test_reorder_changes_value(self):
        # When the bits are scrambled, applying the flip produces a different
        # float than skipping it.
        data = list(b"\x3c\x00")
        val_with = unpack_fp16(data, reorder=True)
        val_without = unpack_fp16(data, reorder=False)
        self.assertNotAlmostEqual(val_with[0], val_without[0], places=5)

    def test_zero_round_trips(self):
        data = list(b"\x00\x00")
        self.assertEqual(unpack_fp16(data, reorder=False), [0.0])
        self.assertEqual(unpack_fp16(data, reorder=True), [0.0])

    def test_multiple_values(self):
        # Two standard fp16 values, no reorder.
        data = list(b"\x3c\x00" + b"\xc0\x00")  # 1.0, -2.0
        result = unpack_fp16(data, reorder=False)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 1.0, places=5)
        self.assertAlmostEqual(result[1], -2.0, places=5)


class TestUnpackBfp16Reorder(unittest.TestCase):
    """unpack_bfp16: verify that reorder=False skips bit-flipping."""

    def test_no_reorder_preserves_standard_bfloat16(self):
        # 0x3F80 is exactly 1.0 in BFloat16.
        data = list(b"\x3f\x80")
        result = unpack_bfp16(data, reorder=False)
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result[0], 1.0, places=5)

    def test_reorder_true_is_default(self):
        data = list(b"\x3f\x80")
        self.assertEqual(unpack_bfp16(data, reorder=True), unpack_bfp16(data))

    def test_reorder_changes_value(self):
        data = list(b"\x3f\x80")
        val_with = unpack_bfp16(data, reorder=True)
        val_without = unpack_bfp16(data, reorder=False)
        self.assertNotAlmostEqual(val_with[0], val_without[0], places=5)

    def test_zero_round_trips(self):
        data = list(b"\x00\x00")
        self.assertEqual(unpack_bfp16(data, reorder=False), [0.0])
        self.assertEqual(unpack_bfp16(data, reorder=True), [0.0])


class TestUnpackFp32Reorder(unittest.TestCase):
    """unpack_fp32: verify that reorder=False skips bit-reordering."""

    def _encode_fp32_no_reorder(self, f: float) -> list[int]:
        """Produce the raw byte layout that unpack_fp32(reorder=False) expects."""
        raw = struct.pack(">f", f)
        # unpack_fp32 splits the buffer in half: first half = upper 16 bits,
        # second half = lower 16 bits, iterating in pairs of 2-byte words.
        upper = list(raw[:2])
        lower = list(raw[2:])
        return upper + lower

    def test_no_reorder_parses_plain_fp32(self):
        for value in [0.0, 1.0, -1.0, 3.14, float("inf")]:
            with self.subTest(value=value):
                data = self._encode_fp32_no_reorder(value)
                result = unpack_fp32(data, reorder=False)
                self.assertEqual(len(result), 1)
                if math.isnan(value):
                    self.assertTrue(math.isnan(result[0]))
                elif math.isinf(value):
                    self.assertEqual(result[0], value)
                else:
                    self.assertAlmostEqual(result[0], value, places=5)

    def test_reorder_true_is_default(self):
        data = [0x3F, 0x80, 0x00, 0x00]
        self.assertEqual(unpack_fp32(data, reorder=True), unpack_fp32(data))

    def test_no_reorder_no_pair_swap(self):
        # Build two distinct values and confirm they are NOT swapped.
        d1 = self._encode_fp32_no_reorder(1.0)
        d2 = self._encode_fp32_no_reorder(2.0)
        combined = d1[:2] + d2[:2] + d1[2:] + d2[2:]
        result = unpack_fp32(combined, reorder=False)
        self.assertAlmostEqual(result[0], 1.0, places=5)
        self.assertAlmostEqual(result[1], 2.0, places=5)


class TestUnpackUint16Reorder(unittest.TestCase):
    """unpack_uint16: verify that reorder=False skips pair swapping."""

    def test_no_reorder_preserves_order(self):
        data = [0x00, 0x01, 0x00, 0x02]  # big-endian 1 then 2
        result = unpack_uint16(data, reorder=False)
        self.assertEqual(result, [1, 2])

    def test_reorder_swaps_pairs(self):
        data = [0x00, 0x01, 0x00, 0x02]
        result = unpack_uint16(data, reorder=True)
        self.assertEqual(result, [2, 1])

    def test_reorder_true_is_default(self):
        data = [0x00, 0x01, 0x00, 0x02]
        self.assertEqual(unpack_uint16(data, reorder=True), unpack_uint16(data))

    def test_odd_number_of_values_no_reorder(self):
        data = [0x00, 0x01, 0x00, 0x02, 0x00, 0x03]  # 1, 2, 3
        self.assertEqual(unpack_uint16(data, reorder=False), [1, 2, 3])

    def test_odd_number_of_values_with_reorder(self):
        data = [0x00, 0x01, 0x00, 0x02, 0x00, 0x03]  # 1, 2, 3
        result = unpack_uint16(data, reorder=True)
        self.assertEqual(result, [2, 1, 3])

    def test_four_values_reorder(self):
        data = [0x00, 0x01, 0x00, 0x02, 0x00, 0x03, 0x00, 0x04]  # 1, 2, 3, 4
        result = unpack_uint16(data, reorder=True)
        self.assertEqual(result, [2, 1, 4, 3])


class TestUnpackBfp8bReorder(unittest.TestCase):
    """unpack_bfp8_b: verify that reorder=False skips mantissa chunk reversal."""

    def _make_zero_block(self) -> list[int]:
        """64 exponents + 64*16 mantissas, all zero."""
        return [0] * (64 + 64 * 16)

    def test_no_reorder_zero_block(self):
        data = self._make_zero_block()
        result = unpack_bfp8_b(data, reorder=False)
        self.assertEqual(len(result), 64 * 16)
        self.assertTrue(all(v == 0.0 for v in result))

    def test_reorder_true_is_default(self):
        data = self._make_zero_block()
        self.assertEqual(unpack_bfp8_b(data, reorder=True), unpack_bfp8_b(data))

    def test_reorder_changes_non_trivial_data(self):
        # Use a non-zero mantissa pattern and confirm reorder changes the output.
        data = self._make_zero_block()
        # Set exponent = 127 (=> effective exponent 0) and first mantissa non-zero.
        data[0] = 127
        data[64] = 0b01000000  # non-zero mantissa byte
        result_with = unpack_bfp8_b(data, reorder=True)
        result_without = unpack_bfp8_b(data, reorder=False)
        # The non-zero mantissa ends up in different positions.
        self.assertNotEqual(result_with, result_without)


class TestUnpackDataReorderParam(unittest.TestCase):
    """unpack_data: verify that the reorder parameter is threaded correctly."""

    def test_uint16_no_reorder(self):
        data = [0x00, 0x01, 0x00, 0x02]
        result = unpack_data(data, TensixDataFormat.UInt16, signed=False, reorder=False)
        self.assertEqual(result, [1, 2])

    def test_uint16_with_reorder(self):
        data = [0x00, 0x01, 0x00, 0x02]
        result = unpack_data(data, TensixDataFormat.UInt16, signed=False, reorder=True)
        self.assertEqual(result, [2, 1])

    def test_default_reorder_is_true(self):
        data = [0x00, 0x01, 0x00, 0x02]
        self.assertEqual(
            unpack_data(data, TensixDataFormat.UInt16, signed=False),
            unpack_data(data, TensixDataFormat.UInt16, signed=False, reorder=True),
        )

    def test_df_as_int(self):
        data = [0x00, 0x01, 0x00, 0x02]
        result = unpack_data(data, TensixDataFormat.UInt16.value, signed=False, reorder=False)
        self.assertEqual(result, [1, 2])

    def test_unsupported_format_raises(self):
        with self.assertRaises(ValueError):
            unpack_data([], TensixDataFormat.Int32, signed=False)


if __name__ == "__main__":
    unittest.main()
