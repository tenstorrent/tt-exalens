# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from enum import Enum

from ttexalens.pack_unpack_regfile import TensixDataFormat

# DataFormat from tt-metal's tt-2xx/quasar/tensix_types.h, without the formats that TensixDataFormat does not have.
tensix_data_formats: dict[TensixDataFormat, int] = {
    TensixDataFormat.Float32: 0,
    TensixDataFormat.Tf32: 4,
    TensixDataFormat.Float16: 1,
    TensixDataFormat.Float16_b: 5,
    TensixDataFormat.Int32: 8,
    TensixDataFormat.Int8: 14,
    TensixDataFormat.UInt8: 17,
    TensixDataFormat.UInt16: 130,
    TensixDataFormat.Invalid: 0xFF,
}


# RISC_DEST_ACCESS_CTRL_SEC<n>_fmt: the format the dest window converts to and from (RISC_DEST_FMT_* in ckernel_dest.h).
class QuasarRiscDestFormat(Enum):
    FP32 = 0
    INT32 = 1
    FP16A = 2
    FP16B = 3
    INT16 = 4
    INT8 = 5
