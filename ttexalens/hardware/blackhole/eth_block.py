# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.blackhole.baby_risc_debug import BlackholeBabyRiscDebug
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.blackhole.niu_registers import get_niu_register_base_address_callable, niu_register_map
from ttexalens.hardware.blackhole.noc_block import BlackholeNocBlock
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.register_store import (
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    RiscControlRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


debug_bus_signal_map = {
    "erisc0_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 9 + 1, mask=0x3FFFFFFF),
    "erisc1_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 10 + 1, mask=0x3FFFFFFF),
    "erisc0_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x200),
    "erisc0_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x40000000
    ),
    "erisc0_id_ex_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x100),
    "erisc0_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x80000000
    ),
    "erisc0_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x80),
    "erisc0_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x20),
    "erisc0_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x1F),
    "erisc0_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=19, mask=0xFFFFFFFF),
    "erisc0_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x3FFFFFFF),
    "erisc0_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x10000000),
    "erisc0_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1F00000),
    "erisc0_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x40000),
    "erisc0_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x7C00),
    "erisc0_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x100),
    "erisc0_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1F),
    "erisc0_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "erisc0_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x7FFFFFFF),
    "erisc0_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "erisc0_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x40000000
    ),
    "erisc0_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x3FFFFFFF),
    "erisc0_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "erisc0_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x40000000),
    "erisc0_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x3FFFFFFF),
    "erisc0_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "erisc0_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x7FFFFFFF),
    "erisc1_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x200),
    "erisc1_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=21, mask=0x40000000
    ),
    "erisc1_id_ex_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x100),
    "erisc1_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=21, mask=0x80000000
    ),
    "erisc1_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x80),
    "erisc1_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x20),
    "erisc1_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x1F),
    "erisc1_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=21, mask=0xFFFFFFFF),
    "erisc1_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=21, mask=0x3FFFFFFF),
    "erisc1_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x10000000),
    "erisc1_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x1F00000),
    "erisc1_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x40000),
    "erisc1_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x7C00),
    "erisc1_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x100),
    "erisc1_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x1F),
    "erisc1_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x80000000),
    "erisc1_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x7FFFFFFF),
    "erisc1_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=20, mask=0x80000000),
    "erisc1_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=20, mask=0x40000000
    ),
    "erisc1_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=20, mask=0x3FFFFFFF),
    "erisc1_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=20, mask=0x80000000),
    "erisc1_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=20, mask=0x40000000),
    "erisc1_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=20, mask=0x3FFFFFFF),
    "erisc1_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x80000000),
    "erisc1_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x7FFFFFFF),
}

# Signal name mapping to (DaisySel, sig_sel)
group_map: dict[str, tuple[int, int]] = {
    "erisc0_group_a": (7, 18),
    "erisc0_group_b": (7, 19),
    "erisc1_group_a": (7, 20),
    "erisc1_group_b": (7, 21),
}

register_map = {
    "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=185, mask=0x1F),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG0": DebugRegisterDescription(offset=0x048),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG1": DebugRegisterDescription(offset=0x04C),
    "RISCV_DEBUG_REG_DBG_L1_MEM_REG2": DebugRegisterDescription(offset=0x050),
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
    "RISC_CTRL_REG_RESET_PC_0": RiscControlRegisterDescription(offset=0x000),
    "RISC_CTRL_REG_END_PC_0": RiscControlRegisterDescription(offset=0x004),
    "RISC_CTRL_REG_RESET_PC_1": RiscControlRegisterDescription(offset=0x008),
    "RISC_CTRL_REG_END_PC_1": RiscControlRegisterDescription(offset=0x00C),
    "RISC_CTRL_REG_INTERRUPT_MODE[0]": RiscControlRegisterDescription(offset=0x020),
    "RISC_CTRL_REG_INTERRUPT_MODE[1]": RiscControlRegisterDescription(offset=0x024),
    "RISC_CTRL_REG_INTERRUPT_MODE[2]": RiscControlRegisterDescription(offset=0x028),
    "RISC_CTRL_REG_INTERRUPT_MODE[3]": RiscControlRegisterDescription(offset=0x02C),
    "RISC_CTRL_REG_INTERRUPT_MODE[4]": RiscControlRegisterDescription(offset=0x030),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[0]": RiscControlRegisterDescription(offset=0x040),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[1]": RiscControlRegisterDescription(offset=0x044),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[2]": RiscControlRegisterDescription(offset=0x048),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[3]": RiscControlRegisterDescription(offset=0x04C),
    "RISC_CTRL_REG_INTERRUPT_VECTOR[4]": RiscControlRegisterDescription(offset=0x050),
    "RISC_CTRL_REG_INTERRUPT_ROUTE": RiscControlRegisterDescription(offset=0x060),
}


def get_register_base_address_callable(noc_id: int) -> Callable[[RegisterDescription], DeviceAddress]:
    def get_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
        if isinstance(register_description, ConfigurationRegisterDescription):
            return DeviceAddress(private_address=0xFFEF0000)
        elif isinstance(register_description, DebugRegisterDescription):
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


class BlackholeEthBlock(BlackholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(
            location,
            block_type="eth",
            debug_bus=DebugBusSignalStore(debug_bus_signals_initialization, self),
        )

        self.l1 = MemoryBlock(
            size=512 * 1024,
            address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000),
        )

        self.erisc0 = BabyRiscInfo(
            risc_name="erisc0",
            risc_id=0,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Blackhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=11,
            branch_prediction_register=None,  # We don't have a branch prediction register on erisc0
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

        self.erisc1 = BabyRiscInfo(
            risc_name="erisc1",
            risc_id=1,
            noc_block=self,
            neo_id=None,  # NEO ID is not applicable for Blackhole
            l1=self.l1,
            max_watchpoints=8,
            reset_flag_shift=12,
            branch_prediction_register=None,  # We don't have a branch prediction register on erisc1
            default_code_start_address=None,  # Since we don't have a register to disable code start address override in DRAM block, we cannot have a default code start address
            code_start_address_register="RISC_CTRL_REG_RESET_PC_1",
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

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return [
            self.get_risc_debug(self.erisc0.risc_name, self.erisc0.neo_id),
            self.get_risc_debug(self.erisc1.risc_name, self.erisc1.neo_id),
        ]

    @cache
    def get_default_risc_debug(self) -> RiscDebug:
        return self.get_risc_debug(self.erisc0.risc_name, self.erisc0.neo_id)

    @cache
    def get_risc_debug(self, risc_name: str, neo_id: int | None = None) -> RiscDebug:
        assert neo_id is None, "NEO ID is not applicable for Blackhole device."
        risc_name = risc_name.lower()
        if risc_name == self.erisc0.risc_name:
            return BlackholeBabyRiscDebug(risc_info=self.erisc0)
        elif risc_name == self.erisc1.risc_name:
            return BlackholeBabyRiscDebug(risc_info=self.erisc1)
        raise ValueError(f"RISC debug for {risc_name} is not supported in Blackhole eth block.")
