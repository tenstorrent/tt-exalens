# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
import struct

value = 0b10101010  # binary number for 170
sign = (value & 0x80) >> 7
mag = value & 0x7F
print((1 - 2 * sign) * mag)
