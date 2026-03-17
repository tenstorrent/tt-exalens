# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.wormhole.noc_block import WormholeNocBlock
from ttexalens.memory_map import MemoryMapBlockInfo


class WormholeRouterOnlyBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="router_only")

        self.noc_regs = MemoryBlock(
            size=0x10000, address=DeviceAddress(private_address=0xFFB20000, noc_address=0xFFB20000)
        )
        self.noc_memory_map.add_blocks(
            [
                MemoryMapBlockInfo("noc_regs", self.noc_regs),
            ]
        )
