# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo


class BlackholeBabyRiscDebug(BabyRiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, verbose: bool = False, enable_asserts: bool = True):
        super().__init__(risc_info, verbose, enable_asserts)

    def step(self):
        # There is a bug in hardware and for blackhole step should be executed twice
        super().step()
        super().step()

    def read_gpr(self, register_index: int) -> int:
        if register_index != 32:
            return super().read_gpr(register_index)
        else:
            assert self.noc_block.debug_bus is not None, "Debug bus is not initialized."
            return self.noc_block.debug_bus.read_signal(self.risc_info.risc_name + "_pc")
