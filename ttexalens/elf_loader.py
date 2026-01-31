# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens import util
from ttexalens.elf.parsed import ParsedElfFile
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.memory_access import MemoryAccess


class ElfLoader:
    """
    This class is used to load elf file to a RISC-V core.
    """

    def __init__(self, risc_debug: RiscDebug):
        self.risc_debug = risc_debug
        self.location = risc_debug.risc_location.location
        self.context = self.location.context
        self.mem_access = MemoryAccess.create(risc_debug)

    SECTIONS_TO_LOAD = [".init", ".text", ".ldm_data", ".gcov_info"]

    @staticmethod
    def get_jump_to_offset_instruction(offset: int, rd: int = 0) -> int:
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

    def write_block_through_debug(self, address, data):
        """
        Writes a block of data to a given address through the debug interface.
        """
        self.mem_access.write(address, data)

    def read_block_through_debug(self, address, byte_count):
        """
        Reads a block of data from a given address through the debug interface.
        """
        return self.mem_access.read(address, byte_count)

    @staticmethod
    def __inside_private_memory(memory_block: MemoryBlock | None, address: int) -> bool:
        if memory_block is None:
            return False
        if memory_block.address.private_address is None:
            return False
        return (
            memory_block.address.private_address <= address < memory_block.address.private_address + memory_block.size
        )

    def write_block(self, address, data: bytes):
        """
        Writes a block of bytes to a given address. Knows about the sections not accessible through NOC (0xFFB00000 or 0xFFC00000), and uses
        the debug interface to write them.
        """
        private_data_memory = self.risc_debug.get_data_private_memory()
        private_code_memory = self.risc_debug.get_code_private_memory()
        if (
            private_data_memory is not None
            and ElfLoader.__inside_private_memory(private_data_memory, address)
            and private_data_memory.address.noc_address is None
        ) or (
            private_code_memory is not None
            and ElfLoader.__inside_private_memory(private_code_memory, address)
            and private_code_memory.address.noc_address is None
        ):
            # Use debug interface
            self.write_block_through_debug(address, data)
        else:
            self.location.noc_write(address, data)

    def read_block(self, address, byte_count):
        """
        Reads a block of bytes from a given address. Knows about the sections not accessible through NOC (0xFFB00000 or 0xFFC00000), and uses
        the debug interface to read them.
        """
        private_data_memory = self.risc_debug.get_data_private_memory()
        private_code_memory = self.risc_debug.get_code_private_memory()
        if (
            private_data_memory is not None
            and ElfLoader.__inside_private_memory(private_data_memory, address)
            and private_data_memory.address.noc_address is None
        ) or (
            private_code_memory is not None
            and ElfLoader.__inside_private_memory(private_code_memory, address)
            and private_code_memory.address.noc_address is None
        ):
            # Use debug interface
            return self.read_block_through_debug(address, byte_count)
        else:
            return self.location.noc_read(address, byte_count)

    def remap_address(self, address: int, loader_data: int | None, loader_code: int | None):
        data_private_memory = self.risc_debug.get_data_private_memory()
        if ElfLoader.__inside_private_memory(data_private_memory, address):
            if loader_data is not None and isinstance(loader_data, int):
                assert data_private_memory is not None
                assert data_private_memory.address is not None
                assert data_private_memory.address.private_address is not None
                return address - data_private_memory.address.private_address + loader_data
            return address
        code_private_memory = self.risc_debug.get_code_private_memory()
        if ElfLoader.__inside_private_memory(code_private_memory, address):
            if loader_code is not None and isinstance(loader_code, int):
                assert code_private_memory is not None
                assert code_private_memory.address is not None
                assert code_private_memory.address.private_address is not None
                return address - code_private_memory.address.private_address + loader_code
            return address
        return address

    def load_elf_sections(
        self, elf: ParsedElfFile, loader_data: str | int, loader_code: str | int, verify_write: bool = True
    ):
        """
        Given an ELF file, this function loads the sections specified in SECTIONS_TO_LOAD to the
        memory of the RISC-V core. It also loads (into location 0) the jump instruction to the
        address of the .init section.
        """
        # Remember the .init section address to jump to after loading
        init_section_address = None
        elf_path = elf.elf_file_path

        try:
            address: int
            loader_data_address = loader_data if isinstance(loader_data, int) else None
            loader_code_address = loader_code if isinstance(loader_code, int) else None

            # Try to find address mapping for loader_data and loader_code
            for section in elf.sections:
                if section.name == loader_data:
                    loader_data_address = section.address
                elif section.name == loader_code:
                    loader_code_address = section.address

            # Load section into memory
            for section in elf.sections:
                if section.address is not None and section.name in self.SECTIONS_TO_LOAD and section.data:
                    if section.address % 4 != 0:
                        raise ValueError(
                            f"{elf_path}: section {section.name} (0x{section.address:08x}) is not 32-bit aligned"
                        )

                    address = self.remap_address(section.address, loader_data_address, loader_code_address)
                    if section.name == ".init":
                        init_section_address = address

                    util.VERBOSE(
                        f"Writing section {section.name} to address 0x{address:08x}. Size: {len(section.data)} bytes"
                    )
                    self.write_block(address, section.data)

                    # Check that what we have written is correct
                    if verify_write:
                        read_data = self.read_block(address, len(section.data))
                        if read_data != section.data:
                            util.ERROR(f"Error writing section {section.name} to address 0x{address:08x}.")
                            continue
                        else:
                            util.VERBOSE(
                                f"Section {section.name} loaded successfully to address 0x{address:08x}. Size: {len(section.data)} bytes"
                            )
        except Exception as e:
            util.ERROR(e)
            raise util.TTException(f"Error loading elf file {elf_path}")

        self.context.elf_loaded(self.risc_debug.risc_location, elf_path)
        return init_section_address

    def load_elf(
        self, elf_file: ParsedElfFile, verify_write: bool = True, return_start_address: bool = False
    ) -> int | None:
        # Risc must be in reset
        assert self.risc_debug.is_in_reset(), f"RISC at location {self.risc_debug.risc_location} is not in reset."

        # Load elf file to the L1 memory; avoid writing to private sections
        init_section_address: int | None = self.load_elf_sections(
            elf_file, loader_data=".loader_init", loader_code=".loader_code", verify_write=verify_write
        )
        assert init_section_address is not None, "No .init section found in the ELF file"

        if return_start_address:
            return init_section_address
        else:
            self.risc_debug.set_code_start_address(init_section_address)
            return None

    def run_elf(self, elf_file: ParsedElfFile, verify_write: bool = True):
        # Make sure risc is in reset
        if not self.risc_debug.is_in_reset():
            self.risc_debug.set_reset_signal(True)

        self.load_elf(elf_file, verify_write=verify_write)

        # Take risc out of reset
        self.risc_debug.set_reset_signal(False)
        assert not self.risc_debug.is_in_reset(), f"RISC at location {self.risc_debug.risc_location} is still in reset."
        if self.risc_debug.can_debug():
            assert (
                not self.risc_debug.is_halted() or self.risc_debug.is_ebreak_hit()
            ), f"RISC at location {self.risc_debug.risc_location} is still halted, but not because of ebreak."
