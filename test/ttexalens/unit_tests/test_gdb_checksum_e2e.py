# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""
Tests for GdbInputStream checksum validation (lines 202-210 of gdb_communication.py).

A minimal fake socket feeds raw RSP bytes directly into GdbInputStream.read()
so the checksum branch runs with no hardware, no GDB binary, and no threads.

Regression fixed: checksum nibbles (int 0-15) were compared directly to ASCII
bytes in the input buffer using != instead of converting to ASCII and using ==,
causing every valid packet to be rejected and every doubly-corrupted packet to
be silently accepted.
"""

import io
import unittest

from ttexalens.gdb.gdb_communication import ClientSocket, GdbInputStream


def _checksum(data: bytes) -> int:
    return sum(data) % 256


def _nibble_to_ascii(n: int) -> int:
    return n + 48 if n < 10 else n + 55


def _build_packet(data: bytes, checksum_override: int | None = None) -> bytes:
    """Build $<data>#<cc> with correct or deliberately wrong checksum."""
    cs = checksum_override if checksum_override is not None else _checksum(data)
    return b"$" + data + bytes([ord("#"), _nibble_to_ascii(cs // 16), _nibble_to_ascii(cs % 16)])


class _FakeClientSocket(ClientSocket):
    """ClientSocket that reads from a bytes buffer instead of a real socket."""

    def __init__(self, data: bytes):
        super().__init__(socket=None)
        self._buf = data
        self.nacks: list[bytes] = []

    def read(self, packet_size=None):
        chunk, self._buf = self._buf, b""
        return chunk

    def write(self, data: bytes):
        self.nacks.append(data)

    def input_ready(self, timeout=0):
        return bool(self._buf)


def _run(packet: bytes):
    sock = _FakeClientSocket(packet)
    stream = GdbInputStream(sock, error_stream=io.StringIO())
    parsed = stream.read()
    return parsed, sock.nacks


class TestGdbChecksumValidation(unittest.TestCase):

    # --- valid packets must be accepted ---

    def test_valid_packet_accepted(self):
        payload = b"OK"
        parsed, nacks = _run(_build_packet(payload))
        self.assertIsNotNone(parsed, "valid packet was rejected")
        self.assertEqual(parsed.data, payload)
        self.assertNotIn(b"-", nacks, "NACK sent for valid packet")

    def test_valid_packet_high_nibble_letter_digit(self):
        # checksum digit in A-F range (letter, not just 0-9)
        payload = b"qSupported"
        parsed, nacks = _run(_build_packet(payload))
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.data, payload)
        self.assertNotIn(b"-", nacks)

    def test_valid_packet_checksum_wraps_mod256(self):
        payload = bytes([0xFF] * 256)  # sum wraps to 0
        parsed, nacks = _run(_build_packet(payload))
        self.assertIsNotNone(parsed)
        self.assertNotIn(b"-", nacks)

    # --- corrupted packets must be rejected ---

    def test_wrong_checksum_both_nibbles_sends_nack(self):
        payload = b"OK"
        wrong_cs = _checksum(payload) ^ 0xFF
        parsed, nacks = _run(_build_packet(payload, checksum_override=wrong_cs))
        self.assertIsNone(parsed, "corrupted packet was silently accepted")
        self.assertIn(b"-", nacks, "no NACK sent for corrupted packet")

    def test_wrong_checksum_high_nibble_only_sends_nack(self):
        payload = b"g"
        wrong_cs = (_checksum(payload) ^ 0x10) % 256
        parsed, nacks = _run(_build_packet(payload, checksum_override=wrong_cs))
        self.assertIsNone(parsed)
        self.assertIn(b"-", nacks)

    def test_wrong_checksum_low_nibble_only_sends_nack(self):
        payload = b"g"
        wrong_cs = (_checksum(payload) ^ 0x01) % 256
        parsed, nacks = _run(_build_packet(payload, checksum_override=wrong_cs))
        self.assertIsNone(parsed)
        self.assertIn(b"-", nacks)

    # --- regression guards ---

    def test_regression_valid_packet_not_nacked(self):
        """Before fix: nibble int compared to ASCII byte with != always evaluated
        True for valid packets, causing every valid packet to be NACKed."""
        parsed, nacks = _run(_build_packet(b"vCont;c:p1.1"))
        self.assertNotIn(b"-", nacks, "REGRESSION: valid packet NACKed")
        self.assertIsNotNone(parsed)

    def test_regression_doubly_corrupted_not_accepted(self):
        """Before fix: both nibbles wrong made correct_checksum=True with !=,
        so doubly-corrupted packets were silently accepted."""
        payload = b"OK"
        wrong_cs = _checksum(payload) ^ 0xFF
        parsed, nacks = _run(_build_packet(payload, checksum_override=wrong_cs))
        self.assertIsNone(parsed, "REGRESSION: corrupted packet silently accepted")
        self.assertIn(b"-", nacks)


if __name__ == "__main__":
    unittest.main()
