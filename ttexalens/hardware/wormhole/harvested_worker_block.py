# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.device_address import DeviceAddress
from ttexalens.hardware.wormhole.niu_registers import get_niu_register_store_initialization
from ttexalens.hardware.wormhole.noc_block import WormholeNocBlock
from ttexalens.register_store import RegisterStore


register_store_noc0_initialization = get_niu_register_store_initialization(DeviceAddress(noc_address=0xFFB20000))
register_store_noc1_initialization = get_niu_register_store_initialization(DeviceAddress(noc_address=0xFFB30000))


class WormholeHarvestedWorkerBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="harvested_workers")

        self.register_store_noc0 = RegisterStore(register_store_noc0_initialization, self.location)
        self.register_store_noc1 = RegisterStore(register_store_noc1_initialization, self.location)
