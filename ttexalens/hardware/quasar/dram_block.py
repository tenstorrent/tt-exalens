# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.quasar.noc_block import QuasarNocBlock


class QuasarDramBlock(QuasarNocBlock):
    def __init__(self, location: OnChipCoordinate):
        # TODO: #865
        raise NotImplementedError(f"Quasar DRAM block is not implemented yet (location {location.to_user_str()}.).")
