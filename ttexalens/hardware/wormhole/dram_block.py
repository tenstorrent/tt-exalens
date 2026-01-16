# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.wormhole.niu_registers import get_niu_register_store_initialization
from ttexalens.hardware.wormhole.noc_block import WormholeNocBlock
from ttexalens.memory_map import MemoryMapBlockInfo
from ttexalens.register_store import RegisterStore

register_store_location0_noc0_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0x100080000)
)
register_store_location0_noc1_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0x100088000)
)
register_store_location1_noc0_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0x100090000)
)
register_store_location1_noc1_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0x100098000)
)
register_store_location2_noc0_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0x1000A0000)
)
register_store_location2_noc1_initialization = get_niu_register_store_initialization(
    DeviceAddress(noc_address=0x1000A8000)
)


class WormholeDramBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="dram")

        self.dram_bank = MemoryBlock(
            size=2 * 1024 * 1024 * 1024, address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000)
        )

        # Each DRAM block has three NOC blocks. We need to determine which NOC block to use based on the
        # location coordinate.
        if location._noc0_coord[1] % 3 == 1:
            self.register_store_noc0 = RegisterStore(register_store_location0_noc0_initialization, self.location)
            self.register_store_noc1 = RegisterStore(register_store_location0_noc1_initialization, self.location)
        elif location._noc0_coord[1] % 3 == 2:
            self.register_store_noc0 = RegisterStore(register_store_location1_noc0_initialization, self.location)
            self.register_store_noc1 = RegisterStore(register_store_location1_noc1_initialization, self.location)
        else:
            self.register_store_noc0 = RegisterStore(register_store_location2_noc0_initialization, self.location)
            self.register_store_noc1 = RegisterStore(register_store_location2_noc1_initialization, self.location)

        self.noc_memory_map.add_blocks(
            [
                MemoryMapBlockInfo("dram_bank", self.dram_bank, safe_to_read=True, safe_to_write=True),
                MemoryMapBlockInfo(
                    "chan0_config_regs",
                    MemoryBlock(size=0x40000, address=DeviceAddress(noc_address=0x100000000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo(
                    "chan1_config_regs",
                    MemoryBlock(size=0x40000, address=DeviceAddress(noc_address=0x100040000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo(
                    "loc0_noc0_regs",
                    MemoryBlock(size=0x8000, address=DeviceAddress(noc_address=0x100080000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo(
                    "loc0_noc1_regs",
                    MemoryBlock(size=0x8000, address=DeviceAddress(noc_address=0x100088000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo(
                    "loc1_noc0_regs",
                    MemoryBlock(size=0x8000, address=DeviceAddress(noc_address=0x100090000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo(
                    "loc1_noc1_regs",
                    MemoryBlock(size=0x8000, address=DeviceAddress(noc_address=0x100098000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo(
                    "loc2_noc0_regs",
                    MemoryBlock(size=0x8000, address=DeviceAddress(noc_address=0x1000A0000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo(
                    "loc2_noc1_regs",
                    MemoryBlock(size=0x8000, address=DeviceAddress(noc_address=0x1000A8000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
                MemoryMapBlockInfo(
                    "gddr_config_regs",
                    MemoryBlock(size=0x18000, address=DeviceAddress(noc_address=0x1000B0000)),
                    safe_to_read=True,
                    safe_to_write=False,
                ),
            ]
        )
