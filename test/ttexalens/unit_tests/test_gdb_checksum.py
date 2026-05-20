# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for GdbInputStream checksum validation.

These tests exercise the checksum branch in GdbInputStream.read() without
requiring a real socket or hardware device. A minimal fake socket is used
that returns pre-built raw GDB packets directly.

GDB Remote Serial Protocol packet format:
  $<data>#<cc>
where <cc> is the two hex-digit checksum: sum of all <data> bytes mod 256.
"""

import unittest

from ttexalens.gdb.gdb_communication import GdbInputStream, ClientSocket


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _checksum(data: bytes) -> int:
    """Compute the GDB protocol checksum: sum of bytes mod 256."""
    return sum(data) % 256


def _make_packet(data: bytes, checksum_override: int | None = None) -> bytes:
    """
    Build a well-formed GDB packet: $<data>#<cc>

    Pass checksum_override to deliberately inject a wrong checksum.
    """
    cs = checksum_override if checksum_override is not None else _checksum(data)
    cs_high = cs // 16
    cs_low = cs % 16

    def hex_digit(n: int) -> int:
        return n + 48 if n < 10 else n + 55  # '0'-'9' or 'A'-'F'

    return bytes([ord("$")]) + data + bytes([ord("#"), hex_digit(cs_high), hex_digit(cs_low)])


class _FakeSocket:
    """
    Minimal stand-in for ClientSocket that feeds pre-set bytes to GdbInputStream.

    Each call to read() pops and returns the next chunk from the queue.
    If the queue is empty, returns b"" (connection closed).
    """

    def __init__(self, *chunks: bytes):
        self._chunks = list(chunks)
        self.nacks_sent: list[bytes] = []

    # GdbInputStream calls self.socket.read() and self.socket.write()
    def read(self, packet_size=None) -> bytes:
        if not self._chunks:
            return b""
        return self._chunks.pop(0)

    def write(self, data: bytes) -> None:
        self.nacks_sent.append(data)

    # GdbInputStream also calls input_ready() — not used in the read path we test
    def input_ready(self, timeout=0) -> bool:
        return bool(self._chunks)


def _make_stream(*chunks: bytes) -> tuple[GdbInputStream, _FakeSocket]:
    """Return a (GdbInputStream, fake_socket) pair pre-loaded with the given data chunks."""
    fake = _FakeSocket(*chunks)
    # ClientSocket is just a thin wrapper; we bypass it by patching the socket attribute.
    client = ClientSocket.__new__(ClientSocket)
    client.socket = fake  # type: ignore[attr-defined]
    client.packet_size = 2048
    # Redirect ClientSocket.read/write to our fake
    client.read = fake.read  # type: ignore[method-assign]
    client.write = fake.write  # type: ignore[method-assign]
    stream = GdbInputStream(client)
    return stream, fake


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGdbInputStreamChecksum(unittest.TestCase):
    """Verify that GdbInputStream.read() correctly accepts/rejects packets by checksum."""

    # ------------------------------------------------------------------
    # Acceptance cases
    # ------------------------------------------------------------------

    def test_valid_checksum_accepted(self):
        """A packet with a correct checksum must be parsed and returned."""
        payload = b"OK"
        packet = _make_packet(payload)
        stream, fake = _make_stream(packet)

        parser = stream.read()

        self.assertIsNotNone(parser, "Expected a parsed message, got None")
        self.assertEqual(parser.data, payload)
        self.assertEqual(fake.nacks_sent, [], "No NACK should be sent for a valid packet")

    def test_valid_checksum_various_payloads(self):
        """Several different payloads should all pass checksum validation."""
        payloads = [
            b"qSupported",
            b"g",
            b"S05",
            b"T05thread:p1.1;",
            b"m10000000,4",
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                packet = _make_packet(payload)
                stream, fake = _make_stream(packet)
                parser = stream.read()
                self.assertIsNotNone(parser, f"Valid packet for {payload!r} was rejected")
                self.assertEqual(parser.data, payload)
                self.assertEqual(fake.nacks_sent, [])

    def test_checksum_zero_payload(self):
        """Edge case: empty payload has checksum 0x00."""
        # Empty payload is unusual but the checksum logic must still work.
        payload = b""
        packet = _make_packet(payload)
        stream, fake = _make_stream(packet)
        parser = stream.read()
        self.assertIsNotNone(parser)
        self.assertEqual(parser.data, payload)
        self.assertEqual(fake.nacks_sent, [])

    def test_checksum_max_byte_values(self):
        """Payload that causes checksum rollover (mod 256) is still validated correctly."""
        # 256 bytes of 0xFF → checksum = (256 * 255) % 256 = 0
        payload = bytes([0xFF] * 256)
        packet = _make_packet(payload)
        stream, fake = _make_stream(packet)
        parser = stream.read()
        self.assertIsNotNone(parser)
        self.assertEqual(parser.data, payload)
        self.assertEqual(fake.nacks_sent, [])

    # ------------------------------------------------------------------
    # Rejection cases
    # ------------------------------------------------------------------

    def test_wrong_checksum_both_nibbles_sends_nack(self):
        """A packet with both checksum nibbles wrong must be NACKed."""
        payload = b"OK"
        correct_cs = _checksum(payload)
        wrong_cs = (correct_cs + 0x11) % 256  # flip both nibbles
        packet = _make_packet(payload, checksum_override=wrong_cs)
        # After NACK the stream will try to read again; give it empty to stop.
        stream, fake = _make_stream(packet, b"")

        parser = stream.read()

        self.assertIsNone(parser, "Corrupted packet should not be returned")
        self.assertIn(b"-", fake.nacks_sent, "A NACK ('-') must be sent for wrong checksum")

    def test_wrong_checksum_high_nibble_only_sends_nack(self):
        """A packet with only the high nibble wrong must also be NACKed."""
        payload = b"qC"
        correct_cs = _checksum(payload)
        # Flip only the high nibble (add 0x10, keep low nibble)
        wrong_cs = (correct_cs ^ 0x10) % 256
        packet = _make_packet(payload, checksum_override=wrong_cs)
        stream, fake = _make_stream(packet, b"")

        parser = stream.read()

        self.assertIsNone(parser)
        self.assertIn(b"-", fake.nacks_sent)

    def test_wrong_checksum_low_nibble_only_sends_nack(self):
        """A packet with only the low nibble wrong must also be NACKed."""
        payload = b"qC"
        correct_cs = _checksum(payload)
        # Flip only the low nibble
        wrong_cs = (correct_cs ^ 0x01) % 256
        packet = _make_packet(payload, checksum_override=wrong_cs)
        stream, fake = _make_stream(packet, b"")

        parser = stream.read()

        self.assertIsNone(parser)
        self.assertIn(b"-", fake.nacks_sent)

    # ------------------------------------------------------------------
    # Regression guard: the original (broken) behaviour
    # ------------------------------------------------------------------

    def test_regression_valid_packet_is_not_nacked(self):
        """
        Regression: before the fix, every valid packet was NACKed because
        the comparison used != instead of ==. A valid packet must never
        produce a '-' response.
        """
        payload = b"vCont;c:p1.1"
        packet = _make_packet(payload)
        stream, fake = _make_stream(packet)

        parser = stream.read()

        self.assertNotIn(
            b"-",
            fake.nacks_sent,
            "Regression: a valid packet must not be NACKed (was caused by inverted != comparison)",
        )
        self.assertIsNotNone(parser)

    def test_regression_doubly_corrupted_packet_is_nacked(self):
        """
        Regression: before the fix, a packet where both checksum nibbles were
        wrong was silently *accepted* (correct_checksum evaluated to True with !=).
        After the fix it must be rejected.
        """
        payload = b"OK"
        correct_cs = _checksum(payload)
        # Invert the whole byte → both nibbles differ from expected
        wrong_cs = correct_cs ^ 0xFF
        packet = _make_packet(payload, checksum_override=wrong_cs)
        stream, fake = _make_stream(packet, b"")

        parser = stream.read()

        self.assertIsNone(
            parser,
            "Regression: a doubly-corrupted packet must be rejected (was silently accepted before fix)",
        )
        self.assertIn(b"-", fake.nacks_sent)


if __name__ == "__main__":
    unittest.main()
