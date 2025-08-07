# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import unittest
import time
from test.ttexalens.unit_tests.test_base import init_default_test_context
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from ttexalens import tt_exalens_lib as lib
from ttexalens.elf_loader import ElfLoader


class TestMulticore(unittest.TestCase):
    """Test class for multi-core scenarios."""

    def setUp(self):
        self.context = init_default_test_context()
        self.brisc = RiscvCoreSimulator(self.context, "FW0", "BRISC")
        self.trisc0 = RiscvCoreSimulator(self.context, "FW0", "TRISC0")

    def tearDown(self):
        for core in [self.brisc, self.trisc0]:
            core.set_reset(True)
            core.set_branch_prediction(True)

    def _write_program_sequence(self, core, instructions):
        """Helper to write a sequence of instructions."""
        for i, instruction in enumerate(instructions):
            core.write_program(i * 4, instruction)

    def _verify_core_states(self):
        """Helper to print and verify core states."""
        print("\nCore states:")
        self.brisc.get_pc_and_print()
        self.trisc0.get_pc_and_print()

    def test_mailbox_communication_lockup(self):
        """Test mailbox communication between BRISC and TRISC0 is locked up.

        BRISC Program (Reader):
        - Sets up mailbox read address in t0 (0xFFEC1000)
        - Initializes counter t3 to 0
        - Enters loop:
            - Increments counter
            - Reads from mailbox
            - Jumps back to increment

        TRISC0 Program (Writer):
        - Sets up mailbox write address in t0 (0xFFEC0000)
        - Initializes counter t3 to 0
        - Enters loop:
            - Increments counter
            - Shifts counter left by 20 to create delay
            - If shifted value is not 0, skips write
            - Writes counter to mailbox
            - Jumps back to increment
        """
        # Constants
        MAILBOX_READ_ADDR = 0xFFEC1000
        MAILBOX_WRITE_ADDR = 0xFFEC0000

        # Configure cores
        self.trisc0.set_branch_prediction(False)

        # Write BRISC program (Reader)
        brisc_program = [
            0xFFEC12B7,  # lui t0, 0xffec1 - Load upper immediate: t0 = 0xFFEC1000 (mailbox read address)
            0x00000E37,  # lui t3, 0x0    - Load upper immediate: t3 = 0 (initialize counter)
            0x001E0E13,  # addi t3, t3, 1 - Add immediate: t3 += 1 (increment counter)
            0x0002A303,  # lw t1, 0(t0)   - Load word: t1 = MEM[t0 + 0] (read from mailbox)
            ElfLoader.get_jump_to_offset_instruction(-8),  # Jump back 8 bytes (2 instructions) to addi
        ]
        self._write_program_sequence(self.brisc, brisc_program)

        # Write TRISC0 program (Writer)
        trisc0_program = [
            0xFFEC02B7,  # lui t0, 0xffec0 - Load upper immediate: t0 = 0xFFEC0000 (mailbox write address)
            0x00000E37,  # lui t3, 0x0     - Load upper immediate: t3 = 0 (initialize counter)
            0x001E0E13,  # addi t3, t3, 1  - Add immediate: t3 += 1 (increment counter)
            0x014E1313,  # slli t1, t3, 20 - Shift left logical immediate: t1 = t3 << 20 (delay write frequency)
            0xFE031CE3,  # bne t1, x0, -8  - Branch if not equal: if(t1 != 0) goto t0_loop (branch to addi)
            0x01C2A023,  # sw t3, 0(t0)    - Store word: MEM[t0 + 0] = t3 (write counter to mailbox)
            ElfLoader.get_jump_to_offset_instruction(-16),  # Jump and link: jump back to addi (loop)
        ]
        self._write_program_sequence(self.trisc0, trisc0_program)

        try:
            # Start execution
            self.brisc.set_reset(False)
            self.trisc0.set_reset(False)
            time.sleep(1)

            # Attempt to halt - should raise exception
            self.trisc0.halt()
            self.fail("Expected exception when halting locked core")

        except Exception as e:
            print(f"\nExpected exception occurred: {e}")
            self._verify_core_states()


