# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from abc import abstractmethod
from typing import Union

from ttexalens.register_store import RegisterStore


class RiscInfo:
    @abstractmethod
    def get_code_start_address(self, register_store: RegisterStore) -> int:
        pass

    @abstractmethod
    def set_code_start_address(self, register_store: RegisterStore, address: Union[int, None]):
        pass

    # TODO: Find better home for this method :)
    @staticmethod
    def get_jump_to_offset_instruction(offset, rd=0):
        """
        Generate a JAL instruction code based on the given offset.

        :param offset: The offset to jump to, can be positive or negative.
        :param rd: The destination register (default is x1 for the return address).
        :return: The 32-bit JAL instruction code.
        """
        if rd < 0 or rd > 31:
            raise ValueError("Invalid register number. rd must be between 0 and 31.")

        if offset < -(2**20) or offset >= 2**20:
            raise ValueError("Offset out of range. Must be between -2^20 and 2^20-1.")

        # Make sure the offset is within the range for a 20-bit signed integer
        offset &= 0x1FFFFF

        # Extracting the bit fields from the offset
        jal_offset_bit_20 = (offset >> 20) & 0x1
        jal_offset_bits_10_to_1 = (offset >> 1) & 0x3FF
        jal_offset_bit_11 = (offset >> 11) & 0x1
        jal_offset_bits_19_to_12 = (offset >> 12) & 0xFF

        # Reconstruct the 20-bit immediate in the JAL instruction format
        jal_offset = (
            (jal_offset_bit_20 << 31)
            | (jal_offset_bits_19_to_12 << 12)
            | (jal_offset_bit_11 << 20)
            | (jal_offset_bits_10_to_1 << 21)
        )

        # Construct the instruction
        return jal_offset | (rd << 7) | 0x6F
