# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator


class RiscvProgramWriter:
    """Class to write programs to a RISC-V core for testing purposes."""

    def __init__(self, core_simulator: RiscvCoreSimulator):
        self.core_simulator = core_simulator
        self.start_address = core_simulator.program_base_address
        self.instructions: list[int] = []

    @property
    def current_address(self) -> int:
        return self.start_address + len(self.instructions) * 4

    def write_program(self):
        for i, instruction in enumerate(self.instructions):
            self.core_simulator.write_program(i * 4, instruction)

    def append(self, instruction: int):
        # Ensure instruction is 32 bits
        assert 0 <= instruction <= 0xFFFFFFFF, "Instruction must be a 32-bit integer"
        self.instructions.append(instruction)

    def append_nop(self):
        """Append a NOP instruction (ADDI x0, x0, 0)."""
        self.append(0x00000013)

    def append_ebreak(self):
        """Append an EBREAK instruction."""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/ebreak.html
        self.append(0x00100073)

    def append_lui(self, register: int, value: int):
        """Load the zero-extended value into register."""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/lui.html
        assert 0 < register < 32, "Register must be between 1 and 31"
        assert value & (0xFFF) == 0, "Lower 12 bits must be zero for LUI"
        self.append(value | (register << 7) | 0b0110111)

    def append_addi(self, destination_register: int, source_register: int, value: int):
        """Adds an immediate value to the value in source_register, and store the result in destination_register"""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/addi.html
        assert 0 < destination_register < 32, "Destination register must be between 1 and 31"
        assert 0 <= source_register < 32, "Source register must be between 0 and 31"
        assert -2048 <= value < 2048, "Immediate value must be between -2048 and 2047"
        value = value & 0xFFF  # Ensure value is 12 bits signed integer
        self.append((value << 20) | (source_register << 15) | (destination_register << 7) | 0b0010011)

    def append_sb(self, data_register: int, address_register: int, offset: int):
        """Store 8 bits of data from data_register to an address formed by adding address_register to a signed offset."""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/sb.html
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert -2048 <= offset < 2048, "Offset must be between -2048 and 2047"
        offset = offset & 0xFFF
        offset_hi = (offset >> 5) & 0x07F
        offset_low = offset & 0x01F
        self.append(
            (offset_hi << 25)
            | (data_register << 20)
            | (address_register << 15)
            | (0b000 << 12)
            | (offset_low << 7)
            | 0b0100011
        )

    def append_sh(self, data_register: int, address_register: int, offset: int):
        """Store 16 bits of data from data_register to an address formed by adding address_register to a signed offset."""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/sh.html
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert -2048 <= offset < 2048, "Offset must be between -2048 and 2047"
        offset = offset & 0xFFF
        offset_hi = (offset >> 5) & 0x07F
        offset_low = offset & 0x01F
        self.append(
            (offset_hi << 25)
            | (data_register << 20)
            | (address_register << 15)
            | (0b001 << 12)
            | (offset_low << 7)
            | 0b0100011
        )

    def append_sw(self, data_register: int, address_register: int, offset: int):
        """Store 32 bits of data from data_register to an address formed by adding address_register to a signed offset."""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/sw.html
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert -2048 <= offset < 2048, "Offset must be between -2048 and 2047"
        offset = offset & 0xFFF
        offset_hi = (offset >> 5) & 0x07F
        offset_low = offset & 0x01F
        self.append(
            (offset_hi << 25)
            | (data_register << 20)
            | (address_register << 15)
            | (0b010 << 12)
            | (offset_low << 7)
            | 0b0100011
        )

    def append_lw(self, value_register: int, address_register: int, offset: int):
        """Load 32 bits of data into value_register from an address formed by adding address_register to a signed offset. Sign extend the result."""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/lw.html
        assert 0 <= value_register < 32, "Value register must be between 0 and 31"
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert -2048 <= offset < 2048, "Offset must be between -2048 and 2047"
        offset = offset & 0xFFF
        self.append((offset << 20) | (address_register << 15) | (0b010 << 12) | (value_register << 7) | 0b0000011)

    def append_bne(self, offset: int, register1: int, register2: int):
        """Branch to PC + offset if the value in register1 is not equal to the value in register2."""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/bne.html
        assert -4096 <= offset < 4096, "Offset must be between -4096 and 4095"
        assert offset & 1 == 0, "Offset must be even (2-byte aligned)"
        assert 0 <= register1 < 32, "Register1 must be between 0 and 31"
        assert 0 <= register2 < 32, "Register2 must be between 0 and 31"
        offset12 = (offset >> 12) & 0x1
        offset10_5 = (offset >> 5) & 0x3F
        offset4_1 = (offset >> 1) & 0xF
        offset11 = (offset >> 11) & 0x1
        self.append(
            (offset12 << 31)
            | (offset10_5 << 25)
            | (register2 << 20)
            | (register1 << 15)
            | (0b001 << 12)
            | (offset4_1 << 8)
            | (offset11 << 7)
            | 0b1100011
        )

    def append_jal(self, offset: int, return_register: int = 0):
        """Jump to a PC-relative offset and store the return address in return_register."""
        # https://riscv-software-src.github.io/riscv-unified-db/manual/html/isa/isa_20240411/insts/jal.html
        assert -1048576 <= offset < 1048576, "Offset must be between -1048576 and 1048575"
        assert 0 <= return_register < 32, "Return register must be between 0 and 31"
        offset20 = (offset >> 20) & 0x1
        offset10_1 = (offset >> 1) & 0x3FF
        offset11 = (offset >> 11) & 0x1
        offset19_12 = (offset >> 12) & 0xFF
        self.append(
            (offset20 << 31)
            | (offset10_1 << 21)
            | (offset11 << 20)
            | (offset19_12 << 12)
            | (return_register << 7)
            | (0b1101111)
        )

    def append_while_true(self):
        """Append an infinite loop (jal 0)."""
        self.append_jal(0)

    def append_load_constant_to_register(self, register: int, value: int):
        """Append instructions to load a constant value into a register."""
        assert 0 < register < 32, "Register must be between 1 and 31"
        assert 0 <= value < 2**32, "Value must be a 32-bit unsigned integer"
        if value < 0x800:
            # Use ADDI for small constants
            self.append_addi(register, 0, value)
        else:
            # Use LUI and ADDI for larger constants
            upper = value & 0xFFFFF000
            lower = value & 0xFFF
            if lower >= 0x800:
                upper += 0x1000  # Adjust upper if lower part is negative
                lower -= 0x1000
            self.append_lui(register, upper)
            if lower != 0:
                self.append_addi(register, register, lower)

    def append_load_word_from_memory_to_register(self, value_register: int, address: int, address_register: int):
        """Append instructions to load a word from memory into a register."""
        assert 0 < value_register < 32, "Value register must be between 1 and 31"
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert 0 <= address < 2**32, "Address must be a 32-bit unsigned integer"
        if address == 0:
            # Directly use address register as zero
            self.append_lw(value_register, 0, 0)
            return
        address_hi = address & 0xFFFFF000
        address_lo = address & 0xFFF
        if address_lo >= 0x800:
            address_lo -= 0x1000  # Adjust for negative offset
            address_hi = address_hi + 0x1000  # Adjust upper part
        self.append_lui(address_register, address_hi)
        self.append_lw(value_register, address_register, address_lo)

    def append_store_byte_to_memory_from_register(self, address_register: int = 10, data_register: int = 11):
        """Append instructions to store a byte to memory from registers."""
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        self.append_sb(data_register, address_register, 0)

    def append_store_byte_to_memory(
        self, address_constant: int, data_constant: int, address_register: int, data_register: int
    ):
        """Append instructions to store a byte to memory."""
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        assert 0 <= address_constant < 2**32, "Address constant must be a 32-bit unsigned integer"
        assert 0 <= data_constant < 2**8, "Data constant must be a 8-bit unsigned integer"
        self.append_load_constant_to_register(address_register, address_constant)
        self.append_load_constant_to_register(data_register, data_constant)
        self.append_store_byte_to_memory_from_register(address_register, data_register)

    def append_store_half_word_to_memory_from_register(self, address_register: int = 10, data_register: int = 11):
        """Append instructions to store a half word to memory from registers."""
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        self.append_sh(data_register, address_register, 0)

    def append_store_half_word_to_memory(
        self, address_constant: int, data_constant: int, address_register: int, data_register: int
    ):
        """Append instructions to store a half word to memory."""
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        assert 0 <= address_constant < 2**32, "Address constant must be a 32-bit unsigned integer"
        assert 0 <= data_constant < 2**16, "Data constant must be a 16-bit unsigned integer"
        self.append_load_constant_to_register(address_register, address_constant)
        self.append_load_constant_to_register(data_register, data_constant)
        self.append_store_half_word_to_memory_from_register(address_register, data_register)

    def append_store_word_to_memory_from_register(self, address_register: int = 10, data_register: int = 11):
        """Append instructions to store a word to memory from registers."""
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        self.append_sw(data_register, address_register, 0)

    def append_store_word_to_memory(
        self, address_constant: int, data_constant: int, address_register: int, data_register: int
    ):
        """Append instructions to store a word to memory."""
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert 0 <= data_register < 32, "Data register must be between 0 and 31"
        assert 0 <= address_constant < 2**32, "Address constant must be a 32-bit unsigned integer"
        assert 0 <= data_constant < 2**32, "Data constant must be a 32-bit unsigned integer"
        self.append_load_constant_to_register(address_register, address_constant)
        self.append_load_constant_to_register(data_register, data_constant)
        self.append_store_word_to_memory_from_register(address_register, data_register)

    def append_loop(self, loop_start_address: int):
        """Append instructions to create a loop back to loop_start_address."""
        self.append_jal(loop_start_address - self.current_address)
