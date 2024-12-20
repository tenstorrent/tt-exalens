# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
import os

from ttlens import tt_lens_init
from ttlens.tt_lens_context import Context
from ttlens.tt_lens_server import start_server, stop_server


CACHE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_cache.pkl"))


def tearDownModule():
    if os.path.isfile(CACHE_PATH):
        # TODO: WHY IS THIS NOT WORKING!?
        os.remove(CACHE_PATH)


class TestLocalTTLensInit(unittest.TestCase):
    def test_local_init(self):
        """Test local TTLens initialization."""
        context = tt_lens_init.init_ttlens()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_local_with_cache(self):
        """Test local TTLens initialization with cache."""
        context = tt_lens_init.init_ttlens(cache_path=CACHE_PATH)
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_local_wanted_devices(self):
        """Test local TTLens initialization with specification of wanted devices."""
        context = tt_lens_init.init_ttlens(
            wanted_devices=[
                0,
            ]
        )
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)


class TestRemoteTTLens(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(5555)

    @classmethod
    def tearDownClass(cls) -> None:
        stop_server(cls.server)

    def test_remote_init(self):
        """Test remote TTLens initialization."""
        context = tt_lens_init.init_ttlens_remote()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_remote_with_cache(self):
        """Test remote TTLens initialization with cache."""
        context = tt_lens_init.init_ttlens_remote(cache_path=CACHE_PATH)
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)


class TestCachedTTLens(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        context = tt_lens_init.init_ttlens(cache_path=CACHE_PATH)
        # Execute a sample command to populate the cache
        context.server_ifc.get_cluster_description()
        context.server_ifc.save()
        del context

    def test_cached_init(self):
        """Test TTLens initialization with cache."""
        context = tt_lens_init.init_ttlens_cached(cache_path=CACHE_PATH)
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)
        context.server_ifc.get_cluster_description()


if __name__ == "__main__":
    unittest.main()
