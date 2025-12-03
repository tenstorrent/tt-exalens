# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.memory_regions import MemoryRegions
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.hardware.wormhole.baby_risc_debug import WormholeBabyRiscDebug
from ttexalens.hardware.wormhole.functional_worker_debug_bus_signals import debug_bus_signal_map, group_map
from ttexalens.hardware.wormhole.functional_worker_registers import register_map
from ttexalens.hardware.wormhole.niu_registers import get_niu_register_base_address_callable, niu_register_map
from ttexalens.hardware.wormhole.noc_block import WormholeNocBlock
from ttexalens.register_store import (
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    TensixGeneralPurposeRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


def get_register_base_address_callable(noc_id: int) -> Callable[[RegisterDescription], DeviceAddress]:
    def get_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
        if isinstance(register_description, ConfigurationRegisterDescription):
            return DeviceAddress(private_address=0xFFEF0000)
        elif isinstance(register_description, TensixGeneralPurposeRegisterDescription):
            return DeviceAddress(private_address=0xFFE00000)
        elif isinstance(register_description, DebugRegisterDescription):
            return DeviceAddress(private_address=0xFFB12000, noc_address=0xFFB12000)
        elif noc_id == 0:
            return get_niu_register_base_address_callable(
                DeviceAddress(private_address=0xFFB20000, noc_address=0xFFB20000)
            )(register_description)
        else:
            assert noc_id == 1
            return get_niu_register_base_address_callable(
                DeviceAddress(private_address=0xFFB30000, noc_address=0xFFB30000)
            )(register_description)

    return get_register_base_address


register_store_noc0_initialization = RegisterStore.create_initialization(
    [register_map, niu_register_map], get_register_base_address_callable(noc_id=0)
)
register_store_noc1_initialization = RegisterStore.create_initialization(
    [register_map, niu_register_map], get_register_base_address_callable(noc_id=1)
)
debug_bus_signals_initialization = DebugBusSignalStore.create_initialization(group_map, debug_bus_signal_map)

# Memory regions for Wormhole Functional Worker Block
# Note: RISC private memories don't have NOC addresses in Wormhole, only L1 is mapped
memory_regions = MemoryRegions(
    [
        MemoryBlock(
            address=DeviceAddress(noc_address=0x00000000, private_address=0x00000000),
            size=1464 * 1024,
            name="l1",
        ),
    ]
)


class WormholeFunctionalWorkerBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(
            location,
            block_type="functional_workers",
            debug_bus=DebugBusSignalStore(debug_bus_signals_initialization, self),
        )

        self.l1 = memory_regions.get_block("l1")

        self.brisc = BabyRiscInfo(
            risc_name="brisc",
            risc_id=0,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=11,
            branch_prediction_register="DISABLE_RISC_BP_Disable_main",
            branch_prediction_mask=1,
            default_code_start_address=0,
            code_start_address_register=None,  # We don't have a regsiter to override code start address
            data_private_memory=MemoryBlock(
                size=4 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc0 = BabyRiscInfo(
            risc_name="trisc0",
            risc_id=1,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=12,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b001,
            default_code_start_address=0x6000,
            code_start_address_register="TRISC_RESET_PC_SEC0_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b001,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc1 = BabyRiscInfo(
            risc_name="trisc1",
            risc_id=2,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=13,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b010,
            default_code_start_address=0xA000,
            code_start_address_register="TRISC_RESET_PC_SEC1_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b010,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc2 = BabyRiscInfo(
            risc_name="trisc2",
            risc_id=3,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=14,
            branch_prediction_register="DISABLE_RISC_BP_Disable_trisc",
            branch_prediction_mask=0b100,
            default_code_start_address=0xE000,
            code_start_address_register="TRISC_RESET_PC_SEC2_PC",
            code_start_address_enable_register="TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b100,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.ncrisc = BabyRiscInfo(
            risc_name="ncrisc",
            risc_id=4,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=18,
            branch_prediction_register="DISABLE_RISC_BP_Disable_ncrisc",
            branch_prediction_mask=0x1,
            default_code_start_address=0xFFC00000,
            code_start_address_register="NCRISC_RESET_PC_PC",
            code_start_address_enable_register="NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en",
            code_start_address_enable_bit=0b1,
            data_private_memory=MemoryBlock(
                size=4 * 1024,  # TODO: Check if this is correct
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=MemoryBlock(
                size=4 * 1024,  # TODO: Check if this is correct
                address=DeviceAddress(private_address=0xFFC00000),
            ),
            debug_hardware_present=False,
        )

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)

    def get_memory_regions(self) -> MemoryRegions | None:
        return memory_regions

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return [
            self.get_risc_debug(self.brisc.risc_name, self.brisc.neo_id),
            self.get_risc_debug(self.trisc0.risc_name, self.trisc0.neo_id),
            self.get_risc_debug(self.trisc1.risc_name, self.trisc1.neo_id),
            self.get_risc_debug(self.trisc2.risc_name, self.trisc2.neo_id),
            self.get_risc_debug(self.ncrisc.risc_name, self.ncrisc.neo_id),
        ]

    @cache
    def get_default_risc_debug(self) -> RiscDebug:
        return self.get_risc_debug(self.brisc.risc_name, self.brisc.neo_id)

    @cache
    def get_risc_debug(self, risc_name: str, neo_id: int | None = None) -> RiscDebug:
        assert neo_id is None, "NEO ID is not applicable for Wormhole device."
        risc_name = risc_name.lower()
        if risc_name == self.brisc.risc_name:
            return WormholeBabyRiscDebug(risc_info=self.brisc)
        elif risc_name == self.trisc0.risc_name:
            return WormholeBabyRiscDebug(risc_info=self.trisc0)
        elif risc_name == self.trisc1.risc_name:
            return WormholeBabyRiscDebug(risc_info=self.trisc1)
        elif risc_name == self.trisc2.risc_name:
            return WormholeBabyRiscDebug(risc_info=self.trisc2)
        elif risc_name == self.ncrisc.risc_name:
            return WormholeBabyRiscDebug(risc_info=self.ncrisc)
        raise ValueError(f"RISC debug for {risc_name} is not supported in Wormhole functional worker block.")
