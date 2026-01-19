# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.blackhole.baby_risc_debug import BlackholeBabyRiscDebug
from ttexalens.hardware.blackhole.niu_registers import get_niu_register_base_address_callable, niu_register_map
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.blackhole.noc_block import BlackholeNocBlock
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.memory_map import MemoryMapBlockInfo
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.register_store import (
    DebugRegisterDescription,
    RegisterDescription,
    RegisterStore,
    RiscControlRegisterDescription,
)


debug_bus_signal_map = {
    "drisc_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 9 + 1, mask=0x3FFFFFFF),
    "drisc_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x200),
    "drisc_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x40000000
    ),
    "drisc_id_ex_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x100),
    "drisc_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x80000000
    ),
    "drisc_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x80),
    "drisc_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x20),
    "drisc_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x1F),
    "drisc_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=19, mask=0xFFFFFFFF),
    "drisc_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x3FFFFFFF),
    "drisc_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x10000000),
    "drisc_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1F00000),
    "drisc_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x40000),
    "drisc_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x7C00),
    "drisc_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x100),
    "drisc_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1F),
    "drisc_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "drisc_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x7FFFFFFF),
    "drisc_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "drisc_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x40000000
    ),
    "drisc_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x3FFFFFFF),
    "drisc_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "drisc_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x40000000),
    "drisc_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x3FFFFFFF),
    "drisc_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "drisc_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x7FFFFFFF),
}

