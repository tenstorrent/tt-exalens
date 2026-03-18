# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.blackhole.noc_block import BlackholeNocBlock
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.memory_map import MemoryMapBlockInfo


class BlackholeL2cpuBlock(BlackholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="l2cpu")

        self.noc_regs = MemoryBlock(size=0x10000, address=DeviceAddress(noc_address=0xFFFFFFFF_FF000000))
        self.noc_memory_map.add_blocks(
            [
                MemoryMapBlockInfo("noc_regs", self.noc_regs),
            ]
        )
