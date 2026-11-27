# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import io
import unittest
from typing import Iterable

from parameterized import parameterized

from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.gdb.gdb_communication import ClientSocket, GdbInputStream, ServerSocket
from ttexalens.gdb.gdb_server import GdbServer


def frame(raw: bytes) -> bytes:
    return b"$" + raw + b"#" + f"{sum(raw) % 256:02X}".encode()


class FakeClientSocket(ClientSocket):
    def __init__(self, reads: Iterable[bytes]):
        super().__init__()
        self.reads = iter(reads)
        self.written: list[bytes] = []

    def read(self, packet_size: int | None = None) -> bytes:
        return next(self.reads, b"")

    def write(self, data: bytes | bytearray) -> None:
        self.written.append(bytes(data))


class TestGdbInputStream(unittest.TestCase):
    def test_packet_split_at_every_byte(self):
        wire = b"+" + frame(b"X1000,2:}\x03}]")
        for index in range(1, len(wire)):
            stream = GdbInputStream(FakeClientSocket([wire[:index], wire[index:]]))
            messages = [parser.data for parser in iter(stream.read, None)]
            self.assertEqual(messages, [b"+", b"X1000,2:#}"], f"split at {index}")


class TestGdbServerPackets(unittest.TestCase):
    @parameterized.expand(
        [
            ("written", b"vFile:pwrite:5,0," + b"a" * 26, b"F1A"),
            ("bad_arguments", b"vFile:pwrite:", b"F-1"),
            ("write_failed", b"vFile:pwrite:6,0,abc", b"F-2,Error while writing."),
        ]
    )
    def test_pwrite_replies_one_result(self, _name: str, packet: bytes, reply: bytes):
        server = GdbServer(init_cached_test_context(), ServerSocket(), error_stream=io.StringIO())
        server.file_server.opened_files.update({5: io.BytesIO(), 6: io.BufferedReader(io.BytesIO())})
        client = FakeClientSocket([frame(packet)])
        server.process_client(client)
        self.assertEqual(client.written, [b"+", frame(reply)])


if __name__ == "__main__":
    unittest.main()