class ProgramWriter:
    """Helper class to write programs to cores."""

    def __init__(self, start_address: int):
        self.start_address = start_address
        self.instructions = []

    @property
    def current_address(self) -> int:
        return self.start_address + len(self.instructions) * 4

    def append(self, instruction: int):
        self.instructions.append(instruction & 0xFFFFFFFF)  # Ensure instruction is 32 bits

    def write_program(self, core: RiscvCoreSimulator):
        for i, instruction in enumerate(self.instructions):
            core.write_program(i * 4, instruction)

    def append_ebreak(self):
        self.append(0x00100073)

    def append_lui(self, register: int, value: int):
        assert 0 < register < 32, "Register must be between 1 and 31"
        assert value & (0xFFF) == 0, "Lower 12 bits must be zero for LUI"
        self.append(value | (register << 7) | 0b0110111)

    def append_addi(self, destination_register: int, source_register: int, value: int):
        assert 0 < destination_register < 32, "Destination register must be between 1 and 31"
        assert 0 <= source_register < 32, "Source register must be between 0 and 31"
        assert -2048 <= value < 2048, "Immediate value must be between -2048 and 2047"
        value = value & 0xFFF  # Ensure value is 12 bits signed integer
        self.append((value << 20) | (source_register << 15) | (destination_register << 7) | 0b0010011)

    def append_sw(self, constant_register: int, address_register: int, offset: int):
        assert 0 <= constant_register < 32, "Constant register must be between 0 and 31"
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert -2048 <= offset < 2048, "Offset must be between -2048 and 2047"
        offset = offset & 0xFFF
        offset_hi = (offset >> 5) & 0x07F
        offset_low = offset & 0x01F
        self.append((offset_hi << 25) | (constant_register << 20) | (address_register << 15) | (0b010 << 12) | (offset_low << 7) | 0b0100011)

    def append_lw(self, value_register: int, address_register: int, offset: int):
        assert 0 <= value_register < 32, "Value register must be between 0 and 31"
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert -2048 <= offset < 2048, "Offset must be between -2048 and 2047"
        offset = offset & 0xFFF
        self.append((offset << 20) | (address_register << 15) | (0b010 << 12) | (value_register << 7) | 0b0000011)

    def append_bne(self, offset: int, register1: int, register2: int):
        assert -4096 <= offset < 4096, "Offset must be between -4096 and 4095"
        assert offset & 1 == 0, "Offset must be even (2-byte aligned)"
        assert 0 <= register1 < 32, "Register1 must be between 0 and 31"
        assert 0 <= register2 < 32, "Register2 must be between 0 and 31"
        offset12 = (offset >> 12) & 0x1
        offset10_5 = (offset >> 5) & 0x3F
        offset4_1 = (offset >> 1) & 0xF
        offset11 = (offset >> 11) & 0x1
        self.append((offset12 << 31) | (offset10_5 << 25) | (register2 << 20) | (register1 << 15) | (0b001 << 12) | (offset4_1 << 8) | (offset11 << 7) | 0b1100011)

    def append_jal(self, offset: int, return_register: int = 0):
        assert -1048576 <= offset < 1048576, "Offset must be between -1048576 and 1048575"
        assert 0 <= return_register < 32, "Return register must be between 0 and 31"
        offset20 = (offset >> 20) & 0x1
        offset10_1 = (offset >> 1) & 0x3FF
        offset11 = (offset >> 11) & 0x1
        offset19_12 = (offset >> 12) & 0xFF
        self.append((offset20 << 31) | (offset10_1 << 21) | (offset11 << 20) | (offset19_12 << 12) | (return_register << 7) | (0b1101111))

    def append_constant_to_register(self, register: int, value: int):
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

    def append_memory_to_register(self, value_register: int, address: int, address_register: int):
        assert 0 < value_register < 32, "Value register must be between 1 and 31"
        assert 0 <= address_register < 32, "Address register must be between 0 and 31"
        assert 0 <= address < 2**32, "Address must be a 32-bit unsigned integer"
        address_hi = address & 0xFFFFF000
        address_lo = address & 0xFFF
        if address_lo >= 0x800:
            address_lo -= 0x1000  # Adjust for negative offset
            address_hi = address_hi + 0x1000  # Adjust upper part
        self.append_lui(address_register, address_hi)
        self.append_lw(value_register, address_register, address_lo)

    # Blackhole NOC constants
    NOC_REG_SPACE_START_ADDR = 0xFF000000
    NOC_REGS_START_ADDR = 0xFFB20000
    NOC_CMD_BUF_OFFSET = 0x00000800
    NOC_CMD_BUF_OFFSET_BIT = 11
    NOC_INSTANCE_OFFSET = 0x00010000
    NOC_INSTANCE_OFFSET_BIT = 16

    NOC_CTRL_SEND_REQ = 0x1 << 0
    NOC_CTRL_STATUS_READY = 0x0

    NOC_TARG_ADDR_LO = NOC_REGS_START_ADDR + 0x0
    NOC_TARG_ADDR_MID = NOC_REGS_START_ADDR + 0x4
    NOC_TARG_ADDR_HI = NOC_REGS_START_ADDR + 0x8
    NOC_RET_ADDR_LO = NOC_REGS_START_ADDR + 0xC
    NOC_RET_ADDR_MID = NOC_REGS_START_ADDR + 0x10
    NOC_RET_ADDR_HI = NOC_REGS_START_ADDR + 0x14
    NOC_AT_LEN_BE = NOC_REGS_START_ADDR + 0x20
    NOC_AT_LEN_BE_1 = NOC_REGS_START_ADDR + 0x24
    NOC_CMD_CTRL = NOC_REGS_START_ADDR + 0x40

    NOC_ADDR_COORD_SHIFT = 36
    NOC_TARG_ADDR_COORDINATE = NOC_TARG_ADDR_HI
    NOC_RET_ADDR_COORDINATE = NOC_RET_ADDR_HI
    NOC_COORDINATE_MASK = 0xFFFFFF

    NIU_MST_RD_RESP_RECEIVED = 0x2

    MEM_NOC_ATOMIC_RET_VAL_ADDR = 4

    NOC_CMD_AT = (0x1 << 0)
    NOC_CMD_CPY = (0x0 << 0)
    NOC_CMD_RD = (0x0 << 1)
    NOC_CMD_WR = (0x1 << 1)
    NOC_CMD_WR_BE = (0x1 << 2)
    NOC_CMD_WR_INLINE = (0x1 << 3)
    NOC_CMD_RESP_MARKED = (0x1 << 4)
    NOC_CMD_BRCST_PACKET = (0x1 << 5)
    NOC_CMD_VC_LINKED = (0x1 << 6)
    NOC_CMD_VC_STATIC = (0x1 << 7)
    NOC_CMD_PATH_RESERVE = (0x1 << 8)
    NOC_CMD_MEM_RD_DROP_ACK = (0x1 << 9)
    #NOC_CMD_STATIC_VC(vc) (((uint32_t)(vc)) << 13)

    # Wormhole NOC constants
    #NOC_TARG_ADDR_COORDINATE = NOC_TARG_ADDR_MID

    def append_noc_cmd_buf_write_reg(self, noc: int, cmd_buf: int, addr: int, value: int, address_register: int = 10, constant_register: int = 11):
        assert noc in range(2), "NOC must be 0 or 1"
        assert cmd_buf in range(4), "Command buffer must be between 0 and 3"
        assert 0 <= addr < 2**32, "Address must be a 32-bit unsigned integer"
        assert address_register in range(32), "Address register must be between 0 and 31"
        assert constant_register in range(32), "Constant register must be between 0 and 31"
        if value == 0:
            constant_register = 0
        else:
            self.append_constant_to_register(constant_register, value)
        address = (cmd_buf << ProgramWriter.NOC_CMD_BUF_OFFSET_BIT) + (noc << ProgramWriter.NOC_INSTANCE_OFFSET_BIT) + addr
        address_hi = address & 0xFFFFF000
        address_lo = address & 0xFFF
        if address_lo >= 0x800:
            address_lo -= 0x1000  # Adjust for negative offset
            address_hi = address_hi + 0x1000  # Adjust upper part
        self.append_lui(address_register, address_hi)
        self.append_sw(constant_register, address_register, address_lo)

    def append_noc_fast_read(self, noc: int, cmd_buf: int, src_addr: int, dest_addr: int, len_bytes: int, address_register: int = 10, constant_register: int = 11):
        assert noc in range(2), "NOC must be 0 or 1"
        assert cmd_buf in range(4), "Command buffer must be between 0 and 3"
        assert 0 <= src_addr < 2**64, "Source address must be a 64-bit unsigned integer"
        assert 0 <= dest_addr < 2**32, "Destination address must be a 32-bit unsigned integer"
        assert 0 <= len_bytes < 2**32, "Length in bytes must be a 32-bit unsigned integer"
        assert address_register in range(32), "Address register must be between 0 and 31"
        assert constant_register in range(32), "Constant register must be between 0 and 31"
        # Maybe not needed to repeat in test
        self.append_noc_cmd_buf_write_reg(noc, cmd_buf, ProgramWriter.NOC_RET_ADDR_LO, dest_addr, address_register, constant_register)
        self.append_noc_cmd_buf_write_reg(noc, cmd_buf, ProgramWriter.NOC_TARG_ADDR_LO, src_addr & 0xFFFFFFFF, address_register, constant_register)
        self.append_noc_cmd_buf_write_reg(noc, cmd_buf, ProgramWriter.NOC_TARG_ADDR_MID, (src_addr >> 32) & 0x1000000F, address_register, constant_register)
        self.append_noc_cmd_buf_write_reg(noc, cmd_buf, ProgramWriter.NOC_TARG_ADDR_COORDINATE, (src_addr >> ProgramWriter.NOC_ADDR_COORD_SHIFT) & ProgramWriter.NOC_COORDINATE_MASK, address_register, constant_register)
        self.append_noc_cmd_buf_write_reg(noc, cmd_buf, ProgramWriter.NOC_AT_LEN_BE, len_bytes, address_register, constant_register)

        self.append_noc_cmd_buf_write_reg(noc, cmd_buf, ProgramWriter.NOC_CMD_CTRL, ProgramWriter.NOC_CTRL_SEND_REQ, address_register, constant_register)

    def append_noc_cmd_buf_read_reg(self, noc: int, cmd_buf: int, addr: int, address_register: int = 10, value_register: int = 11):
        assert noc in range(2), "NOC must be 0 or 1"
        assert cmd_buf in range(4), "Command buffer must be between 0 and 3"
        assert 0 <= addr < 2**32, "Address must be a 32-bit unsigned integer"
        assert address_register in range(32), "Address register must be between 0 and 31"
        assert value_register in range(32), "Value register must be between 0 and 31"
        address = (cmd_buf << ProgramWriter.NOC_CMD_BUF_OFFSET_BIT) + (noc << ProgramWriter.NOC_INSTANCE_OFFSET_BIT) + addr
        self.append_memory_to_register(value_register, address, address_register)

    def append_noc_status_read_reg(self, noc: int, reg_id: int, address_register: int = 10, value_register: int = 11):
        assert noc in range(2), "NOC must be 0 or 1"
        assert reg_id in range(32), "Register ID must be between 0 and 31"
        assert address_register in range(32), "Address register must be between 0 and 31"
        assert value_register in range(32), "Value register must be between 0 and 31"
        address = (noc << ProgramWriter.NOC_INSTANCE_OFFSET_BIT) + ProgramWriter.NOC_REGS_START_ADDR + 0x200 + ((reg_id) * 4)
        self.append_memory_to_register(value_register, address, address_register)

    def append_wait_noc_cmd_buf_ready(self, noc: int, cmd_buf: int, address_register: int = 10, constant_register: int = 11, check_register: int = 12):
        constant = ProgramWriter.NOC_CTRL_STATUS_READY
        if constant == 0:
            constant_register = 0 # Use zero register for constant
        else:
            self.append_constant_to_register(constant_register, constant)
        loop_address = self.current_address
        self.append_noc_cmd_buf_read_reg(noc, cmd_buf, ProgramWriter.NOC_CMD_CTRL, address_register, check_register)
        self.append_bne(loop_address - self.current_address, constant_register, check_register)

    def append_wait_noc_reads_received(self, noc: int, received: int, address_register: int = 10, constant_register: int = 11, check_register: int = 12):
        self.append_constant_to_register(constant_register, received)
        loop_address = self.current_address
        self.append_noc_status_read_reg(noc, ProgramWriter.NIU_MST_RD_RESP_RECEIVED, address_register, check_register)
        self.append_bne(loop_address - self.current_address, constant_register, check_register)

    def append_noc_init(self, noc_node_id: int, noc: int):
        atomic_ret_val = ProgramWriter.MEM_NOC_ATOMIC_RET_VAL_ADDR
        noc_id_reg = noc_node_id
        my_x = noc_id_reg & 0x3F
        my_y = (noc_id_reg >> 6) & 0x3F
        xy_local_addr = (my_x << ProgramWriter.NOC_ADDR_COORD_SHIFT) + (my_y << (ProgramWriter.NOC_ADDR_COORD_SHIFT + 6)) + 0

        # NOC_CMD_BUF_WRITE_REG(noc, NCRISC_WR_CMD_BUF, NOC_TARG_ADDR_MID, 0x0);
        # NOC_CMD_BUF_WRITE_REG(
        #     noc,
        #     NCRISC_WR_CMD_BUF,
        #     NOC_TARG_ADDR_COORDINATE,
        #     (uint32_t)(xy_local_addr >> NOC_ADDR_COORD_SHIFT) & NOC_COORDINATE_MASK);
        # NOC_CMD_BUF_WRITE_REG(noc, NCRISC_WR_REG_CMD_BUF, NOC_TARG_ADDR_MID, 0x0);
        # NOC_CMD_BUF_WRITE_REG(
        #     noc,
        #     NCRISC_WR_REG_CMD_BUF,
        #     NOC_TARG_ADDR_COORDINATE,
        #     (uint32_t)(xy_local_addr >> NOC_ADDR_COORD_SHIFT) & NOC_COORDINATE_MASK);

        # uint64_t atomic_ret_addr = NOC_XY_ADDR(my_x, my_y, atomic_ret_val);
        # NOC_CMD_BUF_WRITE_REG(noc, NCRISC_AT_CMD_BUF, NOC_RET_ADDR_LO, (uint32_t)(atomic_ret_addr & 0xFFFFFFFF));
        # NOC_CMD_BUF_WRITE_REG(noc, NCRISC_AT_CMD_BUF, NOC_RET_ADDR_MID, 0x0);
        # NOC_CMD_BUF_WRITE_REG(
        #     noc,
        #     NCRISC_AT_CMD_BUF,
        #     NOC_RET_ADDR_COORDINATE,
        #     (uint32_t)(atomic_ret_addr >> NOC_ADDR_COORD_SHIFT) & NOC_COORDINATE_MASK);

        noc_rd_cmd_field = ProgramWriter.NOC_CMD_CPY | ProgramWriter.NOC_CMD_RD | ProgramWriter.NOC_CMD_RESP_MARKED | ProgramWriter.NOC_CMD_VC_STATIC | (1 << 13)
        self.append_noc_cmd_buf_write_reg(noc, 0, ProgramWriter.NOC_CMD_CTRL, noc_rd_cmd_field)
        self.append_noc_cmd_buf_write_reg(noc, 0, ProgramWriter.NOC_RET_ADDR_MID, 0x0) # get rid of this?
        self.append_noc_cmd_buf_write_reg(noc, 0, ProgramWriter.NOC_RET_ADDR_COORDINATE, (xy_local_addr >> ProgramWriter.NOC_ADDR_COORD_SHIFT) & ProgramWriter.NOC_COORDINATE_MASK)


