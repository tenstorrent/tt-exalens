# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.wormhole.noc_block import WormholeNocBlock


class WormholeRouterOnlyBlock(WormholeNocBlock):
    def __init__(self, location: OnChipCoordinate):
        super().__init__(location, block_type="router_only")
