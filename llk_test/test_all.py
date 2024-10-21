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

def reorg_bytes(bytes_list):
    return [0, 0, bytes_list[0] , bytes_list[1]]
    #return [bytes_list[1] , bytes_list[0] , 0 ,0]
    #return [0, 0, bytes_list[1] , bytes_list[0]]

def flatten_list(sublists):
    return [item for sublist in sublists for item in sublist]

def int_to_bytes_list(n):
    # Get binary representation and strip '0b' prefix
    binary_str = bin(n)[2:]
    
    # Pad with leading zeros to make the length a multiple of 8
    padded_binary = binary_str.zfill(32)  # Always 32 bits for 4 bytes
    
    # Split into bytes (8 bits each)
    bytes_list = [int(padded_binary[i:i + 8], 2) for i in range(0, 32, 8)]
    
    return bytes_list

# Function to convert a float to a list of bytes for float16
def float16_to_bytes(value):
    float16_value = torch.tensor(value, dtype=torch.float16)
    packed_bytes = struct.pack('>e', float16_value.item())
    byte_list = list(packed_bytes)
    return byte_list + [0] * (4 - len(byte_list))

# Function to convert a list of bytes back to float16
def bytes_to_float16(byte_list):
    bytes_data = bytes(byte_list[:2])
    unpacked_value = struct.unpack('>e', bytes_data)[0]
    return torch.tensor(unpacked_value, dtype=torch.float16)

# Function to convert a float to a list of bytes for bfloat16
def bfloat16_to_bytes(value):
    float16_value = torch.tensor(value, dtype=torch.bfloat16)
    packed_bytes = struct.pack('>e', float16_value.item())
    byte_list = list(packed_bytes)
    return byte_list + [0] * (4 - len(byte_list))

# Function to convert a list of bytes back to bfloat16
def bytes_to_bfloat16(byte_list):
    bytes_data = bytes(byte_list[:2])
    unpacked_value = struct.unpack('>e', bytes_data)[0]
    return torch.tensor(unpacked_value, dtype=torch.bfloat16)


def fp32_2_datum(number, masked):
    number_unpacked = struct.unpack('!I', struct.pack('!f', number))[0]
    res_masked = number_unpacked & 0xFFFFF000
    return res_masked if masked else struct.unpack('!f', struct.pack('!I', res_masked))[0]


def generate_stimuli(stimuli_format):
    srcA = torch.rand(32 * 32, dtype=format_dict[stimuli_format]) + 0.5
    srcB = torch.rand(32 * 32, dtype=format_dict[stimuli_format]) + 0.5

    return srcA.tolist() , srcB.tolist()

    #return [fp32_2_datum(i, masked=False) for i in srcA.tolist()], [fp32_2_datum(i, masked=False) for i in srcB.tolist()]

def generate_golden(operation, operand1, operand2):
    tensor1_float32 = torch.tensor(operand1, dtype=torch.float16)
    tensor2_float32 = torch.tensor(operand2, dtype=torch.float16)

    if operation == "elwadd":
        dest = tensor1_float32 + tensor2_float32
    elif operation == "elwsub":
        dest = tensor2_float32 - tensor1_float32
    elif operation == "elwmul":
        dest = tensor1_float32 * tensor2_float32
    else:
        raise ValueError("Unsupported operation!")

    return dest.tolist()

def write_stimuli_to_l1(buffer_A, buffer_B,stimuli_format):

    decimal_A = []
    decimal_B = []

    if(stimuli_format == "Float16"):
        for i in buffer_A:
            decimal_A.append(float16_to_bytes(i)[::-1])
        for i in buffer_B:
            decimal_B.append(float16_to_bytes(i)[::-1])
    elif(stimuli_format == "Float16_b"):
        for i in buffer_A:
            decimal_A.append(bfloat16_to_bytes(i)[::-1])
        for i in buffer_B:
            decimal_B.append(bfloat16_to_bytes(i)[::-1])
    
    print()
    print("*"*70)
    print(buffer_A[0])
    print(buffer_B[0])
    print(decimal_A[0])
    print(decimal_B[0])
    print("*"*70) 

    decimal_A = flatten_list(decimal_A)
    decimal_B = flatten_list(decimal_B)

    write_to_device("18-18", 0x1c000, decimal_A)
    write_to_device("18-18", 0x1b000, decimal_B)

@pytest.mark.parametrize("format", ["Float16", "Float16_b"])
@pytest.mark.parametrize("testname", ["eltwise_add_test"])
@pytest.mark.parametrize("mathop", ["elwadd", "elwsub"])
@pytest.mark.parametrize("machine", ["wormhole"])
def test_all(format, mathop, testname, machine):
    context = init_debuda()
    src_A, src_B = generate_stimuli(format)
    golden = generate_golden(mathop, src_A, src_B)
    write_stimuli_to_l1(src_A, src_B,format)

    make_cmd = f"make --silent format={format_args_dict[format]} mathop={mathop_args_dict[mathop]} testname={testname} machine={machine}"
    os.system(make_cmd)

    for i in range(3):
        run_elf(f"build/elf/{testname}_trisc{i}.elf", "18-18", risc_id=i + 1)

    read_data = read_words_from_device("18-18", 0x1a000, word_count=1024)
    byte_list = []
    golden_form_L1 = []

    if(format == "Float16_b"):
        for word in read_data:
            byte_list.append(int_to_bytes_list(word))
        
        for i in byte_list:
            golden_form_L1.append(bytes_to_bfloat16(i).item())
    elif(format == "Float16"):
        for word in read_data:
            byte_list.append(int_to_bytes_list(word))
        
        for i in byte_list:
            golden_form_L1.append(bytes_to_float16(i).item())

    print("$"*50)
    print(golden[0])
    print(read_data[0])
    print(hex(read_data[0]))
    print(byte_list[0])
    print(golden_form_L1[0])
    print("$"*50)

    os.system("make clean")

    unpack_mailbox = read_words_from_device("18-18", 0x19FF4, word_count=1)[0].to_bytes(4, 'big')
    math_mailbox = read_words_from_device("18-18", 0x19FF8, word_count=1)[0].to_bytes(4, 'big')
    pack_mailbox = read_words_from_device("18-18", 0x19FFC, word_count=1)[0].to_bytes(4, 'big')

    assert unpack_mailbox == b'\x00\x00\x00\x01'
    assert math_mailbox == b'\x00\x00\x00\x01'
    assert pack_mailbox == b'\x00\x00\x00\x01'

    assert len(golden) == len(golden_form_L1)

    tolerance = 0.5
    for i in range(512):
        assert abs(golden[i] - golden_form_L1[i]) <= tolerance, f"i = {i}, {golden[i]}, {golden_form_L1[i]}"