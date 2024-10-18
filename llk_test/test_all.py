import pytest
import torch
import os
import struct
from dbd.tt_debuda_init import init_debuda
from dbd.tt_debuda_lib import write_to_device, read_words_from_device, run_elf

format_dict = {
    "Float32": torch.float32,
    "Float16": torch.float16,
    "Float16_b": torch.bfloat16,
    "Int32": torch.int32
}

format_args_dict = {
    "Float32": "FORMAT_FLOAT32",
    "Float16": "FORMAT_FLOAT16",
    "Float16_b": "FORMAT_FLOAT16_B",
    "Int32": "FORMAT_INT32"
}

mathop_args_dict = {
    "elwadd": "ELTWISE_BINARY_ADD",
    "elwsub": "ELTWISE_BINARY_SUB",
    "elwmul": "ELTWISE_BINARY_MUL"
}

def int_to_unsigned_32bit_hex(value):
    if not 0 <= value < 2**32:
        raise ValueError("Value must be an unsigned 32-bit integer.")
    return f"{value & 0xFFFFFFFF:08X}"

def fp32_2_datum(number, masked):
    number_unpacked = struct.unpack('!I', struct.pack('!f', number))[0]
    res_masked = number_unpacked & 0xFFFFE000
    return res_masked if masked else struct.unpack('!f', struct.pack('!I', res_masked))[0]

def hex_number_to_decimal_array(hex_string):
    hex_string = hex_string.split('x')[1].replace(" ", "").strip()
    if len(hex_string) != 8:
        raise ValueError("Hex string must be exactly 8 digits long.")
    return list(bytes.fromhex(hex_string))[::-1]  # reverse endian

def generate_stimuli(stimuli_format):
    srcA = torch.rand(32 * 32, dtype=format_dict[stimuli_format]) + 0.5
    srcB = torch.rand(32 * 32, dtype=format_dict[stimuli_format]) + 0.5
    return [fp32_2_datum(i, masked=False) for i in srcA.tolist()], [fp32_2_datum(i, masked=False) for i in srcB.tolist()]

def generate_golden(operation, operand1, operand2):
    tensor1_float32 = torch.tensor(operand1, dtype=torch.float32)
    tensor2_float32 = torch.tensor(operand2, dtype=torch.float32)

    if operation == "elwadd":
        dest = tensor1_float32 + tensor2_float32
    elif operation == "elwsub":
        dest = tensor2_float32 - tensor1_float32
    elif operation == "elwmul":
        dest = tensor1_float32 * tensor2_float32
    else:
        raise ValueError("Unsupported operation!")

    return dest.tolist()

def write_stimuli_to_l1(buffer_A, buffer_B):
    decimal_A = [hex_number_to_decimal_array(hex(fp32_2_datum(i, masked=True))) for i in buffer_A]
    decimal_B = [hex_number_to_decimal_array(hex(fp32_2_datum(i, masked=True))) for i in buffer_B]
    
    write_to_device("18-18", 0x1c000, [item for sublist in decimal_A for item in sublist])
    write_to_device("18-18", 0x1b000, [item for sublist in decimal_B for item in sublist])

def hex_to_float_32(hex_str):
    hex_int = int(hex_str, 16) & 0xFFFF0000
    return struct.unpack('f', struct.pack('I', hex_int))[0]

@pytest.mark.parametrize("format", ["Float16", "Float16_b"])
@pytest.mark.parametrize("testname", ["eltwise_add_test"])
@pytest.mark.parametrize("mathop", ["elwadd", "elwsub"])
@pytest.mark.parametrize("machine", ["wormhole"])
def test_all(format, mathop, testname, machine):
    context = init_debuda()
    src_A, src_B = generate_stimuli(format)
    golden = generate_golden(mathop, src_A, src_B)
    write_stimuli_to_l1(src_A, src_B)

    make_cmd = f"make --silent format={format_args_dict[format]} mathop={mathop_args_dict[mathop]} testname={testname} machine={machine}"
    os.system(make_cmd)

    for i in range(3):
        run_elf(f"build/elf/{testname}_trisc{i}.elf", "18-18", risc_id=i + 1)

    read_data = read_words_from_device("18-18", 0x1a000, word_count=1024)
    
    golden_form_L1 = [hex_to_float_32(int_to_unsigned_32bit_hex(word)) for word in read_data]

    os.system("make clean")

    unpack_mailbox = read_words_from_device("18-18", 0x19FF4, word_count=1)[0].to_bytes(4, 'big')
    math_mailbox = read_words_from_device("18-18", 0x19FF8, word_count=1)[0].to_bytes(4, 'big')
    pack_mailbox = read_words_from_device("18-18", 0x19FFC, word_count=1)[0].to_bytes(4, 'big')

    assert unpack_mailbox == b'\x00\x00\x00\x01'
    assert math_mailbox == b'\x00\x00\x00\x01'
    assert pack_mailbox == b'\x00\x00\x00\x01'

    assert len(golden) == len(golden_form_L1)

    tolerance = 0.2 if format == "Float16" else 0.01
    for i in range(min(512, len(golden))):
        assert abs(golden[i] - golden_form_L1[i]) <= tolerance, f"i = {i}, {golden[i]}, {golden_form_L1[i]}"
