# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import struct


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


def unpack_data(data, df):
    if df == 1:  # Float16
        return unpack_fp16(data)
    elif df == 5:  # Float16_b
        return unpack_bfp16(data)
    elif df == 6:  # Bfp8_b
        return unpack_bfp8_b(data)
    else:
        raise ValueError(f"Unknown data format {df}")
