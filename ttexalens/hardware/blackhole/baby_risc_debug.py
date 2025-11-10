# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from typing import Callable
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.baby_risc_info import BabyRiscInfo
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device
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
            return self.noc_block.debug_bus.read_signal(self.risc_info.risc_name + "_pc")

    def write_memory(self, address: int, value: int):
        if self.enable_asserts:
            self.assert_not_in_reset()

        write_memory: Callable[[int, int], None]

        noc_address = self.risc_info.translate_to_noc_address(address)
        if noc_address is not None and not self.is_in_reset():
            address = noc_address
            write_memory = lambda addr, val: write_words_to_device(
                self.risc_info.noc_block.location, addr, val, device_id=self.risc_info.noc_block.location.device_id
            )
        else:
            self.assert_debug_hardware()
            assert self.debug_hardware is not None, "Debug hardware is not initialized"

            if self.risc_info.risc_name == "trisc2" and address % 16 > 4:
                raise TTException(
                    f"Writing to trisc2 private memory address 0x{address:08x} does not work due to blackhole bug. For more information see issue #528 in tt-exalens repo."
                )
            write_memory = self.debug_hardware.write_memory

        word_size_bytes = 4
        word_size_bits = word_size_bytes * 8
        bytes_shifted = address % word_size_bytes
        # We have to treat unaligned write separately due to blackhole bug
        if bytes_shifted == 0:
            # aligned write
            write_memory(address, value)
        else:
            # unaligned write
            bits_shifted = bytes_shifted * 8
            word1 = value >> bits_shifted
            mask = (1 << bits_shifted) - 1
            word2 = (value & mask) << (word_size_bits - bits_shifted)
            write_memory(address - bytes_shifted, word1)
            write_memory(address + word_size_bytes - bytes_shifted, word2)

    def read_memory(self, address: int):
        if self.enable_asserts:
            self.assert_not_in_reset()

        read_memory: Callable[[int], int]

        noc_address = self.risc_info.translate_to_noc_address(address)
        if noc_address is not None and not self.is_in_reset():
            address = noc_address
            read_memory = lambda addr: read_word_from_device(
                self.risc_info.noc_block.location, addr, device_id=self.risc_info.noc_block.location.device_id
            )
        else:
            self.assert_debug_hardware()
            assert self.debug_hardware is not None, "Debug hardware is not initialized"

            if self.risc_info.risc_name == "trisc2" and address % 16 > 4:
                raise TTException(
                    f"Reading from trisc2 private memory address 0x{address:08x} does not work due to blackhole bug. For more information see issue #528 in tt-exalens repo."
                )
            read_memory = self.debug_hardware.read_memory

        word_size_bytes = 4
        word_size_bits = word_size_bytes * 8
        bytes_shifted = address % word_size_bytes
        # We have to treat unaligned read separately due to blackhole bug
        if bytes_shifted == 0:
            # aligned read
            return read_memory(address)
        else:
            # unaligned read
            bits_shifted = bytes_shifted * 8
            word1 = read_memory(address - bytes_shifted)
            word2 = read_memory(address + word_size_bytes - bytes_shifted)
            mask = (1 << (word_size_bits - bits_shifted)) - 1
            return ((word1 & mask) << bits_shifted) | (word2 >> (word_size_bits - bits_shifted))
