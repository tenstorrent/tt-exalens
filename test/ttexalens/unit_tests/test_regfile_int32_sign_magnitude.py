# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized

from ttexalens.pack_unpack_regfile import (
    TensixDataFormat,
    pack_data_direct_access,
    unpack_data_direct_access,
)

# (value, sign/magnitude word, two's complement word)
INT32_WORDS = [
    (0, 0x00000000, 0x00000000),
    (1, 0x00000001, 0x00000001),
    (-1, 0x80000001, 0xFFFFFFFF),
    (-2, 0x80000002, 0xFFFFFFFE),
    (2**31 - 1, 0x7FFFFFFF, 0x7FFFFFFF),
    (-(2**31 - 1), 0xFFFFFFFF, 0x80000001),
]


class TestRegfileInt32SignMagnitude(unittest.TestCase):
    @parameterized.expand(INT32_WORDS)
    def test_pack(self, value: int, sign_magnitude_word: int, twos_complement_word: int):
        self.assertEqual(
            pack_data_direct_access([value], TensixDataFormat.Int32, sign_magnitude=True), [sign_magnitude_word]
        )
        self.assertEqual(pack_data_direct_access([value], TensixDataFormat.Int32), [twos_complement_word])

    @parameterized.expand(INT32_WORDS)
    def test_unpack(self, value: int, sign_magnitude_word: int, twos_complement_word: int):
        df = TensixDataFormat.Int32
        self.assertEqual(unpack_data_direct_access([sign_magnitude_word], df, True, sign_magnitude=True), [value])
        self.assertEqual(unpack_data_direct_access([twos_complement_word], df, True), [value])

    def test_negative_zero_reads_as_zero(self):
        self.assertEqual(
            unpack_data_direct_access([0x80000000], TensixDataFormat.Int32, True, sign_magnitude=True), [0]
        )

    def test_pack_rejects_minus_two_to_the_31(self):
        # Sign/magnitude cannot hold -2**31.
        with self.assertRaises(ValueError):
            pack_data_direct_access([-(2**31)], TensixDataFormat.Int32, sign_magnitude=True)

    def test_unsigned_and_float_ignore_sign_magnitude(self):
        self.assertEqual(
            unpack_data_direct_access([0x80000001], TensixDataFormat.Int32, False, sign_magnitude=True), [0x80000001]
        )
        self.assertEqual(
            unpack_data_direct_access([0xBF800000], TensixDataFormat.Float32, True, sign_magnitude=True), [-1.0]
        )
        self.assertEqual(
            pack_data_direct_access([2**32 - 1], TensixDataFormat.UInt32, sign_magnitude=True), [2**32 - 1]
        )


if __name__ == "__main__":
    unittest.main()
