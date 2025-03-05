# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import struct
from enum import Enum
from typing import Union


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


def unpack_data(data, df: Union[int, TensixDataFormat]):
    if isinstance(df, int):
        df = TensixDataFormat(df)

    if df == TensixDataFormat.Float16:
        return unpack_fp16(data)
    elif df == TensixDataFormat.Float16_b:
        return unpack_bfp16(data)
    elif df == TensixDataFormat.Bfp8_b:
        return unpack_bfp8_b(data)
    else:
        raise ValueError(f"Unknown or unsupported data format {df}")
