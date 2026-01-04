# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from typing import Callable
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.util import TTException


class BlackholeBabyRiscDebug(BabyRiscDebug):
    def __init__(self, risc_info: BabyRiscInfo, enable_asserts: bool = True):
        super().__init__(risc_info, enable_asserts)

    def step(self):
        # There is a bug in hardware and for blackhole step should be executed twice
        super().step()
        super().step()

    def read_gpr(self, register_index: int) -> int:
        if register_index != 32:
            return super().read_gpr(register_index)
        else:
            assert self.noc_block.debug_bus is not None, "Debug bus is not initialized."
            return int(self.noc_block.debug_bus.read_signal(self.risc_info.risc_name + "_pc"))

    def read_memory_bytes(self, address: int, size_bytes: int):
        if self.enable_asserts:
            self.assert_not_in_reset()

        noc_address = self.risc_info.translate_to_noc_address(address)
        if noc_address is not None and not self.is_in_reset():
            return self.risc_info.noc_block.location.noc_read(noc_address, size_bytes)
        else:
            self.assert_trisc2_address(address)
            return super().read_memory_bytes(address, size_bytes)

    def write_memory_bytes(self, address: int, data: bytes):
        if self.enable_asserts:
            self.assert_not_in_reset()

        noc_address = self.risc_info.translate_to_noc_address(address)
        if noc_address is not None and not self.is_in_reset():
            self.risc_info.noc_block.location.noc_write(noc_address, data)
        else:
            self.assert_trisc2_address(address)
            super().write_memory_bytes(address, data)

    def assert_trisc2_address(self, address: int):
        if self.risc_info.risc_name == "trisc2" and address % 16 > 4:
            raise TTException(
                f"Accessing trisc2 private memory address 0x{address:08x} does not work due to blackhole bug. For more information see issue #528 in tt-exalens repo."
            )