# Signal name mapping to (DaisySel, sig_sel)
group_map: dict[str, tuple[int, int]] = {
    "drisc_group_a": (7, 18),
    "drisc_group_b": (7, 19),
}

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
    "RISCV_DEBUG_REG_DBG_BUS_CNTL_REG": DebugRegisterDescription(offset=0x054),
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
            return DeviceAddress(private_address=0xFFB12000, noc_address=0x100FFB12000)
        elif isinstance(register_description, RiscControlRegisterDescription):
            return DeviceAddress(private_address=0xFFB14000, noc_address=0x100FFB14000)
        elif noc_id == 0:
            return get_niu_register_base_address_callable(
                DeviceAddress(private_address=0xFFB20000, noc_address=0x100FFB20000)
            )(register_description)
        else:
            assert noc_id == 1
            return get_niu_register_base_address_callable(
                DeviceAddress(private_address=0xFFB30000, noc_address=0x100FFB30000)
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
            size=4 * 1024 * 1024 * 1024,
            address=DeviceAddress(noc_address=0x00000000),
        )

        self.l1 = MemoryBlock(
            size=128 * 1024,
            address=DeviceAddress(private_address=0x00000000, noc_address=0x2000000000),
        )
        self.tx_stream0_regs = MemoryBlock(
            size=256,
            address=DeviceAddress(private_address=0xFC000000, noc_address=0x100FC000000),
        )
        self.tx_stream1_regs = MemoryBlock(
            size=256,
            address=DeviceAddress(private_address=0xFC000100, noc_address=0x100FC000100),
        )
        self.tx_control_regs = MemoryBlock(
            size=4 * 1024,
            address=DeviceAddress(private_address=0xFC001000, noc_address=0x100FC001000),
        )
        self.gddr_mc_regs = MemoryBlock(
            size=0x10000,
            address=DeviceAddress(private_address=0xFC100000, noc_address=0x100FC100000),
        )
        self.gddr_control_regs = MemoryBlock(
            size=0x100,
            address=DeviceAddress(private_address=0xFC200000, noc_address=0x100FC200000),
        )
        self.ictrl_regs = MemoryBlock(
            size=0x100,
            address=DeviceAddress(private_address=0xFC300000, noc_address=0x100FC300000),
        )
        self.gddr_xbar0_regs = MemoryBlock(
            size=0x1000,
            address=DeviceAddress(private_address=0xFC301000, noc_address=0x100FC301000),
        )
        self.gddr_xbar1_regs = MemoryBlock(
            size=0x1000,
            address=DeviceAddress(private_address=0xFC302000, noc_address=0x100FC302000),
        )
        self.gddr_xbar2_regs = MemoryBlock(
            size=0x1000,
            address=DeviceAddress(private_address=0xFC303000, noc_address=0x100FC303000),
        )
        self.gddr_phy_regs = MemoryBlock(
            size=0x20000,
            address=DeviceAddress(private_address=0xFC400000, noc_address=0x100FC400000),
        )
        self.debug_regs = MemoryBlock(
            size=0x1000,
            address=DeviceAddress(private_address=0xFFB12000, noc_address=0x100FFB12000),
        )
        self.pic_regs = MemoryBlock(
            size=0x1000,
            address=DeviceAddress(private_address=0xFFB13000, noc_address=0x100FFB13000),
        )
        self.control_regs = MemoryBlock(
            size=0x1000,
            address=DeviceAddress(private_address=0xFFB14000, noc_address=0x100FFB14000),
        )
        self.noc0_regs = MemoryBlock(
            size=0x10000,
            address=DeviceAddress(private_address=0xFFB20000, noc_address=0x100FFB20000),
        )
        self.noc1_regs = MemoryBlock(
            size=0x10000,
            address=DeviceAddress(private_address=0xFFB30000, noc_address=0x100FFB30000),
        )
        self.noc_overlay = MemoryBlock(
            size=0x10000,
            address=DeviceAddress(private_address=0xFFB40000, noc_address=0x100FFB40000),
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

        self.noc_memory_map.add_blocks(
            [
                MemoryMapBlockInfo("dram_bank", self.dram_bank, safe_to_write=True),
                MemoryMapBlockInfo("l1", self.l1.just_noc_address(), safe_to_write=True),
                MemoryMapBlockInfo("tx_stream0_regs", self.tx_stream0_regs.just_noc_address()),
                MemoryMapBlockInfo("tx_stream1_regs", self.tx_stream1_regs.just_noc_address()),
                MemoryMapBlockInfo("tx_control_regs", self.tx_control_regs.just_noc_address()),
                MemoryMapBlockInfo("gddr_mc_regs", self.gddr_mc_regs.just_noc_address()),
                MemoryMapBlockInfo(
                    "gddr_control_regs",
                    self.gddr_control_regs.just_noc_address(),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo("ictrl_regs", self.ictrl_regs.just_noc_address()),
                MemoryMapBlockInfo("gddr_xbar0_regs", self.gddr_xbar0_regs.just_noc_address()),
                MemoryMapBlockInfo("gddr_xbar1_regs", self.gddr_xbar1_regs.just_noc_address()),
                MemoryMapBlockInfo("gddr_xbar2_regs", self.gddr_xbar2_regs.just_noc_address()),
                MemoryMapBlockInfo("gddr_phy_regs", self.gddr_phy_regs.just_noc_address()),
                MemoryMapBlockInfo("debug_regs", self.debug_regs.just_noc_address()),
                MemoryMapBlockInfo("pic_regs", self.pic_regs.just_noc_address()),
                MemoryMapBlockInfo("control_regs", self.control_regs.just_noc_address()),
                MemoryMapBlockInfo("noc0_regs", self.noc0_regs.just_noc_address()),
                MemoryMapBlockInfo("noc1_regs", self.noc1_regs.just_noc_address()),
                MemoryMapBlockInfo("noc_overlay", self.noc_overlay.just_noc_address()),
            ]
        )

        self.drisc.memory_map.add_blocks(
            [
                MemoryMapBlockInfo("l1", self.l1, safe_to_write=True),
                MemoryMapBlockInfo("tx_stream0_regs", self.tx_stream0_regs),
                MemoryMapBlockInfo("tx_stream1_regs", self.tx_stream1_regs),
                MemoryMapBlockInfo("tx_control_regs", self.tx_control_regs),
                MemoryMapBlockInfo("gddr_mc_regs", self.gddr_mc_regs),
                MemoryMapBlockInfo("gddr_control_regs", self.gddr_control_regs),
                MemoryMapBlockInfo("ictrl_regs", self.ictrl_regs),
                MemoryMapBlockInfo("gddr_xbar0_regs", self.gddr_xbar0_regs),
                MemoryMapBlockInfo("gddr_xbar1_regs", self.gddr_xbar1_regs),
                MemoryMapBlockInfo("gddr_xbar2_regs", self.gddr_xbar2_regs),
                MemoryMapBlockInfo("gddr_phy_regs", self.gddr_phy_regs),
                MemoryMapBlockInfo("debug_regs", self.debug_regs),
                MemoryMapBlockInfo("pic_regs", self.pic_regs),
                MemoryMapBlockInfo("control_regs", self.control_regs),
                MemoryMapBlockInfo("noc0_regs", self.noc0_regs),
                MemoryMapBlockInfo("noc1_regs", self.noc1_regs),
                MemoryMapBlockInfo("noc_overlay", self.noc_overlay),
            ]
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
            return BlackholeBabyRiscDebug(risc_info=self.drisc)
        raise ValueError(f"RISC debug for {risc_name} is not supported in Blackhole eth block.")
