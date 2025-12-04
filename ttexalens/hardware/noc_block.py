# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from abc import abstractmethod
from functools import cache, cached_property
from typing import TYPE_CHECKING

from ttexalens.memory_map import MemoryMap

if TYPE_CHECKING:
    from ttexalens.device import Device
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.debug_bus_signal_store import DebugBusSignalStore
    from ttexalens.hardware.risc_debug import RiscDebug
    from ttexalens.register_store import RegisterStore
    from ttexalens.memory_map import MemoryMap


class NocBlock:
    def __init__(self, location: OnChipCoordinate, block_type: str, debug_bus: DebugBusSignalStore | None = None):
        self.location = location
        self.block_type = block_type
        self.debug_bus = debug_bus
        self.memory_map: MemoryMap = MemoryMap()

    @property
    def device(self) -> Device:
        return self.location._device

    @abstractmethod
    def get_register_store(self, noc_id: int = 0, neo_id: int | None = None) -> RegisterStore:
        pass

    def get_noc_memory_map(self) -> MemoryMap | None:
        # Currently only mapping NoC address space
        return self.memory_map

    def get_debug_bus(self, neo_id: int | None = None) -> DebugBusSignalStore | None:
        if neo_id is None:
            return self.debug_bus
        return None

    @cached_property
    def has_risc_cores(self) -> bool:
        return len(self.debuggable_riscs) > 0

    @cached_property
    def debuggable_riscs(self) -> list[RiscDebug]:
        return [risc_debug for risc_debug in self.all_riscs if risc_debug.can_debug()]

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        return []

    @cached_property
    def risc_names(self) -> list[str]:
        """
        Returns a list of RISC core names available in the NocBlock.
        This method should be overridden in subclasses to provide a specific implementation.
        """
        return [risc.risc_location.risc_name for risc in self.all_riscs]

    @cache
    def get_default_risc_debug(self) -> RiscDebug:
        """
        Returns a default RiscDebug instance for the NocBlock. It is meant to be used by RegisterStore to read/write configuration regusters.
        This method should be overridden in subclasses to provide a specific implementation.
        """
        raise NotImplementedError(f"Noc block on location {self.location.to_user_str()} doesn't have RISC cores.")

    @cache
    def get_risc_debug(self, risc_name: str, neo_id: int | None = None) -> RiscDebug:
        """
        Returns a RiscDebug instance for the specified RISC core.
        This method should be overridden in subclasses to provide a specific implementation.
        """
        raise NotImplementedError(f"Noc block on location {self.location.to_user_str()} doesn't have RISC cores.")
