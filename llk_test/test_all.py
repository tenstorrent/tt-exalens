import pytest
import torch
import os
import struct
from ieee754 import half, single, double, quadruple, octuple
from dbd.tt_debuda_init import init_debuda
from dbd.tt_debuda_lib import write_to_device, read_words_from_device
from dbd.tt_debuda_lib import run_elf
from fxpmath import Fxp

format_dict = {"Float32" : torch.float32, 
               "Float16" : torch.float16, 
               "Float16_b" : torch.bfloat16, 
               "Int32" : torch.int32}
               
format_args_dict = {"Float32" : "FORMAT_FLOAT16_B", 
                    "Float16" : "FORMAT_FLOAT16", 
                    "Float16_b" : "FORMAT_FLOAT32", 
                    "Int32" : "FORMAT_INT32"}

mathop_args_dict = {"elwadd" : "ELTWISE_BINARY_ADD",    
                    "elwsub" : "ELTWISE_BINARY_SUB",
                    "elwmul" : "ELTWISE_BINARY_MUL"}

binary_ops = ["elwadd", "elwsub", "elwmul"]

def flatten(sublists):
    return [item for sublist in sublists for item in sublist]

def fp32_2_datum(number, masked):
    number_unpacked = struct.unpack('!I', struct.pack('!f', number))[0]
    # Step 3: Apply the bitwise mask (0xFFFFE000)
    res_masked = number_unpacked & 0xFFFFE000
    # Step 4: Convert back to float

    res_float = struct.unpack('!f', struct.pack('!I', res_masked))[0]

    if(masked == True):
        return res_masked
    else:
        return res_float

def fp16_2_datum(number, masked):
    # Step 1: Unpack the 16-bit float to its integer representation
    number_unpacked = struct.unpack('!I', struct.pack('!f', number))[0]
    
    # Step 2: Shift the 16-bit integer representation left by 3 bits to append three zeros
    res_masked = number_unpacked << 3
    
    # Step 3: Create a 32-bit representation
    res_32bit = res_masked & 0x7FFFFFFF  # Mask to ensure only the lower 19 bits are used
    
    if masked:
        return res_masked
    else:
        # Step 4: Convert back to 32-bit float
        return struct.unpack('!f', struct.pack('!I', res_32bit))[0]


def int_2_float32(decimal_number):
    # Convert the integer to bytes (4 bytes for float32)
    byte_representation = struct.pack('I', decimal_number)
    # Unpack the bytes as a float32
    float32_representation = struct.unpack('f', byte_representation)[0]
    return float32_representation, byte_representation

def hex_number_to_decimal_array(hex_string, format):
    
    hex_string = hex_string.split('x')[1]
    hex_string = hex_string.replace(" ", "").strip()
    
    # Check if the hex string has 8 characters
    if len(hex_string) != 8:
        print(len(hex_string))
        raise ValueError("Hex string must be exactly 8 digits long.")

    # Convert hex string to bytes
    byte_array = bytes.fromhex(hex_string)
    
    # Convert bytes to a list of decimal values
    decimal_array = list(byte_array)
    
    return decimal_array[::-1] # reverse endian

def generate_stimuli(stimuli_format):
    
    srcA = [1.00048828125]*1024  # Example values
    srcB = [1.00048828125]*1024

    # srcA = torch.rand(32*32, dtype = format_dict[stimuli_format]) + 0.5
    # srcB = torch.rand(32*32, dtype = format_dict[stimuli_format]) + 0.5
    # srcA = srcA.tolist()
    # srcB = srcB.tolist()

    resA = []
    resB = []

    if(format == "Float32"):
        for i in srcA:
            resA.append(fp32_2_datum(number = i,masked = False))
        for i in srcB:
            resB.append(fp32_2_datum(number = i,masked = False))
    else:
        for i in srcA:
            resA.append(fp32_2_datum(number = i,masked = False))
        for i in srcB:
            resB.append(fp32_2_datum(number = i,masked = False))


    return resA , resB

def generate_golden(operation, operand1, operand2,format):
    
    dest = [0]*1024

    match operation:
        case "elwadd":
            for i in range(0,1023):
                dest[i] = operand1[i] + operand2[i]
        case "elwsub":
            for i in range(0,1023):
                dest[i] = operand2[i] - operand1[i]
        case "elwmul":
            for i in range(0,1023):
                dest[i] = operand1[i] * operand2[i]
        case "matmul":
            dest =  torch.matmul(operand2,operand1)
        case _:
            print("Unsupported operation!") 


    return dest

