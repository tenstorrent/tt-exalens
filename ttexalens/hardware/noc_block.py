# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore


class NocBlock:
    def __init__(self, location: OnChipCoordinate, block_type: str, debug_bus: DebugBusSignalStore | None = None):
        self.location = location
        self.block_type = block_type
        self.debug_bus = debug_bus

    @property
    def device(self):
        return self.location._device
