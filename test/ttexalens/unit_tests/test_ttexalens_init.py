# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import tempfile
import unittest
import os

from ttexalens import tt_exalens_init
from ttexalens.context import Context
from ttexalens.tt_exalens_ifc import init_pybind
from ttexalens.tt_exalens_server import start_server


class TestLocalTTExaLensInit(unittest.TestCase):
    def test_local_init(self):
        """Test local TTExaLens initialization."""
        context = tt_exalens_init.init_ttexalens()
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

    def test_remote_read_file(self):
        """Test remote TTExaLens file reading."""
        context = tt_exalens_init.init_ttexalens_remote()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

        # Create file in temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test_file.txt")
            with open(file_path, "w") as f:
                f.write("Hello, TTExaLens!")

            # Read file remotely
            content = context.server_ifc.get_file(file_path)
            self.assertEqual(content, "Hello, TTExaLens!")

            # Read file through streaming interface
            stream = context.server_ifc.get_binary(file_path)
            size = stream.seek(0, os.SEEK_END)
            stream.seek(0)
            stream_content = stream.read(size).decode("utf-8")
            self.assertEqual(stream_content, "Hello, TTExaLens!")


if __name__ == "__main__":
    unittest.main()
