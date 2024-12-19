# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# This code is used to interact with the ARC debug firmware on the device.
import os
from typing import Union, List
from ttlens.tt_arc_dbg_fw_log_context import (
    LogInfo,
    ArcDfwLogContext,
    ArcDfwLogContextFromList,
    ArcDfwLogContextFromYaml,
)
from math import floor
import struct
from abc import abstractmethod, ABC
from ttlens.tt_util import TTException


class ArcDfwCompiler(ABC):
    def __init__(self, base_fw_file_path: str, symbols_file_path: str, output_fw_file_path: str):
        self.base_fw_file_path = base_fw_file_path
        self.output_fw_file_path = output_fw_file_path
        self.symbols_file_path = symbols_file_path

        self.symbol_locations = self._parse_elf_symbols()

        self.MAX_WRITE_BYTES = 256 * 4

    def _parse_elf_symbols(self) -> dict:
        """
        Parses the symbols from the symbol table file.

        Returns:
            dict: Dictionary of symbol names and their addresses.
        """
        file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.symbols_file_path)
        symbol_table = {}

        with open(file_name, "r") as f:
            lines = f.readlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            name, address = line.split(":")
            symbol_table[name.strip()] = address.strip()

        return symbol_table

    def _change_byte_at_address(self, hex_lines: List[int], address: int, new_byte: int) -> List[int]:
        """
        Changes a single byte at the specified address in the hex lines.

        Args:
            hex_lines (List[int]): List of hex lines.
            address (int): Address to change the byte.
            new_byte (int): New byte value.

        Returns:
            List[int]: Updated list of hex lines.
        """
        line_index = address // 4
        byte_index = address % 4
        line = hex_lines[line_index]
        line = int.from_bytes(line.to_bytes(4, byteorder="big"), byteorder="little")
        mask = 0xFF << (byte_index * 8)
        new_line = (line & ~mask) | (new_byte << (byte_index * 8))
        new_line = int.from_bytes(new_line.to_bytes(4, byteorder="little"), byteorder="big")
        hex_lines[line_index] = new_line
        return hex_lines

    def _change_two_bytes_at_address(self, hex_lines: List[int], address: int, new_bytes: int) -> List[int]:
        """
        Changes two bytes at the specified address in the hex lines.

        Args:
            hex_lines (List[int]): List of hex lines.
            address (int): Address to change the bytes.
            new_bytes (int): New bytes value.

        Returns:
            List[int]: Updated list of hex lines.
        """
        line_index = address // 4
        byte_index = address % 4
        line = hex_lines[line_index]
        line = int.from_bytes(line.to_bytes(4, byteorder="big"), byteorder="little")
        mask = 0xFFFF << (byte_index * 8)
        new_line = (line & ~mask) | (new_bytes << (byte_index * 8))
        new_line = int.from_bytes(new_line.to_bytes(4, byteorder="little"), byteorder="big")
        hex_lines[line_index] = new_line
        return hex_lines

    def _change_four_bytes_at_address(self, hex_lines: List[int], address: int, new_bytes: int) -> List[int]:
        """
        Changes four bytes at the specified address in the hex lines.

        Args:
            hex_lines (List[int]): List of hex lines.
            address (int): Address to change the bytes.
            new_bytes (int): New bytes value.

        Returns:
            List[int]: Updated list of hex lines.
        """
        line_index = address // 4
        new_bytes = int.from_bytes(new_bytes.to_bytes(4, byteorder="big"), byteorder="little")
        hex_lines[line_index] = new_bytes
        return hex_lines

    def _load_hex_file(self, file_path: str) -> List[int]:
        """
        Loads a hex file into a list of hex lines.

        Args:
            file_path (str): Path to the hex file.

        Returns:
            List[int]: List of hex lines.
        """
        with open(file_path, "r") as file:
            hex_lines = [int(line, 16) for line in file.read().splitlines()]
        return hex_lines

    def _save_hex_file(self, file_path: str, hex_lines: List[int]) -> None:
        """
        Saves the hex lines to a file.

        Args:
            file_path (str): Path to the hex file.
            hex_lines (List[int]): List of hex lines to save.
        """
        with open(file_path, "w") as file:
            file.write("\n".join(f"{line:08x}" for line in hex_lines))

    def _create_load_instruction(self, register: int, address: int) -> List[int]:
        """
        Creates an 8 byte load instruction for the specified register and address.

        Args:
            register (int): Register to load.
            address: Address to load from.

        Returns:
            List[int]: Load instruction.
        """
        instruction = 0x16007801 | (register & 0b111111)
        return [
            (instruction >> 24) & 0xFF,
            (instruction >> 16) & 0xFF,
            (instruction >> 8) & 0xFF,
            instruction & 0xFF,
            (address >> 24) & 0xFF,
            (address >> 16) & 0xFF,
            (address >> 8) & 0xFF,
            address & 0xFF,
        ]

    def _create_store_instruction(self, r_addr: int, r_data: int, offset: int) -> List[int]:
        """
        Creates a 2 byte store instruction for the specified register and offset.

        Args:
            register (int): Register to store.
            offset (int): Offset to store to.

        Returns:
            List[int]: Store instruction.
        """
        # ST_S b,[SP,u7] 11000bbb010uuuuu
        opcode = 0b10100 << 11
        r_addr_bits = (r_addr & 0b111) << 8
        reg_data_bits = (r_data & 0b111) << 5
        # offset is 5 bits but is shifted left by 2
        offset_bits = offset & 0x1F
        instruction = opcode | r_addr_bits | reg_data_bits | offset_bits
        return [(instruction >> 8) & 0xFF, instruction & 0xFF]

    def _add_instructions_to_hex_lines(
        self, hex_lines: List[int], from_address: int, instruction_bytes: List[int]
    ) -> None:
        """
        Adding instructions to hex lines that are read from a hex file.

        Args:
            hex_lines (List[int]): List of hex lines.
            from_address (int): Address to add the instructions.
            instruction_bytes (List[int]): Instructions to add.

        Raises:
            TTException: If too many bytes are written to the new hex.
        """
        bytes_written = 0
        # Write new instructions to the hex file, because of the endianess
        for i in range(0, len(instruction_bytes), 2):
            byte_pair = (instruction_bytes[i] << 8) | (
                instruction_bytes[i + 1] if i + 1 < len(instruction_bytes) else 0
            )
            self._change_two_bytes_at_address(hex_lines, from_address + i, byte_pair)
            bytes_written += 2

        if bytes_written > self.MAX_WRITE_BYTES:
            raise TTException(
                f"Too many bytes written to the new hex, reduce the number of logs: {bytes_written} > {self.MAX_WRITE_BYTES}"
            )
        pass

    def compile(self):
        """
        Adds logging instructions to the ARC debug firmware.

        Args:
            base_fw_file_path (str): Path to the base firmware file.
            output_fw_file_path (str): Path to the modified firmware file.
            log_context (ArcDfwLogContext): Log context containing log information.
        """
        LOG_FUNCITON_EDITABLE = int(self.symbol_locations["log_function"], 16)  # + 0x24
        base_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.base_fw_file_path)
        hex_lines = self._load_hex_file(base_file_name)

        instruction_bytes = self._get_modified_instruction_bytes()

        self._add_instructions_to_hex_lines(hex_lines, LOG_FUNCITON_EDITABLE, instruction_bytes)

        save_file_name = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.output_fw_file_path)
        print(save_file_name)
        self._save_hex_file(save_file_name, hex_lines)

    @abstractmethod
    def _get_modified_instruction_bytes(self) -> List[int]:
        """
        Gets the modified instruction bytes for the ARC debug firmware.

        Returns:
            List[int]: Modified instructions
        """
        pass


