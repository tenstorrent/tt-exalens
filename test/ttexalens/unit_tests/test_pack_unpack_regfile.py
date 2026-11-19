# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized

from ttexalens.pack_unpack_regfile import (
    TensixDataFormat,
    bfp8_to_float_block,
    pack_value_direct_access,
    unpack_value_direct_access,
)


class TestPackUnpackRegfile(unittest.TestCase):
    @parameterized.expand(
        [
            # (shared exponent byte, sign/mantissa byte, expected value)
            (127, 0x40, 1.0),
            (126, 0x40, 0.5),
            (125, 0x40, 0.25),
            (125, 0xC0, -0.25),
            (125, 0x60, 0.375),
            (110, 0x40, 2.0**-17),
            (133, 0x40, 64.0),
            (134, 0x40, 128.0),
            (135, 0x7F, 127 / 64 * 2.0**8),
            (127, 0x00, 0.0),
        ]
    )
    def test_bfp8_to_float_block(self, exponent: int, mantissa: int, expected: float):
        self.assertEqual(bfp8_to_float_block(exponent, [mantissa]), [expected])

    @parameterized.expand(
        [
            # Integers in 32-bit Dst are sign/magnitude: sign in bit 31, magnitude in the low bits.
            (TensixDataFormat.Int8, -1, 0x80000001),
            (TensixDataFormat.Int8, -127, 0x8000007F),
            (TensixDataFormat.Int8, 5, 5),
            (TensixDataFormat.Int8, -0.5, 0),
            (TensixDataFormat.Int32, -0.5, 0),
            (TensixDataFormat.Int32, -1.5, 0xFFFFFFFF),
        ]
    )
    def test_pack_value_direct_access(self, df: TensixDataFormat, value: float, expected: int):
        self.assertEqual(pack_value_direct_access(value, df), expected)

    @parameterized.expand([(0x80000001, -1), (0x8000007F, -127), (5, 5)])
    def test_unpack_int8_direct_access(self, word: int, expected: int):
        self.assertEqual(unpack_value_direct_access(word, TensixDataFormat.Int8, signed=True), expected)

    def test_pack_int8_rejects_minus_128(self):
        # Sign/magnitude cannot hold -128.
        with self.assertRaises(ValueError):
            pack_value_direct_access(-128, TensixDataFormat.Int8)


if __name__ == "__main__":
    unittest.main()