def write_stimuli_to_l1(buffer_A, loc_A, buffer_B, loc_B,format):
    # input: buffer_A,buffer_B -> list
    #        loc_A, loc_B -> integer

    hex_A = []
    hex_B = []
    decimal_A = []
    decimal_B = []

    for i in buffer_A:
        hex_A.append(hex(fp32_2_datum(i,masked = True)))
    for i in buffer_B:
        hex_B.append(hex(fp32_2_datum(i,masked = True)))

    for i in hex_A:
        decimal_A.append(hex_number_to_decimal_array(i,format))
    for i in hex_B:
        decimal_B.append(hex_number_to_decimal_array(i,format))

    decimal_A = flatten(decimal_A)
    decimal_B = flatten(decimal_B)

    # print()
    # print("-"*100)
    # print(decimal_A[0:8])
    # print(decimal_B[0:8])
    # print("-"*100)

    num_bytes = write_to_device("18-18", 0x1c000, decimal_A)
    num_bytes = write_to_device("18-18", 0x1b000, decimal_B)

    # change later
    return 0,0


# FOR NOW SUPPORT ONLY TORCH TYPES
@pytest.mark.parametrize("format", ["Float32", "Float16_b"]) # "Float16_b","Int32"])
@pytest.mark.parametrize("testname", ["eltwise_add_test"])
@pytest.mark.parametrize("mathop", ["elwadd", "elwsub", "elwmul"])

# Parametrized architecture. When needed add grayskull and blackhole
@pytest.mark.parametrize("machine", ["wormhole"])

def test_all(format, mathop, testname, machine):
    
    context = init_debuda()

    src_A, src_B = generate_stimuli(format)
    golden = generate_golden(mathop, src_A, src_B,format)
    bytes_A, bytes_B = write_stimuli_to_l1(src_A, 0x1b000, src_B, 0x1c000, format)
   
    # Running make on host and generated elfs on TRISC cores

    make_cmd = "make format="+format_args_dict[format]+ " " + "mathop=" + mathop_args_dict[mathop] + " testname=" + testname
    make_cmd = make_cmd + " machine=" + machine 
    os.system(make_cmd)
    
    run_elf("build/elf/"+testname+"_trisc0.elf", "18-18", risc_id = 1)
    run_elf("build/elf/"+testname+"_trisc1.elf", "18-18", risc_id = 2)
    run_elf("build/elf/"+testname+"_trisc2.elf", "18-18", risc_id = 3)
    
    # Read result from L1
    # *************************************
    read_data = read_words_from_device("18-18", 0x1a000, word_count = 1024)
    
    golden_form_L1 = []
    golden_bytes = []

    for word in read_data:
        number,bytess = int_2_float32(word)
        golden_form_L1.append(number)
        golden_bytes.append(bytess)

    #print("*************************************************************************")
    #print(format, mathop)
    #print(src_A[0])
    #print(src_B[0])
    if(format == "Float16_b"):
        print("*************************************************************************")
        print(format,mathop)
        print(golden[10])
        print(golden_form_L1[10])
        print(golden_bytes[10])
        # print("#########################################################################")
        # print(hex_read_data[0:4])
        print("*************************************************************************")

    os.system("make clean")

    # read mailboxes from L1 and assert their values
    # **************************************
    # UNPACK_MAILBOX's address is temporary
    unpack_mailbox = read_words_from_device("18-18", 0x19FF4, word_count = 1)
    unpack_mailbox = unpack_mailbox[0].to_bytes(4, 'big')
    unpack_mailbox = list(unpack_mailbox)

    math_mailbox = read_words_from_device("18-18", 0x19FF8, word_count = 1)
    math_mailbox = math_mailbox[0].to_bytes(4, 'big')
    math_mailbox = list(math_mailbox)

    pack_mailbox = read_words_from_device("18-18", 0x19FFC, word_count = 1)
    pack_mailbox = pack_mailbox[0].to_bytes(4, 'big')
    pack_mailbox = list(pack_mailbox)
    # **************************************
    
    assert len(golden) == len(golden_form_L1)

    # **************************************

    # if kerenls ran successfully all mailboxes should be 0x00000001
    assert unpack_mailbox == [0,0,0,1]
    assert math_mailbox == [0,0,0,1]
    assert pack_mailbox == [0,0,0,1]

    # compare results calculated by kernel and golden

    if(format == "Float32"):
        for i in range(0,512):
            assert abs(golden[i]-golden_form_L1[i]) <= 0.5 , f" i = {i} , {golden[i], golden_form_L1[i]}"  
    if(format == "Float16_b"):
        for i in range(0,512):
            assert abs(golden[i]-golden_form_L1[i]) <= 0.5 , f" i = {i},  {golden[i], golden_form_L1[i]}"  
