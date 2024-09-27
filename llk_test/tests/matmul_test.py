import pytest
import numpy as np
import torch
#import numfi

format_dict = {"Float32" : torch.float32, "Float16" : torch.float16, "Float16_b" : torch.bfloat16, "Int32" : torch.int32}

def generate_golden(srcA,srcB):
    #print(torch.matmul(srcB,srcA))
    return torch.matmul(srcB,srcA)


# FOR NOW SUPPORT ONLY TORCH TYPES

@pytest.mark.parametrize("format", ["Float32", "Float16", "Float16_b", "Int32"])
@pytest.mark.parametrize("tiles_cnt", [1])
@pytest.mark.parametrize("operation", ["matmul"])

#cpp_files = [] # Include some files after compilation is done
#golden = []

def test_matmul(format,tiles_cnt,operation):
    # generate random parameters for every format
    # problem exists with ints in pytorch so this if fixes it
    print(format)

    if(format != "Int32"):
        srcA = torch.rand(32,32, dtype = format_dict[format])
        srcB = torch.rand(32,32, dtype = format_dict[format])
    else:
        srcA = torch.randint(high = 200, size = (32,32)) # change high later
        srcB = torch.randint(high = 200, size = (32,32))

    golden = generate_golden(srcA,srcB)

    assert format in format_dict