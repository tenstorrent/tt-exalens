# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo


class QuasarBabyRiscDebug(BabyRiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, verbose: bool = False, enable_asserts: bool = True):
        super().__init__(risc_info, verbose, enable_asserts)

    def invalidate_instruction_cache(self):
        pc = self.get_pc()

        # Execute invalidate instruction cache
        """
        Invalidates the instruction cache of the RISC-V core.
        """
        register = self.register_store.get_register_description("RISCV_IC_INVALIDATE_InvalidateAll")
        self.__write_register(register, 0)
        self.__write_register(register, 1 << (3 - self.risc_info.risc_id))

        # Flush PC address to activate instruction cache (needed on Quasar)
        assert self.debug_hardware is not None
        self.debug_hardware.flush(pc)

    def read_gpr(self, register_index: int) -> int:
        if register_index != 32:
            return super().read_gpr(register_index)
        else:
            assert self.noc_block.debug_bus is not None, "Debug bus is not initialized."
            return self.noc_block.debug_bus.read_signal(self.risc_info.risc_name + "_pc")
