# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from functools import cache, cached_property

from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.quasar.functional_overlay_registers import (
    OverlayDebugRegisterDescription,
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
    elif isinstance(register_description, OverlayDebugRegisterDescription):
        return DeviceAddress(noc_address=0x0300A000)
    elif isinstance(register_description, SmnRegisterDescription):
        return DeviceAddress(noc_address=0x03010000)
    elif isinstance(register_description, NeoRegisterDescription):
        return DeviceAddress(noc_address=0x03020000)
    else:
        raise ValueError(f"Unknown register description type: {type(register_description)}")


overlay_register_store_initialization = RegisterStore.create_initialization(
    register_map, get_overlay_register_base_address
)


class QuasarFunctionalOverlayBlock(NocBlock):
    """
    Represents the Quasar overlay cluster: 8 in-order 64-bit Rocket RISC-V
    data-movement cores sharing a 128 KB L2 cache and a 4 MB SRAM region.

    This block is not a separate NOC tile — it lives inside the functional
    worker tile and is accessed through the same (x, y) NOC coordinate.
    """

    def __init__(self, noc_block: QuasarFunctionalWorkerBlock):
        self.noc_block = noc_block

        self.overlay_register_store = RegisterStore(overlay_register_store_initialization, noc_block.location)

        self.rocket0 = BabyRiscInfo(
            risc_name="rocket0",
            risc_id=0,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=0,
            debug_hardware_present=False,
        )
        self.rocket1 = BabyRiscInfo(
            risc_name="rocket1",
            risc_id=1,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=0,
            debug_hardware_present=False,
        )
        self.rocket2 = BabyRiscInfo(
            risc_name="rocket2",
            risc_id=2,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=0,
            debug_hardware_present=False,
        )
        self.rocket3 = BabyRiscInfo(
            risc_name="rocket3",
            risc_id=3,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=0,
            debug_hardware_present=False,
        )
        self.rocket4 = BabyRiscInfo(
            risc_name="rocket4",
            risc_id=4,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=0,
            debug_hardware_present=False,
        )
        self.rocket5 = BabyRiscInfo(
            risc_name="rocket5",
            risc_id=5,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=0,
            debug_hardware_present=False,
        )
        self.rocket6 = BabyRiscInfo(
            risc_name="rocket6",
            risc_id=6,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=0,
            debug_hardware_present=False,
        )
        self.rocket7 = BabyRiscInfo(
            risc_name="rocket7",
            risc_id=7,
            noc_block=noc_block,
            neo_id=None,
            l1=noc_block.l1,
            max_watchpoints=0,
            reset_flag_shift=0,
            debug_hardware_present=False,
        )

    def get_register_store(self) -> RegisterStore:
        return self.overlay_register_store

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return [
            QuasarRocketCoreDebug(self.rocket0, self.overlay_register_store),
            QuasarRocketCoreDebug(self.rocket1, self.overlay_register_store),
            QuasarRocketCoreDebug(self.rocket2, self.overlay_register_store),
            QuasarRocketCoreDebug(self.rocket3, self.overlay_register_store),
            QuasarRocketCoreDebug(self.rocket4, self.overlay_register_store),
            QuasarRocketCoreDebug(self.rocket5, self.overlay_register_store),
            QuasarRocketCoreDebug(self.rocket6, self.overlay_register_store),
            QuasarRocketCoreDebug(self.rocket7, self.overlay_register_store),
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
                return QuasarRocketCoreDebug(core, self.overlay_register_store)
        raise ValueError(f"Rocket core '{risc_name}' not found in overlay block at {self.noc_block.location}")
