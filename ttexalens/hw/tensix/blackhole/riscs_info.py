# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from typing import Union
from ttexalens.baby_risc_info import BabyRiscInfo
from ttexalens.register_store import RegisterStore


class BriscInfo(BabyRiscInfo):
    def __init__(self):
        super().__init__(
            risc_name="brisc",
            risc_id=0,
            reset_flag_shift=11,
            branch_prediction_register="DISABLE_RISC_BP_Disable_main",
            branch_prediction_mask=1,
            default_code_start_address=0,
            code_start_address_register="",
            code_start_address_enable_register="",
            code_start_address_enable_bit=0,
            l1_size=1536 * 1024,
            private_memory_base=0xFFB00000,
        )

    def get_code_start_address(self, register_store: RegisterStore) -> int:
        # BRISC code always starts at 0x00000000
        return 0

    def set_code_start_address(self, register_store: RegisterStore, address: Union[int, None]):
        assert address is None or address == 0, "BRISC code start address can only be set to 0"


class Trisc0Info(BabyRiscInfo):
    def __init__(self):
        super().__init__(
            risc_name="trisc0",
            risc_id=1,
            reset_flag_shift=12,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b001,
            default_code_start_address=0x6000,
            code_start_address_register="TRISC_RESET_PC_SEC0_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b001,
            l1_size=1536 * 1024,
            private_memory_base=0xFFB00000,
        )


class Trisc1Info(BabyRiscInfo):
    def __init__(self):
        super().__init__(
            risc_name="trisc1",
            risc_id=2,
            reset_flag_shift=13,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b010,
            default_code_start_address=0xA000,
            code_start_address_register="TRISC_RESET_PC_SEC1_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b010,
            l1_size=1536 * 1024,
            private_memory_base=0xFFB00000,
        )


class Trisc2Info(BabyRiscInfo):
    def __init__(self):
        super().__init__(
            risc_name="trisc2",
            risc_id=3,
            reset_flag_shift=14,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b100,
            default_code_start_address=0xE000,
            code_start_address_register="TRISC_RESET_PC_SEC2_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b100,
            l1_size=1536 * 1024,
            private_memory_base=0xFFB00000,
        )


class NcriscInfo(BabyRiscInfo):
    def __init__(self):
        super().__init__(
            risc_name="ncrisc",
            risc_id=3,
            reset_flag_shift=18,
            branch_prediction_register="DISABLE_RISC_BP_Disable_ncrisc",
            branch_prediction_mask=0x1,
            default_code_start_address=0xFFC00000,
            code_start_address_register="NCRISC_RESET_PC_PC",
            code_start_address_enable_register="NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b1,
            l1_size=1536 * 1024,
            private_memory_base=0xFFB00000,
            private_code_base=0xFFC00000,
        )


class EriscInfo(BabyRiscInfo):
    def __init__(self):
        super().__init__(
            risc_name="erisc",
            risc_id=0,
            reset_flag_shift=11,
            branch_prediction_register="DISABLE_RISC_BP_Disable_main",
            branch_prediction_mask=1,
            default_code_start_address=0,
            code_start_address_register="",
            code_start_address_enable_register="",
            code_start_address_enable_bit=0,
            l1_size=512 * 1024,
            private_memory_base=0xFFB00000,
        )

    def get_code_start_address(self, register_store: RegisterStore) -> int:
        # ERISC code always starts at 0x00000000
        return 0

    def set_code_start_address(self, register_store: RegisterStore, address: Union[int, None]):
        assert address is None or address == 0, "ERISC code start address can only be set to 0"