class ArcDfwLoggerCompiler(ArcDfwCompiler):
    def __init__(
        self, base_fw_file_path: str, symbols_file_path: str, output_fw_file_path: str, log_context: ArcDfwLogContext
    ):
        super().__init__(base_fw_file_path, symbols_file_path, output_fw_file_path)
        self.log_context = log_context

    def _get_modified_instruction_bytes(self) -> List[int]:
        instruction_bytes = []
        for i, log_info in enumerate(self.log_context.log_list):
            instruction_bytes += self._create_load_instruction(1, log_info.address)
            instruction_bytes += self._create_store_instruction(0, 1, i)

        # Loading dfw_buffer_header address so it can be incremented
        instruction_bytes += self._create_load_instruction(1, int(self.symbol_locations["dfw_buffer_header"], 16))
        # Incrementing the number of log calls and returning to the main loop
        # end_address:	     443c                	ld_s	r0,[r1,0x1c]
        # end_address + 0x2: 7104                	add_s	r0,r0,1
        # end_address + 0x4: a107                	st_s	r0,[r1,0x1c]
        # end_address + 0x6: 7ee0                	j_s	[blink]
        instruction_bytes += [0x44, 0x3C, 0x71, 0x04, 0xA1, 0x07, 0x7E, 0xE0]

        return instruction_bytes
