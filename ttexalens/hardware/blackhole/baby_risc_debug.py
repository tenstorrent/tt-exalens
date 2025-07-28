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

    def read_memory(self, address: int):
        if self.enable_asserts:
            self.assert_not_in_reset()
        self.assert_debug_hardware()
        assert self.debug_hardware is not None, "Debug hardware is not initialized"
        bytes_shifted = address % 4
        if bytes_shifted == 0:  # aligned read
            return self.debug_hardware.read_memory(address)
        else:
            A = self.debug_hardware.read_memory(address)
            B = self.debug_hardware.read_memory(address + 4)
            mask_A = 1 << ((4 - bytes_shifted) * 8) - 1
            mask_B = bytes_shifted * 8
            return ((A & mask_A) << 8 * bytes_shifted) | (B >> (32 - mask_B))
