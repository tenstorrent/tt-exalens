import pytest
import torch
import os
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

if __name__=="__main__":
    context = init_debuda()

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

def write_stimuli_to_l1(buffer_A, loc_A, buffer_B, loc_B):
    
    num_bytes = write_to_device("18-18", loc_A, buffer_A, context=context)
    num_bytes = write_to_device("18-18", loc_B, buffer_B, context=context)



# FOR NOW SUPPORT ONLY TORCH TYPES
@pytest.mark.parametrize("format", ["Float32", "Float16", "Float16_b"]) #, "Int32"])
#@pytest.mark.parametrize("tiles_cnt", [1])
@pytest.mark.parametrize("mathop", ["elwadd", "elwsub", "elwmul"])

def test_all(format,mathop):
    
    print("\n")
    print("===================")
    print(format)
    print(mathop)
    print("===================")

    srcA, srcB = generate_stimuli(format)
    golden = generate_golden(mathop,srcA,srcB)

    write_stimuli_to_l1(srcA,0x1c000,srcB,0x1b000)

    print(golden)

    make_cmd = "make dis format="+format_args_dict[format]+ " " + "mathop=" + mathop_args_dict[mathop]
    os.system(make_cmd)
    
    # copy stimuli to L1
    # run cores with dedicated elf files
    # read stimuli back from L1
    # read mailboxes and assert 1
    # compare results
    
    os.system("make clean")

    assert format in format_dict
    assert mathop in mathop_args_dict