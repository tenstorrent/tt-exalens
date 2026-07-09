# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.context import NocId
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.perf_counters import TensixPerfCounters
from ttexalens.register_store import RegisterStore
from ttexalens.hardware.quasar.niu_registers import (
    default_niu_register_store_initialization_noc,
    default_niu_register_store_initialization_smn,
)


class QuasarNocBlock(NocBlock):
    def __init__(
        self,
        location: OnChipCoordinate,
        block_type: str,
        debug_bus: DebugBusSignalStore | None = None,
        perf_counters: TensixPerfCounters | None = None,
    ):
        super().__init__(location, block_type, debug_bus, perf_counters)

        self.register_store_noc = RegisterStore(default_niu_register_store_initialization_noc, self.location)
        self.register_store_smn = RegisterStore(default_niu_register_store_initialization_smn, self.location)

    def get_register_store(self, noc_id: NocId | None = None, neo_id: int | None = None) -> RegisterStore:
        assert neo_id is None, "Default NOC block does not support neo_id"
        if noc_id is None:
            noc_id = self.device.active_noc
        if noc_id == NocId.NOC0:
            return self.register_store_noc
        elif noc_id == NocId.SYSTEM_NOC:
            return self.register_store_smn
        else:
            raise ValueError(f"Invalid NOC ID for Quasar: {noc_id}. Quasar supports NOC0 and SYSTEM_NOC.")
