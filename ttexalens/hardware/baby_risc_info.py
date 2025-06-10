# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.risc_info import RiscInfo
from ttexalens.register_store import RegisterStore


class BabyRiscInfo(RiscInfo):
    def __init__(
        self,
        risc_name: str,
        risc_id: int,
        noc_block: NocBlock,
        neo_id: int | None,
        l1: MemoryBlock,
        max_watchpoints: int,
        reset_flag_shift: int,
        branch_prediction_register: str,
        branch_prediction_mask: int,
        default_code_start_address: int,
        code_start_address_register: str,
        code_start_address_enable_register: str,
        code_start_address_enable_bit: int,
        data_private_memory: MemoryBlock | None = None,
        code_private_memory: MemoryBlock | None = None,
        status_read_valid_mask: int = 1 << 30,
        debug_hardware_present: bool = False,
        can_change_code_start_address: bool = True,
    ):
        super().__init__(risc_name, risc_id, noc_block, neo_id, l1)
        self.max_watchpoints = max_watchpoints
        self.reset_flag_shift = reset_flag_shift
        self.branch_prediction_register = branch_prediction_register
        self.branch_prediction_mask = branch_prediction_mask
        self.default_code_start_address = default_code_start_address
        self.code_start_address_register = code_start_address_register
        self.code_start_address_enable_register = code_start_address_enable_register
        self.code_start_address_enable_bit = code_start_address_enable_bit
        self.data_private_memory = data_private_memory
        self.code_private_memory = code_private_memory
        self.status_read_valid_mask = status_read_valid_mask
        self.debug_hardware_present = debug_hardware_present
        self.can_change_code_start_address = can_change_code_start_address

    def get_code_start_address(self, register_store: RegisterStore) -> int:
        if not self.can_change_code_start_address:
            return self.default_code_start_address
        enabled_register_value = register_store.read_register(self.code_start_address_enable_register)
        if (enabled_register_value & self.code_start_address_enable_bit) == 0:
            return self.default_code_start_address
        return register_store.read_register(self.code_start_address_register)

    def set_code_start_address(self, register_store: RegisterStore, address: int | None):
        if not self.can_change_code_start_address:
            if address is None or address == self.default_code_start_address:
                return
            raise RuntimeError(
                f"Cannot change code start address for {self.risc_name} on {self.noc_block.location.to_user_str()}"
            )
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
