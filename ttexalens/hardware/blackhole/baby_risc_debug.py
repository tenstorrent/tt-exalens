# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from typing import Callable
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.tt_exalens_lib import read_from_device, write_to_device
from ttexalens.util import TTException


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
            return int(self.noc_block.debug_bus.read_signal(self.risc_info.risc_name + "_pc"))

    def read_memory(self, address: int):
        return int.from_bytes(self.read_memory_bytes(address, 4), byteorder="little")

    def write_memory(self, address: int, value: int):
        data = value.to_bytes(4, byteorder="little")
        self.write_memory_bytes(address, data)

    def read_memory_bytes(self, address: int, size_bytes: int):
        if self.enable_asserts:
            self.assert_not_in_reset()

        read_memory: Callable[[int, int], bytes]
        noc_address = self.risc_info.translate_to_noc_address(address)
        if noc_address is not None and not self.is_in_reset():
            address = noc_address
            read_memory = lambda addr, size_bytes: read_from_device(
                self.risc_info.noc_block.location, addr, self.risc_info.noc_block.location.device_id, size_bytes
            )
        else:
            self.assert_debug_hardware_and_address(address)
            read_memory = super().read_memory_bytes

        return read_memory(address, size_bytes)

    def write_memory_bytes(self, address: int, data: bytes):
        if self.enable_asserts:
            self.assert_not_in_reset()

        write_memory: Callable[[int, bytes], None]

        noc_address = self.risc_info.translate_to_noc_address(address)
        if noc_address is not None and not self.is_in_reset():
            address = noc_address
            write_memory = lambda addr, data: (
                write_to_device(
                    self.risc_info.noc_block.location, addr, data, self.risc_info.noc_block.location.device_id
                ),
                None,
            )[1]
        else:
            self.assert_debug_hardware_and_address(address)
            write_memory = super().write_memory_bytes

        write_memory(address, data)

    def assert_debug_hardware_and_address(self, address: int):
        self.assert_debug_hardware()
        assert self.debug_hardware is not None, "Debug hardware is not initialized"

        if self.risc_info.risc_name == "trisc2" and address % 16 > 4:
            raise TTException(
                f"Accessing trisc2 private memory address 0x{address:08x} does not work due to blackhole bug. For more information see issue #528 in tt-exalens repo."
            )
