# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.register_store import RegisterStore
from ttexalens.hardware.wormhole.niu_registers import (
    default_niu_register_store_noc0_initialization,
    default_niu_register_store_noc1_initialization,
)


class WormholeNocBlock(NocBlock):
    def __init__(self, location: OnChipCoordinate, block_type: str, debug_bus: DebugBusSignalStore | None = None):
        super().__init__(location, block_type, debug_bus)

        self.register_store_noc0 = RegisterStore(default_niu_register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(default_niu_register_store_noc1_initialization, self.location)

    def get_register_store(self, noc_id: int = 0, neo_id: int | None = None) -> RegisterStore:
        if noc_id == 0:
            return self.register_store_noc0
        elif noc_id == 1:
            return self.register_store_noc1
        else:
            raise ValueError(f"Invalid NOC ID: {noc_id}")
