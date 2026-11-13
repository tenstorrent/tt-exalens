# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from enum import Enum


# DataFormat from tt-metal's tt-2xx/quasar/tensix_types.h.
class QuasarDataFormat(Enum):
    Float32 = 0
    Tf32 = 4
    Float16 = 1
    Float16_b = 5
    Fp8R = 10
    Fp8P = 16
    MxFp8R = 18
    MxFp8P = 20
    MxFp6R = 19
    MxFp6P = 21
    MxFp4 = 22
    MxInt8 = 2
    MxInt4 = 3
    MxInt2 = 11
    Int32 = 8
    Int8 = 14
    Int16 = 9
    UInt8 = 17
    UInt16 = 130
    Int4 = 23
    UInt4 = 25
    MxFp4_2x_A = 27
    MxFp4_2x_B = 24
    Int8_2x = 26
    UInt8_2x = 28
    Invalid = 0xFF


# RISC_DEST_ACCESS_CTRL_SEC<n>_fmt: the format the dest window converts to and from (RISC_DEST_FMT_* in ckernel_dest.h).
class QuasarRiscDestFormat(Enum):
    FP32 = 0
    INT32 = 1
    FP16A = 2
    FP16B = 3
    INT16 = 4
    INT8 = 5
