import pytest
import torch
import os
import struct
from ieee754 import half, single, double, quadruple, octuple
from dbd.tt_debuda_init import init_debuda
from dbd.tt_debuda_lib import write_to_device, read_words_from_device
from dbd.tt_debuda_lib import run_elf

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

def merge_pairs(lst):
    return [lst[i] + lst[i + 1].split('x')[1] for i in range(0, len(lst) - 1, 2)]

def reverse_sublists(lst):
    return [lst[i:i+4][::-1] for i in range(0, len(lst), 4)]

def int_to_bytes_hex(value):
    # Pack the integer into bytes and convert to hex
    return [hex(b) for b in struct.pack('>I', value)]

def tensor2bytes(tens,format):
    buffer_A = tens.tolist()
    bin_A = []
    hex_A = []
    bytes_A = []
   
    for number in buffer_A:
        if format=="Float16":
            bin_A.append((['0000','0000','0000','0000'] + half(number).hex()[1]))
        else: #Float32 -> expand later
            bin_A.append((half(number).hex()[1]))
    
    for binary in bin_A:
        for i in binary:
            hex_A.append(str(hex(int(i,2))))
    
    hex_A  = merge_pairs(hex_A)
    #hex_A_reversed_endian = reverse_sublists(hex_A)
    # flatten list of lists
    #hex_A_reversed_endian = [item for sublist in hex_A_reversed_endian for item in sublist] 
    
    for hex_byte in hex_A:
        bytes_A.append(int(hex_byte,16))
    
    return bytes_A

def generate_stimuli(stimuli_format):

    srcA = [0]    
    srcB = [0]

    if(format != "Int32"):
        srcA = torch.rand(32*32, dtype = format_dict[stimuli_format]) + 0.5
        srcB = torch.rand(32*32, dtype = format_dict[stimuli_format]) + 0.5
    else:
        srcA = torch.randint(high = 200, size = 32*32) # change high later
        srcB = torch.randint(high = 200, size = 32*32)
    
    return srcA, srcB

def generate_golden(operation, operand1, operand2,format):
    
    dest = torch.zeros(32*32)

    match operation:
        case "elwadd":
            dest = operand1 + operand2
        case "elwsub":
            dest = operand2 - operand1
        case "elwmul":
            for i in range(0,1023):
                dest[i] = operand1[i] * operand2[i]
        case "matmul":
            dest =  torch.matmul(operand2,operand1)
        case _:
            print("Unsupported operation!") 

    dest = dest.to(format_dict[format])

    return dest

def write_stimuli_to_l1(buffer_A, loc_A, buffer_B, loc_B,format):
    # input: buffer_A,buffer_B -> list
    #        loc_A, loc_B -> integer

    bin_A = []
    hex_A = []
    bytes_A = []
    bin_B = []
    hex_B = []
    bytes_B = []        

    for number in buffer_A:
        if format=="Float16":
            bin_A.append((['0000','0000','0000','0000'] + half(number).hex()[1]))
        else: #Float32 -> expand later
            bin_A.append((single(number).hex()[1]))
    
    for binary in bin_A:
        for i in binary:
            hex_A.append(str(hex(int(i,2))))
    
    #print("********************HEX A***************************************")
    #print(hex_A[0:4])
    #print("****************************************************************")

    hex_A  = merge_pairs(hex_A)
    hex_A_reversed_endian = reverse_sublists(hex_A)
    # flatten list of lists
    hex_A_reversed_endian = [item for sublist in hex_A_reversed_endian for item in sublist] 
    
    for hex_byte in hex_A_reversed_endian:
        bytes_A.append(int(hex_byte,16))


    #********* B ***********

    for number in buffer_B:
        if format=="Float16":
            bin_B.append((['0000','0000','0000','0000'] + half(number).hex()[1]))
        else: #Float32 -> expand later
            bin_B.append((single(number).hex()[1]))
    
    for binary in bin_B:
        for i in binary:
            hex_B.append(str(hex(int(i,2))))
    
    hex_B  = merge_pairs(hex_B)
    hex_B_reversed_endian = reverse_sublists(hex_B)
    # flatten list of lists
    hex_B_reversed_endian = [item for sublist in hex_B_reversed_endian for item in sublist] 
    
    for hex_byte in hex_B_reversed_endian:
        bytes_B.append(int(hex_byte,16))

    num_bytes = write_to_device("18-18", 0x1c000, bytes_A)
    num_bytes = write_to_device("18-18", 0x1b000, bytes_B)

    #print("****************************************************************")
    #print(format)
    #print(hex_A[0:4])
    #print(hex_A_reversed_endian[0:4])
    #print(bytes_A[0:4])
    #print(buffer_A[0])
    #print("Writing_A " + str(bytes_A[0:4]) +" to "+ str(hex(loc_A)))
    #print("Writing_B " + str(bytes_B[0:4]) +" to "+ str(hex(loc_B)))
    #print("****************************************************************")

    return bytes_A, bytes_B


