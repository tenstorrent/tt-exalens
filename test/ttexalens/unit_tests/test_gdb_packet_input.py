# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Host-only tests for how the GDB server reads packets from the socket and how it frames file-I/O replies.
# No device is needed.

import io
import unittest
from unittest.mock import MagicMock

from ttexalens.gdb.gdb_communication import GdbInputStream, GdbMessageParser, GdbMessageWriter
from ttexalens.gdb.gdb_server import GdbServer


class _ChunkedSocket:
    """Returns the queued chunks one per read(), like a TCP stream split across recv() calls."""

    packet_size = 2048

    def __init__(self, chunks: list[bytes]):
        self.chunks = list(chunks)
        self.written = bytearray()

    def read(self, packet_size=None):
        return self.chunks.pop(0) if self.chunks else b""

    def write(self, data):
        self.written.extend(data)


def _frame(payload: bytes) -> bytes:
    return b"$" + payload + b"#" + f"{sum(payload) % 256:02x}".encode()


class TestGdbPacketInput(unittest.TestCase):
    def read_all(self, chunks: list[bytes]) -> list[bytes]:
        stream = GdbInputStream(_ChunkedSocket(chunks))  # type: ignore
        packets = []
        while (parser := stream.read()) is not None:
            packets.append(parser.data)
        return packets

    def test_packet_in_one_chunk(self):
        self.assertEqual(self.read_all([_frame(b"m1000,4")]), [b"m1000,4"])

    def test_packet_split_across_reads(self):
        frame = _frame(b"m1000,4")
        for split in range(1, len(frame)):
            with self.subTest(split=split):
                self.assertEqual(self.read_all([frame[:split], frame[split:]]), [b"m1000,4"])

    def test_packet_split_after_ack(self):
        frame = _frame(b"M100,4:00112233")
        self.assertEqual(self.read_all([b"+" + frame[:8], frame[8:]]), [b"+", b"M100,4:00112233"])

    def test_packet_longer_than_one_read(self):
        payload = b"M100,400:" + b"AB" * 0x400
        frame = _frame(payload)
        self.assertGreater(len(frame), _ChunkedSocket.packet_size)
        chunks = [frame[:2048], frame[2048:]]
        self.assertEqual(self.read_all(chunks), [payload])

    def test_two_packets_split_across_reads(self):
        data = _frame(b"qC") + _frame(b"g")
        self.assertEqual(self.read_all([data[:5], data[5:]]), [b"qC", b"g"])


class TestGdbFileReplies(unittest.TestCase):
    def test_pwrite_reply_is_single_f_reply(self):
        server = GdbServer(MagicMock(), MagicMock())
        server.file_server.opened_files[1] = io.BytesIO()
        writer = GdbMessageWriter(_ChunkedSocket([]))  # type: ignore
        self.assertTrue(server.process_message(GdbMessageParser(b"vFile:pwrite:1,0,abc"), writer))
        self.assertEqual(bytes(writer.data[1:]), b"F3")

    def test_pwrite_bad_arguments_reply_is_single_f_reply(self):
        server = GdbServer(MagicMock(), MagicMock())
        writer = GdbMessageWriter(_ChunkedSocket([]))  # type: ignore
        self.assertTrue(server.process_message(GdbMessageParser(b"vFile:pwrite:1,0,"), writer))
        self.assertEqual(bytes(writer.data[1:]), b"F-1")


if __name__ == "__main__":
    unittest.main()
