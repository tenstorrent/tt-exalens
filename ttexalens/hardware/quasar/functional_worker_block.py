# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from ttexalens.context import NocId
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.quasar.functional_neo_block import QuasarFunctionalNeoBlock
from ttexalens.hardware.quasar.functional_overlay_block import QuasarFunctionalOverlayBlock
from ttexalens.hardware.quasar.noc_block import QuasarNocBlock
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.memory_map import MemoryMapBlockInfo
from ttexalens.register_store import RegisterStore


class QuasarFunctionalWorkerBlock(QuasarNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="functional_workers")

        self.l1 = MemoryBlock(
            size=4 * 1024 * 1024, address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000)
        )

        self.neo0 = QuasarFunctionalNeoBlock(
            noc_block=self,
            neo_id=0,
            neo_base_address=DeviceAddress(private_address=0x00800000, noc_address=0x01800000),
            risc_base_start_address=0x00000000,
        )

        self.neo1 = QuasarFunctionalNeoBlock(
            noc_block=self,
            neo_id=1,
            neo_base_address=DeviceAddress(private_address=0x00800000, noc_address=0x01810000),
            risc_base_start_address=0x00010000,
        )

        self.neo2 = QuasarFunctionalNeoBlock(
            noc_block=self,
            neo_id=2,
            neo_base_address=DeviceAddress(private_address=0x00800000, noc_address=0x01820000),
            risc_base_start_address=0x00020000,
        )

        self.neo3 = QuasarFunctionalNeoBlock(
            noc_block=self,
            neo_id=3,
            neo_base_address=DeviceAddress(private_address=0x00800000, noc_address=0x01830000),
            risc_base_start_address=0x00030000,
        )

        self.neos = [self.neo0, self.neo1, self.neo2, self.neo3]

        self.overlay = QuasarFunctionalOverlayBlock(noc_block=self)

        self.noc_memory_map.initialize_blocks(
            [MemoryMapBlockInfo("l1", self.l1, safe_to_write=True)]
            + [memory for neo in self.neos for memory in neo.noc_memory_list]
            + self.overlay.noc_memory_list
        )

    @property
    def neo_ids(self) -> list[int]:
        return [neo.neo_id for neo in self.neos]

    def get_sub_block(self, neo_id: int | None) -> QuasarFunctionalNeoBlock | QuasarFunctionalOverlayBlock | None:
        if neo_id is None:
            return self.overlay
        for neo in self.neos:
            if neo.neo_id == neo_id:
                return neo
        return None

    def get_debug_bus(self, neo_id: int | None = None) -> DebugBusSignalStore | None:
        neo = self.get_sub_block(neo_id)
        if neo is not None and not isinstance(neo, QuasarFunctionalOverlayBlock):
            return neo.debug_bus
        return super().get_debug_bus(neo_id)

    def get_register_store(self, noc_id: NocId | None = None, neo_id: int | None = None) -> RegisterStore:
        neo = self.get_sub_block(neo_id)
        if neo is not None:
            return neo.register_store
        return super().get_register_store(noc_id, neo_id)

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        riscs = [risc for neo in self.neos for risc in neo.all_riscs]
        riscs.extend(self.overlay.all_riscs)
        return riscs

    @cache
    def get_risc_debug(self, risc_name: str, neo_id: int | None = None) -> RiscDebug:
        neo = self.get_sub_block(neo_id)
        if neo is not None:
            return neo.get_risc_debug(risc_name)
        raise ValueError(
            f"RISC debug for {risc_name} [neo: {neo_id}] is not supported in Quasar functional worker block."
        )
