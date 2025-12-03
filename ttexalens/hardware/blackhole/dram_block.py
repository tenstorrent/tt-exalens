# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.blackhole.niu_registers import get_niu_register_base_address_callable, niu_register_map
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.blackhole.noc_block import BlackholeNocBlock
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.noc_memory_map import NocMemoryMap
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.register_store import (
    DebugRegisterDescription,
    RegisterDescription,
    RegisterStore,
    RiscControlRegisterDescription,
)


# TODO #432: Once signals are added, we can remove type hint
debug_bus_signal_map: dict[str, DebugBusSignalDescription] = {}

# TODO(#651) Once signals are grouped, we can remove type hint
group_map: dict[str, tuple[int, int]] = {}


register_map: dict[str, RegisterDescription] = {
    "RISCV_DEBUG_REG_PERF_CNT_INSTRN_THREAD0": DebugRegisterDescription(offset=0x00),
    "RISCV_DEBUG_REG_PERF_CNT_INSTRN_THREAD1": DebugRegisterDescription(offset=0x004),
    "RISCV_DEBUG_REG_PERF_CNT_INSTRN_THREAD2": DebugRegisterDescription(offset=0x008),
    "RISCV_DEBUG_REG_PERF_CNT_TDMA0": DebugRegisterDescription(offset=0x00C),
    "RISCV_DEBUG_REG_PERF_CNT_TDMA1": DebugRegisterDescription(offset=0x010),
    "RISCV_DEBUG_REG_PERF_CNT_TDMA2": DebugRegisterDescription(offset=0x014),
    "RISCV_DEBUG_REG_PERF_CNT_FPU0": DebugRegisterDescription(offset=0x018),
    "RISCV_DEBUG_REG_PERF_CNT_FPU1": DebugRegisterDescription(offset=0x01C),
    "RISCV_DEBUG_REG_PERF_CNT_FPU2": DebugRegisterDescription(offset=0x020),
    "RISCV_DEBUG_REG_PERF_CNT_L1_0": DebugRegisterDescription(offset=0x030),
    "RISCV_DEBUG_REG_PERF_CNT_L1_1": DebugRegisterDescription(offset=0x034),
    "RISCV_DEBUG_REG_PERF_CNT_L1_2": DebugRegisterDescription(offset=0x038),
    "RISCV_DEBUG_REG_PERF_CNT_ALL": DebugRegisterDescription(offset=0x03C),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG0": DebugRegisterDescription(offset=0x048),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG1": DebugRegisterDescription(offset=0x04C),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG2": DebugRegisterDescription(offset=0x050),
    "RISCV_DEBUG_REG_DBG_BUS_CTRL": DebugRegisterDescription(offset=0x054),
    "RISCV_DEBUG_REG_CFGREG_RD_CNTL": DebugRegisterDescription(offset=0x58),  # Old name
    "RISCV_DEBUG_REG_TENSIX_CREG_READ": DebugRegisterDescription(offset=0x058),  # New name
    "RISCV_DEBUG_REG_DBG_RD_DATA": DebugRegisterDescription(offset=0x05C),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_EN": DebugRegisterDescription(offset=0x060),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD": DebugRegisterDescription(offset=0x064),
    "RISCV_DEBUG_REG_DBG_FEATURE_DISABLE": DebugRegisterDescription(offset=0x068),
    "RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA": DebugRegisterDescription(offset=0x06C),
    "RISCV_DEBUG_REG_CG_CTRL_HYST0": DebugRegisterDescription(offset=0x070),
    "RISCV_DEBUG_REG_CG_CTRL_HYST1": DebugRegisterDescription(offset=0x074),
    "RISCV_DEBUG_REG_CFGREG_RDDATA": DebugRegisterDescription(offset=0x78),  # Old name
    "RISCV_DEBUG_REG_TENSIX_CREG_RDDATA": DebugRegisterDescription(offset=0x078),  # New name
    "RISCV_DEBUG_REG_CG_CTRL_HYST2": DebugRegisterDescription(offset=0x07C),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": DebugRegisterDescription(offset=0x080),
    "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": DebugRegisterDescription(offset=0x084),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": DebugRegisterDescription(offset=0x088),
    "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": DebugRegisterDescription(offset=0x08C),
    "RISCV_DEBUG_REG_TRISC_PC_BUF_OVERRIDE": DebugRegisterDescription(offset=0x090),
    "RISCV_DEBUG_REG_DBG_INVALID_INSTRN": DebugRegisterDescription(offset=0x094),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0": DebugRegisterDescription(offset=0x0A0),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL1": DebugRegisterDescription(offset=0x0A4),
    "RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS": DebugRegisterDescription(offset=0x0A8),
    "RISCV_DEBUG_REG_STOCH_RND_MASK0": DebugRegisterDescription(offset=0x0AC),
    "RISCV_DEBUG_REG_STOCH_RND_MASK1": DebugRegisterDescription(offset=0x0B0),
    "RISCV_DEBUG_REG_FPU_STICKY_BITS": DebugRegisterDescription(offset=0x0B4),
    "RISCV_DEBUG_REG_ETH_RISC_PREFECTH_CTRL": DebugRegisterDescription(offset=0x0B8),
    "RISCV_DEBUG_REG_ETH_RISC_PREFECTH_PC": DebugRegisterDescription(offset=0x0BC),
    "RISCV_DEBUG_REG_SOFT_RESET_0": DebugRegisterDescription(offset=0x1B0),
    "RISCV_DEBUG_REG_ECC_CTRL": DebugRegisterDescription(offset=0x1D0),
    "RISCV_DEBUG_REG_ECC_STATUS": DebugRegisterDescription(offset=0x1D4),
    "RISCV_DEBUG_REG_WATCHDOG_TIMER": DebugRegisterDescription(offset=0x1E0),
    "RISCV_DEBUG_REG_WDT_CNTL": DebugRegisterDescription(offset=0x1E4),
    "RISCV_DEBUG_REG_WDT_STATUS": DebugRegisterDescription(offset=0x1E8),
    "RISCV_DEBUG_REG_WALL_CLOCK_0": DebugRegisterDescription(offset=0x1F0),
    "RISCV_DEBUG_REG_WALL_CLOCK_1": DebugRegisterDescription(offset=0x1F4),
    "RISCV_DEBUG_REG_WALL_CLOCK_1_AT": DebugRegisterDescription(offset=0x1F8),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_CMD": DebugRegisterDescription(offset=0x1FC),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_CNTL": DebugRegisterDescription(offset=0x200),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_STATUS": DebugRegisterDescription(offset=0x204),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_BUF0_START_ADDR": DebugRegisterDescription(offset=0x208),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_BUF0_END_ADDR": DebugRegisterDescription(offset=0x20C),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_BUF1_START_ADDR": DebugRegisterDescription(offset=0x210),
    "RISCV_DEBUG_REG_TIMESTAMP_DUMP_BUF1_END_ADDR": DebugRegisterDescription(offset=0x214),
    "RISCV_DEBUG_REG_PERF_CNT_MUX_CTRL": DebugRegisterDescription(offset=0x218),
    "RISCV_DEBUG_REG_DBG_L1_READBACK_OFFSET": DebugRegisterDescription(offset=0x21C),
    "RISC_CTRL_REG_RESET_PC_0": RiscControlRegisterDescription(offset=0x000),
    "RISC_CTRL_REG_END_PC_0": RiscControlRegisterDescription(offset=0x004),
    "RISC_CTRL_REG_SCRATCH[0]": RiscControlRegisterDescription(offset=0x010),
    "RISC_CTRL_REG_SCRATCH[1]": RiscControlRegisterDescription(offset=0x014),
    "RISC_CTRL_REG_SCRATCH[2]": RiscControlRegisterDescription(offset=0x018),
    "RISC_CTRL_REG_SCRATCH[3]": RiscControlRegisterDescription(offset=0x01C),
    "RISC_CTRL_REG_CLK_GATING": RiscControlRegisterDescription(offset=0x020),
    "RISC_CTRL_REG_ECC_SCRUBBER": RiscControlRegisterDescription(offset=0x024),
    "RISC_CTRL_REG_INTERRUPT_MODE[0]": RiscControlRegisterDescription(offset=0x040),
    "RISC_CTRL_REG_INTERRUPT_MODE[1]": RiscControlRegisterDescription(offset=0x044),
    "RISC_CTRL_REG_INTERRUPT_MODE[2]": RiscControlRegisterDescription(offset=0x048),
    "RISC_CTRL_REG_INTERRUPT_MODE[3]": RiscControlRegisterDescription(offset=0x04C),
    "RISC_CTRL_REG_INTERRUPT_MODE[4]": RiscControlRegisterDescription(offset=0x050),
    "RISC_CTRL_REG_INTERRUPT_MODE[5]": RiscControlRegisterDescription(offset=0x054),
    "RISC_CTRL_REG_INTERRUPT_MODE[6]": RiscControlRegisterDescription(offset=0x058),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[0]": RiscControlRegisterDescription(offset=0x060),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[1]": RiscControlRegisterDescription(offset=0x064),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[2]": RiscControlRegisterDescription(offset=0x068),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[3]": RiscControlRegisterDescription(offset=0x06C),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[4]": RiscControlRegisterDescription(offset=0x070),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[5]": RiscControlRegisterDescription(offset=0x074),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[6]": RiscControlRegisterDescription(offset=0x078),
}


