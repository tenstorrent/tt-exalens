# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.risc_info import RiscInfo
from ttexalens.register_store import RegisterStore
from ttexalens.risc_loader import RiscLoader
from ttexalens.tt_exalens_lib import write_words_to_device


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
        branch_prediction_register: str | None = None,
        branch_prediction_mask: int | None = None,
        default_code_start_address: int | None = None,
        code_start_address_register: str | None = None,
        code_start_address_enable_register: str | None = None,
        code_start_address_enable_bit: int | None = None,
        data_private_memory: MemoryBlock | None = None,
        code_private_memory: MemoryBlock | None = None,
        status_read_valid_mask: int = 1 << 30,
        debug_hardware_present: bool = False,
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
        self.can_change_code_start_address = self.code_start_address_register is not None

    def get_code_start_address(self, register_store: RegisterStore) -> int:
        override_enabled = self.can_change_code_start_address
        if override_enabled and (
            self.code_start_address_enable_register is not None and self.code_start_address_enable_bit is not None
        ):
            enabled_register_value = register_store.read_register(self.code_start_address_enable_register)
            if (enabled_register_value & self.code_start_address_enable_bit) == 0:
                override_enabled = True

        if not override_enabled:
            assert self.default_code_start_address is not None
            return self.default_code_start_address
        else:
            assert self.code_start_address_register is not None
            return register_store.read_register(self.code_start_address_register)

    def set_code_start_address(self, register_store: RegisterStore, address: int | None):
        if not self.can_change_code_start_address:
            if address is None or address == self.default_code_start_address:
                return

            # If we cannot change the code start address, we write a jump instruction to the specified address
            jump_instruction = RiscLoader.get_jump_to_offset_instruction(address)
            write_words_to_device(
                register_store.location,
                0,
                jump_instruction,
                register_store.location._device._id,
                register_store.location._device._context,
            )
        elif address is not None:
            if self.code_start_address_enable_register is not None and self.code_start_address_enable_bit is not None:
                enabled_register_value = register_store.read_register(self.code_start_address_enable_register)
                register_store.write_register(
                    self.code_start_address_enable_register, enabled_register_value | self.code_start_address_enable_bit
                )
            assert self.code_start_address_register is not None
            register_store.write_register(self.code_start_address_register, address)
        else:
            assert (
                self.code_start_address_enable_register is not None and self.code_start_address_enable_bit is not None
            )
            enabled_register_value = register_store.read_register(self.code_start_address_enable_register)
            register_store.write_register(
                self.code_start_address_enable_register, enabled_register_value & ~self.code_start_address_enable_bit
            )
