# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from functools import cache, cached_property
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.quasar.functional_neo_block import QuasarFunctionalNeoBlock
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

        self.overlay = QuasarFunctionalWorkerBlock(noc_block=self)

        self.noc_memory_map.add_block(MemoryMapBlockInfo("l1", self.l1, safe_to_write=True))
        self.noc_memory_map.add_blocks(self.neo0.noc_memory_list)
        self.noc_memory_map.add_blocks(self.neo1.noc_memory_list)
        self.noc_memory_map.add_blocks(self.neo2.noc_memory_list)
        self.noc_memory_map.add_blocks(self.neo3.noc_memory_list)

    def get_debug_bus(self, neo_id: int | None = None) -> DebugBusSignalStore | None:
        if neo_id == 0:
            return self.neo0.debug_bus
        elif neo_id == 1:
            return self.neo1.debug_bus
        elif neo_id == 2:
            return self.neo2.debug_bus
        elif neo_id == 3:
            return self.neo3.debug_bus
        return super().get_debug_bus(neo_id)

    def get_register_store(self, noc_id: int = 0, neo_id: int | None = None) -> RegisterStore:
        if neo_id == 0:
            return self.neo0.register_store
        elif neo_id == 1:
            return self.neo1.register_store
        elif neo_id == 2:
            return self.neo2.register_store
        elif neo_id == 3:
            return self.neo3.register_store
        elif neo_id is None:
            return self.overlay.register_store
        return super().get_register_store(noc_id, neo_id)

    @cached_property
    def all_riscs(self) -> list[RiscDebug]:
        riscs = []
        riscs.extend(self.neo0.all_riscs)
        riscs.extend(self.neo1.all_riscs)
        riscs.extend(self.neo2.all_riscs)
        riscs.extend(self.neo3.all_riscs)
        riscs.extend(self.overlay.all_riscs)
        return riscs

    @cache
    def get_risc_debug(self, risc_name: str, neo_id: int | None = None) -> RiscDebug:
        if neo_id == self.neo0.neo_id:
            return self.neo0.get_risc_debug(risc_name)
        elif neo_id == self.neo1.neo_id:
            return self.neo1.get_risc_debug(risc_name)
        elif neo_id == self.neo2.neo_id:
            return self.neo2.get_risc_debug(risc_name)
        elif neo_id == self.neo3.neo_id:
            return self.neo3.get_risc_debug(risc_name)
        elif risc_name.startswith("rocket"):
            return self.overlay.get_risc_debug(risc_name)
        raise ValueError(
            f"RISC debug for {risc_name} [neo: {neo_id}] is not supported in Quasar functional worker block."
        )
