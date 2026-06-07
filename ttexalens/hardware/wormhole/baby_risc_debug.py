# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo


class WormholeBabyRiscDebug(BabyRiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, enable_asserts: bool = True):
        super().__init__(risc_info, enable_asserts)

    def cont(self):
        # If this is functional worker core, we need to disable branch prediction as a hardware workaround
        if self.baby_risc_info.branch_prediction_register is not None:
            self.set_branch_prediction(False)
        else:
            # erisc has no branch-prediction register to disable. Resuming from an ebreak with a plain
            # CONTINUE re-asserts the ebreak (Wormhole/Blackhole ebreak hardware bug): the fetch pipeline
            # re-runs the window after the ebreak and the core re-halts with ebreak still set. Flushing
            # the pipeline to the current PC clears the latched ebreak so we can continue in debug mode
            # (which keeps watchpoints active), instead of falling back to continue_without_debug().
            if self.is_halted() and self.is_ebreak_hit():
                self.assert_debug_hardware()
                assert self.debug_hardware is not None, "Debug hardware is not initialized"
                self.debug_hardware.flush(self.get_pc())
        super().cont()

    def step(self):
        # We need to disable branch prediction as a hardware workaround, if there is an option to do so
        if self.baby_risc_info.branch_prediction_register is not None:
            self.set_branch_prediction(False)
        return super().step()

    def read_gpr(self, register_index: int) -> int:
        if register_index != 32:
            return super().read_gpr(register_index)
        else:
            assert self.noc_block.debug_bus is not None, "Debug bus is not initialized."
            return int(self.noc_block.debug_bus.read_signal(self.risc_info.risc_name + "_pc"))
