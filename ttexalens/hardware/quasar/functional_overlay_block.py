# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from functools import cache, cached_property

from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.quasar.functional_overlay_registers import (
    SmnRegisterDescription,
    ControlStatusRegisterDescription,
    ClusterControlRegisterDescription,
    NeoRegisterDescription,
    OverlayLlkTileCountersRegisterDescription,
    RoccAcellRegisterDescription,
    register_map,
)
from ttexalens.hardware.quasar.functional_worker_block import QuasarFunctionalWorkerBlock
from ttexalens.hardware.quasar.rocket_core_debug import QuasarRocketCoreDebug
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.register_store import (
    DebugRegisterDescription,
    RegisterDescription,
    RegisterStore,
)


def get_overlay_register_base_address(register_description: RegisterDescription) -> DeviceAddress:
    if isinstance(register_description, ClusterControlRegisterDescription):
        return DeviceAddress(noc_address=0x03000000)
    elif isinstance(register_description, ControlStatusRegisterDescription):
        return DeviceAddress(noc_address=0x03000200)
    elif isinstance(register_description, OverlayLlkTileCountersRegisterDescription):
        return DeviceAddress(noc_address=0x03003000)
    elif isinstance(register_description, RoccAcellRegisterDescription):
        return DeviceAddress(noc_address=0x03004000)
    elif isinstance(register_description, DebugRegisterDescription):
        return DeviceAddress(noc_address=0x0300A000)
    elif isinstance(register_description, SmnRegisterDescription):
        return DeviceAddress(noc_address=0x03010000, noc_id=1)  # These registers are only available through SMN
    elif isinstance(register_description, NeoRegisterDescription):
        return DeviceAddress(noc_address=0x03020000)
    else:
        raise ValueError(f"Unknown register description type: {type(register_description)}")


register_store_initialization = RegisterStore.create_initialization(register_map, get_overlay_register_base_address)


class QuasarFunctionalOverlayBlock:
    """
    Represents the Quasar overlay cluster: 8 in-order 64-bit Rocket RISC-V
    data-movement cores sharing a 128 KB L2 cache and a 4 MB SRAM region.
    """

    def __init__(self, noc_block: QuasarFunctionalWorkerBlock):
        self.noc_block = noc_block

        self.register_store = RegisterStore(register_store_initialization, noc_block.location)

        self.rocket0 = BabyRiscInfo(
            risc_name="rocket0",
            risc_id=0,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=8,
            default_code_start_address=None,
            code_start_address_register="TT_CLUSTER_CTRL_RESET_VECTOR_0",
            code_start_address_enable_register=None,
        )
        self.rocket1 = BabyRiscInfo(
            risc_name="rocket1",
            risc_id=1,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=9,
            default_code_start_address=None,
            code_start_address_register="TT_CLUSTER_CTRL_RESET_VECTOR_1",
            code_start_address_enable_register=None,
        )
        self.rocket2 = BabyRiscInfo(
            risc_name="rocket2",
            risc_id=2,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=10,
            default_code_start_address=None,
            code_start_address_register="TT_CLUSTER_CTRL_RESET_VECTOR_2",
            code_start_address_enable_register=None,
        )
        self.rocket3 = BabyRiscInfo(
            risc_name="rocket3",
            risc_id=3,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=11,
            default_code_start_address=None,
            code_start_address_register="TT_CLUSTER_CTRL_RESET_VECTOR_3",
            code_start_address_enable_register=None,
        )
        self.rocket4 = BabyRiscInfo(
            risc_name="rocket4",
            risc_id=4,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=12,
            default_code_start_address=None,
            code_start_address_register="TT_CLUSTER_CTRL_RESET_VECTOR_4",
            code_start_address_enable_register=None,
        )
        self.rocket5 = BabyRiscInfo(
            risc_name="rocket5",
            risc_id=5,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=13,
            default_code_start_address=None,
            code_start_address_register="TT_CLUSTER_CTRL_RESET_VECTOR_5",
            code_start_address_enable_register=None,
        )
        self.rocket6 = BabyRiscInfo(
            risc_name="rocket6",
            risc_id=6,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=14,
            default_code_start_address=None,
            code_start_address_register="TT_CLUSTER_CTRL_RESET_VECTOR_6",
            code_start_address_enable_register=None,
        )
        self.rocket7 = BabyRiscInfo(
            risc_name="rocket7",
            risc_id=7,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=15,
            default_code_start_address=None,
            code_start_address_register="TT_CLUSTER_CTRL_RESET_VECTOR_7",
            code_start_address_enable_register=None,
        )

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return [
            QuasarRocketCoreDebug(self.rocket0, self.register_store),
            QuasarRocketCoreDebug(self.rocket1, self.register_store),
            QuasarRocketCoreDebug(self.rocket2, self.register_store),
            QuasarRocketCoreDebug(self.rocket3, self.register_store),
            QuasarRocketCoreDebug(self.rocket4, self.register_store),
            QuasarRocketCoreDebug(self.rocket5, self.register_store),
            QuasarRocketCoreDebug(self.rocket6, self.register_store),
            QuasarRocketCoreDebug(self.rocket7, self.register_store),
        ]

    @cache
    def get_risc_debug(self, risc_name: str) -> RiscDebug:
        rocket_infos = [
            self.rocket0,
            self.rocket1,
            self.rocket2,
            self.rocket3,
            self.rocket4,
            self.rocket5,
            self.rocket6,
            self.rocket7,
        ]
        for core in rocket_infos:
            if core.risc_name == risc_name:
                return QuasarRocketCoreDebug(core, self.register_store)
        raise ValueError(f"Rocket core '{risc_name}' not found in overlay block at {self.noc_block.location}")
