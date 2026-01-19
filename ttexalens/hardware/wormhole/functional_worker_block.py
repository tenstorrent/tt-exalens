# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.memory_map import MemoryMapBlockInfo
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


class WormholeFunctionalWorkerBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(
            location,
            block_type="functional_workers",
            debug_bus=DebugBusSignalStore(debug_bus_signals_initialization, self),
        )

        self.l1 = MemoryBlock(
            size=1464 * 1024, address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000)
        )
        self.tdma_regs = MemoryBlock(
            size=0x1000, address=DeviceAddress(private_address=0xFFB11000, noc_address=0xFFB11000)
        )
        self.debug_regs = MemoryBlock(
            size=0x1000, address=DeviceAddress(private_address=0xFFB12000, noc_address=0xFFB12000)
        )
        self.pic_regs = MemoryBlock(
            size=0x1000, address=DeviceAddress(private_address=0xFFB13000, noc_address=0xFFB13000)
        )
        self.noc0_regs = MemoryBlock(
            size=0x10000, address=DeviceAddress(private_address=0xFFB20000, noc_address=0xFFB20000)
        )
        self.noc1_regs = MemoryBlock(
            size=0x10000, address=DeviceAddress(private_address=0xFFB30000, noc_address=0xFFB30000)
        )
        self.noc_overlay = MemoryBlock(
            size=0x40000, address=DeviceAddress(private_address=0xFFB40000, noc_address=0xFFB40000)
        )

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
                size=4 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=MemoryBlock(
                size=16 * 1024,
                address=DeviceAddress(private_address=0xFFC00000),
            ),
            debug_hardware_present=False,
        )

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)

        self._update_memory_maps()

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

    def _update_memory_maps(self):
        # Reading some TDMA registers on Wormhole can brick the device and or host, so we disallow those reads.
        forbidden_tdma_addresses = (
            0xFFB11030,
            0xFFB11070,
            0xFFB110B0,
            0xFFB110F0,
            0xFFB11130,
            0xFFB11170,
            0xFFB111B0,
            0xFFB111F0,
            0xFFB11230,
            0xFFB11270,
            0xFFB112B0,
            0xFFB112F0,
            0xFFB11330,
            0xFFB11370,
            0xFFB113B0,
            0xFFB113F0,
            0xFFB11430,
            0xFFB11470,
            0xFFB114B0,
            0xFFB114F0,
            0xFFB11530,
            0xFFB11570,
            0xFFB115B0,
            0xFFB115F0,
            0xFFB11630,
            0xFFB11670,
            0xFFB116B0,
            0xFFB116F0,
            0xFFB11730,
            0xFFB11770,
            0xFFB117B0,
            0xFFB117F0,
            0xFFB11830,
            0xFFB11870,
            0xFFB118B0,
            0xFFB118F0,
            0xFFB11930,
            0xFFB11970,
            0xFFB119B0,
            0xFFB119F0,
            0xFFB11A30,
            0xFFB11A70,
            0xFFB11AB0,
            0xFFB11AF0,
            0xFFB11B30,
            0xFFB11B70,
            0xFFB11BB0,
            0xFFB11BF0,
            0xFFB11C30,
            0xFFB11C70,
            0xFFB11CB0,
            0xFFB11CF0,
            0xFFB11D30,
            0xFFB11D70,
            0xFFB11DB0,
            0xFFB11DF0,
            0xFFB11E30,
            0xFFB11E70,
            0xFFB11EB0,
            0xFFB11EF0,
            0xFFB11F30,
            0xFFB11F70,
            0xFFB11FB0,
            0xFFB11FF0,
        )

        def tdma_read_check(address: int, num_bytes: int) -> bool:
            read_end = address + num_bytes - 1
            return not any(
                address <= forbidden_addr + 3 and forbidden_addr <= read_end
                for forbidden_addr in forbidden_tdma_addresses
            )

        self.noc_memory_map.add_blocks(
            [
                MemoryMapBlockInfo("l1", self.l1, safe_to_write=True),
                MemoryMapBlockInfo("tdma_regs", self.tdma_regs, safe_to_read=tdma_read_check),
                MemoryMapBlockInfo("debug_regs", self.debug_regs),
                MemoryMapBlockInfo("pic_regs", self.pic_regs),
                MemoryMapBlockInfo("noc0_regs", self.noc0_regs),
                MemoryMapBlockInfo("noc1_regs", self.noc1_regs),
                MemoryMapBlockInfo("noc_overlay", self.noc_overlay),
            ]
        )

        self.brisc.memory_map.add_blocks(
            [
                MemoryMapBlockInfo("l1", self.l1, safe_to_write=True),
                MemoryMapBlockInfo("data_private_memory", self.brisc.data_private_memory, safe_to_write=True),  # type: ignore[arg-type]
                MemoryMapBlockInfo("tdma_regs", self.tdma_regs, safe_to_read=tdma_read_check),
                MemoryMapBlockInfo("debug_regs", self.debug_regs),
                MemoryMapBlockInfo("pic_regs", self.pic_regs),
                MemoryMapBlockInfo("noc0_regs", self.noc0_regs),
                MemoryMapBlockInfo("noc1_regs", self.noc1_regs),
                MemoryMapBlockInfo("noc_overlay", self.noc_overlay),
                MemoryMapBlockInfo(
                    "t0_gprs",
                    MemoryBlock(size=0x100, address=DeviceAddress(private_address=0xFFE00000)),
                ),
                MemoryMapBlockInfo(
                    "t1_gprs",
                    MemoryBlock(size=0x100, address=DeviceAddress(private_address=0xFFE00100)),
                ),
                MemoryMapBlockInfo(
                    "t2_gprs",
                    MemoryBlock(size=0x100, address=DeviceAddress(private_address=0xFFE00200)),
                ),
                MemoryMapBlockInfo(
                    "t0_instruction_buffer",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFE40000)),
                ),
                MemoryMapBlockInfo(
                    "t1_instruction_buffer",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFE50000)),
                ),
                MemoryMapBlockInfo(
                    "t2_instruction_buffer",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFE60000)),
                ),
                MemoryMapBlockInfo(
                    "pcbuf0",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFE80000)),
                ),
                MemoryMapBlockInfo(
                    "pcbuf1",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFE90000)),
                ),
                MemoryMapBlockInfo(
                    "pcbuf2",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFEA0000)),
                ),
                MemoryMapBlockInfo(
                    "mailboxes0",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC0000)),
                ),  # brisc
                MemoryMapBlockInfo(
                    "mailboxes1",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC1000)),
                ),  # trisc0
                MemoryMapBlockInfo(
                    "mailboxes2",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC2000)),
                ),  # trisc1
                MemoryMapBlockInfo(
                    "mailboxes3",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC3000)),
                ),  # trisc2
                MemoryMapBlockInfo(
                    "config_regs",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFEF0000)),
                ),
            ]
        )

        self.trisc0.memory_map.add_blocks(
            [
                MemoryMapBlockInfo("l1", self.l1, safe_to_write=True),
                MemoryMapBlockInfo("data_private_memory", self.trisc0.data_private_memory, safe_to_write=True),  # type: ignore[arg-type]
                MemoryMapBlockInfo("tdma_regs", self.tdma_regs, safe_to_read=tdma_read_check),
                MemoryMapBlockInfo("debug_regs", self.debug_regs),
                MemoryMapBlockInfo("pic_regs", self.pic_regs),
                MemoryMapBlockInfo("noc0_regs", self.noc0_regs),
                MemoryMapBlockInfo("noc1_regs", self.noc1_regs),
                MemoryMapBlockInfo("noc_overlay", self.noc_overlay),
                MemoryMapBlockInfo(
                    "mop_config",
                    MemoryBlock(size=0x24, address=DeviceAddress(private_address=0xFFB14000)),
                ),  # T0 MOP extender configuration
                MemoryMapBlockInfo(
                    "t0_gprs",
                    MemoryBlock(size=0x100, address=DeviceAddress(private_address=0xFFE00000)),
                ),
                MemoryMapBlockInfo(
                    "t0_instruction_buffer",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFE40000)),
                ),
                MemoryMapBlockInfo(
                    "pcbuf",
                    MemoryBlock(size=0x4, address=DeviceAddress(private_address=0xFFE80000)),
                ),
                MemoryMapBlockInfo(
                    "ttsync",
                    MemoryBlock(size=0x1C, address=DeviceAddress(private_address=0xFFE80004)),
                ),
                MemoryMapBlockInfo(
                    "semaphores",
                    MemoryBlock(size=0xFFD0, address=DeviceAddress(private_address=0xFFE80020)),
                ),
                MemoryMapBlockInfo(
                    "mailboxes0",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC0000)),
                ),  # brisc
                MemoryMapBlockInfo(
                    "mailboxes1",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC1000)),
                ),  # trisc0
                MemoryMapBlockInfo(
                    "mailboxes2",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC2000)),
                ),  # trisc1
                MemoryMapBlockInfo(
                    "mailboxes3",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC3000)),
                ),  # trisc2
                MemoryMapBlockInfo(
                    "config_regs",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFEF0000)),
                ),
            ]
        )

        self.trisc1.memory_map.add_blocks(
            [
                MemoryMapBlockInfo("l1", self.l1, safe_to_write=True),
                MemoryMapBlockInfo("data_private_memory", self.trisc1.data_private_memory, safe_to_write=True),  # type: ignore[arg-type]
                MemoryMapBlockInfo("tdma_regs", self.tdma_regs, safe_to_read=tdma_read_check),
                MemoryMapBlockInfo("debug_regs", self.debug_regs),
                MemoryMapBlockInfo("pic_regs", self.pic_regs),
                MemoryMapBlockInfo("noc0_regs", self.noc0_regs),
                MemoryMapBlockInfo("noc1_regs", self.noc1_regs),
                MemoryMapBlockInfo("noc_overlay", self.noc_overlay),
                MemoryMapBlockInfo(
                    "mop_config",
                    MemoryBlock(size=0x24, address=DeviceAddress(private_address=0xFFB14000)),
                ),  # T1 MOP extender configuration
                MemoryMapBlockInfo(
                    "t1_gprs",
                    MemoryBlock(size=0x100, address=DeviceAddress(private_address=0xFFE00000)),
                ),
                MemoryMapBlockInfo(
                    "t1_instruction_buffer",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFE40000)),
                ),
                MemoryMapBlockInfo(
                    "pcbuf",
                    MemoryBlock(size=0x4, address=DeviceAddress(private_address=0xFFE80000)),
                ),
                MemoryMapBlockInfo(
                    "ttsync",
                    MemoryBlock(size=0x1C, address=DeviceAddress(private_address=0xFFE80004)),
                ),
                MemoryMapBlockInfo(
                    "semaphores",
                    MemoryBlock(size=0xFFD0, address=DeviceAddress(private_address=0xFFE80020)),
                ),
                MemoryMapBlockInfo(
                    "mailboxes0",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC0000)),
                ),  # brisc
                MemoryMapBlockInfo(
                    "mailboxes1",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC1000)),
                ),  # trisc0
                MemoryMapBlockInfo(
                    "mailboxes2",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC2000)),
                ),  # trisc1
                MemoryMapBlockInfo(
                    "mailboxes3",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC3000)),
                ),  # trisc2
                MemoryMapBlockInfo(
                    "config_regs",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFEF0000)),
                ),
            ]
        )

        self.trisc2.memory_map.add_blocks(
            [
                MemoryMapBlockInfo("l1", self.l1, safe_to_write=True),
                MemoryMapBlockInfo("data_private_memory", self.trisc2.data_private_memory, safe_to_write=True),  # type: ignore[arg-type]
                MemoryMapBlockInfo("tdma_regs", self.tdma_regs, safe_to_read=tdma_read_check),
                MemoryMapBlockInfo("debug_regs", self.debug_regs),
                MemoryMapBlockInfo("pic_regs", self.pic_regs),
                MemoryMapBlockInfo("noc0_regs", self.noc0_regs),
                MemoryMapBlockInfo("noc1_regs", self.noc1_regs),
                MemoryMapBlockInfo("noc_overlay", self.noc_overlay),
                MemoryMapBlockInfo(
                    "mop_config",
                    MemoryBlock(size=0x24, address=DeviceAddress(private_address=0xFFB14000)),
                ),  # T1 MOP extender configuration
                MemoryMapBlockInfo(
                    "t2_gprs",
                    MemoryBlock(size=0x100, address=DeviceAddress(private_address=0xFFE00000)),
                ),
                MemoryMapBlockInfo(
                    "t2_instruction_buffer",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFE40000)),
                ),
                MemoryMapBlockInfo(
                    "pcbuf",
                    MemoryBlock(size=0x4, address=DeviceAddress(private_address=0xFFE80000)),
                ),
                MemoryMapBlockInfo(
                    "ttsync",
                    MemoryBlock(size=0x1C, address=DeviceAddress(private_address=0xFFE80004)),
                ),
                MemoryMapBlockInfo(
                    "semaphores",
                    MemoryBlock(size=0xFFD0, address=DeviceAddress(private_address=0xFFE80020)),
                ),
                MemoryMapBlockInfo(
                    "mailboxes0",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC0000)),
                ),  # brisc
                MemoryMapBlockInfo(
                    "mailboxes1",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC1000)),
                ),  # trisc0
                MemoryMapBlockInfo(
                    "mailboxes2",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC2000)),
                ),  # trisc1
                MemoryMapBlockInfo(
                    "mailboxes3",
                    MemoryBlock(size=0x1000, address=DeviceAddress(private_address=0xFFEC3000)),
                ),  # trisc2
                MemoryMapBlockInfo(
                    "config_regs",
                    MemoryBlock(size=0x10000, address=DeviceAddress(private_address=0xFFEF0000)),
                ),
            ]
        )

        self.ncrisc.memory_map.add_blocks(
            [
                MemoryMapBlockInfo("l1", self.l1, safe_to_write=True),
                MemoryMapBlockInfo("data_private_memory", self.ncrisc.data_private_memory, safe_to_write=True),  # type: ignore[arg-type]
                MemoryMapBlockInfo("tdma_regs", self.tdma_regs, safe_to_read=tdma_read_check),
                MemoryMapBlockInfo("debug_regs", self.debug_regs),
                MemoryMapBlockInfo("pic_regs", self.pic_regs),
                MemoryMapBlockInfo("noc0_regs", self.noc0_regs),
                MemoryMapBlockInfo("noc1_regs", self.noc1_regs),
                MemoryMapBlockInfo("noc_overlay", self.noc_overlay),
                MemoryMapBlockInfo("code_private_memory", self.ncrisc.code_private_memory),  # type: ignore[arg-type]
            ]
        )
