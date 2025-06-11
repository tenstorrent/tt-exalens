# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.blackhole.niu_registers import get_niu_register_store_initialization
from ttexalens.hardware.blackhole.noc_block import BlackholeNocBlock
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.register_store import RegisterStore


register_store_noc0_initialization = get_niu_register_store_initialization(DeviceAddress(noc_address=0xFFB20000))
register_store_noc1_initialization = get_niu_register_store_initialization(DeviceAddress(noc_address=0xFFB30000))


class BlackholeDramBlock(BlackholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="dram")

        self.dram_bank = MemoryBlock(
            # TODO #432: Check if this size is correct
            size=2 * 1024 * 1024 * 1024,
            address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000),
        )

        # TODO #432: Check if there is risc core on DRAM block and if we can debug it.

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)
