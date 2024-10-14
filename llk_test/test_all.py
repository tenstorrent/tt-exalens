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

def generate_stimuli(stimuli_format):

    srcA = [0]    
    srcB = [0]

    if(format != "Int32"):
        srcA = torch.rand(32*32, dtype = format_dict[stimuli_format])
        srcB = torch.rand(32*32, dtype = format_dict[stimuli_format])
    else:
        srcA = torch.randint(high = 200, size = 32*32) # change high later
        srcB = torch.randint(high = 200, size = 32*32)
    
    return srcA, srcB

def generate_golden(operation, operand1, operand2):
    
    dest = torch.zeros(32*32)

    match operation:
        case "elwadd":
            dest = operand1 + operand2
        case "elwsub":
            dest = operand1 - operand2
        case "elwmul":
            for i in range(0,1023):
                dest[i] = operand1[i] * operand2[i]
        case "matmul":
            dest =  torch.matmul(operand2,operand1)
        case _:
            print("Unsupported operation!") 

def write_stimuli_to_l1(buffer_A, loc_A, buffer_B, loc_B,format):

    hex_A = []
    hex_B = []

    if(format == "Float16") or (format == "Float16_b"):
        for i in buffer_A:
            hex_A.append(str((half(i).hex())[0]))
        for i in buffer_B:
            hex_B.append(str((half(i).hex())[0]))
    else:  
        for i in buffer_A:
            hex_A.append(str((single(i).hex())[0]))
        for i in buffer_B:
            hex_B.append(str((single(i).hex())[0]))

    hex_A_string = []    
    hex_B_string = []
    
    for i in hex_A:
        hex_A_string.append(("0x"+str(i)))
    for i in hex_B:
        hex_B_string.append(("0x"+str(i)))

    bytes_A = []
    bytes_B = []

    for i in hex_A_string:
        for j in range(2,len(i),2):
            byte_str = i[j:j+2]
            byte_nr = int(byte_str,16)
            bytes_A.append(byte_nr)

    for i in hex_B_string:
        for j in range(2,len(i),2):
            byte_str = i[j:j+2]
            byte_nr = int(byte_str,16)
            bytes_B.append(byte_nr)

    num_bytes = write_to_device("18-18", 0x1c000, bytes_A)
    num_bytes = write_to_device("18-18", 0x1b000, bytes_B)

    return bytes_A, bytes_B


# FOR NOW SUPPORT ONLY TORCH TYPES
@pytest.mark.parametrize("format", ["Float32", "Float16", "Float16_b"]) #, "Int32"])
#@pytest.mark.parametrize("tiles_cnt", [1])
@pytest.mark.parametrize("testname", ["eltwise_add_test"])
@pytest.mark.parametrize("mathop", ["elwadd", "elwsub", "elwmul"])

def test_all(format,mathop,testname):
    
    print("\n")
    print("===================")
    print(format)
    print(mathop)
    print("===================")

    srcA, srcB = generate_stimuli(format)
    golden = generate_golden(mathop,srcA,srcB)

    bytes_A, bytes_B = write_stimuli_to_l1(srcA.tolist(),0x1c000,srcB.tolist(),0x1b000,format)
    read_data = read_words_from_device("18-18",0x1c000,word_count = 1024)

    read_bytes = []
    read_hex = []

    for i in read_data:
        read_bytes.append(i.to_bytes(4,'little'))
    
    for i in read_bytes:
        l = list(i)
        for byte in l:
            read_hex.append(hex(byte))

    make_cmd = "make format="+format_args_dict[format]+ " " + "mathop=" + mathop_args_dict[mathop] + " testname="+testname
    os.system(make_cmd)
    
    run_elf("build/elf/"+testname+"_trisc0.elf", "18-18", risc_id = 1)
    run_elf("build/elf/"+testname+"_trisc1.elf", "18-18", risc_id = 2)
    run_elf("build/elf/"+testname+"_trisc2.elf", "18-18", risc_id = 3)
    
    os.system("make clean")

    dec_data = []
    for i in read_hex:
        dec_data.append(int(i,16))

    # read mailboxes from L1 and assert their values
    unpack_mailbox = read_words_from_device("18-18", 0xd004, word_count = 1)
    unpack_mailbox = unpack_mailbox[0].to_bytes(4, 'big')
    unpack_mailbox = list(unpack_mailbox)

    math_mailbox = read_words_from_device("18-18", 0x12004, word_count = 1)
    math_mailbox = math_mailbox[0].to_bytes(4, 'big')
    math_mailbox = list(math_mailbox)

    pack_mailbox = read_words_from_device("18-18", 0x16004, word_count = 1)
    pack_mailbox = pack_mailbox[0].to_bytes(4, 'big')
    pack_mailbox = list(pack_mailbox)

    # if kerenls ran successfully all mailboxes should be 0x00000001
    #assert unpack_mailbox == [0,0,0,1]
    assert math_mailbox == [0,0,0,1]
    assert pack_mailbox == [0,0,0,1]

    #investigate what happens with float16 and float16_b and byte count

    assert (len(bytes_A) == len(dec_data)) or (len(bytes_A) == len(dec_data)/2)
    assert (bytes_A == dec_data) or (bytes_A == dec_data[:2048])
    assert format in format_dict
    assert mathop in mathop_args_dict