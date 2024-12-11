# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens.tt_lens_lib import read_word_from_device, write_to_device


def read_config_register0(address, mask, shift, loc, device_id, context):
    device = context.devices[device_id]
    write_to_device(loc, device.RISCV_DEBUG_REG_CFGREG_RD_CNTL, [address], device_id, context)
    a = read_word_from_device(loc, device.RISCV_DEBUG_REG_CFGREG_RDDATA, device_id, context)
    return (a & mask) >> shift


def cfg_get_data_format(core_loc, device_id, context):
    device = context.devices[device_id]
    return read_config_register0(
        device.ALU_FORMAT_SPEC_REG2_Dstacc_ADDR32,
        device.ALU_FORMAT_SPEC_REG2_Dstacc_MASK,
        device.ALU_FORMAT_SPEC_REG2_Dstacc_SHAMT,
        core_loc,
        device_id,
        context,
    )


def cfg_get_force_32bit_format(core_loc, device_id, context):
    device = context.devices[device_id]
    return read_config_register0(
        device.ALU_ACC_CTRL_Fp32_enabled_ADDR32,
        device.ALU_ACC_CTRL_Fp32_enabled_MASK,
        device.ALU_ACC_CTRL_Fp32_enabled_SHAMT,
        core_loc,
        device_id,
        context,
    )
