# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache
from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.hardware.wormhole.baby_risc_debug import WormholeBabyRiscDebug
from ttexalens.hardware.wormhole.niu_registers import get_niu_register_base_address_callable, niu_register_map
from ttexalens.hardware.wormhole.noc_block import WormholeNocBlock
from ttexalens.register_store import (
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


# TODO: Once signals are added, we can remove type hint
debug_bus_signal_map: dict[str, DebugBusSignalDescription] = {}

register_map = {
    "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=157, mask=0x1F),
    "TRISC_RESET_PC_SEC0_PC": ConfigurationRegisterDescription(index=158),
    "TRISC_RESET_PC_SEC1_PC": ConfigurationRegisterDescription(index=159),
    "TRISC_RESET_PC_SEC2_PC": ConfigurationRegisterDescription(index=160),
    "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=161, mask=0x7),
    "NCRISC_RESET_PC_PC": ConfigurationRegisterDescription(index=162),
    "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=163, mask=0x1),
    "RISCV_DEBUG_REG_DBG_BUS_CNTL_REG": DebugRegisterDescription(offset=0x54),
    "RISCV_DEBUG_REG_CFGREG_RD_CNTL": DebugRegisterDescription(offset=0x58),
    "RISCV_DEBUG_REG_DBG_RD_DATA": DebugRegisterDescription(offset=0x5C),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_EN": DebugRegisterDescription(offset=0x60),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD": DebugRegisterDescription(offset=0x64),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA": DebugRegisterDescription(offset=0x6C),
    "RISCV_DEBUG_REG_CFGREG_RDDATA": DebugRegisterDescription(offset=0x78),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": DebugRegisterDescription(offset=0x80),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": DebugRegisterDescription(offset=0x84),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": DebugRegisterDescription(offset=0x88),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": DebugRegisterDescription(offset=0x8C),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0": DebugRegisterDescription(offset=0xA0),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL1": DebugRegisterDescription(offset=0xA4),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS": DebugRegisterDescription(offset=0xA8),
    "RISCV_DEBUG_REG_SOFT_RESET_0": DebugRegisterDescription(offset=0x1B0),
}


def get_register_base_address_callable(noc_id: int) -> Callable[[RegisterDescription], DeviceAddress]:
    def get_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
        if isinstance(register_description, ConfigurationRegisterDescription):
            return DeviceAddress(private_address=0xFFEF0000)
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


class WormholeEthBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="eth", debug_bus=DebugBusSignalStore(debug_bus_signal_map, location))

        self.l1 = MemoryBlock(
            size=256 * 1024, address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000)
        )

        self.erisc = BabyRiscInfo(
            risc_name="erisc",
            risc_id=0,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Wormhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=11,
            branch_prediction_register="DISABLE_RISC_BP_Disable_main",  # TODO: Check if we have branch prediction register on erisc
            branch_prediction_mask=1,
            default_code_start_address=0,
            code_start_address_register="",
            code_start_address_enable_register="",
            code_start_address_enable_bit=0,
            data_private_memory=MemoryBlock(
                size=4 * 1024,  # TODO: Check if this is correct
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
            can_change_code_start_address=False,
        )

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)

    @cache
    def get_default_risc_debug(self) -> RiscDebug:
        return self.get_risc_debug(self.erisc.risc_name, self.erisc.neo_id)

    @cache
    def get_risc_debug(self, risc_name: str, neo_id: int | None = None) -> RiscDebug:
        assert neo_id is None, "NEO ID is not applicable for Wormhole device."
        risc_name = risc_name.lower()
        if risc_name == self.erisc.risc_name:
            return WormholeBabyRiscDebug(risc_info=self.erisc)
        raise ValueError(f"RISC debug for {risc_name} is not supported in Wormhole eth block.")
