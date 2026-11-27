# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized

from ttexalens.pack_unpack_regfile import TensixDataFormat, unpack_data


class TestPackUnpackRegfile(unittest.TestCase):
    @parameterized.expand(
        [
            (125, 0x40, 0.25),
            (125, 0xC0, -0.25),
            (127, 0x40, 1.0),
            (134, 0x40, 128.0),
            (120, 0x7F, 0.0155029296875),
        ]
    )
    def test_unpack_bfp8_b(self, exponent: int, mantissa: int, expected: float):
        values = unpack_data([exponent] * 64 + [mantissa] * 1024, TensixDataFormat.Bfp8_b, signed=True)
        self.assertEqual(values, [expected] * 1024)
        self.assertIsInstance(values[0], float)
