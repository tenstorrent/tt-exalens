import pytest
import torch
import os
import struct
from dbd.tt_debuda_init import init_debuda
from dbd.tt_debuda_lib import write_to_device, read_words_from_device, run_elf

import time

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
}

def generate_stimuli(stimuli_format):
    srcA = [0x4040] * 1024
    srcB = [0x4040] * 1024

    return srcA , srcB

@pytest.mark.parametrize("format", ["Float16_b"])
@pytest.mark.parametrize("testname", ["configurable_test"])
@pytest.mark.parametrize("machine", ["wormhole"])
def test_multiple_kernels(format, testname, machine):
    context = init_debuda()

    make_cmd = f"make format={format_args_dict[format]} testname={testname} machine={machine}"
    make_cmd += " unpack_kern_cnt=3 unpack_kerns=1,1,1"
    make_cmd += " math_kern_cnt=3 math_kerns=1,2,3"
    make_cmd += " pack_kern_cnt=3 pack_kerns=1,1,1"
    print()
    print(make_cmd)
    os.system(make_cmd)

    time.sleep(3)

    os.system("make clean")

    assert 1==1