def get_register_base_address_callable(noc_id: int) -> Callable[[RegisterDescription], DeviceAddress]:
    def get_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
        if isinstance(register_description, DebugRegisterDescription):
            return DeviceAddress(private_address=0xFFB12000, noc_address=0xFFB12000)
        elif isinstance(register_description, RiscControlRegisterDescription):
            return DeviceAddress(private_address=0xFFB14000, noc_address=0xFFB14000)
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


class BlackholeDramBlock(BlackholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(
            location,
            block_type="dram",
            debug_bus=DebugBusSignalStore(debug_bus_signals_initialization, self),
        )

        self.dram_bank = MemoryBlock(
            # TODO #432: Check if this size is correct
            size=2 * 1024 * 1024 * 1024 - 4 * 1024,
            address=DeviceAddress(private_address=0x00001000, noc_address=0x00001000),
        )

        self.l1 = MemoryBlock(
            size=4 * 1024,  # TODO #432: Check if this size is correct
            address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000),
        )

        self.drisc = BabyRiscInfo(
            risc_name="drisc",
            risc_id=0,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Blackhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=11,
            branch_prediction_register=None,  # We don't have a branch prediction register on DRAM block
            default_code_start_address=None,  # Since we don't have a register to disable code start address override in DRAM block, we cannot have a default code start address
            code_start_address_register="RISC_CTRL_REG_RESET_PC_0",
            code_start_address_enable_register=None,  # We don't have a register to enable code start address override in DRAM block
            data_private_memory=MemoryBlock(
                size=8 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)

        # Create NOC memory map
        self.noc_memory_map = NocMemoryMap(
            {
                "l1": {"noc_address": 0x00000000, "size": 4 * 1024},
                "dram_bank": {"noc_address": 0x00001000, "size": 2 * 1024 * 1024 * 1024 - 4 * 1024},
            }
        )

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return [
            self.get_risc_debug(self.drisc.risc_name, self.drisc.neo_id),
        ]

    @cache
    def get_default_risc_debug(self) -> RiscDebug:
        return self.get_risc_debug(self.drisc.risc_name, self.drisc.neo_id)

    @cache
    def get_risc_debug(self, risc_name: str, neo_id: int | None = None) -> RiscDebug:
        assert neo_id is None, "NEO ID is not applicable for Blackhole device."
        risc_name = risc_name.lower()
        if risc_name == self.drisc.risc_name:
            return BabyRiscDebug(
                risc_info=self.drisc
            )  # TODO: Once we have debug bus signals, we will create WormholeBabyRiscDebug instance
        raise ValueError(f"RISC debug for {risc_name} is not supported in Blackhole eth block.")
