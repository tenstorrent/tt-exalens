# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.register_store import RegisterStore
from ttexalens.hardware.quasar.niu_registers import default_niu_register_store_initialization


class QuasarNocBlock(NocBlock):
    def __init__(self, location: OnChipCoordinate, block_type: str, debug_bus: DebugBusSignalStore | None = None):
        super().__init__(location, block_type, debug_bus)

        self.register_store = RegisterStore(default_niu_register_store_initialization, self.location)

    def get_register_store(self, noc_id: int = 0, neo_id: int | None = None) -> RegisterStore:
        assert neo_id is None, "Default NOC block does not support neo_id"
        if noc_id == 0:
            return self.register_store
        else:
            raise ValueError(f"Invalid NOC ID: {noc_id}")
