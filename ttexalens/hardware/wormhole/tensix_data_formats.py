# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from enum import Enum


# DataFormat from tt-metal's tt-1xx/wormhole/wormhole_b0_defines/tensix_types.h.
class WormholeDataFormat(Enum):
    Float32 = 0
    Float16 = 1
    Bfp8 = 2
    Bfp4 = 3
    Bfp2 = 11
    Float16_b = 5
    Bfp8_b = 6
    Bfp4_b = 7
    Bfp2_b = 15
    Lf8 = 10
    Int8 = 14
    UInt8 = 30
    UInt16 = 9
    Int32 = 8
    UInt32 = 24
    Tf32 = 4
    Invalid = 0xFF
