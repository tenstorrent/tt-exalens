# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.baby_risc_debug import BabyRiscDebug, BabyRiscLocation
from ttexalens.baby_risc_info import BabyRiscInfo


class BlackholeBabyRiscDebug(BabyRiscDebug):
    def __init__(
        self, location: BabyRiscLocation, risc_info: BabyRiscInfo, verbose: bool = False, enable_asserts: bool = True
    ):
        super().__init__(location, risc_info, verbose, enable_asserts)
        self.debug_bus = self.location.coord._device.get_debug_bus_signal_store(location.coord)

    def read_gpr(self, register_index: int) -> int:
        if register_index != 32:
            return super().read_gpr(register_index)
        else:
            return self.debug_bus.read_signal(self.risc_info.risc_name + "_pc")
