# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from multiprocessing import Value
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
    Fp8_e4m3 = 26  # 0x1A in decimal
    Int8 = 14
    Tf32 = 4
    UInt8 = 30
    UInt16 = 9
    Int32 = 8
    UInt32 = 24
    RawUInt8 = 240  # 0xf0 in decimal
    RawUInt16 = 241  # 0xf1 in decimal
    RawUInt32 = 242  # 0xf2 in decimal
    Invalid = 255


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


# Reorders the bits of a given raw datum according to DST's storage scheme.
def reorder_fp32(datum: int) -> int:
    # Low eight bits go right next to the high bit,
    # the seven bits after the high bit become the lowest,
    # and the high bit stays in place.
    return (datum & 0x8000) | ((datum & 0x7F00) >> 8) | ((datum & 0xFF) << 7)


def unpack_fp32(data) -> list[float]:
    floats: list[float] = []
    half = len(data) // 2
    hi_bytes = data[:half]
    lo_bytes = data[half:]

    for i in range(0, half, 2):
        upper = int.from_bytes(hi_bytes[i : i + 2], byteorder="big")
        lower = int.from_bytes(lo_bytes[i : i + 2], byteorder="big")
        # Both parts are shuffled.
        upper_reordered = reorder_fp32(upper)
        lower_reordered = reorder_fp32(lower)
        result = (upper_reordered << 16) | lower_reordered
        floats.append(struct.unpack(">f", result.to_bytes(4, "big"))[0])

    for i in range(0, len(floats) - 1, 2):
        floats[i], floats[i + 1] = floats[i + 1], floats[i]

    return floats


def unpack_uint16(data: list[int]) -> list[int]:
    byte_data = bytes(data)
    unpacked_data = struct.unpack(f">{len(byte_data)//2}H", byte_data)

    # Reorder in pairs
    result = []
    for i in range(0, len(unpacked_data), 2):
        if i + 1 < len(unpacked_data):
            # Here we swap values in pair
            result.extend([unpacked_data[i + 1], unpacked_data[i]])
        else:
            result.append(unpacked_data[i])

    return result


def unpack_data(data, df: int | TensixDataFormat, signed: bool):
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
    elif df == TensixDataFormat.UInt16:
        return unpack_uint16(data)
    else:
        raise ValueError(f"Unsupported data format {df} for unpacking.")


# Unpacking data read with direct access require different approach
def unpack_value_direct_access(value: int, df: TensixDataFormat, signed: bool) -> int | float:
    if df == TensixDataFormat.Float32:
        return struct.unpack(">f", value.to_bytes(4, "big"))[0]
    # Because in ALU register format for dest is INT32 for both INT32 and UINT32 we need to check sign bit
    elif df == TensixDataFormat.Int32 and signed:
        # If the sign bit is set, we need to convert it to a signed integer
        return value - 0x100000000 if value & 0x80000000 else value
    elif df == TensixDataFormat.Int32 and not signed:
        return value
    # Same as for INT32/UINT32
    elif df == TensixDataFormat.Int8 and signed:
        # Since 1-byte integers are stored in 32-bit mode sign bit is in MSB, bytes look like this: 0x80 0x00 0x00 value
        return (value & 0x000000FF) - 0x80 if value & 0x80000000 else value
    elif df == TensixDataFormat.Int8 and not signed:
        return value
    else:
        raise ValueError(f"Unsupported data format {df} for unpacking.")


def unpack_data_direct_access(data: list[int], df: int | TensixDataFormat, signed: bool):
    if isinstance(df, int):
        df = TensixDataFormat(df)

    return [unpack_value_direct_access(value, df, signed) for value in data]


def pack_value_direct_access(value: int, df: TensixDataFormat) -> int:
    if df == TensixDataFormat.Float32:
        return int.from_bytes(struct.pack(">f", float(value)), "big")
    elif df == TensixDataFormat.Int32:
        if value < -(2**31) or value > 2**31 - 1:
            raise ValueError(f"Value {value} is out of range for Int32.")
        return value if int(value) >= 0 else int(value) + 0x100000000
    elif df == TensixDataFormat.UInt32:
        if value < 0 or value > 2**32 - 1:
            raise ValueError(f"Value {value} is out of range for UInt32.")
        return value
    elif df == TensixDataFormat.Int8:
        if value < -(2**7) or value > 2**7 - 1:
            raise ValueError(f"Value {value} is out of range for Int8.")
        return value if value >= 0 else 0x80000000 | (value + 0x80)
    elif df == TensixDataFormat.UInt8:
        if value < 0 or value > 2**8 - 1:
            raise ValueError(f"Value {value} is out of range for UInt8.")
        return value
    else:
        raise ValueError(f"Unsupported data format {df} for packing.")


def pack_data_direct_access(data: list[int | float], df: TensixDataFormat) -> list[int]:
    return [pack_value_direct_access(value, df) for value in data]
