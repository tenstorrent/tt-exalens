# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class

from ttexalens import tt_exalens_lib as lib
from test.ttexalens.unit_tests.test_base import init_default_test_context
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from ttexalens.context import Context
from ttexalens.hardware.baby_risc_debug import get_register_index
from ttexalens.elf_loader import ElfLoader


@parameterized_class(
    [
        # {"core_desc": "ETH0", "risc_name": "ERISC", "neo_id": None},
        # {"core_desc": "ETH0", "risc_name": "ERISC0", "neo_id": None},
        # {"core_desc": "ETH0", "risc_name": "ERISC1", "neo_id": None},
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
        cls.context = init_default_test_context()

    def setUp(self):
        try:
            self.core_sim = RiscvCoreSimulator(self.context, self.core_desc, self.risc_name, self.neo_id)
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

        self.device = self.context.devices[0]

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
        if self.core_sim.is_quasar():
            self.skipTest("Skipping Quasar test since it lasts for 1 hour on simulator.")

        risc_info = self.core_sim.risc_debug.risc_info

        if risc_info.default_code_start_address is None:
            self.skipTest(
                "Default code start address doesn't exist for this RISC. Start address is always controlled by register."
            )
        if self.core_sim.is_eth_block():
            self.skipTest("Skipping ETH test since UMD doesn't support destroying ETH L1 memory.")

        # Fill L1 with 0x00100073 (ebreak)
        l1_start = risc_info.l1.address.noc_address
        assert l1_start is not None, "L1 address should not be None."
        word_bytes = 0x00100073.to_bytes(4, byteorder="little")
        bytes = word_bytes * (risc_info.l1.size // 4)
        lib.write_to_device(self.core_sim.location, l1_start, bytes, self.core_sim.device._id, self.core_sim.context)

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

        # NOP
        self.core_sim.write_program(0, 0x00000013)
        # Infinite loop (jal 0)
        self.core_sim.write_program(4, ElfLoader.get_jump_to_offset_instruction(0))

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

        # Infinite loop (jal 0)
        self.core_sim.write_program(0, ElfLoader.get_jump_to_offset_instruction(0))

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

        # Infinite loop (jal 0)
        self.core_sim.write_program(0, ElfLoader.get_jump_to_offset_instruction(0))

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

        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(0, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(4, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(8, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(12, ElfLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.core_sim.set_reset(False)
        self.assertFalse(self.core_sim.is_in_reset())

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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(12, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(16, ElfLoader.get_jump_to_offset_instruction(0))

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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(12, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(16, ElfLoader.get_jump_to_offset_instruction(0))

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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(12, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(16, ElfLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Continue
        self.core_sim.continue_execution()

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)

    def test_core_lockup(self):
        """Running code that should lock up the core and then trying to halt it."""
        if not self.core_sim.is_wormhole():
            self.skipTest("Issue is hit only on wormhole.")

        # lui t3, 0 - 0x00000e37
        # b_loop:
        #    addi t3, t3, 1 # Counter increment 0x001e0e13
        #    lw t1, 0(x0) # L1 read             0x00002303
        #    lw t2, 0(x0) # L1 read             0x00002383
        #    jal b_loop(-12) 0xff5ff06f
        self.core_sim.write_program(0, 0x00000E37)
        self.core_sim.write_program(4, 0x001E0E13)
        self.core_sim.write_program(8, 0x00002303)
        self.core_sim.write_program(12, 0x00002383)
        self.core_sim.write_program(16, ElfLoader.get_jump_to_offset_instruction(-12))

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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(12, 0x00B52023)
        # Increment x11 by 1 (addi x11, x11, 1)
        self.core_sim.write_program(16, 0x00158593)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(20, 0x00B52023)
        # Infinite loop (jal -8)
        self.core_sim.write_program(24, ElfLoader.get_jump_to_offset_instruction(-8))

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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(12, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(16, ElfLoader.get_jump_to_offset_instruction(0))

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
        if self.core_sim.is_wormhole():
            self.skipTest("Invalidate cache is not reliable on wormhole.")

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
        self.core_sim.write_program(0, ElfLoader.get_jump_to_offset_instruction(0))
        self.core_sim.write_program(4, ElfLoader.get_jump_to_offset_instruction(0))
        self.core_sim.write_program(8, ElfLoader.get_jump_to_offset_instruction(0))
        self.core_sim.write_program(12, ElfLoader.get_jump_to_offset_instruction(0))

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

        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(0, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(4, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(8, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(12, ElfLoader.get_jump_to_offset_instruction(0))

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
        self.core_sim.write_program(0, ElfLoader.get_jump_to_offset_instruction(0))
        self.core_sim.write_program(4, ElfLoader.get_jump_to_offset_instruction(0))
        self.core_sim.write_program(8, ElfLoader.get_jump_to_offset_instruction(0))
        self.core_sim.write_program(12, ElfLoader.get_jump_to_offset_instruction(0))

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

        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(0, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(4, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(8, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(12, ElfLoader.get_jump_to_offset_instruction(0))

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

        if self.core_sim.is_eth_block() and self.core_sim.is_wormhole():
            self.skipTest("This test is not applicable for ETH cores.")
        if (self.core_sim.is_wormhole() or self.core_sim.is_blackhole()) and self.core_sim.risc_name == "TRISC2":
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
        if self.core_sim.is_quasar():
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

        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(0, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(4, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(8, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(12, ElfLoader.get_jump_to_offset_instruction(0))

        # Continue execution
        self.core_sim.continue_execution()
        self.assertFalse(self.core_sim.is_halted(), "Core should not be halted.")

        # Since simulator is slow, we need to wait a bit by reading something
        if self.core_sim.is_quasar():
            for i in range(200):
                if self.core_sim.read_data(addr) == 0x87654000:
                    break

        # Halt to verify PC
        self.core_sim.halt()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertPcEquals(12)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x87654000)

    def test_watchpoint_on_pc_address(self):
        """Test running 36 bytes of generated code that just write data on memory and does watchpoint on pc address. All that is done on brisc."""

        if self.core_sim.is_eth_block():
            self.skipTest("This test sometimes fails on ETH cores. Issue: #452")

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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # nop
        self.core_sim.write_program(4, 0x00000013)
        # nop
        self.core_sim.write_program(8, 0x00000013)
        # nop
        self.core_sim.write_program(12, 0x00000013)
        # nop
        self.core_sim.write_program(16, 0x00000013)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(20, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(24, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(28, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(32, ElfLoader.get_jump_to_offset_instruction(0))

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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Infinite loop (jal 0)
        self.core_sim.write_program(4, ElfLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify that we hit ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

        # Set PC watchpoints
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(0, 12)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(1, 32)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(2, 0x1234)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(3, 0x8654)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(4, 0x87654321)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(5, 0x12345678)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(6, 0)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(7, 0xFFFFFFFF)

        # Read PC watchpoints addresses and verify it is the same as we set
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(0), 12, "Address should be 12.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(1), 32, "Address should be 32.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(2), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(3), 0x8654, "Address should be 0x8654.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(4), 0x87654321, "Address should be 0x87654321."
        )
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(5), 0x12345678, "Address should be 0x12345678."
        )
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(6), 0, "Address should be 0.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(7), 0xFFFFFFFF, "Address should be 0xFFFFFFFF."
        )

        # Set memory watchpoints for access
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(0, 0xFFFFFFFF)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(1, 12)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(2, 32)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(3, 0x1234)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(4, 0x8654)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(5, 0x87654321)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(6, 0x12345678)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(7, 0)

        # Read memory watchpoints addresses and verify it is the same as we set
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(0), 0xFFFFFFFF, "Address should be 0xFFFFFFFF."
        )
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(1), 12, "Address should be 12.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(2), 32, "Address should be 32.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(3), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(4), 0x8654, "Address should be 0x8654.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(5), 0x87654321, "Address should be 0x87654321."
        )
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(6), 0x12345678, "Address should be 0x12345678."
        )
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(7), 0, "Address should be 0.")

        # Set memory watchpoints for read
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(0, 0)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(1, 0xFFFFFFFF)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(2, 12)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(3, 32)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(4, 0x1234)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(5, 0x8654)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(6, 0x87654321)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(7, 0x12345678)

        # Read memory watchpoints addresses and verify it is the same as we set
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(0), 0, "Address should be 0.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(1), 0xFFFFFFFF, "Address should be 0xFFFFFFFF."
        )
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(2), 12, "Address should be 12.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(3), 32, "Address should be 32.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(4), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(5), 0x8654, "Address should be 0x8654.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(6), 0x87654321, "Address should be 0x87654321."
        )
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(7), 0x12345678, "Address should be 0x12345678."
        )

        # Set memory watchpoints for write
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(0, 0x12345678)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(1, 0)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(2, 0xFFFFFFFF)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(3, 12)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(4, 32)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(5, 0x1234)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(6, 0x8654)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(7, 0x87654321)

        # Read memory watchpoints addresses and verify it is the same as we set
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(0), 0x12345678, "Address should be 0x12345678."
        )
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(1), 0, "Address should be 0.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(2), 0xFFFFFFFF, "Address should be 0xFFFFFFFF."
        )
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(3), 12, "Address should be 12.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(4), 32, "Address should be 32.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(5), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(6), 0x8654, "Address should be 0x8654.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(7), 0x87654321, "Address should be 0x87654321."
        )

        # Set mixed watchpoins
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(0, 12)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(1, 32)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(2, 0x1234)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(3, 0x8654)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(4, 0x87654321)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(5, 0x12345678)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(6, 0)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(7, 0xFFFFFFFF)

        # Read watchpoints addresses and verify it is the same as we set
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(0), 12, "Address should be 12.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(1), 32, "Address should be 32.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(2), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(3), 0x8654, "Address should be 0x8654.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(4), 0x87654321, "Address should be 0x87654321."
        )
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(5), 0x12345678, "Address should be 0x12345678."
        )
        self.assertEqual(self.core_sim.debug_hardware.read_watchpoint_address(6), 0, "Address should be 0.")
        self.assertEqual(
            self.core_sim.debug_hardware.read_watchpoint_address(7), 0xFFFFFFFF, "Address should be 0xFFFFFFFF."
        )

    def test_watchpoint_state(self):
        """Test setting and disabling watchpoint state (both memory and PC)."""

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   while (true);

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Infinite loop (jal 0)
        self.core_sim.write_program(4, ElfLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify that we hit ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

        # Set watchpoints
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(0, 12)
        self.core_sim.debug_hardware.set_watchpoint_on_pc_address(1, 32)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(2, 0x1234)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(3, 0x8654)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(4, 0x87654321)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(5, 0x12345678)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(6, 0)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(7, 0xFFFFFFFF)

        # Read watchpoints state and verify it is the same as we set
        state = self.core_sim.debug_hardware.read_watchpoints_state()
        self.assertTrue(state[0].is_enabled, "Watchpoint 0 should be enabled.")
        self.assertFalse(state[0].is_memory, "Watchpoint 0 should not be memory watchpoint.")
        self.assertFalse(state[0].is_read, "Watchpoint 0 should not watch for reads.")
        self.assertFalse(state[0].is_write, "Watchpoint 0 should not watch for writes.")
        self.assertTrue(state[1].is_enabled, "Watchpoint 1 should be enabled.")
        self.assertFalse(state[1].is_memory, "Watchpoint 1 should not be memory watchpoint.")
        self.assertFalse(state[1].is_read, "Watchpoint 1 should not watch for reads.")
        self.assertFalse(state[1].is_write, "Watchpoint 1 should not watch for writes.")
        self.assertTrue(state[2].is_enabled, "Watchpoint 2 should be enabled.")
        self.assertTrue(state[2].is_memory, "Watchpoint 2 should be memory watchpoint.")
        self.assertTrue(state[2].is_read, "Watchpoint 2 should watch for reads.")
        self.assertTrue(state[2].is_write, "Watchpoint 2 should watch for writes.")
        self.assertTrue(state[3].is_enabled, "Watchpoint 3 should be enabled.")
        self.assertTrue(state[3].is_memory, "Watchpoint 3 should be memory watchpoint.")
        self.assertTrue(state[3].is_read, "Watchpoint 3 should watch for reads.")
        self.assertTrue(state[3].is_write, "Watchpoint 3 should watch for writes.")
        self.assertTrue(state[4].is_enabled, "Watchpoint 4 should be enabled.")
        self.assertTrue(state[4].is_memory, "Watchpoint 4 should be memory watchpoint.")
        self.assertTrue(state[4].is_read, "Watchpoint 4 should watch for reads.")
        self.assertFalse(state[4].is_write, "Watchpoint 4 should not watch for writes.")
        self.assertTrue(state[5].is_enabled, "Watchpoint 5 should be enabled.")
        self.assertTrue(state[5].is_memory, "Watchpoint 5 should be memory watchpoint.")
        self.assertTrue(state[5].is_read, "Watchpoint 5 should watch for reads.")
        self.assertFalse(state[5].is_write, "Watchpoint 5 should not watch for writes.")
        self.assertTrue(state[6].is_enabled, "Watchpoint 6 should be enabled.")
        self.assertTrue(state[6].is_memory, "Watchpoint 6 should be memory watchpoint.")
        self.assertFalse(state[6].is_read, "Watchpoint 6 should not watch for reads.")
        self.assertTrue(state[6].is_write, "Watchpoint 6 should watch for writes.")
        self.assertTrue(state[7].is_enabled, "Watchpoint 7 should be enabled.")
        self.assertTrue(state[7].is_memory, "Watchpoint 7 should be memory watchpoint.")
        self.assertFalse(state[7].is_read, "Watchpoint 7 should not watch for reads.")
        self.assertTrue(state[7].is_write, "Watchpoint 7 should watch for writes.")

        # Disable some watchpoints
        self.core_sim.debug_hardware.disable_watchpoint(0)
        self.core_sim.debug_hardware.disable_watchpoint(3)
        self.core_sim.debug_hardware.disable_watchpoint(4)
        self.core_sim.debug_hardware.disable_watchpoint(6)

        # Read watchpoints state and verify that we disabled some of the and rest have the same state as we set before
        state = self.core_sim.debug_hardware.read_watchpoints_state()
        self.assertFalse(state[0].is_enabled, "Watchpoint 0 should not be enabled.")
        self.assertFalse(state[0].is_memory, "Watchpoint 0 should not be memory watchpoint.")
        self.assertFalse(state[0].is_read, "Watchpoint 0 should not watch for reads.")
        self.assertFalse(state[0].is_write, "Watchpoint 0 should not watch for writes.")
        self.assertTrue(state[1].is_enabled, "Watchpoint 1 should be enabled.")
        self.assertFalse(state[1].is_memory, "Watchpoint 1 should not be memory watchpoint.")
        self.assertFalse(state[1].is_read, "Watchpoint 1 should not watch for reads.")
        self.assertFalse(state[1].is_write, "Watchpoint 1 should not watch for writes.")
        self.assertTrue(state[2].is_enabled, "Watchpoint 2 should be enabled.")
        self.assertTrue(state[2].is_memory, "Watchpoint 2 should be memory watchpoint.")
        self.assertTrue(state[2].is_read, "Watchpoint 2 should watch for reads.")
        self.assertTrue(state[2].is_write, "Watchpoint 2 should watch for writes.")
        self.assertFalse(state[3].is_enabled, "Watchpoint 3 should not be enabled.")
        self.assertFalse(state[3].is_memory, "Watchpoint 3 should not be memory watchpoint.")
        self.assertFalse(state[3].is_read, "Watchpoint 3 should not watch for reads.")
        self.assertFalse(state[3].is_write, "Watchpoint 3 should not watch for writes.")
        self.assertFalse(state[4].is_enabled, "Watchpoint 4 should not be enabled.")
        self.assertFalse(state[4].is_memory, "Watchpoint 4 should not be memory watchpoint.")
        self.assertFalse(state[4].is_read, "Watchpoint 4 should not watch for reads.")
        self.assertFalse(state[4].is_write, "Watchpoint 4 should not watch for writes.")
        self.assertTrue(state[5].is_enabled, "Watchpoint 5 should be enabled.")
        self.assertTrue(state[5].is_memory, "Watchpoint 5 should be memory watchpoint.")
        self.assertTrue(state[5].is_read, "Watchpoint 5 should watch for reads.")
        self.assertFalse(state[5].is_write, "Watchpoint 5 should not watch for writes.")
        self.assertFalse(state[6].is_enabled, "Watchpoint 6 should not be enabled.")
        self.assertFalse(state[6].is_memory, "Watchpoint 6 should not be memory watchpoint.")
        self.assertFalse(state[6].is_read, "Watchpoint 6 should not watch for reads.")
        self.assertFalse(state[6].is_write, "Watchpoint 6 should not watch for writes.")
        self.assertTrue(state[7].is_enabled, "Watchpoint 7 should be enabled.")
        self.assertTrue(state[7].is_memory, "Watchpoint 7 should be memory watchpoint.")
        self.assertFalse(state[7].is_read, "Watchpoint 7 should not watch for reads.")
        self.assertTrue(state[7].is_write, "Watchpoint 7 should watch for writes.")

    def test_memory_watchpoint(self):
        """Test running 64 bytes of generated code that just write data on memory and tests memory watchpoints. All that is done on brisc."""

        if self.core_sim.is_eth_block():
            self.skipTest("This test sometimes fails on ETH cores. Issue: #452")

        addr1 = 0x10000
        addr2 = 0x20000
        addr3 = 0x30000
        addr4 = 0x30000

        # Write our data to memory
        self.core_sim.write_data_checked(addr1, 0x12345678)
        self.core_sim.write_data_checked(addr2, 0x12345678)
        self.core_sim.write_data_checked(addr3, 0x12345678)
        self.core_sim.write_data_checked(addr4, 0x12345678)

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
        #   while (true);

        # ebreak
        self.core_sim.write_program(0, 0x00100073)

        # nop
        self.core_sim.write_program(4, 0x00000013)
        # nop
        self.core_sim.write_program(8, 0x00000013)
        # nop
        self.core_sim.write_program(12, 0x00000013)
        # nop
        self.core_sim.write_program(16, 0x00000013)

        # First write
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(20, 0x00010537)
        # Load Immediate Value 0x45678000 into x11 (lui x11, 0x45678)
        self.core_sim.write_program(24, 0x456785B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(28, 0x00B52023)

        # Read from memory
        # Load Immediate Address 0x20000 into x10 (lui x10, 0x20)
        self.core_sim.write_program(32, 0x00020537)
        # Load the word from memory at address held in x10 (0x20000) into x12
        self.core_sim.write_program(36, 0x00052603)

        # Second write
        # Load Immediate Address 0x30000 into x10 (lui x10, 0x30)
        self.core_sim.write_program(40, 0x00030537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(44, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(48, 0x00B52023)

        # Second from memory
        # Load Immediate Address 0x40000 into x10 (lui x10, 0x20)
        self.core_sim.write_program(52, 0x00040537)
        # Load the word from memory at address held in x10 (0x40000) into x12
        self.core_sim.write_program(56, 0x00052603)

        # Infinite loop (jal 0)
        self.core_sim.write_program(60, ElfLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr1), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

        # Set memory watchpoints
        self.core_sim.debug_hardware.set_watchpoint_on_memory_write(0, 0x10000)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_read(1, 0x20000)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(2, 0x30000)
        self.core_sim.debug_hardware.set_watchpoint_on_memory_access(3, 0x40000)

        # Continue and verify that we hit first watchpoint
        self.core_sim.continue_execution()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertTrue(self.core_sim.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
        self.assertTrue(self.core_sim.read_status().watchpoints_hit[0], "Watchpoint 0 should be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[1], "Watchpoint 1 should not be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[2], "Watchpoint 2 should not be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[3], "Watchpoint 3 should not be hit.")

        self.assertEqual(self.core_sim.read_data(addr1), 0x45678000)

        # Continue and verify that we hit second watchpoint
        self.core_sim.continue_execution()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertTrue(self.core_sim.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[0], "Watchpoint 0 should not be hit.")
        self.assertTrue(self.core_sim.read_status().watchpoints_hit[1], "Watchpoint 1 should be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[2], "Watchpoint 2 should not be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[3], "Watchpoint 3 should not be hit.")

        # Continue and verify that we hit third watchpoint
        self.core_sim.continue_execution()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertTrue(self.core_sim.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[0], "Watchpoint 0 should not be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[1], "Watchpoint 1 should not be hit.")
        self.assertTrue(self.core_sim.read_status().watchpoints_hit[2], "Watchpoint 2 should be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[3], "Watchpoint 3 should not be hit.")

        self.assertEqual(self.core_sim.read_data(addr3), 0x87654000)

        # Continue and verify that we hit fourth watchpoint
        self.core_sim.continue_execution()
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertFalse(self.core_sim.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertTrue(self.core_sim.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[0], "Watchpoint 0 should not be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[1], "Watchpoint 1 should not be hit.")
        self.assertFalse(self.core_sim.read_status().watchpoints_hit[2], "Watchpoint 2 should not be hit.")
        self.assertTrue(self.core_sim.read_status().watchpoints_hit[3], "Watchpoint 3 should be hit.")

    def test_bne_with_debug_fail(self):
        """Test running 48 bytes of generated code that confirms problem with BNE when debugging hardware is enabled."""

        if self.core_sim.is_eth_block():
            self.skipTest("We don't know how to enable/disable branch prediction ETH cores.")

        if self.core_sim.is_blackhole():
            self.skipTest("BNE instruction with debug hardware enabled is fixed in blackhole.")

        if self.core_sim.is_quasar():
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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Store 0 to x1 (addi x1, x0, 0)
        self.core_sim.write_program(4, 0x00000093)
        # Store 63 to x2 (addi x2, x0, 63)
        self.core_sim.write_program(8, 0x03F00113)
        # See if they are equal (bne x1, x2, 8)
        self.core_sim.write_program(12, 0x00209463)
        # Jump to ebreak
        self.core_sim.write_program(16, ElfLoader.get_jump_to_offset_instruction(12))
        # Increase value in x1 (addi x1, x1, 1)
        self.core_sim.write_program(20, 0x00108093)
        # Jump to bne
        self.core_sim.write_program(24, ElfLoader.get_jump_to_offset_instruction(-12))
        # ebreak
        self.core_sim.write_program(28, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(32, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(36, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(40, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(44, ElfLoader.get_jump_to_offset_instruction(0))

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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Store 0 to x1 (addi x1, x0, 0)
        self.core_sim.write_program(4, 0x00000093)
        # Store 63 to x2 (addi x2, x0, 63)
        self.core_sim.write_program(8, 0x03F00113)
        # See if they are equal (bne x1, x2, 8)
        self.core_sim.write_program(12, 0x00209463)
        # Jump to ebreak
        self.core_sim.write_program(16, ElfLoader.get_jump_to_offset_instruction(12))
        # Increase value in x1 (addi x1, x1, 1)
        self.core_sim.write_program(20, 0x00108093)
        # Jump to bne
        self.core_sim.write_program(24, ElfLoader.get_jump_to_offset_instruction(-12))
        # ebreak
        self.core_sim.write_program(28, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(32, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(36, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(40, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(44, ElfLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")

        # Continue to proceed with bne test
        self.core_sim.debug_hardware.continue_without_debug()  # We need to use debug hardware as there is a bug fix in risc debug implementation for wormhole

        # Since simulator is slow, we need to wait a bit by reading something
        if self.core_sim.is_quasar():
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

        # ebreak
        self.core_sim.write_program(0, 0x00100073)
        # Store 0 to x1 (addi x1, x0, 0)
        self.core_sim.write_program(4, 0x00000093)
        # Store 63 to x2 (addi x2, x0, 63)
        self.core_sim.write_program(8, 0x03F00113)
        # See if they are equal (bne x1, x2, 8)
        self.core_sim.write_program(12, 0x00209463)
        # Jump to ebreak
        self.core_sim.write_program(16, ElfLoader.get_jump_to_offset_instruction(12))
        # Increase value in x1 (addi x1, x1, 1)
        self.core_sim.write_program(20, 0x00108093)
        # Jump to bne
        self.core_sim.write_program(24, ElfLoader.get_jump_to_offset_instruction(-12))
        # ebreak
        self.core_sim.write_program(28, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.core_sim.write_program(32, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.core_sim.write_program(36, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.core_sim.write_program(40, 0x00B52023)
        # Infinite loop (jal 0)
        self.core_sim.write_program(44, ElfLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.core_sim.set_reset(False)

        # Verify value at address
        self.assertEqual(self.core_sim.read_data(addr), 0x12345678)
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "ebreak should be the cause.")

        # Disable branch prediction
        if not self.core_sim.is_blackhole():
            # Disabling branch prediction fails this test on blackhole :(
            self.core_sim.set_branch_prediction(False)

        # Continue to proceed with bne test
        self.core_sim.debug_hardware.cont()  # We need to use debug hardware as there is a bug fix in risc debug implementation for wormhole

        # Since simulator is slow, we need to wait a bit by reading something
        if self.core_sim.is_quasar():
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
