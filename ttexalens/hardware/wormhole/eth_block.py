# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from typing import Callable
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
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


# Commented signals marked with "# Duplicate signal name" are true duplicates -
# their name already exists in the map and they represent the same signal so suffix "_dup" is added.
debug_bus_signal_map = {
    "erisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x7FFFFFFF),
    "erisc_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x200),
    "erisc_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x40000000
    ),
    "erisc_id_ex_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x100),
    "erisc_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x80000000
    ),
    "erisc_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x80),
    "erisc_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x20),
    "erisc_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x1F),
    "erisc_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=19, mask=0xFFFFFFFF),
    "erisc_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=19, mask=0x3FFFFFFF),
    "erisc_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x10000000),
    "erisc_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1F00000),
    "erisc_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x40000),
    "erisc_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x7C00),
    "erisc_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x100),
    "erisc_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1F),
    "erisc_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "erisc_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x7FFFFFFF),
    "erisc_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "erisc_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x40000000
    ),
    "erisc_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x3FFFFFFF),
    "erisc_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "erisc_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x40000000),
    "erisc_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x3FFFFFFF),
    "erisc_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x80000000),
    "erisc_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x7FFFFFFF),
}

# Group name mapping (daisy_sel, sig_sel) based on documentation
"""https://github.com/tenstorrent/tt-isa-documentation/blob/main/WormholeB0/TensixTile/DebugDaisychain.md"""
# Signal name mapping to (DaisySel, sig_sel)
group_map: dict[str, tuple[int, int]] = {
    "erisc_group_a": (7, 18),
    "erisc_group_b": (7, 19),
}

register_map = {
    "RISCV_IC_INVALIDATE_InvalidateAll": ConfigurationRegisterDescription(index=157, mask=0x1F),
    "TRISC_RESET_PC_SEC0_PC": ConfigurationRegisterDescription(index=158),
    "TRISC_RESET_PC_SEC1_PC": ConfigurationRegisterDescription(index=159),
    "TRISC_RESET_PC_SEC2_PC": ConfigurationRegisterDescription(index=160),
    "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=161, mask=0x7),
    "NCRISC_RESET_PC_PC": ConfigurationRegisterDescription(index=162),
    "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": ConfigurationRegisterDescription(index=163, mask=0x1),
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
debug_bus_signals_initialization = DebugBusSignalStore.create_initialization(group_map, debug_bus_signal_map)


class WormholeEthBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(
            location,
            block_type="eth",
            debug_bus=DebugBusSignalStore(debug_bus_signals_initialization, self),
        )

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
            branch_prediction_register=None,  # We don't have a branch prediction register on erisc
            default_code_start_address=0,
            code_start_address_register=None,  # We don't have a regsiter to override code start address
            status_read_valid_mask=1 << 27,
            data_private_memory=MemoryBlock(
                size=4 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return [self.get_risc_debug(self.erisc.risc_name, self.erisc.neo_id)]

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
