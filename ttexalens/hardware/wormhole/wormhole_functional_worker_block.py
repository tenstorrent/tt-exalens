# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.noc_block import NocBlock


debug_bus_signal_map = {
    # For the other signals applying the pc_mask.
    "brisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 5, mask=0x7FFFFFFF),
    "trisc0_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 6, mask=0x7FFFFFFF),
    "trisc1_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 7, mask=0x7FFFFFFF),
    "trisc2_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 8, mask=0x7FFFFFFF),
    "ncrisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 12, mask=0x7FFFFFFF),
}


class WormholeFunctionalWorkerBlock(NocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(
            location, block_type="functional_workers", debug_bus=DebugBusSignalStore(debug_bus_signal_map, location)
        )

        self.l1 = MemoryBlock(
            size=1464 * 1024, address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000)
        )

        self.brisc = BabyRiscInfo(
            risc_name="brisc",
            risc_id=0,
            noc_block=self,
            l1=self.l1,
            data_private_memory=MemoryBlock(
                size=4 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc0 = BabyRiscInfo(
            risc_name="trisc0",
            risc_id=1,
            noc_block=self,
            l1=self.l1,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc1 = BabyRiscInfo(
            risc_name="trisc1",
            risc_id=2,
            noc_block=self,
            l1=self.l1,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.trisc2 = BabyRiscInfo(
            risc_name="trisc2",
            risc_id=3,
            noc_block=self,
            l1=self.l1,
            data_private_memory=MemoryBlock(
                size=2 * 1024,
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=None,
            debug_hardware_present=True,
        )

        self.ncrisc = BabyRiscInfo(
            risc_name="ncrisc",
            risc_id=4,
            noc_block=self,
            l1=self.l1,
            data_private_memory=MemoryBlock(
                size=4 * 1024,  # TODO: Check if this is correct
                address=DeviceAddress(private_address=0xFFB00000),
            ),
            code_private_memory=MemoryBlock(
                size=4 * 1024,  # TODO: Check if this is correct
                address=DeviceAddress(private_address=0xFFC00000),
            ),
            debug_hardware_present=False,
        )
