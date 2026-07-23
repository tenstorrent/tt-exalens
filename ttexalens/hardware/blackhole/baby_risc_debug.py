# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.exceptions import TTException


class BlackholeBabyRiscDebug(BabyRiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, enable_asserts: bool | None = None):
        super().__init__(risc_info, enable_asserts=enable_asserts)

    def step(self):
        # There is a bug in hardware and for blackhole step should be executed twice
        super().step()
        super().step()

    def cont(self):
        # There is a bug in hardware: resuming from an ebreak with a plain CONTINUE
        # re-asserts the ebreak. The fetch pipeline re-runs the window after the ebreak
        # (the NOPs emitted by -mtt-fix-whbhebreak) and the core re-halts at the end of
        # that pad with ebreak still set. Flushing the pipeline to the current PC clears
        # the latched ebreak so execution resumes cleanly past it.
        if self.is_halted() and self.is_ebreak_hit():
            assert self.debug_hardware is not None, "Debug hardware is not initialized"
            self.debug_hardware.flush(self.get_pc())
        super().cont()

    def read_gpr(self, register_index: int) -> int:
        if register_index != 32:
            return super().read_gpr(register_index)
        else:
            assert self.noc_block.debug_bus is not None, "Debug bus is not initialized."
            return int(self.noc_block.debug_bus.read_signal(self.risc_info.risc_name + "_pc"))

    def read_memory_bytes(self, address: int, buffer: bytearray | memoryview, safe_mode: bool | None = None) -> None:
        self.assert_trisc2_address(address)
        super().read_memory_bytes(address, buffer, safe_mode=safe_mode)

    def write_memory_bytes(self, address: int, data: bytes | bytearray | memoryview, safe_mode: bool | None = None):
        self.assert_trisc2_address(address)
        super().write_memory_bytes(address, data, safe_mode=safe_mode)

    def assert_trisc2_address(self, address: int):
        if self.risc_info.risc_name == "trisc2" and address % 16 > 4:
            raise TTException(
                f"Accessing trisc2 private memory address 0x{address:08x} does not work due to blackhole bug. For more information see issue #528 in tt-exalens repo."
            )
