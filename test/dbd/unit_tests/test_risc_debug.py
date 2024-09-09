# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from dbd import tt_debuda_init
from dbd import tt_debuda_lib as lib

from dbd.tt_coordinate import OnChipCoordinate
from dbd.tt_debuda_context import Context
from dbd.tt_debug_risc import RiscLoader, RiscDebug, RiscLoc, get_register_index

class TestDebugging(unittest.TestCase):
	def setUp(self):
		self.context = tt_debuda_init.init_debuda()
		self.assertIsNotNone(self.context)
		self.assertIsInstance(self.context, Context)

	def is_blackhole(self):
		"""Check if the device is blackhole."""
		return self.context.devices[0]._arch == "blackhole"

	def test_reset_all_functional_workers(self):
		"""Reset all functional workers."""
		for device in self.context.devices.values():
			device.all_riscs_assert_soft_reset()
			for rdbg in device.debuggable_cores:
				self.assertTrue(rdbg.is_in_reset())

	def test_read_write_gpr(self):
		"""Write then read value in all registers (except zero and pc)."""
		core_loc = "0,0"

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)
		self.assertTrue(rdbg.is_in_reset())

		# Write code for brisc core at address 0
		# C++:
		#   asm volatile ("nop");
		#   while (true);

		# NOP
		lib.write_words_to_device(core_loc, 0, 0x00000013, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 4, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)
		self.assertFalse(rdbg.is_in_reset())

		# Halt core
		rdbg.enable_debug()
		rdbg.halt()

		# Value should not be changed and should stay the same since core is in halt
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")

		# Test readonly registers
		self.assertEqual(rdbg.read_gpr(get_register_index("zero")), 0, "zero should always be 0.")
		self.assertEqual(rdbg.read_gpr(get_register_index("pc")), 4, "PC should be 4.")

		# Test write then read for all other registers
		for i in range(1, 31):
			rdbg.write_gpr(i, 0x12345678)
			self.assertEqual(rdbg.read_gpr(i), 0x12345678, f"Register x{i} should be 0x12345678.")
			rdbg.write_gpr(i, 0x87654321)
			self.assertEqual(rdbg.read_gpr(i), 0x87654321, f"Register x{i} should be 0x12345678.")

		# Stop risc with reset
		rdbg.set_reset_signal(True)
		self.assertTrue(rdbg.is_in_reset())

	def test_read_write_l1_memory(self):
		"""Testing read_memory and write_memory through debugging interface on L1 memory range."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)
		self.assertTrue(rdbg.is_in_reset())

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# C++:
		#   while (true);

		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 0, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)
		self.assertFalse(rdbg.is_in_reset())

		# Halt core
		rdbg.enable_debug()
		rdbg.halt()

		# Value should not be changed and should stay the same since core is in halt
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")

		# Test read and write memory
		self.assertEqual(rdbg.read_memory(addr), 0x12345678, "Memory value should be 0x12345678.")
		rdbg.write_memory(addr, 0x87654321)
		self.assertEqual(rdbg.read_memory(addr), 0x87654321, "Memory value should be 0x87654321.")
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x87654321)

		# Stop risc with reset
		rdbg.set_reset_signal(True)
		self.assertTrue(rdbg.is_in_reset())

	def test_read_write_private_memory(self):
		"""Testing read_memory and write_memory through debugging interface on private core memory range."""
		core_loc = "0,0"
		addr = 0xFFB00000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)
		self.assertTrue(rdbg.is_in_reset())

		# Write code for brisc core at address 0
		# C++:
		#   while (true);

		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 0, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)
		self.assertFalse(rdbg.is_in_reset())

		# Halt core
		rdbg.enable_debug()
		rdbg.halt()

		# Value should not be changed and should stay the same since core is in halt
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")

		# Test write and read memory
		rdbg.write_memory(addr, 0x12345678)
		self.assertEqual(rdbg.read_memory(addr), 0x12345678, "Memory value should be 0x12345678.")
		rdbg.write_memory(addr, 0x87654321)
		self.assertEqual(rdbg.read_memory(addr), 0x87654321, "Memory value should be 0x87654321.")

		# Stop risc with reset
		rdbg.set_reset_signal(True)
		self.assertTrue(rdbg.is_in_reset())

	def test_minimal_run_generated_code(self):
		"""Test running 16 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)
		self.assertTrue(rdbg.is_in_reset())

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# C++:
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true);

		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 0, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 4, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 8, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 12, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)
		self.assertFalse(rdbg.is_in_reset())

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x87654000)

		# Stop risc with reset
		rdbg.set_reset_signal(True)
		self.assertTrue(rdbg.is_in_reset())

	def test_ebreak(self):
		"""Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)
		pc_register_index = get_register_index("pc")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# C++:
		#   asm volatile ("ebreak");
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true);

		# ebreak
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 4, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 8, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 12, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 16, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should not be changed and should stay the same since core is in halt
		self.assertEqual(ret[0], 0x12345678)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertTrue(rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
		if self.is_blackhole():
			# Blackhole changed behaviour of PC register, so we need to test it accordingly
			self.assertEqual(rdbg.read_gpr(pc_register_index), 0, "PC should be 0.")
		else:
			self.assertEqual(rdbg.read_gpr(pc_register_index), 4, "PC should be 4.")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_ebreak_and_step(self):
		"""Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)
		pc_register_index = get_register_index("pc")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# C++:
		#   asm volatile ("ebreak");
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true);

		# ebreak
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 4, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 8, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 12, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 16, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# On blackhole, we need to step one more time...
		if self.is_blackhole():
			rdbg.step()

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should not be changed and should stay the same since core is in halt
		self.assertEqual(ret[0], 0x12345678)
		self.assertEqual(rdbg.read_gpr(pc_register_index), 4, "PC should be 4.")

		# Step and verify that pc is 8 and value is not changed
		rdbg.step()
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)
		self.assertEqual(rdbg.read_gpr(pc_register_index), 8, "PC should be 8.")

		# Step and verify that pc is 12 and value has changed
		rdbg.step()
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x87654000)
		self.assertEqual(rdbg.read_gpr(pc_register_index), 12, "PC should be 12.")

		# Since we are on endless loop, we should never go past 16
		for i in range(10):
			# Step and verify that pc is 16 and value has changed
			rdbg.step()
			self.assertEqual(rdbg.read_gpr(pc_register_index), 16, "PC should be 16.")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_continue(self):
		"""Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# C++:
		#   asm volatile ("ebreak");
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true);

		# ebreak
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 4, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 8, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 12, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 16, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Continue
		rdbg.enable_debug()
		rdbg.cont()

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should not be changed and should stay the same since core is in halt
		self.assertEqual(ret[0], 0x87654000)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_halt_continue(self):
		"""Test running 28 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# C++:
		#   asm volatile ("ebreak");
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true)
		#     *a++;

		# ebreak
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 4, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 8, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 12, 0x00B52023, context=self.context)
		# Increment x11 by 1 (addi x11, x11, 1)
		lib.write_words_to_device(core_loc, 16, 0x00158593, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 20, 0x00B52023, context=self.context)
		# Infinite loop (jal -8)
		lib.write_words_to_device(core_loc, 24, RiscLoader.get_jump_to_offset_instruction(-8), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify that value didn't change cause of ebreak
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Continue
		rdbg.enable_debug()
		rdbg.cont()

		# Verify that value changed cause of continue
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertGreaterEqual(ret[0], 0x87654000)
		previous_value = ret[0]

		# Loop halt and continue
		for i in range(10):
			# Halt
			rdbg.halt()

			# Read value
			ret = lib.read_words_from_device(core_loc, addr, context=self.context)
			self.assertGreater(ret[0], previous_value)
			previous_value = ret[0]

			# Second read should have the same value if core is halted
			ret = lib.read_words_from_device(core_loc, addr, context=self.context)
			self.assertEqual(ret[0], previous_value)

			# Continue
			rdbg.cont()

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_halt_status(self):
		"""Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# C++:
		#   asm volatile ("ebreak");
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true);

		# ebreak
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 4, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 8, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 12, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 16, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should not be changed and should stay the same since core is in halt
		self.assertEqual(ret[0], 0x12345678)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertTrue(rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")

		# Continue
		rdbg.enable_debug()
		rdbg.cont()

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should not be changed and should stay the same since core is in halt
		self.assertEqual(ret[0], 0x87654000)
		self.assertFalse(rdbg.read_status().is_halted, "Core should not be halted.")

		# Halt and test status
		rdbg.halt()
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertFalse(rdbg.read_status().is_ebreak_hit, "ebreak should not be the cause.")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	@unittest.skip("Invalidate cache is not reliable on wormhole and not working on blackhole at all...")
	def test_invalidate_cache(self):
		"""Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)
		pc_register_index = get_register_index("pc")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write endless loop for brisc core at address 0
		# C++:
		#   while (true);
		#   while (true);
		#   while (true);
		#   while (true);
		lib.write_words_to_device(core_loc, 0, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)
		lib.write_words_to_device(core_loc, 4, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)
		lib.write_words_to_device(core_loc, 8, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)
		lib.write_words_to_device(core_loc, 12, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Halt core
		rdbg.enable_debug()
		rdbg.halt()

		# Value should not be changed and should stay the same since core is in halt
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertEqual(rdbg.read_gpr(pc_register_index), 0, "PC should be 0.")

		# Write new code for brisc core at address 0
		# C++:
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true);

		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 0, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 4, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 8, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 12, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Invalidate instruction cache
		rdbg.invalidate_instruction_cache()

		# Continue
		rdbg.cont()
		self.assertFalse(rdbg.read_status().is_halted, "Core should not be halted.")

		# Halt to verify PC
		rdbg.halt()
		self.assertTrue(rdbg.read_status().is_halted, "Core should not be halted.")
		self.assertEqual(rdbg.read_gpr(pc_register_index), 12, "PC should be 12.")

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should be changed
		self.assertEqual(ret[0], 0x87654000)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_invalidate_cache_with_reset(self):
		"""Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation by reseting core. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)
		pc_register_index = get_register_index("pc")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write endless loop for brisc core at address 0
		# C++:
		#   while (true);
		#   while (true);
		#   while (true);
		#   while (true);
		lib.write_words_to_device(core_loc, 0, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)
		lib.write_words_to_device(core_loc, 4, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)
		lib.write_words_to_device(core_loc, 8, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)
		lib.write_words_to_device(core_loc, 12, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Halt core
		rdbg.enable_debug()
		rdbg.halt()

		# Value should not be changed and should stay the same since core is in halt
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertEqual(rdbg.read_gpr(pc_register_index), 0, "PC should be 0.")

		# Write new code for brisc core at address 0
		# C++:
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true);

		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 0, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 4, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 8, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 12, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Invalidate instruction cache with reset
		rdbg.set_reset_signal(True)
		rdbg.set_reset_signal(False)
		self.assertFalse(rdbg.read_status().is_halted, "Core should not be halted.")

		# Halt to verify PC
		rdbg.halt()
		self.assertTrue(rdbg.read_status().is_halted, "Core should not be halted.")
		self.assertEqual(rdbg.read_gpr(pc_register_index), 12, "PC should be 12.")

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should be changed
		self.assertEqual(ret[0], 0x87654000)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_invalidate_cache_with_nops_and_long_jump(self):
		"""Test running 16 bytes of generated code that just write data on memory and tries to reload it with instruction cache invalidation by having NOPs block and jump back. All that is done on brisc."""
		core_loc = "0,0"
		break_addr = 0x950
		jump_addr = 0x2000
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)
		pc_register_index = get_register_index("pc")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

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
		for i in range(jump_addr//4):
			lib.write_words_to_device(core_loc, i * 4, 0x00000013, context=self.context)
		lib.write_words_to_device(core_loc, break_addr, 0x00100073, context=self.context)
		lib.write_words_to_device(core_loc, jump_addr, RiscLoader.get_jump_to_offset_instruction(-jump_addr), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Value should not be changed and should stay the same since core is in halt
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertTrue(rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
		if self.is_blackhole():
			# Blackhole changed behaviour of PC register, so we need to test it accordingly
			self.assertEqual(rdbg.read_gpr(pc_register_index), break_addr, f"PC should be {break_addr}.")
		else:
			self.assertEqual(rdbg.read_gpr(pc_register_index), break_addr + 4, f"PC should be {break_addr + 4}.")

		# Write new code for brisc core at address 0
		# C++:
		#   int* a = (int*)0x10000;
		#   *a = 0x87654000;
		#   while (true);

		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 0, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 4, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 8, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 12, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Continue execution
		rdbg.cont(False)
		self.assertFalse(rdbg.read_status().is_halted, "Core should not be halted.")

		# Halt to verify PC
		rdbg.halt()
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertEqual(rdbg.read_gpr(pc_register_index), 12, "PC should be 12.")

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should be changed
		self.assertEqual(ret[0], 0x87654000)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_watchpoint_on_pc_address(self):
		"""Test running 36 bytes of generated code that just write data on memory and does watchpoint on pc address. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)
		pc_register_index = get_register_index("pc")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

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
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)
		# nop
		lib.write_words_to_device(core_loc, 4, 0x00000013, context=self.context)
		# nop
		lib.write_words_to_device(core_loc, 8, 0x00000013, context=self.context)
		# nop
		lib.write_words_to_device(core_loc, 12, 0x00000013, context=self.context)
		# nop
		lib.write_words_to_device(core_loc, 16, 0x00000013, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 20, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 24, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 28, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 32, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should not be changed and should stay the same since core is in halt
		self.assertEqual(ret[0], 0x12345678)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertTrue(rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
		self.assertFalse(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
		if self.is_blackhole():
			# Blackhole changed behaviour of PC register, so we need to test it accordingly
			self.assertEqual(rdbg.read_gpr(pc_register_index), 0, "PC should be 0.")
		else:
			self.assertEqual(rdbg.read_gpr(pc_register_index), 4, "PC should be 4.")

		# Set watchpoint on address 12 and 32
		rdbg.set_watchpoint_on_pc_address(0, 12)
		rdbg.set_watchpoint_on_pc_address(1, 32)

		# Continue and verify that we hit first watchpoint
		rdbg.cont(False)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertFalse(rdbg.read_status().is_ebreak_hit, "ebreak should not be the cause.")
		self.assertTrue(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should be the cause.")
		self.assertFalse(rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should not be the cause.")
		self.assertTrue(rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should not be hit.")

		self.assertLess(rdbg.read_gpr(pc_register_index), 28, "PC should be less than 28.")
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Continue and verify that we hit first watchpoint
		rdbg.cont(False)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertFalse(rdbg.read_status().is_ebreak_hit, "ebreak should not be the cause.")
		self.assertTrue(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should be the cause.")
		self.assertFalse(rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should not be the cause.")
		self.assertFalse(rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should not be hit.")
		self.assertTrue(rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should be hit.")
		self.assertEqual(rdbg.read_gpr(pc_register_index), 32, "PC should be 32.")
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x87654000)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_watchpoint_address(self):
		"""Test setting and reading watchpoint address (both memory and PC)."""
		core_loc = "0,0"

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write code for brisc core at address 0
		# C++:
		#   asm volatile ("ebreak");
		#   while (true);

		# ebreak
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 4, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify that we hit ebreak
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertTrue(rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
		self.assertFalse(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

		# Set PC watchpoints
		rdbg.set_watchpoint_on_pc_address(0, 12)
		rdbg.set_watchpoint_on_pc_address(1, 32)
		rdbg.set_watchpoint_on_pc_address(2, 0x1234)
		rdbg.set_watchpoint_on_pc_address(3, 0x8654)
		rdbg.set_watchpoint_on_pc_address(4, 0x87654321)
		rdbg.set_watchpoint_on_pc_address(5, 0x12345678)
		rdbg.set_watchpoint_on_pc_address(6, 0)
		rdbg.set_watchpoint_on_pc_address(7, 0xFFFFFFFF)

		# Read PC watchpoints addresses and verify it is the same as we set
		self.assertEqual(rdbg.read_watchpoint_address(0), 12, "Address should be 12.")
		self.assertEqual(rdbg.read_watchpoint_address(1), 32, "Address should be 32.")
		self.assertEqual(rdbg.read_watchpoint_address(2), 0x1234, "Address should be 0x1234.")
		self.assertEqual(rdbg.read_watchpoint_address(3), 0x8654, "Address should be 0x8654.")
		self.assertEqual(rdbg.read_watchpoint_address(4), 0x87654321, "Address should be 0x87654321.")
		self.assertEqual(rdbg.read_watchpoint_address(5), 0x12345678, "Address should be 0x12345678.")
		self.assertEqual(rdbg.read_watchpoint_address(6), 0, "Address should be 0.")
		self.assertEqual(rdbg.read_watchpoint_address(7), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")

		# Set memory watchpoints for access
		rdbg.set_watchpoint_on_memory_access(0, 0xFFFFFFFF)
		rdbg.set_watchpoint_on_memory_access(1, 12)
		rdbg.set_watchpoint_on_memory_access(2, 32)
		rdbg.set_watchpoint_on_memory_access(3, 0x1234)
		rdbg.set_watchpoint_on_memory_access(4, 0x8654)
		rdbg.set_watchpoint_on_memory_access(5, 0x87654321)
		rdbg.set_watchpoint_on_memory_access(6, 0x12345678)
		rdbg.set_watchpoint_on_memory_access(7, 0)

		# Read memory watchpoints addresses and verify it is the same as we set
		self.assertEqual(rdbg.read_watchpoint_address(0), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")
		self.assertEqual(rdbg.read_watchpoint_address(1), 12, "Address should be 12.")
		self.assertEqual(rdbg.read_watchpoint_address(2), 32, "Address should be 32.")
		self.assertEqual(rdbg.read_watchpoint_address(3), 0x1234, "Address should be 0x1234.")
		self.assertEqual(rdbg.read_watchpoint_address(4), 0x8654, "Address should be 0x8654.")
		self.assertEqual(rdbg.read_watchpoint_address(5), 0x87654321, "Address should be 0x87654321.")
		self.assertEqual(rdbg.read_watchpoint_address(6), 0x12345678, "Address should be 0x12345678.")
		self.assertEqual(rdbg.read_watchpoint_address(7), 0, "Address should be 0.")

		# Set memory watchpoints for read
		rdbg.set_watchpoint_on_memory_read(0, 0)
		rdbg.set_watchpoint_on_memory_read(1, 0xFFFFFFFF)
		rdbg.set_watchpoint_on_memory_read(2, 12)
		rdbg.set_watchpoint_on_memory_read(3, 32)
		rdbg.set_watchpoint_on_memory_read(4, 0x1234)
		rdbg.set_watchpoint_on_memory_read(5, 0x8654)
		rdbg.set_watchpoint_on_memory_read(6, 0x87654321)
		rdbg.set_watchpoint_on_memory_read(7, 0x12345678)

		# Read memory watchpoints addresses and verify it is the same as we set
		self.assertEqual(rdbg.read_watchpoint_address(0), 0, "Address should be 0.")
		self.assertEqual(rdbg.read_watchpoint_address(1), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")
		self.assertEqual(rdbg.read_watchpoint_address(2), 12, "Address should be 12.")
		self.assertEqual(rdbg.read_watchpoint_address(3), 32, "Address should be 32.")
		self.assertEqual(rdbg.read_watchpoint_address(4), 0x1234, "Address should be 0x1234.")
		self.assertEqual(rdbg.read_watchpoint_address(5), 0x8654, "Address should be 0x8654.")
		self.assertEqual(rdbg.read_watchpoint_address(6), 0x87654321, "Address should be 0x87654321.")
		self.assertEqual(rdbg.read_watchpoint_address(7), 0x12345678, "Address should be 0x12345678.")

		# Set memory watchpoints for write
		rdbg.set_watchpoint_on_memory_write(0, 0x12345678)
		rdbg.set_watchpoint_on_memory_write(1, 0)
		rdbg.set_watchpoint_on_memory_write(2, 0xFFFFFFFF)
		rdbg.set_watchpoint_on_memory_write(3, 12)
		rdbg.set_watchpoint_on_memory_write(4, 32)
		rdbg.set_watchpoint_on_memory_write(5, 0x1234)
		rdbg.set_watchpoint_on_memory_write(6, 0x8654)
		rdbg.set_watchpoint_on_memory_write(7, 0x87654321)

		# Read memory watchpoints addresses and verify it is the same as we set
		self.assertEqual(rdbg.read_watchpoint_address(0), 0x12345678, "Address should be 0x12345678.")
		self.assertEqual(rdbg.read_watchpoint_address(1), 0, "Address should be 0.")
		self.assertEqual(rdbg.read_watchpoint_address(2), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")
		self.assertEqual(rdbg.read_watchpoint_address(3), 12, "Address should be 12.")
		self.assertEqual(rdbg.read_watchpoint_address(4), 32, "Address should be 32.")
		self.assertEqual(rdbg.read_watchpoint_address(5), 0x1234, "Address should be 0x1234.")
		self.assertEqual(rdbg.read_watchpoint_address(6), 0x8654, "Address should be 0x8654.")
		self.assertEqual(rdbg.read_watchpoint_address(7), 0x87654321, "Address should be 0x87654321.")

		# Set mixed watchpoins
		rdbg.set_watchpoint_on_pc_address(0, 12)
		rdbg.set_watchpoint_on_pc_address(1, 32)
		rdbg.set_watchpoint_on_memory_access(2, 0x1234)
		rdbg.set_watchpoint_on_memory_access(3, 0x8654)
		rdbg.set_watchpoint_on_memory_read(4, 0x87654321)
		rdbg.set_watchpoint_on_memory_read(5, 0x12345678)
		rdbg.set_watchpoint_on_memory_write(6, 0)
		rdbg.set_watchpoint_on_memory_write(7, 0xFFFFFFFF)

		# Read watchpoints addresses and verify it is the same as we set
		self.assertEqual(rdbg.read_watchpoint_address(0), 12, "Address should be 12.")
		self.assertEqual(rdbg.read_watchpoint_address(1), 32, "Address should be 32.")
		self.assertEqual(rdbg.read_watchpoint_address(2), 0x1234, "Address should be 0x1234.")
		self.assertEqual(rdbg.read_watchpoint_address(3), 0x8654, "Address should be 0x8654.")
		self.assertEqual(rdbg.read_watchpoint_address(4), 0x87654321, "Address should be 0x87654321.")
		self.assertEqual(rdbg.read_watchpoint_address(5), 0x12345678, "Address should be 0x12345678.")
		self.assertEqual(rdbg.read_watchpoint_address(6), 0, "Address should be 0.")
		self.assertEqual(rdbg.read_watchpoint_address(7), 0xFFFFFFFF, "Address should be 0xFFFFFFFF.")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_watchpoint_state(self):
		"""Test setting and disabling watchpoint state (both memory and PC)."""
		core_loc = "0,0"

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write code for brisc core at address 0
		# C++:
		#   asm volatile ("ebreak");
		#   while (true);

		# ebreak
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 4, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify that we hit ebreak
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertTrue(rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
		self.assertFalse(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

		# Set watchpoints
		rdbg.set_watchpoint_on_pc_address(0, 12)
		rdbg.set_watchpoint_on_pc_address(1, 32)
		rdbg.set_watchpoint_on_memory_access(2, 0x1234)
		rdbg.set_watchpoint_on_memory_access(3, 0x8654)
		rdbg.set_watchpoint_on_memory_read(4, 0x87654321)
		rdbg.set_watchpoint_on_memory_read(5, 0x12345678)
		rdbg.set_watchpoint_on_memory_write(6, 0)
		rdbg.set_watchpoint_on_memory_write(7, 0xFFFFFFFF)

		# Read watchpoints state and verify it is the same as we set
		state = rdbg.read_watchpoints_state()
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
		rdbg.disable_watchpoint(0)
		rdbg.disable_watchpoint(3)
		rdbg.disable_watchpoint(4)
		rdbg.disable_watchpoint(6)

		# Read watchpoints state and verify that we disabled some of the and rest have the same state as we set before
		state = rdbg.read_watchpoints_state()
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

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_memory_watchpoint(self):
		"""Test running 64 bytes of generated code that just write data on memory and tests memory watchpoints. All that is done on brisc."""
		core_loc = "0,0"
		addr1 = 0x10000
		addr2 = 0x20000
		addr3 = 0x30000
		addr4 = 0x30000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)
		pc_register_index = get_register_index("pc")

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_words_to_device(core_loc, addr1, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr1, context=self.context)
		self.assertEqual(ret[0], 0x12345678)
		lib.write_words_to_device(core_loc, addr2, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr2, context=self.context)
		self.assertEqual(ret[0], 0x12345678)
		lib.write_words_to_device(core_loc, addr3, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr3, context=self.context)
		self.assertEqual(ret[0], 0x12345678)
		lib.write_words_to_device(core_loc, addr4, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr4, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

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
		lib.write_words_to_device(core_loc, 0, 0x00100073, context=self.context)

		# nop
		lib.write_words_to_device(core_loc, 4, 0x00000013, context=self.context)
		# nop
		lib.write_words_to_device(core_loc, 8, 0x00000013, context=self.context)
		# nop
		lib.write_words_to_device(core_loc, 12, 0x00000013, context=self.context)
		# nop
		lib.write_words_to_device(core_loc, 16, 0x00000013, context=self.context)

		# First write
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_words_to_device(core_loc, 20, 0x00010537, context=self.context)
		# Load Immediate Value 0x45678000 into x11 (lui x11, 0x45678)
		lib.write_words_to_device(core_loc, 24, 0x456785B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 28, 0x00B52023, context=self.context)

		# Read from memory
		# Load Immediate Address 0x20000 into x10 (lui x10, 0x20)
		lib.write_words_to_device(core_loc, 32, 0x00020537, context=self.context)
		# Load the word from memory at address held in x10 (0x20000) into x12
		lib.write_words_to_device(core_loc, 36, 0x00052603, context=self.context)

		# Second write
		# Load Immediate Address 0x30000 into x10 (lui x10, 0x30)
		lib.write_words_to_device(core_loc, 40, 0x00030537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_words_to_device(core_loc, 44, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_words_to_device(core_loc, 48, 0x00B52023, context=self.context)

		# Second from memory
		# Load Immediate Address 0x40000 into x10 (lui x10, 0x20)
		lib.write_words_to_device(core_loc, 52, 0x00040537, context=self.context)
		# Load the word from memory at address held in x10 (0x40000) into x12
		lib.write_words_to_device(core_loc, 56, 0x00052603, context=self.context)

		# Infinite loop (jal 0)
		lib.write_words_to_device(core_loc, 60, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr1, context=self.context)
		# Value should not be changed and should stay the same since core is in halt
		self.assertEqual(ret[0], 0x12345678)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertTrue(rdbg.read_status().is_ebreak_hit, "ebreak should be the cause.")
		self.assertFalse(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")

		# Set memory watchpoints
		rdbg.set_watchpoint_on_memory_write(0, 0x10000)
		rdbg.set_watchpoint_on_memory_read(1, 0x20000)
		rdbg.set_watchpoint_on_memory_access(2, 0x30000)
		rdbg.set_watchpoint_on_memory_access(3, 0x40000)

		# Continue and verify that we hit first watchpoint
		rdbg.cont(False)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertFalse(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
		self.assertTrue(rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
		self.assertTrue(rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should not be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint2_hit, "Watchpoint 2 should not be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint3_hit, "Watchpoint 3 should not be hit.")

		ret = lib.read_words_from_device(core_loc, addr1, context=self.context)
		self.assertEqual(ret[0], 0x45678000)

		# Continue and verify that we hit second watchpoint
		rdbg.cont(False)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertFalse(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
		self.assertTrue(rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
		self.assertFalse(rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should not be hit.")
		self.assertTrue(rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint2_hit, "Watchpoint 2 should not be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint3_hit, "Watchpoint 3 should not be hit.")

		# Continue and verify that we hit third watchpoint
		rdbg.cont(False)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertFalse(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
		self.assertTrue(rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
		self.assertFalse(rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should not be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should not be hit.")
		self.assertTrue(rdbg.read_status().is_watchpoint2_hit, "Watchpoint 2 should be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint3_hit, "Watchpoint 3 should not be hit.")

		ret = lib.read_words_from_device(core_loc, addr3, context=self.context)
		self.assertEqual(ret[0], 0x87654000)

		# Continue and verify that we hit fourth watchpoint
		rdbg.cont(False)
		self.assertTrue(rdbg.read_status().is_halted, "Core should be halted.")
		self.assertFalse(rdbg.read_status().is_pc_watchpoint_hit, "PC watchpoint should not be the cause.")
		self.assertTrue(rdbg.read_status().is_memory_watchpoint_hit, "Memory watchpoint should be the cause.")
		self.assertFalse(rdbg.read_status().is_watchpoint0_hit, "Watchpoint 0 should not be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint1_hit, "Watchpoint 1 should not be hit.")
		self.assertFalse(rdbg.read_status().is_watchpoint2_hit, "Watchpoint 2 should not be hit.")
		self.assertTrue(rdbg.read_status().is_watchpoint3_hit, "Watchpoint 3 should be hit.")

		# Stop risc with reset
		rdbg.set_reset_signal(True)
