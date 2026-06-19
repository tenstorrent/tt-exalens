# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo


class WormholeBabyRiscDebug(BabyRiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, enable_asserts: bool | None = None):
        super().__init__(risc_info, enable_asserts)

    def cont(self):
        # If this is functional worker core, we need to disable branch prediction as a hardware workaround
        if self.baby_risc_info.branch_prediction_register is not None:
            self.set_branch_prediction(False)
            super().cont()
        else:
            # For erisc we cannot disable branch prediction: the eth tile has no DISABLE_RISC_BP config
            # register, the RISC debug module cannot reach CSRs to set cfg0.DisBp (its register-access
            # command masks the index to the GPR file), and a `csr` instruction in a debugger-loaded
            # program traps. A debug-mode CONTINUE with branch prediction enabled corrupts the core
            # (subsequent NoC writes to its L1 intermittently fail), so we continue without debug mode.
            # This is stable but means hardware watchpoints cannot halt the erisc (see #762).
            if self.enable_asserts:
                self.assert_not_in_reset()
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
