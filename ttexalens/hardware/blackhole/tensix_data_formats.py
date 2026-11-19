# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.pack_unpack_regfile import TensixDataFormat

# DataFormat from tt-metal's tt-1xx/blackhole/tensix_types.h.
tensix_data_formats: dict[TensixDataFormat, int] = {
    TensixDataFormat.Float32: 0,
    TensixDataFormat.Float16: 1,
    TensixDataFormat.Bfp8: 2,
    TensixDataFormat.Bfp4: 3,
    TensixDataFormat.Bfp2: 11,
    TensixDataFormat.Float16_b: 5,
    TensixDataFormat.Bfp8_b: 6,
    TensixDataFormat.Bfp4_b: 7,
    TensixDataFormat.Bfp2_b: 15,
    TensixDataFormat.Lf8: 10,
    TensixDataFormat.Int8: 14,
    TensixDataFormat.UInt8: 30,
    TensixDataFormat.UInt16: 9,
    TensixDataFormat.Int32: 8,
    TensixDataFormat.UInt32: 24,
    TensixDataFormat.Tf32: 4,
    TensixDataFormat.Fp8_e4m3: 26,  # Not a HW encoding: Lf8 with an extra bit for E4M3
    TensixDataFormat.Invalid: 0xFF,
}
