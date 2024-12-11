# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens.tt_lens_lib import read_word_from_device, write_to_device

RISCV_DEBUG_REG_CFGREG_RD_CNTL = 0xFFB12058
RISCV_DEBUG_REG_DBG_RD_DATA = 0xFFB1205C
RISCV_DEBUG_REG_CFGREG_RDDATA = 0xFFB12078


def read_config_register0(address, mask, shift, loc, device_id, context):
    write_to_device(loc, RISCV_DEBUG_REG_CFGREG_RD_CNTL, [address], device_id, context)
    a = read_word_from_device(loc, RISCV_DEBUG_REG_CFGREG_RDDATA, device_id, context)
    return (a & mask) >> shift


ALU_FORMAT_SPEC_REG2_Dstacc_ADDR32 = 1
ALU_FORMAT_SPEC_REG2_Dstacc_MASK = 0x1E000000
ALU_FORMAT_SPEC_REG2_Dstacc_SHAMT = 25

ALU_ACC_CTRL_Fp32_enabled_ADDR32 = 1
ALU_ACC_CTRL_Fp32_enabled_SHAMT = 29
ALU_ACC_CTRL_Fp32_enabled_MASK = 0x20000000


def cfg_get_data_format(core_loc, device_id, context):
    return read_config_register0(
        ALU_FORMAT_SPEC_REG2_Dstacc_ADDR32,
        ALU_FORMAT_SPEC_REG2_Dstacc_MASK,
        ALU_FORMAT_SPEC_REG2_Dstacc_SHAMT,
        core_loc,
        device_id,
        context,
    )


def cfg_get_force_32bit_format(core_loc, device_id, context):
    return read_config_register0(
        ALU_ACC_CTRL_Fp32_enabled_ADDR32,
        ALU_ACC_CTRL_Fp32_enabled_MASK,
        ALU_ACC_CTRL_Fp32_enabled_SHAMT,
        core_loc,
        device_id,
        context,
    )
