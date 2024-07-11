# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
import os

import tt_debuda_init
from tt_debuda_context import Context
from tt_debuda_server import start_server, stop_server



CACHE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_cache.pkl'))

def tearDownModule():
	if os.path.exists(CACHE_PATH):
		os.remove(CACHE_PATH)

class TestLocalDebudaInit(unittest.TestCase):
	def test_local_init(self):
		"""Test local debuda initialization."""
		context = tt_debuda_init.init_debuda()
		self.assertIsNotNone(context)
		self.assertIsInstance(context, Context)

	def test_local_with_cache(self):
		"""Test local debuda initialization with cache."""
		context = tt_debuda_init.init_debuda(cache_path=CACHE_PATH)
		self.assertIsNotNone(context)
		self.assertIsInstance(context, Context)

	def test_local_wanted_devices(self):
		"""Test local debuda initialization with specification of wanted devices."""
		context = tt_debuda_init.init_debuda(wanted_devices=[0,])
		self.assertIsNotNone(context)
		self.assertIsInstance(context, Context)

	# TODO: See how to go about testing debuda with output dir & netlist path

class TestRemoteDebuda(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		cls.server = start_server(5555, "")

	@classmethod
	def tearDownClass(cls) -> None:
		stop_server(cls.server)

	def test_remote_init(self):
		"""Test remote debuda initialization."""
		context = tt_debuda_init.init_debuda_remote()
		self.assertIsNotNone(context)
		self.assertIsInstance(context, Context)

	def test_remote_with_cache(self):
		"""Test remote debuda initialization with cache."""
		context = tt_debuda_init.init_debuda_remote(cache_path=CACHE_PATH)
		self.assertIsNotNone(context)
		self.assertIsInstance(context, Context)


class TestCachedDebuda(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		context = tt_debuda_init.init_debuda(cache_path=CACHE_PATH)
		# Execute a sample command to populate the cache
		context.server_ifc.get_run_dirpath()
		context.server_ifc.save()
		del context

	def test_cached_init(self):
		"""Test debuda initialization with cache."""
		context = tt_debuda_init.init_debuda_cached(cache_path=CACHE_PATH)
		self.assertIsNotNone(context)
		self.assertIsInstance(context, Context)
		context.server_ifc.get_run_dirpath()


if __name__ == "__main__":
	unittest.main()
