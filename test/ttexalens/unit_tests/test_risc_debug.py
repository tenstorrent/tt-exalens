# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class, parameterized

from ttexalens import tt_exalens_lib as lib
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.program_writer import RiscvProgramWriter
from ttexalens.context import Context
from ttexalens.hardware.baby_risc_debug import BabyRiscDebugWatchpointState, get_register_index
from ttexalens.elf_loader import ElfLoader


@parameterized_class(
    [
        {"core_desc": "ETH0", "risc_name": "ERISC", "neo_id": None},
        {"core_desc": "ETH0", "risc_name": "ERISC0", "neo_id": None},
        {"core_desc": "ETH0", "risc_name": "ERISC1", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "BRISC", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "BRISC", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "TRISC0", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "TRISC1", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "TRISC2", "neo_id": None},
        # {"core_desc": "DRAM0", "risc_name": "DRISC", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": 0},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": 0},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": 0},
        {"core_desc": "FW0", "risc_name": "TRISC3", "neo_id": 0},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": 1},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": 1},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": 1},
        {"core_desc": "FW0", "risc_name": "TRISC3", "neo_id": 1},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": 2},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": 2},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": 2},
        {"core_desc": "FW0", "risc_name": "TRISC3", "neo_id": 2},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": 3},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": 3},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": 3},
        {"core_desc": "FW0", "risc_name": "TRISC3", "neo_id": 3},
    ]
)
class TestDebugging(unittest.TestCase):
    risc_name: str  # Risc name
    neo_id: int | None  # NEO ID
    context: Context  # TTExaLens context
    core_desc: str  # Core description ETH0, FW0, FW1 - being parametrized
    core_sim: RiscvCoreSimulator  # RISC-V core simulator instance

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

    def setUp(self):
        try:
            self.core_sim = RiscvCoreSimulator(self.context, self.core_desc, self.risc_name, self.neo_id)
            self.program_writer = RiscvProgramWriter(self.core_sim)
        except ValueError as e:
            if self.risc_name.lower() in e.__str__().lower():
                self.skipTest(f"Core {self.risc_name} not available on this platform: {e}")
            elif "ETH core" in e.__str__() or "FW core" in e.__str__():
                self.skipTest(f"Core {self.core_desc}:{self.risc_name} not available on this platform: {e}")
            else:
                raise e
        except AssertionError as e:
            if self.neo_id is not None and "NEO ID" in e.__str__():
                self.skipTest(f"Test requires NEO ID, but is not supported on this platform: {e}")
            else:
                raise e

        # Stop risc with reset
        self.core_sim.set_reset(True)
        self.assertTrue(self.core_sim.is_in_reset())

    def tearDown(self):
        # Stop risc with reset
        self.core_sim.set_reset(True)
        self.assertTrue(self.core_sim.is_in_reset())

    def assertPcEquals(self, expected):
        """Assert PC register equals to expected value."""
        self.assertEqual(
            self.core_sim.get_pc(),
            self.core_sim.program_base_address + expected,
            f"Pc should be {expected} + program_base_addres ({self.core_sim.program_base_address + expected}).",
        )

    def assertPcLess(self, expected):
        """Assert PC register is less than expected value."""
        self.assertLess(
            self.core_sim.get_pc(),
            self.core_sim.program_base_address + expected,
            f"Pc should be less than {expected} + program_base_addres ({self.core_sim.program_base_address + expected}).",
        )

    def test_default_start_address(self):
        if self.device.is_quasar():
            self.skipTest("Skipping Quasar test since it lasts for 1 hour on simulator.")

        risc_info = self.core_sim.risc_debug.risc_info
        if risc_info.default_code_start_address is None:
            self.skipTest(
                "Default code start address doesn't exist for this RISC. Start address is always controlled by register."
            )

        # Fill L1 with 0x00100073 (ebreak)
        l1_start = risc_info.l1.address.noc_address
        assert l1_start is not None, "L1 address should not be None."
        word_bytes = 0x00100073.to_bytes(4, byteorder="little")
        bytes = word_bytes * (risc_info.l1.size // 4)
        lib.write_to_device(self.core_sim.location, l1_start, bytes, self.device._id, self.core_sim.context)

        # Take risc out of reset
        if risc_info.can_change_code_start_address:
            self.core_sim.risc_debug.set_code_start_address(None)
        self.core_sim.set_reset(False)

        # Verify that PC is what we expect
        # We take into account that ebreak instruction has completed and that the PC is now at the next instruction
        self.assertEqual(self.core_sim.get_pc() - 4, risc_info.default_code_start_address)
        self.core_sim.set_reset(True)

    def test_read_write_gpr(self):
        """Write then read value in all registers (except zero and pc)."""

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("nop");
        #   while (true);
        self.program_writer.append_nop()
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)
        self.assertFalse(self.core_sim.is_in_reset())

        # Halt core
        self.core_sim.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")

        # Test readonly registers
        self.assertEqual(self.core_sim.read_gpr(get_register_index("zero")), 0, "zero should always be 0.")
        self.assertPcEquals(4)

        # Test write then read for all other registers
        for i in range(1, 31):
            self.core_sim.write_gpr(i, 0x12345678)
            self.assertEqual(self.core_sim.read_gpr(i), 0x12345678, f"Register x{i} should be 0x12345678.")
            self.core_sim.write_gpr(i, 0x87654321)
            self.assertEqual(self.core_sim.read_gpr(i), 0x87654321, f"Register x{i} should be 0x87654321.")

    def test_read_write_l1_memory(self):
        """Testing read_memory and write_memory through debugging interface on L1 memory range."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   while (true);
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)
        self.assertFalse(self.core_sim.is_in_reset())

        # Halt core
        self.core_sim.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")

        # Test read and write memory
        self.assertEqual(self.core_sim.risc_debug.read_memory(addr), 0x12345678, "Memory value should be 0x12345678.")
        self.core_sim.risc_debug.write_memory(addr, 0x87654321)
        self.assertEqual(self.core_sim.risc_debug.read_memory(addr), 0x87654321, "Memory value should be 0x87654321.")
        self.assertEqual(self.core_sim.read_data(addr), 0x87654321)

    def test_read_write_private_memory(self):
        """Testing read_memory and write_memory through debugging interface on private core memory range."""
        data_private = self.core_sim.risc_debug.get_data_private_memory()
        self.assertIsNotNone(data_private, "Data private memory should not be None.")
        assert data_private is not None
        self.assertIsNotNone(data_private.address.private_address, "Private address should not be None.")
        assert data_private.address.private_address is not None

        addr = data_private.address.private_address
        noc_addr = data_private.address.noc_address

        # Write code for brisc core at address 0
        # C++:
        #   while (true);
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)
        self.assertFalse(self.core_sim.is_in_reset())

        # Halt core
        self.core_sim.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")

        # Test read if noc address exists
        if noc_addr is not None:
            self.core_sim.write_data_checked(noc_addr, 0xAABBCCDD)
            self.assertEqual(
                self.core_sim.risc_debug.read_memory(addr), 0xAABBCCDD, "Memory value should be 0xaabbccdd."
            )

        # Test write and read memory
        self.core_sim.risc_debug.write_memory(addr, 0x12345678)
        self.assertEqual(self.core_sim.risc_debug.read_memory(addr), 0x12345678, "Memory value should be 0x12345678.")
        if noc_addr is not None:
            self.assertEqual(
                self.core_sim.read_data(noc_addr), 0x12345678, "Memory value read over NOC should be 0x12345678."
            )
        self.core_sim.risc_debug.write_memory(addr, 0x87654321)
        self.assertEqual(self.core_sim.risc_debug.read_memory(addr), 0x87654321, "Memory value should be 0x87654321.")
        if noc_addr is not None:
            self.assertEqual(
                self.core_sim.read_data(noc_addr), 0x87654321, "Memory value read over NOC should be 0x87654321."
            )

    def test_read_write_memory_bytes_aligned(self):
        """Test reading and writing aligned memory blocks using read_memory_bytes and write_memory_bytes."""
        addr = 0x10000

        # Write initial data to memory
        self.core_sim.write_data_checked(addr, 0x11223344)
        self.core_sim.write_data_checked(addr + 4, 0x55667788)
        self.core_sim.write_data_checked(addr + 8, 0x99AABBCC)

        # Write code for brisc core at address 0
        # C++:
        #   while (true);
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)
        self.assertFalse(self.core_sim.is_in_reset())

        # Halt core
        self.core_sim.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")

        # Test reading initial data
        data = self.core_sim.risc_debug.read_memory_bytes(addr, 8)
        self.assertEqual(data, b"\x44\x33\x22\x11\x88\x77\x66\x55", "Should read initial 8 bytes")

        # Test writing new data
        self.core_sim.risc_debug.write_memory_bytes(addr, b"\x78\x56\x34\x12\xdd\xcc\xbb\xaa")

        # Test reading back what we wrote
        data = self.core_sim.risc_debug.read_memory_bytes(addr, 8)
        self.assertEqual(data, b"\x78\x56\x34\x12\xdd\xcc\xbb\xaa", "Should read/write 8 bytes correctly")
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertEqual(self.core_sim.read_data(addr + 4), 0xAABBCCDD)

        # Verify third word is unchanged
        self.assertEqual(self.core_sim.read_data(addr + 8), 0x99AABBCC, "Third word should be unchanged")

    @parameterized.expand(
        [
            # (offset, size, expected_read, write_data)
            # Aligned cases
            (0, 4, b"\x78\x56\x34\x12", b"\xAA\xBB\xCC\xDD"),
            (0, 8, b"\x78\x56\x34\x12\xdd\xcc\xbb\xaa", b"\x11\x22\x33\x44\x55\x66\x77\x88"),
            (4, 4, b"\xdd\xcc\xbb\xaa", b"\xEE\xFF\x00\x11"),
            # Single byte at each offset
            (0, 1, b"\x78", b"\xF0"),
            (1, 1, b"\x56", b"\xF1"),
            (2, 1, b"\x34", b"\xF2"),
            (3, 1, b"\x12", b"\xF3"),
            # Two bytes at each offset
            (0, 2, b"\x78\x56", b"\xE0\xE1"),
            (1, 2, b"\x56\x34", b"\xE2\xE3"),
            (2, 2, b"\x34\x12", b"\xE4\xE5"),
            (3, 2, b"\x12\xdd", b"\xE6\xE7"),
            # Three bytes at various offsets
            (0, 3, b"\x78\x56\x34", b"\xD0\xD1\xD2"),
            (1, 3, b"\x56\x34\x12", b"\xD3\xD4\xD5"),
            (2, 3, b"\x34\x12\xdd", b"\xD6\xD7\xD8"),
            (3, 3, b"\x12\xdd\xcc", b"\xD9\xDA\xDB"),
            # Four bytes unaligned (crosses boundary)
            (1, 4, b"\x56\x34\x12\xdd", b"\xC0\xC1\xC2\xC3"),
            (2, 4, b"\x34\x12\xdd\xcc", b"\xC4\xC5\xC6\xC7"),
            (3, 4, b"\x12\xdd\xcc\xbb", b"\xC8\xC9\xCA\xCB"),
            # Five bytes
            (0, 5, b"\x78\x56\x34\x12\xdd", b"\xB0\xB1\xB2\xB3\xB4"),
            (1, 5, b"\x56\x34\x12\xdd\xcc", b"\xB5\xB6\xB7\xB8\xB9"),
            (2, 5, b"\x34\x12\xdd\xcc\xbb", b"\xBA\xBB\xBC\xBD\xBE"),
            (3, 5, b"\x12\xdd\xcc\xbb\xaa", b"\xBF\xC0\xC1\xC2\xC3"),
            # Six bytes
            (0, 6, b"\x78\x56\x34\x12\xdd\xcc", b"\xA0\xA1\xA2\xA3\xA4\xA5"),
            (1, 6, b"\x56\x34\x12\xdd\xcc\xbb", b"\xA6\xA7\xA8\xA9\xAA\xAB"),
            (2, 6, b"\x34\x12\xdd\xcc\xbb\xaa", b"\xAC\xAD\xAE\xAF\xB0\xB1"),
            # Seven bytes
            (0, 7, b"\x78\x56\x34\x12\xdd\xcc\xbb", b"\x90\x91\x92\x93\x94\x95\x96"),
            (1, 7, b"\x56\x34\x12\xdd\xcc\xbb\xaa", b"\x97\x98\x99\x9A\x9B\x9C\x9D"),
        ]
    )
    def test_read_write_memory_bytes_unaligned(self, offset, size, expected_read, write_data):
        """Test reading and writing unaligned memory blocks (not on 4-byte boundary)."""
        addr = 0x10000

        # Initialize memory and halt
        self.core_sim.write_data_checked(addr, 0x12345678)
        self.core_sim.write_data_checked(addr + 4, 0xAABBCCDD)
        self.core_sim.write_data_checked(addr + 8, 0x99887766)
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)
        self.assertFalse(self.core_sim.is_in_reset())

        # Halt core
        self.core_sim.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")

        # Test unaligned read
        data = self.core_sim.risc_debug.read_memory_bytes(addr + offset, size)
        self.assertEqual(data, expected_read, f"Should read {size} bytes at offset {offset}")

        # Test unaligned write preserves surrounding data
        self.core_sim.write_data_checked(addr, [0x12345678, 0xAABBCCDD, 0x99887766])
        self.core_sim.risc_debug.write_memory_bytes(addr + offset, write_data)

        # Verify the write by reading back and comparing
        read_back = self.core_sim.risc_debug.read_memory_bytes(addr + offset, size)
        self.assertEqual(read_back, write_data, f"Read back data should match written data at offset {offset}")

        # Verify all three words to ensure proper boundary handling
        word0 = self.core_sim.read_data(addr)
        word1 = self.core_sim.read_data(addr + 4)
        word2 = self.core_sim.read_data(addr + 8)

        # Calculate expected words based on the write
        memory = bytearray()
        memory.extend((0x12345678).to_bytes(4, byteorder="little"))
        memory.extend((0xAABBCCDD).to_bytes(4, byteorder="little"))
        memory.extend((0x99887766).to_bytes(4, byteorder="little"))

        # Apply the write
        for i, byte in enumerate(write_data):
            memory[offset + i] = byte

        # Extract expected words
        expected_word0 = int.from_bytes(memory[0:4], byteorder="little")
        expected_word1 = int.from_bytes(memory[4:8], byteorder="little")
        expected_word2 = int.from_bytes(memory[8:12], byteorder="little")

        self.assertEqual(
            word0, expected_word0, f"Word 0 should be correct after writing {len(write_data)} bytes at offset {offset}"
        )
        self.assertEqual(
            word1, expected_word1, f"Word 1 should be correct after writing {len(write_data)} bytes at offset {offset}"
        )
        self.assertEqual(
            word2,
            expected_word2,
            f"Word 2 should be preserved after writing {len(write_data)} bytes at offset {offset}",
        )

    def test_minimal_run_generated_code(self):
        """Test running 16 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)
        self.assertFalse(self.core_sim.is_in_reset())

        # Since simulator is slow, we need to wait a bit by reading something
        if self.device.is_quasar():
            for i in range(50):
                if self.core_sim.read_data(addr) == 0x87654000:
                    break

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)

    def test_ebreak(self):
        """Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address, value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertPcEquals(4)

    def test_ebreak_and_step(self):
        """Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        self.core_sim.set_reset(False)

        # On blackhole, we need to step one more time...

        # Verify value at address, value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertPcEquals(4)
        # Step and verify that pc is 8 and value is not changed
        self.core_sim.step()
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertPcEquals(8)
        # Adding two steps since logic in hw automatically updates register and memory values
        self.core_sim.step()
        self.core_sim.step()
        # Verify that pc is 16 and value has changed
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)
        self.assertPcEquals(16)
        # Since we are on endless loop, we should never go past 16
        for i in range(10):
            # Step and verify that pc is 16 and value has changed
            self.core_sim.step()
            self.assertPcEquals(16)

    def test_continue(self):
        """Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Continue
        self.core_sim.continue_execution()

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)

    def test_core_lockup(self):
        """Running code that should lock up the core and then trying to halt it."""
        if not self.device.is_wormhole():
            self.skipTest("Issue is hit only on wormhole.")

        # Write code for brisc core at address 0
        # C++:
        #    for (int i = 0; ; i++) {
        #        int* a = (int*)0x0;
        #        int* b = (int*)0x0;
        #        c = *a;
        #        d = *b;
        #    }
        self.program_writer.append_load_constant_to_register(28, 0)
        b_loop_address = self.program_writer.current_address
        self.program_writer.append_load_word_from_memory_to_register(6, 0, 0)
        self.program_writer.append_load_word_from_memory_to_register(7, 0, 0)
        self.program_writer.append_addi(28, 28, 1)
        self.program_writer.append_loop(b_loop_address)
        self.program_writer.write_program()

        self.core_sim.set_reset(False)
        iteration = 0
        while True:
            try:
                self.core_sim.halt()
                self.core_sim.continue_execution(enable_debug=False)
                iteration = iteration + 1
                if iteration > 1000:
                    break
            except Exception as e:
                # print pc
                self.core_sim.set_reset(True)
                return

        self.assertFalse(True, "Exception not raised")
        self.core_sim.set_reset(True)

    def test_halt_continue(self):
        """Test running 28 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true)
        #     *a++;
        self.program_writer.append_ebreak()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        loop_address = self.program_writer.current_address
        self.program_writer.append_addi(11, 11, 1)  # Increment x11 by 1
        self.program_writer.append_store_word_to_memory_from_register(10, 11)  # Store x11 to address in x10
        self.program_writer.append_loop(loop_address)
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify that value didn't change cause of ebreak
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)

        # Continue
        self.core_sim.continue_execution()

        # Verify that value changed cause of continue
        previous_value = self.core_sim.read_data(addr)
        self.assertGreaterEqual(previous_value, 0x87654000)

        # Loop halt and continue
        for i in range(10):
            # Halt
            self.core_sim.halt()

            # Read value
            value = self.core_sim.read_data(addr)
            self.assertGreater(value, previous_value)
            previous_value = value

            # Second read should have the same value if core is halted
            self.assertEqual(self.core_sim.read_data(addr), previous_value)

            # Continue
            self.core_sim.continue_execution()

    def test_halt_status(self):
        """Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")

        # Continue
        self.core_sim.continue_execution()

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)
        self.assertFalse(self.core_sim.is_halted(), "Core should not be halted.")

        # Halt and test status
        self.core_sim.halt()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.is_ebreak_hit(), "ebreak should not be the cause.")

    def test_invalidate_cache(self):
        if self.core_sim.is_eth_block():
            self.skipTest("This test is not applicable for ETH cores.")

        """Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write endless loop for brisc core at address 0
        # C++:
        #   while (true);
        #   while (true);
        #   while (true);
        #   while (true);
        self.program_writer.append_while_true()
        self.program_writer.append_while_true()
        self.program_writer.append_while_true()
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Halt core
        self.core_sim.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertPcEquals(0)

        # Write new code for brisc core at address 0
        # C++:
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer = RiscvProgramWriter(self.core_sim)
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Invalidate instruction cache
        self.core_sim.invalidate_instruction_cache()

        # Continue
        self.core_sim.continue_execution()
        self.assertFalse(self.core_sim.is_halted(), "Core should not be halted.")

        # Halt to verify PC
        self.core_sim.halt()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")

        # There is hardware bug on blackhole that causes PC to be 0, but we added a fix to read pc using debug bus
        self.assertPcEquals(12)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)

    def test_invalidate_cache_with_reset(self):
        """Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation by reseting core. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write endless loop for brisc core at address 0
        # C++:
        #   while (true);
        #   while (true);
        #   while (true);
        #   while (true);
        self.program_writer.append_while_true()
        self.program_writer.append_while_true()
        self.program_writer.append_while_true()
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Halt core
        self.core_sim.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertPcEquals(0)

        # Write new code for brisc core at address 0
        # C++:
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer = RiscvProgramWriter(self.core_sim)
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Invalidate instruction cache with reset
        self.core_sim.set_reset(True)
        self.core_sim.set_reset(False)
        self.assertFalse(self.core_sim.is_halted(), "Core should not be halted.")

        # Halt to verify PC
        self.core_sim.halt()
        self.assertTrue(self.core_sim.is_halted(), "Core should not be halted.")
        self.assertPcEquals(12)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)

    def test_invalidate_cache_with_nops_and_long_jump(self):
        """Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation by having NOPs block and jump back. All that is done on brisc."""

        if self.core_sim.is_eth_block() and self.device.is_wormhole():
            self.skipTest("This test is not applicable for ETH cores.")
        if (self.device.is_wormhole() or self.device.is_blackhole()) and self.core_sim.risc_name == "TRISC2":
            self.skipTest("This test is unreliable on TRISC2 on wormhole or blackhole.")

        break_addr = 0x950
        jump_addr = 0x2000
        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write endless loop for brisc core at address 0
        # C++:
        #  start:
        #   asm volatile ("nop");
        #   ...
        #   asm volatile ("nop");
        #  break_addr:
        #   asm volatile ("ebreak");
        #   asm volatile ("nop");
        #   ...
        #   asm volatile ("nop");
        #  jump_addr:
        #   goto start;
        self.core_sim.write_program(0, [0x00000013] * (jump_addr // 4))
        self.core_sim.write_program(break_addr, 0x00100073)
        self.core_sim.write_program(jump_addr, ElfLoader.get_jump_to_offset_instruction(-jump_addr))

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Since simulator is slow, we need to wait a bit by reading something
        if self.device.is_quasar():
            for i in range(50):
                self.core_sim.read_data(0)

        # Value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertPcEquals(break_addr + 4)

        # Write new code for brisc core at address 0
        # C++:
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Continue execution
        self.core_sim.continue_execution()
        self.assertFalse(self.core_sim.is_halted(), "Core should not be halted.")

        # Since simulator is slow, we need to wait a bit by reading something
        if self.device.is_quasar():
            for i in range(200):
                if self.core_sim.read_data(addr) == 0x87654000:
                    break

        # Halt to verify PC
        self.core_sim.halt()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertPcEquals(12)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)

    # Wrapper for setting watchpoints on different types of watchpoints.
    def _set_watchpoint(self, watchpoint_type: str, watchpoint_index: int, address: int):
        match watchpoint_type:
            case "pc":
                self.core_sim.debug_hardware.set_watchpoint_on_pc_address(watchpoint_index, address)
            case "access":
                self.core_sim.debug_hardware.set_watchpoint_on_memory_access(watchpoint_index, address)
            case "read":
                self.core_sim.debug_hardware.set_watchpoint_on_memory_read(watchpoint_index, address)
            case "write":
                self.core_sim.debug_hardware.set_watchpoint_on_memory_write(watchpoint_index, address)
            case _:
                raise ValueError(f"Invalid watchpoint type: {watchpoint_type}")

    def test_watchpoint_on_pc_address(self):
        """Test running 36 bytes of generated code that just write data on memory and does watchpoint on pc address. All that is done on brisc."""

        if self.core_sim.is_eth_block() and self.device.is_wormhole():
            self.skipTest("This test ND fails in CI. Issue: #770")

        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   asm volatile ("nop");
        #   asm volatile ("nop");
        #   asm volatile ("nop");
        #   asm volatile ("nop");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_nop()
        self.program_writer.append_nop()
        self.program_writer.append_nop()
        self.program_writer.append_nop()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertPcEquals(4)

        # Set watchpoint on address 12 and 32
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(0, self.core_sim.program_base_address + 12)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(1, self.core_sim.program_base_address + 32)

        # Continue and verify that we hit first watchpoint
        self.core_sim.continue_execution()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.is_ebreak_hit(), "ebreak should not be the cause.")
        self.assertTrue(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should be the cause.")
        self.assertFalse(
            self.core_sim.read_status().is_memory_watchpoint_hit, "Memory watchpoint should not be the cause."
        )
        self.assertTrue(self.core_sim.read_status().watchpoints_hit[0], "Watchpoint 0 should be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[1], "Watchpoint 1 should not be hit.")

        self.assertPcLess(28)
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)

        # Continue and verify that we hit first watchpoint
        self.core_sim.continue_execution()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.is_ebreak_hit(), "ebreak should not be the cause.")
        self.assertTrue(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should be the cause.")
        self.assertFalse(
            self.core_sim.read_status().is_memory_watchpoint_hit, "Memory watchpoint should not be the cause."
        )
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[0], "Watchpoint 0 should not be hit.")
        self.assertTrue(self.core_sim.read_status().watchpoints_hit[1], "Watchpoint 1 should be hit.")
        self.assertPcEquals(32)
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)

    def test_watchpoint_address(self):
        """Test setting and reading watchpoint address (both memory and PC)."""

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify that we hit ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

        addresses_to_set = [12, 32, 0x1234, 0x8654, 0x87654321, 0x12345678, 0, 0xFFFFFFFF]

        # Set PC watchpoints
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.core_sim.debug_hardware.set_watchpoint_on_pc_address(i, addresses_to_set[i])

        # Read PC watchpoints addresses and verify it is the same as we set
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.assertEqual(
                self.core_sim.debug_hardware.read_watchpoint_address(i),
                addresses_to_set[i],
                f"Address should be {addresses_to_set[i]}.",
            )

        # Set memory watchpoints for access
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.core_sim.debug_hardware.set_watchpoint_on_memory_access(i, addresses_to_set[i])

        # Read memory watchpoints addresses and verify it is the same as we set
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.assertEqual(
                self.core_sim.debug_hardware.read_watchpoint_address(i),
                addresses_to_set[i],
                f"Address should be {addresses_to_set[i]}.",
            )

        # Set memory watchpoints for read
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.core_sim.debug_hardware.set_watchpoint_on_memory_read(i, addresses_to_set[i])

        # Read memory watchpoints addresses and verify it is the same as we set
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.assertEqual(
                self.core_sim.debug_hardware.read_watchpoint_address(i),
                addresses_to_set[i],
                f"Address should be {addresses_to_set[i]}.",
            )

        # Set memory watchpoints for write
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.core_sim.debug_hardware.set_watchpoint_on_memory_write(i, addresses_to_set[i])

        # Read memory watchpoints addresses and verify it is the same as we set
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.assertEqual(
                self.core_sim.debug_hardware.read_watchpoint_address(i),
                addresses_to_set[i],
                f"Address should be {addresses_to_set[i]}.",
            )

        # Set mixed watchpoins
        watchpoint_types = ["pc", "pc", "access", "access", "read", "read", "write", "write"]
        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self._set_watchpoint(watchpoint_types[i], i, addresses_to_set[i])

        for i in range(self.core_sim.risc_debug.risc_info.max_watchpoints):
            self.assertEqual(
                self.core_sim.debug_hardware.read_watchpoint_address(i),
                addresses_to_set[i],
                f"Address should be {addresses_to_set[i]}.",
            )

    def test_watchpoint_state(self):
        """Test setting and disabling watchpoint state (both memory and PC)."""

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify that we hit ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        addresses_to_set = [12, 32, 0x1234, 0x8654, 0x87654321, 0x12345678, 0, 0xFFFFFFFF]
        watchpoint_types = ["pc", "pc", "access", "access", "read", "read", "write", "write"]

        # Set watchpoints
        for i in range(len(watchpoint_types)):
            if i >= self.core_sim.risc_debug.risc_info.max_watchpoints:
                break
            self._set_watchpoint(watchpoint_types[i], i, addresses_to_set[i])

        def check_watchpoint_state(
            state: BabyRiscDebugWatchpointState, watchpoint_index: int, watchpoint_type: str
        ) -> None:
            match watchpoint_type:
                case "pc":
                    self.assertTrue(state.is_enabled, f"Watchpoint {watchpoint_index} should not be enabled.")
                    self.assertFalse(state.is_memory, f"Watchpoint {watchpoint_index} should not be memory watchpoint.")
                    self.assertFalse(state.is_read, f"Watchpoint {watchpoint_index} should not watch for reads.")
                    self.assertFalse(state.is_write, f"Watchpoint {watchpoint_index} should not watch for writes.")
                case "access":
                    self.assertTrue(state.is_enabled, f"Watchpoint {watchpoint_index} should be enabled.")
                    self.assertTrue(state.is_memory, f"Watchpoint {watchpoint_index} should be memory watchpoint.")
                    self.assertTrue(state.is_read, f"Watchpoint {watchpoint_index} should watch for reads.")
                    self.assertTrue(state.is_write, f"Watchpoint {watchpoint_index} should watch for writes.")
                case "read":
                    self.assertTrue(state.is_enabled, f"Watchpoint {watchpoint_index} should be enabled.")
                    self.assertTrue(state.is_memory, f"Watchpoint {watchpoint_index} should be memory watchpoint.")
                    self.assertTrue(state.is_read, f"Watchpoint {watchpoint_index} should not watch for reads.")
                    self.assertFalse(state.is_write, f"Watchpoint {watchpoint_index} should not watch for writes.")
                case "write":
                    self.assertTrue(state.is_enabled, f"Watchpoint {watchpoint_index} should be enabled.")
                    self.assertTrue(state.is_memory, f"Watchpoint {watchpoint_index} should be memory watchpoint.")
                    self.assertFalse(state.is_read, f"Watchpoint {watchpoint_index} should not watch for reads.")
                    self.assertTrue(state.is_write, f"Watchpoint {watchpoint_index} should watch for writes.")

        # Read watchpoints state and verify it is the same as we set
        state = self.core_sim.debug_hardware.read_watchpoints_state()
        for i in range(len(watchpoint_types)):
            if i >= self.core_sim.risc_debug.risc_info.max_watchpoints:
                break
            check_watchpoint_state(state[i], i, watchpoint_types[i])

        # Disable some watchpoints
        watchpoints_to_disable = [0, 3, 4, 6]
        for watchpoint_index in watchpoints_to_disable:
            if watchpoint_index >= self.core_sim.risc_debug.risc_info.max_watchpoints:
                break
            self.core_sim.debug_hardware.disable_watchpoint(watchpoint_index)

        # Read watchpoints state and verify that we disabled some of the and rest have the same state as we set before
        state = self.core_sim.debug_hardware.read_watchpoints_state()

        for i in range(len(watchpoint_types)):
            if i >= self.core_sim.risc_debug.risc_info.max_watchpoints:
                break
            if i in watchpoints_to_disable:
                self.assertFalse(state[i].is_enabled, f"Watchpoint {i} should not be enabled.")
                self.assertFalse(state[i].is_memory, f"Watchpoint {i} should not be memory watchpoint.")
                self.assertFalse(state[i].is_read, f"Watchpoint {i} should not watch for reads.")
                self.assertFalse(state[i].is_write, f"Watchpoint {i} should not watch for writes.")
            else:
                check_watchpoint_state(state[i], i, watchpoint_types[i])

    def test_memory_watchpoint(self):
        """Test running 64 bytes of generated code that just write data on memory and tests memory watchpoints. All that is done on brisc."""

        addresses = [0x10000, 0x20000, 0x30000, 0x40000]

        value = 0x12345678
        # Write our data to memory
        self.core_sim.write_data_checked(addresses[0], value)
        self.core_sim.write_data_checked(addresses[1], value)
        self.core_sim.write_data_checked(addresses[2], value)
        self.core_sim.write_data_checked(addresses[3], value)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   asm volatile ("nop");
        #   asm volatile ("nop");
        #   asm volatile ("nop");
        #   asm volatile ("nop");
        #   int* a = (int*)0x10000;
        #   *a = 0x45678000;
        #   int* c = (int*)0x20000;
        #   int d = *c;
        #   int* c = (int*)0x30000;
        #   *c = 0x87654000;
        #   c = (int*)0x40000;
        #   d = *c;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_nop()
        self.program_writer.append_nop()
        self.program_writer.append_nop()
        self.program_writer.append_nop()
        self.program_writer.append_store_word_to_memory(addresses[0], 0x45678000, 10, 11)  # First write
        self.program_writer.append_load_word_from_memory_to_register(12, addresses[1], 10)  # First read
        self.program_writer.append_store_word_to_memory(addresses[2], 0x87654000, 10, 11)  # Second write
        self.program_writer.append_load_word_from_memory_to_register(12, addresses[3], 10)  # Second read
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addresses[0]), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

        watchpoint_types = ["write", "read", "access", "access"]

        # Set watchpoints
        for i in range(len(watchpoint_types)):
            if i >= self.core_sim.risc_debug.risc_info.max_watchpoints:
                break
            self._set_watchpoint(watchpoint_types[i], i, addresses[i])

        # Verify that we hit the correct watchpoints
        for i in range(len(watchpoint_types)):
            if i >= self.core_sim.risc_debug.risc_info.max_watchpoints:
                break
            self.core_sim.continue_execution()
            self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
            self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
            self.assertTrue(
                self.core_sim.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause."
            )
            self.assertTrue(self.core_sim.read_status().watchpoints_hit[i], f"Watchpoint {i} should be hit.")
            for j in range(len(watchpoint_types)):
                if j >= self.core_sim.risc_debug.risc_info.max_watchpoints:
                    break
                if j == i:
                    continue
                self.assertFalse(self.core_sim.read_status().watchpoints_hit[j], f"Watchpoint {j} should not be hit.")

            if i == 0:
                self.assertEqual(self.core_sim.read_data(addresses[i]), 0x45678000)
            elif i == 2:
                self.assertEqual(self.core_sim.read_data(addresses[i]), 0x87654000)

    def test_bne_with_debug_fail(self):
        """Test running 48 bytes of generated code that confirms problem with BNE when debugging hardware is enabled."""

        if self.core_sim.is_eth_block():
            self.skipTest("We don't know how to enable/disable branch prediction ETH cores.")

        if self.device.is_blackhole():
            self.skipTest("BNE instruction with debug hardware enabled is fixed in blackhole.")

        if self.device.is_quasar():
            self.skipTest("BNE instruction with debug hardware enabled is fixed in quasar.")

        # Enable branch prediction
        self.core_sim.set_branch_prediction(True)

        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   for (int i = 0; i < 64; i++);
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_load_constant_to_register(1, 0)  # x1 = 0
        self.program_writer.append_load_constant_to_register(2, 63)  # x2 = 63
        loop_address = self.program_writer.current_address
        self.program_writer.append_bne(8, 1, 2)  # Skip this and next instruction if x1 != x2
        self.program_writer.append_jal(12)  # Skip 3 instructions and goto ebreak
        self.program_writer.append_addi(1, 1, 1)  # x1 = x1 + 1
        self.program_writer.append_loop(loop_address)
        self.program_writer.append_ebreak()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")

        # Continue to proceed with bne test
        self.core_sim.debug_hardware.cont()  # We need to use debug hardware as there is a bug fix in risc debug implementation for wormhole

        # Confirm failure
        self.assertFalse(self.core_sim.is_halted(), "Core should not be halted.")
        self.core_sim.halt()
        x1 = self.core_sim.read_gpr(1)  # x1 is counter and it should never go over x2
        x2 = self.core_sim.read_gpr(2)  # x2 is value for loop end
        self.assertGreater(x1, x2)  # Bug will prevent BNE to stop the loop, so x1 will be greater than x2
        self.assertEqual(
            self.core_sim.read_data(addr), 0x12345678
        )  # Value shouldn't be changed since we never reached the store instruction

    def test_bne_without_debug(self):
        """Test running 48 bytes of generated code that confirms that there is no problem with BNE when debugging hardware is disabled."""

        if self.core_sim.is_eth_block():
            self.skipTest("We don't know how to enable/disable branch prediction ETH cores.")

        # Enable branch prediction
        self.core_sim.set_branch_prediction(True)

        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   for (int i = 0; i < 64; i++);
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_load_constant_to_register(1, 0)  # x1 = 0
        self.program_writer.append_load_constant_to_register(2, 63)  # x2 = 63
        loop_address = self.program_writer.current_address
        self.program_writer.append_bne(8, 1, 2)  # Skip this and next instruction if x1 != x2
        self.program_writer.append_jal(12)  # Skip 3 instructions and goto ebreak
        self.program_writer.append_addi(1, 1, 1)  # x1 = x1 + 1
        self.program_writer.append_loop(loop_address)
        self.program_writer.append_ebreak()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")

        # Continue to proceed with bne test
        self.core_sim.debug_hardware.continue_without_debug()  # We need to use debug hardware as there is a bug fix in risc debug implementation for wormhole

        # Since simulator is slow, we need to wait a bit by reading something
        if self.device.is_quasar():
            for i in range(20):
                self.core_sim.read_data(0)

        # We should pass for loop very fast and should be halted here already
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")

        # Verify value at address
        self.core_sim.debug_hardware.cont()  # We need to use debug hardware as there is a bug fix in risc debug implementation for wormhole
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)
        self.assertFalse(self.core_sim.is_halted(), "Core should not be halted.")

        # Halt and test status
        self.core_sim.halt()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.is_ebreak_hit(), "ebreak should not be the cause.")

    def test_bne_with_debug_without_bp(self):
        """Test running 48 bytes of generated code that confirms that there is no problem with BNE when debugging hardware is enabled and branch prediction is disabled."""

        if self.core_sim.is_eth_block():
            self.skipTest("We don't know how to enable/disable branch prediction ETH cores.")

        # Enable branch prediction
        self.core_sim.set_branch_prediction(True)

        addr = 0x10000

        # Write our data to memory
        self.core_sim.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   for (int i = 0; i < 64; i++);
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);
        self.program_writer.append_ebreak()
        self.program_writer.append_load_constant_to_register(1, 0)  # x1 = 0
        self.program_writer.append_load_constant_to_register(2, 63)  # x2 = 63
        loop_address = self.program_writer.current_address
        self.program_writer.append_bne(8, 1, 2)  # Skip this and next instruction if x1 != x2
        self.program_writer.append_jal(12)  # Skip 3 instructions and goto ebreak
        self.program_writer.append_addi(1, 1, 1)  # x1 = x1 + 1
        self.program_writer.append_loop(loop_address)
        self.program_writer.append_ebreak()
        self.program_writer.append_store_word_to_memory(
            0x10000, 0x87654000, 10, 11
        )  # Load address into x10, data into x11, store word
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")

        # Disable branch prediction
        if not self.device.is_blackhole():
            # Disabling branch prediction fails this test on blackhole :(
            self.core_sim.set_branch_prediction(False)

        # Continue to proceed with bne test
        self.core_sim.debug_hardware.cont()  # We need to use debug hardware as there is a bug fix in risc debug implementation for wormhole

        # Since simulator is slow, we need to wait a bit by reading something
        if self.device.is_quasar():
            for i in range(20):
                self.core_sim.read_data(0)

        # We should pass for loop very fast and should be halted here already
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")

        # Verify value at address
        self.core_sim.debug_hardware.cont()  # We need to use debug hardware as there is a bug fix in risc debug implementation for wormhole
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)
        self.assertFalse(self.core_sim.is_halted(), "Core should not be halted.")

        # Halt and test status
        self.core_sim.halt()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.is_ebreak_hit(), "ebreak should not be the cause.")
