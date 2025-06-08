# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.register_store import (
    DebugRegisterDescription,
    RegisterDescription,
)


register_map: dict[str, RegisterDescription] = {
    "RISCV_DEBUG_REG_DBG_BUS_CNTL_REG": DebugRegisterDescription(offset=0x28),
    "RISCV_DEBUG_REG_CFGREG_RD_CNTL": DebugRegisterDescription(offset=0x2C),
    "RISCV_DEBUG_REG_DBG_RD_DATA": DebugRegisterDescription(offset=0x30),
    "DISABLE_RISC_BP_Disable_trisc": DebugRegisterDescription(
        offset=0x260, mask=0xF, shift=0
    ),  # Old name from previous architectures
    "RISC_BRANCH_PREDICTION_CTRL": DebugRegisterDescription(offset=0x260, mask=0xF, shift=0),  # New name
    "RISCV_IC_INVALIDATE_InvalidateAll": DebugRegisterDescription(offset=0x248, mask=0xF, shift=0),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": DebugRegisterDescription(offset=0x54),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": DebugRegisterDescription(offset=0x58),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": DebugRegisterDescription(offset=0x5C),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": DebugRegisterDescription(offset=0x60),
    "RISCV_DEBUG_REG_SOFT_RESET_0": DebugRegisterDescription(offset=0xB0),
    "TRISC_RESET_PC_SEC0_PC": DebugRegisterDescription(offset=0xF8),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC0_RESET_PC": DebugRegisterDescription(offset=0xF8),  # New name
    "TRISC_RESET_PC_SEC1_PC": DebugRegisterDescription(offset=0xFC),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC1_RESET_PC": DebugRegisterDescription(offset=0xFC),  # New name
    "TRISC_RESET_PC_SEC2_PC": DebugRegisterDescription(offset=0x100),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC2_RESET_PC": DebugRegisterDescription(offset=0x100),  # New name
    "TRISC_RESET_PC_SEC3_PC": DebugRegisterDescription(offset=0x104),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC3_RESET_PC": DebugRegisterDescription(offset=0x104),  # New name
    "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": DebugRegisterDescription(
        offset=0x108, mask=0xF, shift=0
    ),  # Old name from configuration register
    "RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE": DebugRegisterDescription(offset=0x108, mask=0xF, shift=0),  # New name
}
