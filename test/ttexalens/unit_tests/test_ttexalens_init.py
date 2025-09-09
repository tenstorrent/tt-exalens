# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
import os

from ttexalens import tt_exalens_init
from ttexalens.context import Context
from ttexalens.tt_exalens_ifc import init_pybind
from ttexalens.tt_exalens_server import start_server

CACHE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_cache.pkl"))


def tearDownModule():
    if os.path.isfile(CACHE_PATH):
        # TODO: WHY IS THIS NOT WORKING!?
        os.remove(CACHE_PATH)


class TestLocalTTExaLensInit(unittest.TestCase):
    def test_local_init(self):
        """Test local TTExaLens initialization."""
        context = tt_exalens_init.init_ttexalens()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_local_with_cache(self):
        """Test local TTExaLens initialization with cache."""
        context = tt_exalens_init.init_ttexalens(cache_path=CACHE_PATH)
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_local_wanted_devices(self):
        """Test local TTExaLens initialization with specification of wanted devices."""
        context = tt_exalens_init.init_ttexalens(
            wanted_devices=[
                0,
            ]
        )
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)


class TestRemoteTTExaLens(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(5555, init_pybind())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()

    def test_remote_init(self):
        """Test remote TTExaLens initialization."""
        context = tt_exalens_init.init_ttexalens_remote()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_remote_with_cache(self):
        """Test remote TTExaLens initialization with cache."""
        context = tt_exalens_init.init_ttexalens_remote(cache_path=CACHE_PATH)
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)


class TestCachedTTExaLens(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        context = tt_exalens_init.init_ttexalens(cache_path=CACHE_PATH)
        # Execute a sample command to populate the cache
        context.server_ifc.get_cluster_description()
        context.server_ifc.save()
        del context

    def test_cached_init(self):
        """Test TTExaLens initialization with cache."""
        context = tt_exalens_init.init_ttexalens_cached(cache_path=CACHE_PATH)
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)
        context.server_ifc.get_cluster_description()


if __name__ == "__main__":
    unittest.main()