# FOR NOW SUPPORT ONLY TORCH TYPES
@pytest.mark.parametrize("format", ["Float32", "Float16"]) # "Float16_b","Int32"])
@pytest.mark.parametrize("testname", ["eltwise_add_test"])
@pytest.mark.parametrize("mathop", ["elwadd", "elwsub", "elwmul"])

# Parametrized architecture. When needed add grayskull and blackhole
@pytest.mark.parametrize("machine", ["wormhole"])

def test_all(format, mathop, testname, machine):
    
    context = init_debuda()

    src_A, src_B = generate_stimuli(format)
    golden = generate_golden(mathop, src_A, src_B,format)
    golden_bytes = tensor2bytes(golden,format)
    bytes_A, bytes_B = write_stimuli_to_l1(src_A.tolist(), 0x1b000, src_B.tolist(), 0x1c000, format)
   
    # Running make on host and generated elfs on TRISC cores

    make_cmd = "make format="+format_args_dict[format]+ " " + "mathop=" + mathop_args_dict[mathop] + " testname=" + testname
    make_cmd = make_cmd + " machine=" + machine 
    os.system(make_cmd)
    
    run_elf("build/elf/"+testname+"_trisc0.elf", "18-18", risc_id = 1)
    run_elf("build/elf/"+testname+"_trisc1.elf", "18-18", risc_id = 2)
    run_elf("build/elf/"+testname+"_trisc2.elf", "18-18", risc_id = 3)
    
    read_data = read_words_from_device("18-18", 0x1a000, word_count = 1024)
    hex_read_data = []
    for element in read_data:
        hex_read_data.append(int_to_bytes_hex(element))
    
    # flatten
    hex_read_data = [item for sublist in hex_read_data for item in sublist] 
    
    read_bytes = []
    for byte in hex_read_data:
        read_bytes.append(int(byte,16))

    print("*************************************************************************")
    print(format, mathop)
    print(src_A[0].tolist())
    print(src_B[0].tolist())
    print(golden[0].tolist())
    print("#########################################################################")
    print(bytes_A[0:4])
    print(bytes_B[0:4])
    print(golden_bytes[0:4])
    print("-------------------------------------------------------------------------")
    print(read_bytes[0:4])
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

    # if kerenls ran successfully all mailboxes should be 0x00000001
    assert unpack_mailbox == [0,0,0,1]
    assert math_mailbox == [0,0,0,1]
    assert pack_mailbox == [0,0,0,1]

    # compare results calculated by kernel and golden

    #assert (len(bytes_A) == len(dec_data)) or (len(bytes_A) == len(dec_data)/2)
    #assert (bytes_A == dec_data) or (bytes_A == dec_data[:2048])

    #assert read_bytes[0:4] == golden_bytes[0:4]
    tolerance = 2
    for read_byte, golden_byte in zip(read_bytes[0:4], golden_bytes[0:4]):
        assert abs(read_byte - golden_byte) <= tolerance, f"Difference too large: {read_byte} vs {golden_byte}"

    assert format in format_dict
    assert mathop in mathop_args_dict