class TestMulticoreNoc(unittest.TestCase):
    """Test class for multi-core scenarios."""

    def setUp(self):
        self.context = init_default_test_context()
        self.device = self.context.devices[0]
        self.dram_location = self.device.get_block_locations("dram")[0]
        self.brisc = RiscvCoreSimulator(self.context, "FW0", "BRISC")
        self.trisc0 = RiscvCoreSimulator(self.context, "FW0", "TRISC0")

    def _create_simulator_and_prepare_for_dram_write(self, fw_index: int, noc_id: int, dram_address: int, l1_address: int, data_len: int):
        core_sim = RiscvCoreSimulator(self.context, f"FW{fw_index}", "NCRISC" if noc_id == 0 else "BRISC")
        source_noc_id = self.device.get_block(self.dram_location).get_register_store(noc_id).read_register("NOC_ID_LOGICAL")
        source_x = source_noc_id & 0x3f
        source_y = (source_noc_id >> 6) & 0x3f
        source_address = (source_x << 36) + (source_y << 42) + dram_address
        program_writer = ProgramWriter(core_sim.program_base_address)
        #program_writer.append_ebreak()
        program_writer.append_noc_init(core_sim.noc_block.get_register_store(noc_id).read_register("NOC_ID_LOGICAL"), noc_id)
        loop_address = program_writer.current_address
        program_writer.append_wait_noc_cmd_buf_ready(noc_id, 0)
        program_writer.append_noc_fast_read(noc_id, 0, source_address, l1_address, data_len)
        program_writer.append_jal(loop_address - program_writer.current_address)
        program_writer.write_program(core_sim)
        return core_sim

    def test_break_dram(self):
        input_words = [0xBEBACECA] * 512  # Example data to write
        input_bytes = bytearray()
        for word in input_words:
            input_bytes.extend(word.to_bytes(4, 'little'))

        input_words2 = [0xBEBAFAFA] * 512  # Example data to write
        input_bytes2 = bytearray()
        for word in input_words2:
            input_bytes2.extend(word.to_bytes(4, 'little'))

        clear_words = [0xBABADEDA] * 512  # Example data to write
        clear_bytes = bytearray()
        for word in clear_words:
            clear_bytes.extend(word.to_bytes(4, 'little'))

        dram_address1 = 0  # Example DRAM address to write to
        dram_address2 = 2048  # Example DRAM address to write to

        lib.write_to_device(self.dram_location, dram_address1, bytes(input_bytes), self.device._id, self.context)
        lib.write_to_device(self.dram_location, dram_address2, bytes(input_bytes2), self.device._id, self.context)

        for fw_index in range(len(self.device.get_block_locations("functional_workers"))):

            l1_address1 = 0x10000  # Example L1 address to read from
            l1_address2 = 0x10000 + 2048  # Example L1 address to read from
            core_sim1 = self._create_simulator_and_prepare_for_dram_write(fw_index, 0, dram_address1, l1_address1, len(input_bytes))
            core_sim2 = self._create_simulator_and_prepare_for_dram_write(fw_index, 1, dram_address2, l1_address2, len(input_bytes2))
            lib.write_to_device(core_sim1.core_loc, l1_address1, bytes(clear_bytes), self.device._id, self.context)
            lib.write_to_device(core_sim2.core_loc, l1_address2, bytes(clear_bytes), self.device._id, self.context)
            core_sim1.set_reset(False)
            core_sim2.set_reset(False)

            # l1_bytes = lib.read_from_device(core_sim1.core_loc, l1_address1, self.device._id, len(input_bytes), self.context)
            # self.assertEqual(l1_bytes, input_bytes, "Data read from L1 does not match written data")
            # l1_bytes = lib.read_from_device(core_sim2.core_loc, l1_address2, self.device._id, len(input_bytes2), self.context)
            # self.assertEqual(l1_bytes, input_bytes2, "Data read from L1 does not match written data")


    def test_dram_read(self):
        input_words = [0xBEBACECA] * 512  # Example data to write
        input_bytes = bytearray()
        for word in input_words:
            input_bytes.extend(word.to_bytes(4, 'little'))

        clear_words = [0xBABADEDA] * 512  # Example data to write
        clear_bytes = bytearray()
        for word in clear_words:
            clear_bytes.extend(word.to_bytes(4, 'little'))


        noc_id = 0
        dram_address = 0  # Example DRAM address to write to
        l1_address = 0x10000  # Example L1 address to read from
        # source_x: int = self.dram_location.to(f"noc{noc_id}")[0]
        # source_y: int = self.dram_location.to(f"noc{noc_id}")[1]
        source_noc_id = self.device.get_block(self.dram_location).get_register_store(noc_id).read_register("NOC_ID_LOGICAL")
        source_x = source_noc_id & 0x3f
        source_y = (source_noc_id >> 6) & 0x3f
        # source_x: int = self.dram_location.to(f"noc0")[0]
        # source_y: int = self.dram_location.to(f"noc0")[1]
        source_address = (source_x << 36) + (source_y << 42) + dram_address

        lib.write_to_device(self.dram_location, dram_address, bytes(input_bytes), self.device._id, self.context)
        lib.write_to_device(self.brisc.core_loc, l1_address, bytes(clear_bytes), self.device._id, self.context)

        l1_bytes = lib.read_from_device(self.brisc.core_loc, l1_address, self.device._id, len(clear_bytes), self.context)
        self.assertEqual(l1_bytes, clear_bytes, "Data read from L1 does not match written data")

        program_writer = ProgramWriter(self.brisc.program_base_address)
        #program_writer.append_ebreak()
        program_writer.append_noc_init(self.brisc.noc_block.get_register_store(noc_id).read_register("NOC_ID_LOGICAL"), noc_id)
        program_writer.append_wait_noc_cmd_buf_ready(noc_id, 0)
        program_writer.append_noc_fast_read(noc_id, 0, source_address, l1_address, len(input_bytes))
        program_writer.append_wait_noc_reads_received(noc_id, 1)
        program_writer.append_jal(0)
        program_writer.write_program(self.brisc)
        self.brisc.set_reset(False)

        #time.sleep(1)  # Allow time for the program to execute
        #print(self.brisc.get_pc_and_print())
        #self.assertEqual(self.brisc.get_pc_relative(), (len(program_writer.instructions) - 2) * 4)
        l1_bytes = lib.read_from_device(self.brisc.core_loc, l1_address, self.device._id, len(input_bytes), self.context)
        self.assertEqual(l1_bytes, input_bytes, "Data read from L1 does not match written data")


if __name__ == "__main__":
    unittest.main()
