# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import struct
from enum import Enum


class TensixDataFormat(Enum):
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
    Fp8_e4m3 = 0x1A
    UInt16 = 9
    Int8 = 14
    UInt8 = 30
    Tf32 = 4
    Int32 = 8
    RawUInt8 = 0xF0
    RawUInt16 = 0xF1
    RawUInt32 = 0xF2
    Invalid = 0xFF


def flip_bfp16_bits(value):
    sign = (value & 0x8000) >> 15
    mantisa = (value & 0x7F00) >> 8
    exponent = value & 0xFF
    result = (sign << 15) | (exponent << 7) | mantisa
    return result


def flip_fp16_bits(value):
    sign = (value & 0x8000) >> 15
    mantisa = (value & 0x7FE0) >> 5
    exponent = value & 0x1F
    result = (sign << 15) | (exponent << 10) | mantisa
    return result


def unpack_fp16(data):
    return [
        struct.unpack(
            ">e", int.to_bytes(flip_fp16_bits(int.from_bytes(data[i : i + 2], byteorder="big")), 2, byteorder="big")
        )[0]
        for i in range(0, len(data), 2)
    ]


def unpack_bfp16(data):
    return [
        struct.unpack(
            ">f",
            int.to_bytes(flip_bfp16_bits(int.from_bytes(data[i : i + 2], byteorder="big")), 2, byteorder="big")
            + b"\x00\x00",
        )[0]
        for i in range(0, len(data), 2)
    ]


def bfp8_to_float_block(exponent, bfp8_mantissas):
    bfloat16_values = []
    exponent = exponent - 127
    for mantissa in bfp8_mantissas:
        sign_mantissa = str(format(mantissa, "08b"))
        sign = int(sign_mantissa[0], 2)
        mantissa_value = sign_mantissa[1:]
        int_part = mantissa_value[: exponent + 1]
        fract_part = mantissa_value[exponent + 1 :]

        if len(int_part) != 0:
            int_value = int(int_part, 2)
        else:
            int_value = 0

        fract_value = 0
        for i in range(len(fract_part)):
            if fract_part[i] == "1":
                fract_value += 1 / (2 ** (i + 1))

        bfloat16_values.append(((-1) ** sign) * (int_value + fract_value))

    return bfloat16_values


def unpack_bfp8_b(data):
    exponents = data[:64]
    mantissas = data[64:]

    bfloat16_values = []
    for i in range(len(exponents)):
        exponent = exponents[i]
        bfp8_mantissas = mantissas[i * 16 : (i + 1) * 16]
        reversed_chunks = []
        for j in range(0, len(bfp8_mantissas), 4):
            chunk = bfp8_mantissas[j : j + 4]  # Get the next chunk of 4 elements
            reversed_chunk = chunk[::-1]  # Reverse the chunk
            reversed_chunks.extend(reversed_chunk)  # Add the reversed chunk to the list

        block_bfloat16_values = bfp8_to_float_block(exponent, reversed_chunks)
        bfloat16_values.extend(block_bfloat16_values)

    return bfloat16_values


def unpack_fp32(data) -> list[float]:
    # 64x32 bytes
    # Each row can be grabbed as 16x uint16_t
    # Swizzle and remap aren't accounted for
    row_size = 32
    total_rows = len(data) // row_size
    print(f"total_rows: {total_rows}")
    assert total_rows % 2 == 0
    half = total_rows // 2

    floats: list[float] = []
    for r in range(half):
        base_hi = r * row_size
        base_lo = (r + half)
        # for each of the 16 uint16_t slots in the row
        for i in range(16):
            hi_bytes = data[base_hi + 2 * i : base_hi + 2 * i + 2]
            lo_bytes = data[base_lo + 2 * i : base_lo + 2 * i + 2]
            hi = int.from_bytes(hi_bytes, byteorder="big")
            lo = int.from_bytes(lo_bytes, byteorder="big")

            # reconstruct an IEEE 32-bit float
            # hi: s m m m m m m m e e e e e e e e
            # lo: m m m m m m m m m m m m m m m m
            # should become: s 8e 23m
            sign = (hi & 0x8000) << 16
            exponent = (hi & 0x00FF) << 23
            mantissa = ((hi & 0x7F00) << 8) | lo
            result = sign | exponent | mantissa

            floats.append(struct.unpack(">f", result.to_bytes(4, "big"))[0])
    
    return floats


def unpack_data(data, df: int | TensixDataFormat):
    if isinstance(df, int):
        df = TensixDataFormat(df)

    if df == TensixDataFormat.Float32:
        return unpack_fp32(data)
    if df == TensixDataFormat.Float16:
        return unpack_fp16(data)
    elif df == TensixDataFormat.Float16_b:
        return unpack_bfp16(data)
    elif df == TensixDataFormat.Bfp8_b:
        return unpack_bfp8_b(data)
    else:
        raise ValueError(f"Unknown or unsupported data format {df}")
