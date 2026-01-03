# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import tempfile
import unittest
import os

from ttexalens import (
    init_ttexalens,
    init_ttexalens_remote,
    Context,
    read_from_device,
    read_word_from_device,
    write_to_device,
)
from ttexalens.umd_api import local_init
from ttexalens.server import start_server
from test.ttexalens.unit_tests.test_base import init_default_test_context


class TestLocalTTExaLensInit(unittest.TestCase):
    def test_local_init(self):
        """Test local TTExaLens initialization."""
        context = init_ttexalens()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)


class TestRemoteTTExaLens(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = start_server(5555, init_default_test_context())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.stop()
        init_default_test_context()

    def test_remote_init(self):
        """Test remote TTExaLens initialization."""
        context = init_ttexalens_remote()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_remote_read_file(self):
        """Test remote TTExaLens file reading."""
        context = init_ttexalens_remote()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

        # Create file in temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test_file.txt")
            with open(file_path, "w") as f:
                f.write("Hello, TTExaLens!")

            # Read file remotely
            content = context.file_api.get_file(file_path)
            self.assertEqual(content, "Hello, TTExaLens!")

            # Read file through streaming interface
            stream = context.file_api.get_binary(file_path)
            size = stream.seek(0, os.SEEK_END)
            stream.seek(0)
            stream_content = stream.read(size).decode("utf-8")
            self.assertEqual(stream_content, "Hello, TTExaLens!")

    def test_write_read_bytes(self):
        context = init_ttexalens_remote()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

        """Test write bytes -- read bytes."""
        location = "0,0"
        address = 0x100

        data = b"abcd"

        ret = write_to_device(location, address, data, device_id=0, context=context)
        self.assertEqual(ret, len(data))

        ret = read_from_device(location, address, num_bytes=len(data), device_id=0, context=context)
        self.assertEqual(ret, data)

        ret = read_word_from_device(location, address, device_id=0, context=context)
        self.assertEqual(ret, int.from_bytes(data, "little"))


if __name__ == "__main__":
    unittest.main()
