# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.blackhole.niu_registers import get_niu_register_store_initialization
from ttexalens.hardware.blackhole.noc_block import BlackholeNocBlock
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.memory_map import MemoryMapBlockInfo
from ttexalens.register_store import RegisterStore

register_store_noc0_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0xFFFFFFFF_FF000000, bar0_address=0x1FD04000, noc_id=0)
)
register_store_noc1_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0xFFFFFFFF_FF000000, bar0_address=0x1FD14000, noc_id=1)
)


class BlackholePcieBlock(BlackholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="pcie")

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)

        self.noc_regs = MemoryBlock(size=0x10000, address=DeviceAddress(noc_address=0xFFFFFFFF_FF000000))
        self.noc_memory_map.add_blocks(
            [
                MemoryMapBlockInfo("noc_regs", self.noc_regs),
            ]
        )
