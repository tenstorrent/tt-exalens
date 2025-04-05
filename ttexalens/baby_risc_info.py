# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from typing import Union
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.register_store import RegisterStore
from ttexalens.risc_info import RiscInfo


class BabyRiscInfo(RiscInfo):
    def __init__(
        self,
        risc_name,
        risc_id,
        reset_flag_shift: int,
        branch_prediction_register: str,
        branch_prediction_mask: int,
        default_code_start_address: int,
        code_start_address_register: int,
        code_start_address_enable_register: str,
        code_start_address_enable_bit: int,
        l1_size: int,
        max_watchpoints: int = 8,
        status_read_valid_mask: int = 1 << 30,
    ):
        self.risc_name = risc_name
        self.risc_id = risc_id
        self.reset_flag_shift = reset_flag_shift
        self.branch_prediction_register = branch_prediction_register
        self.branch_prediction_mask = branch_prediction_mask
        self.default_code_start_address = default_code_start_address
        self.code_start_address_register = code_start_address_register
        self.code_start_address_enable_register = code_start_address_enable_register
        self.code_start_address_enable_bit = code_start_address_enable_bit
        self.l1_size = l1_size
        self.max_watchpoints = max_watchpoints
        self.status_read_valid_mask = status_read_valid_mask

    def get_code_start_address(self, register_store: RegisterStore) -> int:
        enabled_register_value = register_store.read_register(self.code_start_address_enable_register)
        if (enabled_register_value & self.code_start_address_enable_bit) == 0:
            return self.default_code_start_address
        return register_store.read_register(self.code_start_address_register)

    def set_code_start_address(self, register_store: RegisterStore, address: Union[int, None]):
        if address is not None:
            enabled_register_value = register_store.read_register(self.code_start_address_enable_register)
            register_store.write_register(
                self.code_start_address_enable_register, enabled_register_value | self.code_start_address_enable_bit
            )
            register_store.write_register(self.code_start_address_register, address)
        else:
            enabled_register_value = register_store.read_register(self.code_start_address_enable_register)
            register_store.write_register(
                self.code_start_address_enable_register, enabled_register_value & ~self.code_start_address_enable_bit
            )
