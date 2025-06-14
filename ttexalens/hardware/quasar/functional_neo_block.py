# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from typing import Callable
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.quasar.functional_neo_debug_bus_signals import debug_bus_signal_map
from ttexalens.hardware.quasar.functional_neo_registers import register_map
from ttexalens.hardware.quasar.functional_worker_block import QuasarFunctionalWorkerBlock
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.register_store import (
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


def get_register_base_address_callable(
    neo_base_address: DeviceAddress,
) -> Callable[[RegisterDescription], DeviceAddress]:
    def get_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
        assert neo_base_address.private_address is not None, "RISC base address must have a private address"
        assert neo_base_address.noc_address is not None, "RISC base address must have a NOC address"

        if isinstance(register_description, ConfigurationRegisterDescription):
            return DeviceAddress(
                private_address=neo_base_address.private_address + 0xA000,
                noc_address=neo_base_address.noc_address + 0xA000,
            )
        elif isinstance(register_description, DebugRegisterDescription):
            return DeviceAddress(
                private_address=neo_base_address.private_address + 0x0000,
                noc_address=neo_base_address.noc_address + 0x0000,
            )
        else:
            raise ValueError(f"Unsupported register description type: {type(register_description)}. ")

    return get_register_base_address


class QuasarFunctionalNeoBlock:
    def __init__(
        self,
        noc_block: QuasarFunctionalWorkerBlock,
        neo_id: int,
        neo_base_address: DeviceAddress,
        risc_base_start_address: int,
    ):
        assert neo_base_address.private_address is not None, "RISC base address must have a private address"
        assert neo_base_address.noc_address is not None, "RISC base address must have a NOC address"

        self.noc_block = noc_block
        self.neo_id = neo_id
        self.debug_bus = DebugBusSignalStore(debug_bus_signal_map, noc_block, neo_id)
        # TODO: This register initialization should be moved to global scope to avoid its calculation every time object is created
        # TODO: It should be done once Quasar is finalized and we know all about its hardware. For simulator we create only few of these blocks
        register_store_initialization = RegisterStore.create_initialization(
            register_map, get_register_base_address_callable(neo_base_address)
        )
        self.register_store = RegisterStore(register_store_initialization, noc_block.location, neo_id)

        self.trisc0 = BabyRiscInfo(
            risc_name="trisc0",
            risc_id=0,
            noc_block=noc_block,
            neo_id=neo_id,
            l1=noc_block.l1,
            max_watchpoints=8,
            reset_flag_shift=11,
            branch_prediction_register="RISC_BRANCH_PREDICTION_CTRL",
            branch_prediction_mask=0b0001,
            default_code_start_address=risc_base_start_address + 0x00006000,
            code_start_address_register="RISCV_DEBUG_REG_TRISC0_RESET_PC",
            code_start_address_enable_register="RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE",
            code_start_address_enable_bit=0,
            data_private_memory=MemoryBlock(
                size=8 * 1024,
                address=DeviceAddress(
                    private_address=neo_base_address.private_address + 0x2000,
                    noc_address=neo_base_address.noc_address + 0x2000,
                ),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc1 = BabyRiscInfo(
            risc_name="trisc1",
            risc_id=1,
            noc_block=noc_block,
            neo_id=neo_id,
            l1=noc_block.l1,
            max_watchpoints=8,
            reset_flag_shift=12,
            branch_prediction_register="RISC_BRANCH_PREDICTION_CTRL",
            branch_prediction_mask=0b0010,
            default_code_start_address=risc_base_start_address + 0x0000A000,
            code_start_address_register="RISCV_DEBUG_REG_TRISC1_RESET_PC",
            code_start_address_enable_register="RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE",
            code_start_address_enable_bit=1,
            data_private_memory=MemoryBlock(
                size=8 * 1024,
                address=DeviceAddress(
                    private_address=neo_base_address.private_address + 0x4000,
                    noc_address=neo_base_address.noc_address + 0x4000,
                ),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc2 = BabyRiscInfo(
            risc_name="trisc2",
            risc_id=2,
            noc_block=noc_block,
            neo_id=neo_id,
            l1=noc_block.l1,
            max_watchpoints=8,
            reset_flag_shift=13,
            branch_prediction_register="RISC_BRANCH_PREDICTION_CTRL",
            branch_prediction_mask=0b0100,
            default_code_start_address=risc_base_start_address + 0x0000E000,
            code_start_address_register="RISCV_DEBUG_REG_TRISC2_RESET_PC",
            code_start_address_enable_register="RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE",
            code_start_address_enable_bit=2,
            data_private_memory=MemoryBlock(
                size=8 * 1024,
                address=DeviceAddress(
                    private_address=neo_base_address.private_address + 0x6000,
                    noc_address=neo_base_address.noc_address + 0x6000,
                ),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc3 = BabyRiscInfo(
            risc_name="trisc3",
            risc_id=3,
            noc_block=noc_block,
            neo_id=neo_id,
            l1=noc_block.l1,
            max_watchpoints=8,
            reset_flag_shift=14,
            branch_prediction_register="RISC_BRANCH_PREDICTION_CTRL",
            branch_prediction_mask=0b1000,
            default_code_start_address=risc_base_start_address + 0x00012000,
            code_start_address_register="RISCV_DEBUG_REG_TRISC3_RESET_PC",
            code_start_address_enable_register="RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE",
            code_start_address_enable_bit=3,
            data_private_memory=MemoryBlock(
                size=8 * 1024,
                address=DeviceAddress(
                    private_address=neo_base_address.private_address + 0x8000,
                    noc_address=neo_base_address.noc_address + 0x8000,
                ),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return [
            self.get_risc_debug(self.trisc0.risc_name),
            self.get_risc_debug(self.trisc1.risc_name),
            self.get_risc_debug(self.trisc2.risc_name),
            self.get_risc_debug(self.trisc3.risc_name),
        ]

    @cache
    def get_risc_debug(self, risc_name: str) -> RiscDebug:
        risc_name = risc_name.lower()
        if risc_name == self.trisc0.risc_name:
            return BabyRiscDebug(self.trisc0)
        elif risc_name == self.trisc1.risc_name:
            return BabyRiscDebug(self.trisc1)
        elif risc_name == self.trisc2.risc_name:
            return BabyRiscDebug(self.trisc2)
        elif risc_name == self.trisc3.risc_name:
            return BabyRiscDebug(self.trisc3)
        raise ValueError(f"RISC with name {risc_name} not found in NEO {self.neo_id}.")
