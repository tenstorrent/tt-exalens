# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.register_store import (
    DebugRegisterDescription,
    RegisterDescription,
)


register_map: dict[str, RegisterDescription] = {
    "RISCV_DEBUG_REG_DBG_BUS_CNTL_REG": DebugRegisterDescription(offset=0x028),
    "RISCV_DEBUG_REG_CFGREG_RD_CNTL": DebugRegisterDescription(offset=0x02C),
    "RISCV_DEBUG_REG_DBG_RD_DATA": DebugRegisterDescription(offset=0x030),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_EN": DebugRegisterDescription(offset=0x034),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD": DebugRegisterDescription(offset=0x038),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_STATUS": DebugRegisterDescription(offset=0x03C),
    "RISCV_DEBUG_REG_DBG_FEATURE_DISABLE": DebugRegisterDescription(offset=0x040),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA": DebugRegisterDescription(offset=0x044),
    "RISCV_DEBUG_REG_CG_CTRL_HYST0": DebugRegisterDescription(offset=0x048),
    "RISCV_DEBUG_REG_CG_CTRL_HYST1": DebugRegisterDescription(offset=0x04C),
    "RISCV_DEBUG_REG_CFGREG_RDDATA": DebugRegisterDescription(offset=0x050),
    "RISCV_DEBUG_REG_CG_CTRL_HYST2": DebugRegisterDescription(offset=0x054),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": DebugRegisterDescription(offset=0x058),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": DebugRegisterDescription(offset=0x05C),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": DebugRegisterDescription(offset=0x060),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": DebugRegisterDescription(offset=0x064),
    "RISCV_DEBUG_REG_TRISC_PC_BUF_OVERRIDE": DebugRegisterDescription(offset=0x068),
    "RISCV_DEBUG_REG_TRISC_PC_BUF_OVERRIDE1": DebugRegisterDescription(offset=0x06C),
    "RISCV_DEBUG_REG_DBG_INVALID_INSTRN": DebugRegisterDescription(offset=0x070),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0": DebugRegisterDescription(offset=0x074),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL1": DebugRegisterDescription(offset=0x078),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS": DebugRegisterDescription(offset=0x07C),
    "RISCV_DEBUG_REG_STOCH_RND_MASK0": DebugRegisterDescription(offset=0x080),
    "RISCV_DEBUG_REG_STOCH_RND_MASK1": DebugRegisterDescription(offset=0x084),
    "RISCV_DEBUG_REG_STICKY_BITS": DebugRegisterDescription(offset=0x088),
    "RISCV_DEBUG_REG_SOFT_RESET_0": DebugRegisterDescription(offset=0x0B8),
    "RISCV_DEBUG_REG_SOFT_RESET_1": DebugRegisterDescription(offset=0x0BC),
    "RISCV_DEBUG_REG_WATCHDOG_TIMER": DebugRegisterDescription(offset=0x0C0),
    "RISCV_DEBUG_REG_WDT_CNTL": DebugRegisterDescription(offset=0x0C4),
    "RISCV_DEBUG_REG_WDT_STATUS": DebugRegisterDescription(offset=0x0C8),
    "RISCV_DEBUG_REG_WALL_CLOCK_0": DebugRegisterDescription(offset=0x0CC),
    "RISCV_DEBUG_REG_WALL_CLOCK_1": DebugRegisterDescription(offset=0x0D0),
    "RISCV_DEBUG_REG_WALL_CLOCK_1_AT": DebugRegisterDescription(offset=0x0D4),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_CMD": DebugRegisterDescription(offset=0x0D8),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_CNTL": DebugRegisterDescription(offset=0x0DC),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_STATUS": DebugRegisterDescription(offset=0x0E0),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_BUF0_START_ADDR": DebugRegisterDescription(offset=0x0E4),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_BUF0_END_ADDR": DebugRegisterDescription(offset=0x0E8),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_BUF1_START_ADDR": DebugRegisterDescription(offset=0x0EC),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_BUF1_END_ADDR": DebugRegisterDescription(offset=0x0F0),
    "RISCV_DEBUG_REG_PERF_CNT_MUX_CTRL": DebugRegisterDescription(offset=0x0F4),
    "RISCV_DEBUG_REG_LFSR_HIT_MASK": DebugRegisterDescription(offset=0x0F8),
    "RISCV_DEBUG_REG_DISABLE_RESET": DebugRegisterDescription(offset=0x0FC),
    "TRISC_RESET_PC_SEC0_PC": DebugRegisterDescription(offset=0x100),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC0_RESET_PC": DebugRegisterDescription(offset=0x100),  # New name
    "TRISC_RESET_PC_SEC1_PC": DebugRegisterDescription(offset=0x104),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC1_RESET_PC": DebugRegisterDescription(offset=0x104),  # New name
    "TRISC_RESET_PC_SEC2_PC": DebugRegisterDescription(offset=0x108),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC2_RESET_PC": DebugRegisterDescription(offset=0x108),  # New name
    "TRISC_RESET_PC_SEC3_PC": DebugRegisterDescription(offset=0x10C),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC3_RESET_PC": DebugRegisterDescription(offset=0x10C),  # New name
    "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": DebugRegisterDescription(
        offset=0x110, mask=0xF, shift=0
    ),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE": DebugRegisterDescription(offset=0x110, mask=0xF, shift=0),  # New name
    "RISCV_DEBUG_REG_DEST_CG_CTRL": DebugRegisterDescription(offset=0x114),
    "RISCV_DEBUG_REG_CG_CTRL_EN": DebugRegisterDescription(offset=0x118),
    "RISCV_DEBUG_REG_CG_KICK": DebugRegisterDescription(offset=0x11C),
    "RISCV_IC_INVALIDATE_InvalidateAll": DebugRegisterDescription(offset=0x258, mask=0xF, shift=0),
    "DISABLE_RISC_BP_Disable_trisc": DebugRegisterDescription(
        offset=0x270, mask=0xF, shift=0
    ),  # Old name from previous architectures
    "RISC_BRANCH_PREDICTION_CTRL": DebugRegisterDescription(offset=0x270, mask=0xF, shift=0),  # New name
}
