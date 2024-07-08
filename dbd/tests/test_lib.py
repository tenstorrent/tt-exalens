import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import tt_debuda_init
import tt_debuda_lib as lib
from tt_debuda_context import Context


class TestAutoContext(unittest.TestCase):
	def test_auto_context(self):
		self.assertIsNone(tt_debuda_init.GLOBAL_CONTEXT)
		context = lib.check_context()
		self.assertIsNotNone(context)
		self.assertIsInstance(context, Context)
	
	def test_set_global_context(self):
		context = tt_debuda_init.init_debuda()
		self.assertIsNotNone(tt_debuda_init.GLOBAL_CONTEXT)
		self.assertIs(tt_debuda_init.GLOBAL_CONTEXT, context)


class testReadWrite(unittest.TestCase):
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
		ret = [int(x) for x in ret]
		self.assertEquals(ret, data)

	def test_write_read_bytes(self):
		"""Test write bytes -- read bytes."""
		core_loc = "1,1"
		address = 0x100
		
		data = b"abcd"
		
		ret = lib.write_to_device(core_loc, address, data)
		self.assertEqual(ret, len(data))

		ret = lib.read_from_device(core_loc, address, num_bytes = len(data))
		self.assertEquals(ret, data)

	def test_write_read_words(self):
		"""Test write words -- read words."""
		core_loc = "2,2"
		
		address = [0x100, 0x104]
		data = 	  [156, 212]	

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
		self.assertEquals(ret, data)
