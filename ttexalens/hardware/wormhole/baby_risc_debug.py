# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo


class WormholeBabyRiscDebug(BabyRiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, verbose: bool = False, enable_asserts: bool = True):
        super().__init__(risc_info, verbose, enable_asserts)

    def cont(self):
        # If this is functional worker core, we need to disable branch prediction as a hardware workaround
        if self.risc_info.branch_prediction_register is not None:
            self.set_branch_prediction(False)
            super().cont()
        else:
            # For erisc, we don't have option to disable branch prediction, so we should continue without debug
            if self.enable_asserts:
                self.assert_not_in_reset()
            self.assert_debug_hardware()
            assert self.debug_hardware is not None, "Debug hardware is not initialized"
            self.debug_hardware.continue_without_debug()

    def step(self):
        # We need to disable branch prediction as a hardware workaround, if there is an option to do so
        if self.risc_info.branch_prediction_register is not None:
            self.set_branch_prediction(False)
        return super().step()

    def read_gpr(self, register_index: int) -> int:
        if register_index != 32:
            return super().read_gpr(register_index)
        else:
            assert self.noc_block.debug_bus is not None, "Debug bus is not initialized."
            return self.noc_block.debug_bus.read_signal(self.risc_info.risc_name + "_pc")
