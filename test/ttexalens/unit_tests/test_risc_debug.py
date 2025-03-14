# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class
from test.ttexalens.unit_tests.test_base import init_default_test_context
from ttexalens import tt_exalens_lib as lib

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_risc import RiscLoader, RiscDebug, RiscLoc, get_register_index, get_risc_id


@parameterized_class(
    [
        # { "core_desc": "ETH0", "risc_name": "BRISC" },
        {"core_desc": "FW0", "risc_name": "BRISC"},
        {"core_desc": "FW0", "risc_name": "TRISC0"},
        {"core_desc": "FW0", "risc_name": "TRISC1"},
        {"core_desc": "FW0", "risc_name": "TRISC2"},
        {"core_desc": "FW1", "risc_name": "BRISC"},
        {"core_desc": "FW1", "risc_name": "TRISC0"},
        {"core_desc": "FW1", "risc_name": "TRISC1"},
        {"core_desc": "FW1", "risc_name": "TRISC2"},
    ]
)
class TestDebugging(unittest.TestCase):
    risc_name: str = None  # Risc name
    risc_id: int = None  # Risc ID - being parametrized
    context: Context = None  # TTExaLens context
    core_desc: str = None  # Core description ETH0, FW0, FW1 - being parametrized
    core_loc: str = None  # Core location
    rdbg: RiscDebug = None  # RiscDebug object
    pc_register_index: int = None  # PC register index
    program_base_address: int = None  # Base address for program code

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()
        cls.pc_register_index = get_register_index("pc")

    def setUp(self):
        # Convert core_desc to core_loc
        if self.core_desc.startswith("ETH"):
            # Ask device for all ETH cores and get first one
            eth_cores = self.context.devices[0].get_block_locations(block_type="eth")
            core_index = int(self.core_desc[3:])
            if len(eth_cores) > core_index:
                self.core_loc = eth_cores[core_index].to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("ETH core is not available on this platform")
        elif self.core_desc.startswith("FW"):
            # Ask device for all ETH cores and get first one
            eth_cores = self.context.devices[0].get_block_locations(block_type="functional_workers")
            core_index = int(self.core_desc[2:])
            if len(eth_cores) > core_index:
                self.core_loc = eth_cores[core_index].to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("ETH core is not available on this platform")
        else:
            self.fail(f"Unknown core description {self.core_desc}")

        loc = OnChipCoordinate.create(self.core_loc, device=self.context.devices[0])
        self.risc_id = get_risc_id(self.risc_name)
        rloc = RiscLoc(loc, 0, self.risc_id)
        self.rdbg = RiscDebug(rloc, self.context)
        loader = RiscLoader(self.rdbg, self.context)
        self.program_base_address = loader.get_risc_start_address()

        # If address wasn't set before, we want to set it to something that is not 0 for testing purposes
        if self.program_base_address == None:
            # Set program base address to 0xd000
            loader.set_risc_start_address(0xD000)
            self.program_base_address = loader.get_risc_start_address()
            self.assertEqual(self.program_base_address, 0xD000)

        # Stop risc with reset
        self.rdbg.set_reset_signal(True)
        self.assertTrue(self.rdbg.is_in_reset())

    def tearDown(self):
        # Stop risc with reset
        self.rdbg.set_reset_signal(True)
        self.assertTrue(self.rdbg.is_in_reset())

    def is_blackhole(self):
        """Check if the device is blackhole."""
        return self.context.devices[0]._arch == "blackhole"

    def is_wormhole(self):
        """Check if the device is wormhole_b0."""
        return self.context.devices[0]._arch == "wormhole_b0"

    def read_data(self, addr):
        """Read data from memory."""
        ret = lib.read_words_from_device(self.core_loc, addr, context=self.context)
        return ret[0]

    def write_data_checked(self, addr, data):
        """Write data to memory and check it was written."""
        lib.write_words_to_device(self.core_loc, addr, data, context=self.context)
        self.assertEqual(self.read_data(addr), data)

    def write_program(self, addr, data):
        """Write program code data to L1 memory."""
        self.write_data_checked(self.program_base_address + addr, data)

    def assertPcEquals(self, expected):
        """Assert PC register equals to expected value."""
        if self.is_wormhole() or self.is_blackhole():
            # checks pc over debug bus
            self.assertEqual(
                self.get_pc_from_debug_bus(),
                self.program_base_address + expected,
                f"Pc should be {expected} + program_base_addres ({self.program_base_address + expected}).",
            )
        else:
            self.assertEqual(
                self.rdbg.read_gpr(self.pc_register_index),
                self.program_base_address + expected,
                f"Pc should be {expected} + program_base_addres ({self.program_base_address + expected}).",
            )


    def get_pc_from_debug_bus(self):
        return self.context.devices[0].read_debug_bus_signal(self.core_loc, self.risc_name.lower() + "_pc")

    def assertPcLess(self, expected):
        """Assert PC register is less than expected value."""
        self.assertLess(
            self.rdbg.read_gpr(self.pc_register_index),
            self.program_base_address + expected,
            f"Pc should be less than {expected} + program_base_addres ({self.program_base_address + expected}).",
        )

    def test_reset_all_functional_workers(self):
        """Reset all functional workers."""
        if self.core_desc.startswith("ETH"):
            self.skipTest(
                "Playing with ETH core moves device into unknown state after we should warm reset it. This test cannot be run at that moment."
            )
        for device in self.context.devices.values():
            device.all_riscs_assert_soft_reset()
            for rdbg in device.debuggable_cores:
                self.assertTrue(rdbg.is_in_reset())

    def test_read_write_gpr(self):
        """Write then read value in all registers (except zero and pc)."""

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("nop");
        #   while (true);

        # NOP
        self.write_program(0, 0x00000013)
        # Infinite loop (jal 0)
        self.write_program(4, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)
        self.assertFalse(self.rdbg.is_in_reset())

        # Halt core
        self.rdbg.enable_debug()
        self.rdbg.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")

        # Test readonly registers
        self.assertEqual(self.rdbg.read_gpr(get_register_index("zero")), 0, "zero should always be 0.")
        self.assertEqual(self.rdbg.read_gpr(get_register_index("pc")), self.program_base_address + 4, "PC should be 4.")

        # Test write then read for all other registers
        for i in range(1, 31):
            self.rdbg.write_gpr(i, 0x12345678)
            self.assertEqual(self.rdbg.read_gpr(i), 0x12345678, f"Register x{i} should be 0x12345678.")
            self.rdbg.write_gpr(i, 0x87654321)
            self.assertEqual(self.rdbg.read_gpr(i), 0x87654321, f"Register x{i} should be 0x12345678.")

    def test_read_write_l1_memory(self):
        """Testing read_memory and write_memory through debugging interface on L1 memory range."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   while (true);

        # Infinite loop (jal 0)
        self.write_program(0, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)
        self.assertFalse(self.rdbg.is_in_reset())

        # Halt core
        self.rdbg.enable_debug()
        self.rdbg.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")

        # Test read and write memory
        self.assertEqual(self.rdbg.read_memory(addr), 0x12345678, "Memory value should be 0x12345678.")
        self.rdbg.write_memory(addr, 0x87654321)
        self.assertEqual(self.rdbg.read_memory(addr), 0x87654321, "Memory value should be 0x87654321.")
        self.assertEqual(self.read_data(addr), 0x87654321)

    def test_read_write_private_memory(self):
        """Testing read_memory and write_memory through debugging interface on private core memory range."""
        addr = 0xFFB00000

        # Write code for brisc core at address 0
        # C++:
        #   while (true);

        # Infinite loop (jal 0)
        self.write_program(0, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)
        self.assertFalse(self.rdbg.is_in_reset())

        # Halt core
        self.rdbg.enable_debug()
        self.rdbg.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")

        # Test write and read memory
        self.rdbg.write_memory(addr, 0x12345678)
        self.assertEqual(self.rdbg.read_memory(addr), 0x12345678, "Memory value should be 0x12345678.")
        self.rdbg.write_memory(addr, 0x87654321)
        self.assertEqual(self.rdbg.read_memory(addr), 0x87654321, "Memory value should be 0x87654321.")

    def test_minimal_run_generated_code(self):
        """Test running 16 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(0, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(4, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(8, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(12, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)
        self.assertFalse(self.rdbg.is_in_reset())

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x87654000)

    def test_ebreak(self):
        """Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(12, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(16, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify value at address, value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
        self.assertPcEquals(4)

    def test_ebreak_and_step(self):
        """Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(12, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(16, RiscLoader.get_jump_to_offset_instruction(0))

        self.rdbg.set_reset_signal(False)

        # On blackhole, we need to step one more time...

        # Verify value at address, value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertPcEquals(4)
        # Step and verify that pc is 8 and value is not changed
        self.rdbg.step()
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertPcEquals(8)
        # Adding two steps since logic in hw automatically updates register and memory values
        self.rdbg.step()
        self.rdbg.step()
        # Verify that pc is 16 and value has changed
        self.assertEqual(self.read_data(addr), 0x87654000)
        self.assertPcEquals(16)
        # Since we are on endless loop, we should never go past 16
        for i in range(10):
            # Step and verify that pc is 16 and value has changed
            self.rdbg.step()
            self.assertPcEquals(16)

    def test_continue(self):
        """Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(12, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(16, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Continue
        self.rdbg.enable_debug()
        self.rdbg.cont()

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x87654000)

    def test_halt_continue(self):
        """Test running 28 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true)
        #     *a++;

        # ebreak
        self.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(12, 0x00B52023)
        # Increment x11 by 1 (addi x11, x11, 1)
        self.write_program(16, 0x00158593)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(20, 0x00B52023)
        # Infinite loop (jal -8)
        self.write_program(24, RiscLoader.get_jump_to_offset_instruction(-8))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify that value didn't change cause of ebreak
        self.assertEqual(self.read_data(addr), 0x12345678)

        # Continue
        self.rdbg.enable_debug()
        self.rdbg.cont()

        # Verify that value changed cause of continue
        previous_value = self.read_data(addr)
        self.assertGreaterEqual(previous_value, 0x87654000)

        # Loop halt and continue
        for i in range(10):
            # Halt
            self.rdbg.halt()

            # Read value
            value = self.read_data(addr)
            self.assertGreater(value, previous_value)
            previous_value = value

            # Second read should have the same value if core is halted
            self.assertEqual(self.read_data(addr), previous_value)

            # Continue
            self.rdbg.cont()

    def test_halt_status(self):
        """Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(4, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(8, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(12, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(16, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")

        # Continue
        self.rdbg.enable_debug()
        self.rdbg.cont()

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x87654000)
        self.assertFalse(self.rdbg.read_status().is_halted, "Core should not be halted.")

        # Halt and test status
        self.rdbg.halt()
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_ebreak_hit, "ebreak should not be the cause.")

    def test_invalidate_cache(self):
        if not self.is_blackhole():
            self.skipTest("Invalidate cache is not reliable on wormhole.")

        """Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write endless loop for brisc core at address 0
        # C++:
        #   while (true);
        #   while (true);
        #   while (true);
        #   while (true);
        self.write_program(0, RiscLoader.get_jump_to_offset_instruction(0))
        self.write_program(4, RiscLoader.get_jump_to_offset_instruction(0))
        self.write_program(8, RiscLoader.get_jump_to_offset_instruction(0))
        self.write_program(12, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Halt core
        self.rdbg.enable_debug()
        self.rdbg.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertPcEquals(0)

        # Write new code for brisc core at address 0
        # C++:
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(0, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(4, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(8, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(12, RiscLoader.get_jump_to_offset_instruction(0))

        # Invalidate instruction cache
        self.rdbg.invalidate_instruction_cache()

        # Continue
        self.rdbg.cont()
        self.assertFalse(self.rdbg.read_status().is_halted, "Core should not be halted.")

        # Halt to verify PC
        self.rdbg.halt()
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should not be halted.")

        # There is hardware bug on blackhole that causes PC to be 0
        self.assertPcEquals(12)

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x87654000)

    def test_invalidate_cache_with_reset(self):
        """Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation by reseting core. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write endless loop for brisc core at address 0
        # C++:
        #   while (true);
        #   while (true);
        #   while (true);
        #   while (true);
        self.write_program(0, RiscLoader.get_jump_to_offset_instruction(0))
        self.write_program(4, RiscLoader.get_jump_to_offset_instruction(0))
        self.write_program(8, RiscLoader.get_jump_to_offset_instruction(0))
        self.write_program(12, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Halt core
        self.rdbg.enable_debug()
        self.rdbg.halt()

        # Value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertPcEquals(0)

        # Write new code for brisc core at address 0
        # C++:
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(0, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(4, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(8, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(12, RiscLoader.get_jump_to_offset_instruction(0))

        # Invalidate instruction cache with reset
        self.rdbg.set_reset_signal(True)
        self.rdbg.set_reset_signal(False)
        self.assertFalse(self.rdbg.read_status().is_halted, "Core should not be halted.")

        # Halt to verify PC
        self.rdbg.halt()
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should not be halted.")
        self.assertPcEquals(12)

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x87654000)

    def test_invalidate_cache_with_nops_and_long_jump(self):
        """Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation by having NOPs block and jump back. All that is done on brisc."""
        break_addr = 0x950
        jump_addr = 0x2000
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

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
        for i in range(jump_addr // 4):
            self.write_program(i * 4, 0x00000013)
        self.write_program(break_addr, 0x00100073)
        self.write_program(jump_addr, RiscLoader.get_jump_to_offset_instruction(-jump_addr))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Value should not be changed and should stay the same since core is in halt
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
        self.assertPcEquals(break_addr + 4)

        # Write new code for brisc core at address 0
        # C++:
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(0, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(4, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(8, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(12, RiscLoader.get_jump_to_offset_instruction(0))

        # Continue execution
        self.rdbg.cont(False)
        self.assertFalse(self.rdbg.read_status().is_halted, "Core should not be halted.")

        # Halt to verify PC
        self.rdbg.halt()
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertPcEquals(12)

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x87654000)

    def test_watchpoint_on_pc_address(self):
        """Test running 36 bytes of generated code that just write data on memory and does watchpoint on pc address. All that is done on brisc."""
        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

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
        self.write_program(0, 0x00100073)
        # nop
        self.write_program(4, 0x00000013)
        # nop
        self.write_program(8, 0x00000013)
        # nop
        self.write_program(12, 0x00000013)
        # nop
        self.write_program(16, 0x00000013)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(20, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(24, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(28, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(32, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertPcEquals(4)

        # Set watchpoint on address 12 and 32
        self.rdbg.set_watchpoint_on_pc_address(0, self.program_base_address + 12)
        self.rdbg.set_watchpoint_on_pc_address(1, self.program_base_address + 32)

        # Continue and verify that we hit first watchpoint
        self.rdbg.cont(False)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_ebreak_hit, "ebreak should not be the cause.")
        self.assertTrue(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should not be the cause.")
        self.assertTrue(self.rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should not be hit.")

        self.assertPcLess(28)
        self.assertEqual(self.read_data(addr), 0x12345678)

        # Continue and verify that we hit first watchpoint
        self.rdbg.cont(False)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_ebreak_hit, "ebreak should not be the cause.")
        self.assertTrue(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should not be the cause.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should not be hit.")
        self.assertTrue(self.rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should be hit.")
        self.assertPcEquals(32)
        self.assertEqual(self.read_data(addr), 0x87654000)

    def test_watchpoint_address(self):
        """Test setting and reading watchpoint address (both memory and PC)."""

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Infinite loop (jal 0)
        self.write_program(4, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify that we hit ebreak
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

        # Set PC watchpoints
        self.rdbg.set_watchpoint_on_pc_address(0, 12)
        self.rdbg.set_watchpoint_on_pc_address(1, 32)
        self.rdbg.set_watchpoint_on_pc_address(2, 0x1234)
        self.rdbg.set_watchpoint_on_pc_address(3, 0x8654)
        self.rdbg.set_watchpoint_on_pc_address(4, 0x87654321)
        self.rdbg.set_watchpoint_on_pc_address(5, 0x12345678)
        self.rdbg.set_watchpoint_on_pc_address(6, 0)
        self.rdbg.set_watchpoint_on_pc_address(7, 0xFFFFFFFF)

        # Read PC watchpoints addresses and verify it is the same as we set
        self.assertEqual(self.rdbg.read_watchpoint_address(0), 12, "Address should be 12.")
        self.assertEqual(self.rdbg.read_watchpoint_address(1), 32, "Address should be 32.")
        self.assertEqual(self.rdbg.read_watchpoint_address(2), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.rdbg.read_watchpoint_address(3), 0x8654, "Address should be 0x8654.")
        self.assertEqual(self.rdbg.read_watchpoint_address(4), 0x87654321, "Address should be 0x87654321.")
        self.assertEqual(self.rdbg.read_watchpoint_address(5), 0x12345678, "Address should be 0x12345678.")
        self.assertEqual(self.rdbg.read_watchpoint_address(6), 0, "Address should be 0.")
        self.assertEqual(self.rdbg.read_watchpoint_address(7), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")

        # Set memory watchpoints for access
        self.rdbg.set_watchpoint_on_memory_access(0, 0xFFFFFFFF)
        self.rdbg.set_watchpoint_on_memory_access(1, 12)
        self.rdbg.set_watchpoint_on_memory_access(2, 32)
        self.rdbg.set_watchpoint_on_memory_access(3, 0x1234)
        self.rdbg.set_watchpoint_on_memory_access(4, 0x8654)
        self.rdbg.set_watchpoint_on_memory_access(5, 0x87654321)
        self.rdbg.set_watchpoint_on_memory_access(6, 0x12345678)
        self.rdbg.set_watchpoint_on_memory_access(7, 0)

        # Read memory watchpoints addresses and verify it is the same as we set
        self.assertEqual(self.rdbg.read_watchpoint_address(0), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")
        self.assertEqual(self.rdbg.read_watchpoint_address(1), 12, "Address should be 12.")
        self.assertEqual(self.rdbg.read_watchpoint_address(2), 32, "Address should be 32.")
        self.assertEqual(self.rdbg.read_watchpoint_address(3), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.rdbg.read_watchpoint_address(4), 0x8654, "Address should be 0x8654.")
        self.assertEqual(self.rdbg.read_watchpoint_address(5), 0x87654321, "Address should be 0x87654321.")
        self.assertEqual(self.rdbg.read_watchpoint_address(6), 0x12345678, "Address should be 0x12345678.")
        self.assertEqual(self.rdbg.read_watchpoint_address(7), 0, "Address should be 0.")

        # Set memory watchpoints for read
        self.rdbg.set_watchpoint_on_memory_read(0, 0)
        self.rdbg.set_watchpoint_on_memory_read(1, 0xFFFFFFFF)
        self.rdbg.set_watchpoint_on_memory_read(2, 12)
        self.rdbg.set_watchpoint_on_memory_read(3, 32)
        self.rdbg.set_watchpoint_on_memory_read(4, 0x1234)
        self.rdbg.set_watchpoint_on_memory_read(5, 0x8654)
        self.rdbg.set_watchpoint_on_memory_read(6, 0x87654321)
        self.rdbg.set_watchpoint_on_memory_read(7, 0x12345678)

        # Read memory watchpoints addresses and verify it is the same as we set
        self.assertEqual(self.rdbg.read_watchpoint_address(0), 0, "Address should be 0.")
        self.assertEqual(self.rdbg.read_watchpoint_address(1), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")
        self.assertEqual(self.rdbg.read_watchpoint_address(2), 12, "Address should be 12.")
        self.assertEqual(self.rdbg.read_watchpoint_address(3), 32, "Address should be 32.")
        self.assertEqual(self.rdbg.read_watchpoint_address(4), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.rdbg.read_watchpoint_address(5), 0x8654, "Address should be 0x8654.")
        self.assertEqual(self.rdbg.read_watchpoint_address(6), 0x87654321, "Address should be 0x87654321.")
        self.assertEqual(self.rdbg.read_watchpoint_address(7), 0x12345678, "Address should be 0x12345678.")

        # Set memory watchpoints for write
        self.rdbg.set_watchpoint_on_memory_write(0, 0x12345678)
        self.rdbg.set_watchpoint_on_memory_write(1, 0)
        self.rdbg.set_watchpoint_on_memory_write(2, 0xFFFFFFFF)
        self.rdbg.set_watchpoint_on_memory_write(3, 12)
        self.rdbg.set_watchpoint_on_memory_write(4, 32)
        self.rdbg.set_watchpoint_on_memory_write(5, 0x1234)
        self.rdbg.set_watchpoint_on_memory_write(6, 0x8654)
        self.rdbg.set_watchpoint_on_memory_write(7, 0x87654321)

        # Read memory watchpoints addresses and verify it is the same as we set
        self.assertEqual(self.rdbg.read_watchpoint_address(0), 0x12345678, "Address should be 0x12345678.")
        self.assertEqual(self.rdbg.read_watchpoint_address(1), 0, "Address should be 0.")
        self.assertEqual(self.rdbg.read_watchpoint_address(2), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")
        self.assertEqual(self.rdbg.read_watchpoint_address(3), 12, "Address should be 12.")
        self.assertEqual(self.rdbg.read_watchpoint_address(4), 32, "Address should be 32.")
        self.assertEqual(self.rdbg.read_watchpoint_address(5), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.rdbg.read_watchpoint_address(6), 0x8654, "Address should be 0x8654.")
        self.assertEqual(self.rdbg.read_watchpoint_address(7), 0x87654321, "Address should be 0x87654321.")

        # Set mixed watchpoins
        self.rdbg.set_watchpoint_on_pc_address(0, 12)
        self.rdbg.set_watchpoint_on_pc_address(1, 32)
        self.rdbg.set_watchpoint_on_memory_access(2, 0x1234)
        self.rdbg.set_watchpoint_on_memory_access(3, 0x8654)
        self.rdbg.set_watchpoint_on_memory_read(4, 0x87654321)
        self.rdbg.set_watchpoint_on_memory_read(5, 0x12345678)
        self.rdbg.set_watchpoint_on_memory_write(6, 0)
        self.rdbg.set_watchpoint_on_memory_write(7, 0xFFFFFFFF)

        # Read watchpoints addresses and verify it is the same as we set
        self.assertEqual(self.rdbg.read_watchpoint_address(0), 12, "Address should be 12.")
        self.assertEqual(self.rdbg.read_watchpoint_address(1), 32, "Address should be 32.")
        self.assertEqual(self.rdbg.read_watchpoint_address(2), 0x1234, "Address should be 0x1234.")
        self.assertEqual(self.rdbg.read_watchpoint_address(3), 0x8654, "Address should be 0x8654.")
        self.assertEqual(self.rdbg.read_watchpoint_address(4), 0x87654321, "Address should be 0x87654321.")
        self.assertEqual(self.rdbg.read_watchpoint_address(5), 0x12345678, "Address should be 0x12345678.")
        self.assertEqual(self.rdbg.read_watchpoint_address(6), 0, "Address should be 0.")
        self.assertEqual(self.rdbg.read_watchpoint_address(7), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")

    def test_watchpoint_state(self):
        """Test setting and disabling watchpoint state (both memory and PC)."""

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Infinite loop (jal 0)
        self.write_program(4, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify that we hit ebreak
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

        # Set watchpoints
        self.rdbg.set_watchpoint_on_pc_address(0, 12)
        self.rdbg.set_watchpoint_on_pc_address(1, 32)
        self.rdbg.set_watchpoint_on_memory_access(2, 0x1234)
        self.rdbg.set_watchpoint_on_memory_access(3, 0x8654)
        self.rdbg.set_watchpoint_on_memory_read(4, 0x87654321)
        self.rdbg.set_watchpoint_on_memory_read(5, 0x12345678)
        self.rdbg.set_watchpoint_on_memory_write(6, 0)
        self.rdbg.set_watchpoint_on_memory_write(7, 0xFFFFFFFF)

        # Read watchpoints state and verify it is the same as we set
        state = self.rdbg.read_watchpoints_state()
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
        self.rdbg.disable_watchpoint(0)
        self.rdbg.disable_watchpoint(3)
        self.rdbg.disable_watchpoint(4)
        self.rdbg.disable_watchpoint(6)

        # Read watchpoints state and verify that we disabled some of the and rest have the same state as we set before
        state = self.rdbg.read_watchpoints_state()
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
        addr1 = 0x10000
        addr2 = 0x20000
        addr3 = 0x30000
        addr4 = 0x30000

        # Write our data to memory
        self.write_data_checked(addr1, 0x12345678)
        self.write_data_checked(addr2, 0x12345678)
        self.write_data_checked(addr3, 0x12345678)
        self.write_data_checked(addr4, 0x12345678)

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
        self.write_program(0, 0x00100073)

        # nop
        self.write_program(4, 0x00000013)
        # nop
        self.write_program(8, 0x00000013)
        # nop
        self.write_program(12, 0x00000013)
        # nop
        self.write_program(16, 0x00000013)

        # First write
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(20, 0x00010537)
        # Load Immediate Value 0x45678000 into x11 (lui x11, 0x45678)
        self.write_program(24, 0x456785B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(28, 0x00B52023)

        # Read from memory
        # Load Immediate Address 0x20000 into x10 (lui x10, 0x20)
        self.write_program(32, 0x00020537)
        # Load the word from memory at address held in x10 (0x20000) into x12
        self.write_program(36, 0x00052603)

        # Second write
        # Load Immediate Address 0x30000 into x10 (lui x10, 0x30)
        self.write_program(40, 0x00030537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(44, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(48, 0x00B52023)

        # Second from memory
        # Load Immediate Address 0x40000 into x10 (lui x10, 0x20)
        self.write_program(52, 0x00040537)
        # Load the word from memory at address held in x10 (0x40000) into x12
        self.write_program(56, 0x00052603)

        # Infinite loop (jal 0)
        self.write_program(60, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify value at address
        self.assertEqual(self.read_data(addr1), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

        # Set memory watchpoints
        self.rdbg.set_watchpoint_on_memory_write(0, 0x10000)
        self.rdbg.set_watchpoint_on_memory_read(1, 0x20000)
        self.rdbg.set_watchpoint_on_memory_access(2, 0x30000)
        self.rdbg.set_watchpoint_on_memory_access(3, 0x40000)

        # Continue and verify that we hit first watchpoint
        self.rdbg.cont(False)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertTrue(self.rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
        self.assertTrue(self.rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should not be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint2_hit, "Watchpoint 2 should not be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint3_hit, "Watchpoint 3 should not be hit.")

        self.assertEqual(self.read_data(addr1), 0x45678000)

        # Continue and verify that we hit second watchpoint
        self.rdbg.cont(False)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertTrue(self.rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should not be hit.")
        self.assertTrue(self.rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint2_hit, "Watchpoint 2 should not be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint3_hit, "Watchpoint 3 should not be hit.")

        # Continue and verify that we hit third watchpoint
        self.rdbg.cont(False)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertTrue(self.rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should not be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should not be hit.")
        self.assertTrue(self.rdbg.read_status().is_watchpoint2_hit, "Watchpoint 2 should be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint3_hit, "Watchpoint 3 should not be hit.")

        self.assertEqual(self.read_data(addr3), 0x87654000)

        # Continue and verify that we hit fourth watchpoint
        self.rdbg.cont(False)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
        self.assertTrue(self.rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should not be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should not be hit.")
        self.assertFalse(self.rdbg.read_status().is_watchpoint2_hit, "Watchpoint 2 should not be hit.")
        self.assertTrue(self.rdbg.read_status().is_watchpoint3_hit, "Watchpoint 3 should be hit.")

    def test_bne_with_debug_fail(self):
        """Test running 48 bytes of generated code that confirms problem with BNE when debugging hardware is enabled."""

        if self.is_blackhole():
            self.skipTest("BNE instruction with debug hardware enabled is fixed in blackhole.")

        # Enable branch prediction
        loader = RiscLoader(self.rdbg, self.context)
        loader.set_branch_prediction(True)

        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   for (int i = 0; i < 64; i++);
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Store 0 to x1 (addi x1, x0, 0)
        self.write_program(4, 0x00000093)
        # Store 63 to x2 (addi x2, x0, 63)
        self.write_program(8, 0x03F00113)
        # See if they are equal (bne x1, x2, 8)
        self.write_program(12, 0x00209463)
        # Jump to ebreak
        self.write_program(16, RiscLoader.get_jump_to_offset_instruction(12))
        # Increase value in x1 (addi x1, x1, 1)
        self.write_program(20, 0x00108093)
        # Jump to bne
        self.write_program(24, RiscLoader.get_jump_to_offset_instruction(-12))
        # ebreak
        self.write_program(28, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(32, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(36, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(40, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(44, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")

        # Continue to proceed with bne test
        self.rdbg.enable_debug()
        self.rdbg.cont(False)

        # Confirm failure
        self.assertFalse(self.rdbg.read_status().is_halted, "Core should not be halted.")
        self.rdbg.halt()
        x1 = self.rdbg.read_gpr(1)  # x1 is counter and it should never go over x2
        x2 = self.rdbg.read_gpr(2)  # x2 is value for loop end
        self.assertGreater(x1, x2)  # Bug will prevent BNE to stop the loop, so x1 will be greater than x2
        self.assertEqual(
            self.read_data(addr), 0x12345678
        )  # Value shouldn't be changed since we never reached the store instruction

    def test_bne_without_debug(self):
        """Test running 48 bytes of generated code that confirms that there is no problem with BNE when debugging hardware is disabled."""

        # Enable branch prediction
        loader = RiscLoader(self.rdbg, self.context)
        loader.set_branch_prediction(True)

        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   for (int i = 0; i < 64; i++);
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Store 0 to x1 (addi x1, x0, 0)
        self.write_program(4, 0x00000093)
        # Store 63 to x2 (addi x2, x0, 63)
        self.write_program(8, 0x03F00113)
        # See if they are equal (bne x1, x2, 8)
        self.write_program(12, 0x00209463)
        # Jump to ebreak
        self.write_program(16, RiscLoader.get_jump_to_offset_instruction(12))
        # Increase value in x1 (addi x1, x1, 1)
        self.write_program(20, 0x00108093)
        # Jump to bne
        self.write_program(24, RiscLoader.get_jump_to_offset_instruction(-12))
        # ebreak
        self.write_program(28, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(32, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(36, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(40, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(44, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")

        # Continue to proceed with bne test
        self.rdbg.enable_debug()
        self.rdbg.continue_without_debug()

        # We should pass for loop very fast and should be halted here already
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")

        # Verify value at address
        self.rdbg.cont()
        self.assertEqual(self.read_data(addr), 0x87654000)
        self.assertFalse(self.rdbg.read_status().is_halted, "Core should not be halted.")

        # Halt and test status
        self.rdbg.halt()
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_ebreak_hit, "ebreak should not be the cause.")

    def test_bne_with_debug_without_bp(self):
        """Test running 48 bytes of generated code that confirms that there is no problem with BNE when debugging hardware is enabled and branch prediction is disabled."""

        # Enable branch prediction
        loader = RiscLoader(self.rdbg, self.context)
        loader.set_branch_prediction(True)

        addr = 0x10000

        # Write our data to memory
        self.write_data_checked(addr, 0x12345678)

        # Write code for brisc core at address 0
        # C++:
        #   asm volatile ("ebreak");
        #   for (int i = 0; i < 64; i++);
        #   asm volatile ("ebreak");
        #   int* a = (int*)0x10000;
        #   *a = 0x87654000;
        #   while (true);

        # ebreak
        self.write_program(0, 0x00100073)
        # Store 0 to x1 (addi x1, x0, 0)
        self.write_program(4, 0x00000093)
        # Store 63 to x2 (addi x2, x0, 63)
        self.write_program(8, 0x03F00113)
        # See if they are equal (bne x1, x2, 8)
        self.write_program(12, 0x00209463)
        # Jump to ebreak
        self.write_program(16, RiscLoader.get_jump_to_offset_instruction(12))
        # Increase value in x1 (addi x1, x1, 1)
        self.write_program(20, 0x00108093)
        # Jump to bne
        self.write_program(24, RiscLoader.get_jump_to_offset_instruction(-12))
        # ebreak
        self.write_program(28, 0x00100073)
        # Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
        self.write_program(32, 0x00010537)
        # Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
        self.write_program(36, 0x876545B7)
        # Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
        self.write_program(40, 0x00B52023)
        # Infinite loop (jal 0)
        self.write_program(44, RiscLoader.get_jump_to_offset_instruction(0))

        # Take risc out of reset
        self.rdbg.set_reset_signal(False)

        # Verify value at address
        self.assertEqual(self.read_data(addr), 0x12345678)
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")

        # Disable branch prediction
        if not self.is_blackhole():
            # Disabling branch prediction fails this test on blackhole :(
            loader.set_branch_prediction(False)

        # Continue to proceed with bne test
        self.rdbg.enable_debug()
        self.rdbg.cont(False)

        # We should pass for loop very fast and should be halted here already
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertTrue(self.rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")

        # Verify value at address
        self.rdbg.cont()
        self.assertEqual(self.read_data(addr), 0x87654000)
        self.assertFalse(self.rdbg.read_status().is_halted, "Core should not be halted.")

        # Halt and test status
        self.rdbg.halt()
        self.assertTrue(self.rdbg.read_status().is_halted, "Core should be halted.")
        self.assertFalse(self.rdbg.read_status().is_ebreak_hit, "ebreak should not be the cause.")
