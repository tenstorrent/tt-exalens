# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.quasar.functional_neo_block import QuasarFunctionalNeoBlock
from ttexalens.hardware.quasar.noc_block import QuasarNocBlock
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
            neo_base_address=DeviceAddress(private_address=0x00810000, noc_address=0x01810000),
            risc_base_start_address=0x00010000,
        )

        self.neo2 = QuasarFunctionalNeoBlock(
            noc_block=self,
            neo_id=2,
            neo_base_address=DeviceAddress(private_address=0x00820000, noc_address=0x01820000),
            risc_base_start_address=0x00020000,
        )

        self.neo3 = QuasarFunctionalNeoBlock(
            noc_block=self,
            neo_id=3,
            neo_base_address=DeviceAddress(private_address=0x00830000, noc_address=0x01830000),
            risc_base_start_address=0x00030000,
        )

    def get_register_store(self, noc_id: int = 0, neo_id: int | None = None) -> RegisterStore:
        if neo_id == 0:
            return self.neo0.register_store
        elif neo_id == 1:
            return self.neo1.register_store
        elif neo_id == 2:
            return self.neo2.register_store
        elif neo_id == 3:
            return self.neo3.register_store
        return super().get_register_store(noc_id, neo_id)
