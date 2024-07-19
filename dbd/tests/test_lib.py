# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import struct
import unittest

from functools import wraps

from parameterized import parameterized

from dbd import tt_debuda_init
from dbd import tt_debuda_lib as lib
from dbd import tt_util

from dbd.tt_coordinate import OnChipCoordinate
from dbd.tt_debuda_context import Context
from dbd.tt_debug_risc import RiscLoader, RiscDebug, RiscLoc
from dbd.tt_firmware import ELF
from dbd.tt_object import DataArray


def invalid_argument_decorator(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		
		return func(*args, **kwargs)
	return wrapper


class TestAutoContext(unittest.TestCase):
	def test_auto_context(self):
		"""Test auto context creation."""
		tt_debuda_init.GLOBAL_CONTEXT = None
		context = lib.check_context()
		self.assertIsNotNone(context)
		self.assertIsInstance(context, Context)

	def test_set_global_context(self):
		"""Test setting global context."""
		tt_debuda_init.GLOBAL_CONTEXT = None
		context = tt_debuda_init.init_debuda()
		self.assertIsNotNone(tt_debuda_init.GLOBAL_CONTEXT)
		self.assertIs(tt_debuda_init.GLOBAL_CONTEXT, context)

	def test_existing_context(self):
		"""Test recognition of existing context."""
		tt_debuda_init.GLOBAL_CONTEXT = None
		
		# Create new global context
		context1 = tt_debuda_init.init_debuda()
		self.assertIsNotNone(tt_debuda_init.GLOBAL_CONTEXT)
		self.assertIs(tt_debuda_init.GLOBAL_CONTEXT, context1)

		# Check for existing context
		context = lib.check_context()
		self.assertIsNotNone(context)
		self.assertIs(tt_debuda_init.GLOBAL_CONTEXT, context)
		self.assertIs(context, context1)
	

class TestReadWrite(unittest.TestCase):
	def setUp(self):
		self.context = tt_debuda_init.init_debuda()
		self.assertIsNotNone(self.context)
		self.assertIsInstance(self.context, Context)

	def test_write_read(self):
		"""Test write data -- read data."""
		core_loc = "0,0"
		address = 0x100
		
		data = [0, 1, 2, 3]
		
		ret = lib.write_to_device(core_loc, address, data)
		self.assertEqual(ret, len(data))

		ret = lib.read_from_device(core_loc, address, num_bytes = len(data))
		self.assertEqual(ret, bytes(data))

	def test_write_read_bytes(self):
		"""Test write bytes -- read bytes."""
		core_loc = "1,1"
		address = 0x100
		
		data = b"abcd"
		
		ret = lib.write_to_device(core_loc, address, data)
		self.assertEqual(ret, len(data))

		ret = lib.read_from_device(core_loc, address, num_bytes = len(data))
		self.assertEqual(ret, data)

	def test_write_read_words(self):
		"""Test write words -- read words."""
		core_loc = "1,1"
		
		address = [0x100, 0x104]
		data = 	  [156, 2]	

		# Write two words to device
		ret = lib.write_word_to_device(core_loc, address[0], data[0])
		self.assertEqual(ret, 4)

		ret = lib.write_word_to_device(core_loc, address[1], data[1])
		self.assertEqual(ret, 4)

		# Read the first word
		ret = lib.read_words_from_device(core_loc, address[0])
		self.assertEqual(ret[0], data[0])

		# Read the second word
		ret = lib.read_words_from_device(core_loc, address[1])
		self.assertEqual(ret[0], data[1])

		# Read both words
		ret = lib.read_words_from_device(core_loc, address[0], word_count=2)
		self.assertEqual(ret, data)

	def test_write_bytes_read_words(self):
		"""Test write bytes -- read words."""
		core_loc = "1,1"
		address = 0x100
		data = [0, 1, 2, 3]
		
		# Write bytes to device
		ret = lib.write_to_device(core_loc, address, data)
		# *4 is because we write 4-byte words
		self.assertEqual(ret, len(data))

		# Read the bytes as words
		ret = lib.read_words_from_device(core_loc, address, word_count=1)
		self.assertEqual(ret[0].to_bytes(4, 'little'), bytes(data))

	@parameterized.expand([
		("abcd", 0x100, 0, 1),			# Invalid core_loc string
		("-10", 0x100, 0, 1),			# Invalid core_loc string
		("0,0", -1, 0, 1),				# Invalid address
		("0,0", 0x100, -1, 1),			# Invalid device_id
		("0,0", 0x100, 112, 1),			# Invalid device_id (too high)
		("0,0", 0x100, 0, -1),			# Invalid word_count
		("0,0", 0x100, 0, 0)			# Invalid word_count
	])
	def test_invalid_inputs_read(self, core_loc, address, device_id, word_count):
		"""Test invalid inputs for read functions."""
		with self.assertRaises(tt_util.TTException):
			lib.read_words_from_device(core_loc, address, device_id, word_count)
		with self.assertRaises(tt_util.TTException):
			# word_count can be used as num_bytes
			lib.read_from_device(core_loc, address, device_id, word_count)

	@parameterized.expand([
		("abcd", 0x100, 5, 0),			# Invalid core_loc string
		("-10", 0x100, 5, 0),			# Invalid core_loc string
		("0,0", -1, 5, 0),				# Invalid address
		("0,0", 0x100, 5, -1),			# Invalid device_id
		("0,0", 0x100, 5, 112),			# Invalid device_id (too high)
		# ("0,0", 0x100, -171, -1),		# Invalid word TODO: What are the limits for word?
	])
	def test_invalid_write_word(self, core_loc, address, data, device_id):
		with self.assertRaises(tt_util.TTException):
			lib.write_word_to_device(core_loc, address, data, device_id)

	@parameterized.expand([
		("abcd", 0x100, b"abcd", 0),	# Invalid core_loc string
		("-10", 0x100, b"abcd", 0),		# Invalid core_loc string
		("0,0", -1, b"abcd", 0),		# Invalid address
		("0,0", 0x100, b"abcd", -1),	# Invalid device_id
		("0,0", 0x100, b"abcd", 112),	# Invalid device_id (too high)
		("0,0", 0x100, [], 0),			# Invalid data
		("0,0", 0x100, b"", 0)			# Invalid data
	])
	def test_invalid_write(self, core_loc, address, data, device_id):
		"""Test invalid inputs for write function."""
		with self.assertRaises(tt_util.TTException):
			lib.write_to_device(core_loc, address, data, device_id)

class TestRunElf(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.context = tt_debuda_init.init_debuda()
		cls.elf_path = "build/riscv-src/run_elf_brisc_test.elf"


	def test_minimal_run_generated_code(self, happy: bool = True):
		"""Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_word_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_word_to_device(core_loc, 0, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_word_to_device(core_loc, 4, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_word_to_device(core_loc, 8, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_word_to_device(core_loc, 12, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x87654000)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_run_elf(self):
		"""Test running an ELF file."""
		core_loc = "0,0"
		addr = 0x0

		# Reset memory at addr
		lib.write_word_to_device(core_loc, addr, 0, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0)
		
		# Run an ELF that writes to the addr and check if it executed correctly
		lib.run_elf(self.elf_path, core_loc, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

	@parameterized.expand([
		("", "0,0", 0, 0),			 	# Invalid ELF path
		("/sbin/non_existing_elf", "0,0", 0, 0),	# Invalid ELF path
		(None, "abcd", 0, 0),			# Invalid core_loc
		(None, "-10", 0, 0),			# Invalid core_loc
		(None, "0,0/", 0, 0),			# Invalid core_loc
		(None, "0,0/00b", 0, 0), 		# Invalid core_loc
		(None, "0,0", -1, 0),			# Invalid risc_id
		(None, "0,0", 4, 0),			# Invalid risc_id
		(None, "0,0", 0, -1),			# Invalid device_id
		(None, "0,0", 0, 112),			# Invalid device_id (too high)
	])
	def test_run_elf_invalid(self, elf_file, core_loc, risc_id, device_id):
		if elf_file is None:
			elf_file = self.elf_path
		with self.assertRaises(tt_util.TTException):
			lib.run_elf(elf_file, core_loc, risc_id, device_id, context=self.context)

	# TODO: This test should be restructured (Issue #70)
	def test_old_elf_test(self):
		""" Running old elf test, formerly done with -t option. """

		# TODO: Add support for triscs as well  -   @parameterized.expand([
		core_loc = "0,0"
		elf_path = "build/riscv-src/brisc-globals.elf"
		
		lib.run_elf(elf_path, core_loc, context=self.context)

		# Testing
		elf = ELF(self.context.server_ifc, { "fw" : elf_path })
		MAILBOX_ADDR, MAILBOX_SIZE, _ = elf.parse_addr_size_type("fw.g_MAILBOX")
		TESTBYTEACCESS_ADDR, _, _ = elf.parse_addr_size_type("fw.g_TESTBYTEACCESS")

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloader = RiscLoader(loc, 0, self.context, self.context.server_ifc, False)
		rdbg = rloader.risc_debug
		loc = rloader.risc_debug.location.loc
		device = loc._device

		# Step 0: halt and continue a couple of times.
		def halt_cont_test():		
			rdbg.halt()
			assert rdbg.is_halted(), f"RISC at location {loc} is not halted."
			rdbg.cont()
			assert not rdbg.is_halted(), f"RISC at location {loc} is halted."
			rdbg.halt()
			assert rdbg.is_halted(), f"RISC at location {loc} is not halted."
			rdbg.cont()
			assert not rdbg.is_halted(), f"RISC at location {loc} is halted."
		halt_cont_test()

		# Step 1: Check that the RISC at location {loc} set the mailbox value to 0xFFB1208C.
		mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
		self.assertEqual(mbox_val, 0xFFB1208C, f"RISC at location {loc} did not set the mailbox value to 0xFFB1208C.")
		#TODO: Add this back in once we get a library version: gpr_command["module"].run("gpr pc,sp", context, ui_state)

		# Step 2: Write 0x1234 to the mailbox to resume operation.
		try:
			da.data = [0x1234]; bts = da.bytes(); rloader.write_block(MAILBOX_ADDR, bts)
		except Exception as e:
			if e.args[0].startswith("Failed to continue"):
				# We are expecting this to assert as here, the core will halt istself by calling halt()
				pass
			else:
				raise e

		# Step 3: Check that the RISC at location {loc} set the mailbox value to 0xFFB12080.
		mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
		self.assertEqual(mbox_val, 0xFFB12080, f"RISC at location {loc} did not set the mailbox value to 0xFFB12080.")

		# Step 4: Check that the RISC at location {loc} is halted.
		status = rdbg.read_status()
		# print_PC_and_source(rdbg.read_gpr(32), elf)
		self.assertTrue(status.is_halted, f"Step 4: RISC at location {loc} is not halted.")
		self.assertTrue(status.is_ebreak_hit, f"Step 4: RISC at location {loc} is not halted with ebreak.")

		# Step 5a: Make sure that the core did not reach step 5
		mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
		self.assertNotEqual(mbox_val, 0xFFB12088, f"RISC at location {loc} reached step 5, but it should not have.")

		# Step 5b: Continue and check that the core reached 0xFFB12088. But first set the breakpoint at
		# function "decrement_mailbox"
		decrement_mailbox_die = elf.names["fw"]["subprogram"]["decrement_mailbox"]
		decrement_mailbox_linkage_name = decrement_mailbox_die.attributes["DW_AT_linkage_name"].value.decode("utf-8")
		decrement_mailbox_address = elf.names["fw"]["symbols"][decrement_mailbox_linkage_name]

		#Step 6. Setting breakpoint at decrement_mailbox
		watchpoint_id = 1 # Out of 8
		rdbg.set_watchpoint_on_pc_address(watchpoint_id, decrement_mailbox_address)
		rdbg.set_watchpoint_on_memory_write(0, TESTBYTEACCESS_ADDR) # Set memory watchpoint on TESTBYTEACCESS
		rdbg.set_watchpoint_on_memory_write(3, TESTBYTEACCESS_ADDR+3)
		rdbg.set_watchpoint_on_memory_write(4, TESTBYTEACCESS_ADDR+4)
		rdbg.set_watchpoint_on_memory_write(5, TESTBYTEACCESS_ADDR+5)

		mbox_val = 1
		timeout_retries = 20
		while mbox_val >= 0 and mbox_val < 0xff000000 and timeout_retries > 0:
			if rdbg.is_halted():
				if rdbg.is_pc_watchpoint_hit():
					pass	# util.INFO (f"Breakpoint hit.")

			try:
				rdbg.cont()
			except Exception as e:
				if e.args[0].startswith("Failed to continue"):
					# We are expecting this to assert as here, the core will hit a breakpoint
					pass
				else:
					raise e
			mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
			# Step 5b: Continue RISC
			timeout_retries -= 1

		if timeout_retries == 0 and mbox_val != 0:
			raise tt_util.TTFatalException(f"RISC at location {loc} did not get past step 6.")
		self.assertFalse(rdbg.is_pc_watchpoint_hit(), f"RISC at location {loc} hit the breakpoint but it should not have.")

		# STEP 7: Testing byte access memory watchpoints")
		mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
		self.assertEqual(mbox_val, 0xff000003, f"RISC at location {loc} did not set the mailbox value to 0xff000003.")
		status = rdbg.read_status()
		self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
		if not status.is_memory_watchpoint_hit or not status.is_watchpoint3_hit:
			raise tt_util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 3.")
		rdbg.cont(verify=False)

		mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
		self.assertEqual(mbox_val, 0xff000005, f"RISC at location {loc} did not set the mailbox value to 0xff000005.")
		status = rdbg.read_status()
		self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
		if not status.is_memory_watchpoint_hit or not status.is_watchpoint5_hit:
			raise tt_util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 5.")
		rdbg.cont(verify=False)

		mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
		self.assertEqual(mbox_val, 0xff000000, f"RISC at location {loc} did not set the mailbox value to 0xff000000.")
		status = rdbg.read_status()
		self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
		if not status.is_memory_watchpoint_hit or not status.is_watchpoint0_hit:
			raise tt_util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 0.")
			return False
		rdbg.cont(verify=False)

		mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
		self.assertEqual(mbox_val, 0xff000004, f"RISC at location {loc} did not set the mailbox value to 0xff000004.")
		status = rdbg.read_status()
		self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
		if not status.is_memory_watchpoint_hit or not status.is_watchpoint4_hit:
			raise tt_util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 4.")
		rdbg.cont(verify=False)

		# STEP END:
		mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE); da = DataArray("g_MAILBOX"); mbox_val = da.from_bytes(mbox_val)[0]
		self.assertEqual(mbox_val, 0xFFB12088, f"RISC at location {loc} did not reach step STEP END.")

class TestDebugging(unittest.TestCase):
	def setUp(self):
		self.context = tt_debuda_init.init_debuda()
		self.assertIsNotNone(self.context)
		self.assertIsInstance(self.context, Context)

	def test_ebreak(self, happy: bool = True):
		"""Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_word_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# ebreak
		lib.write_word_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_word_to_device(core_loc, 4, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_word_to_device(core_loc, 8, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_word_to_device(core_loc, 12, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_word_to_device(core_loc, 16, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

		# Take risc out of reset
		rdbg.set_reset_signal(False)

		# Verify value at address
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		# Value should not be changed and should stay the same since core is in halt
		self.assertEqual(ret[0], 0x12345678)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

	def test_continue(self, happy: bool = True):
		"""Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_word_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# ebreak
		lib.write_word_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_word_to_device(core_loc, 4, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_word_to_device(core_loc, 8, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_word_to_device(core_loc, 12, 0x00B52023, context=self.context)
		# Infinite loop (jal 0)
		lib.write_word_to_device(core_loc, 16, RiscLoader.get_jump_to_offset_instruction(0), context=self.context)

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

	def test_halt_continue(self, happy: bool = True):
		"""Test running 20 bytes of generated code that just write data on memory and does infinite loop. All that is done on brisc."""
		core_loc = "0,0"
		addr = 0x10000

		loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
		rloc = RiscLoc(loc, 0, 0)
		rdbg = RiscDebug(rloc, self.context.server_ifc)

		# Stop risc with reset
		rdbg.set_reset_signal(True)

		# Write our data to memory
		lib.write_word_to_device(core_loc, addr, 0x12345678, context=self.context)
		ret = lib.read_words_from_device(core_loc, addr, context=self.context)
		self.assertEqual(ret[0], 0x12345678)

		# Write code for brisc core at address 0
		# ebreak
		lib.write_word_to_device(core_loc, 0, 0x00100073, context=self.context)
		# Load Immediate Address 0x10000 into x10 (lui x10, 0x10)
		lib.write_word_to_device(core_loc, 4, 0x00010537, context=self.context)
		# Load Immediate Value 0x87654000 into x11 (lui x11, 0x87654)
		lib.write_word_to_device(core_loc, 8, 0x876545B7, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_word_to_device(core_loc, 12, 0x00B52023, context=self.context)
		# Increment x11 by 1 (addi x11, x11, 1)
		lib.write_word_to_device(core_loc, 16, 0x00158593, context=self.context)
		# Store the word value from register x11 to address from register x10 (sw x11, 0(x10))
		lib.write_word_to_device(core_loc, 20, 0x00B52023, context=self.context)
		# Infinite loop (jal -8)
		lib.write_word_to_device(core_loc, 24, RiscLoader.get_jump_to_offset_instruction(-8), context=self.context)

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
