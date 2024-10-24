import pytest
import torch
import os
import struct
from dbd.tt_debuda_init import init_debuda
from dbd.tt_debuda_lib import write_to_device, read_words_from_device, run_elf

import time

mathop_dict = {
    1 : "elwadd",
    2 : "elwsub"
}

format_dict = {
    "Float32": torch.float32,
    "Float16": torch.float16,
    "Float16_b": torch.bfloat16,
    "Int32": torch.int32
}

format_args_dict = {
    "Float32": "FORMAT_FLOAT32",
    "Float16": "FORMAT_FLOAT16",
    "Float16_b": "FORMAT_FLOAT16_B"
}

def flatten_list(sublists):
    return [item for sublist in sublists for item in sublist]

def int_to_bytes_list(n):
    binary_str = bin(n)[2:]
    padded_binary = binary_str.zfill(32)
    bytes_list = [int(padded_binary[i:i + 8], 2) for i in range(0, 32, 8)]
    return bytes_list

def bfloat16_to_bytes(number):
    number_unpacked = struct.unpack('!I', struct.pack('!f', number))[0]
    res_masked = number_unpacked & 0xFFFF0000
    return int_to_bytes_list(res_masked)

def bytes_to_bfloat16(byte_list):
    bytes_data = bytes(byte_list)
    unpacked_value = struct.unpack('>f', bytes_data)[0]
    return torch.tensor(unpacked_value, dtype=torch.float32)

def write_stimuli_to_l1(buffer_A, buffer_B,stimuli_format):
    decimal_A = []
    decimal_B = []

    for i in buffer_A:
        decimal_A.append(bfloat16_to_bytes(i)[::-1])
    for i in buffer_B:
        decimal_B.append(bfloat16_to_bytes(i)[::-1])

    decimal_A = flatten_list(decimal_A)
    decimal_B = flatten_list(decimal_B)

    write_to_device("18-18", 0x1b000, decimal_A)
    write_to_device("18-18", 0x1c000, decimal_B)

def generate_stimuli(stimuli_format):
    srcA = torch.full((1024,), fill_value=2, dtype=format_dict[stimuli_format]) # hardcoded for now
    srcB = torch.full((1024,), fill_value=2, dtype=format_dict[stimuli_format]) # hardcoded for now

    return srcA.tolist() , srcB.tolist()

def generate_golden(operand1, operand2, operation):
    tensor1_float = torch.tensor(operand1, dtype=torch.float32)
    tensor2_float = torch.tensor(operand2, dtype=torch.float32)

    dest = torch.full((1024,), fill_value=0, dtype=torch.float32)

    if operation == "elwadd":
        dest = tensor1_float + tensor2_float
    elif operation == "elwsub":
        dest = tensor1_float - tensor2_float
    elif operation == "elwmul":
        dest = tensor1_float * tensor2_float
    else:
        raise ValueError("Unsupported operation!")

    return dest.tolist()

def generate_golden(operand1, operand2, format, operations):
    tensor1_float = torch.tensor(operand1, dtype=torch.float32)
    tensor2_float = torch.tensor(operand2, dtype=torch.float32)

    dest = torch.full((1024,), fill_value=0, dtype=torch.float32)

    dest_inter = []

    for op in operations:

        operation = mathop_dict[op]

        if operation == "elwadd":
            dest = tensor1_float + tensor2_float
        elif operation == "elwsub":
            dest = tensor1_float - tensor2_float
        elif operation == "elwmul":
            dest = tensor1_float * tensor2_float
        else:
            raise ValueError("Unsupported operation!")

        dest_inter.append(dest)

    for inter in dest_inter:
        inter = inter.tolist()

    return dest.tolist(), dest_inter
    # return dest #.tolist()

math_kernels = [2,1,2]

@pytest.mark.parametrize("format", ["Float16_b"])
@pytest.mark.parametrize("testname", ["configurable_test"])
@pytest.mark.parametrize("machine", ["wormhole"])
def test_multiple_kernels(format, testname, machine):

    global math_kernels

    # *********** formatting kernels

    kerns_formatted = ""
    for i in math_kernels:
        kerns_formatted+=str(i)+","
    kerns_formatted = kerns_formatted[:-1]

    # ******************************** 

    context = init_debuda()

    src_A, src_B = generate_stimuli(format)
    write_stimuli_to_l1(src_A, src_B,format)
    golden, golden_inter = generate_golden(src_A, src_B, format, math_kernels)

    make_cmd = f"make format={format_args_dict[format]} testname={testname} machine={machine}"
    make_cmd += " unpack_kern_cnt=3 unpack_kerns=2,2,2"
    make_cmd += " math_kern_cnt="+ str(len(math_kernels))+ " math_kerns="+kerns_formatted
    make_cmd += " pack_kern_cnt=3 pack_kerns=1,1,1"

    os.system(make_cmd)

    for i in range(3):
        run_elf(f"build/elf/{testname}_trisc{i}.elf", "18-18", risc_id=i + 1)

    read_data = read_words_from_device("18-18", 0x1a000, word_count=1024)
    byte_list = []
    golden_form_L1 = []

    for word in read_data:
        byte_list.append(int_to_bytes_list(word))
        
    for i in byte_list:
        golden_form_L1.append(bytes_to_bfloat16(i).item())

    os.system("make clean")

    unpack_mailbox = read_words_from_device("18-18", 0x19FF4, word_count=1)[0].to_bytes(4, 'big')
    math_mailbox = read_words_from_device("18-18", 0x19FF8, word_count=1)[0].to_bytes(4, 'big')
    pack_mailbox = read_words_from_device("18-18", 0x19FFC, word_count=1)[0].to_bytes(4, 'big')

    print("*"*50)
    print(golden[127])
    print(golden_form_L1[127])
    print(len(golden_inter))
    print(len(golden_inter[0]))
    print("*"*50)

    tolerance = 0.05
    
    # test end results
    for i in range(128):
        assert abs(golden[i] - golden_form_L1[i]) <= tolerance, f"i = {i}, {golden[i]}, {golden_form_L1[i]}"

    # TODO: test intermediate results

    assert unpack_mailbox == b'\x00\x00\x00\x01'
    assert math_mailbox == b'\x00\x00\x00\x01'
    assert pack_mailbox == b'\x00\x00\x00\x01'