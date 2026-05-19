# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""
End-to-end tests for GdbInputStream checksum validation.

These tests spin up a real ServerSocket, accept a real TCP connection,
and drive it from a raw Python socket that speaks GDB Remote Serial
Protocol. No hardware, no GDB binary, and no mocks are needed.

The code path exercised is identical to what a real GDB client hits:
  raw bytes → ClientSocket.read() → GdbInputStream.read() → checksum branch

Two regression scenarios are tested:

  1. BEFORE the fix: a valid packet was NACKed because `!=` was used instead
     of `==`, so correct_checksum was True only when both nibbles differed.
     The server would write b"-" and the session would never progress.

  2. BEFORE the fix: a packet where both checksum nibbles were wrong was
     silently accepted (correct_checksum=True with !=), so corrupted data
     reached the caller.

After the fix both of these behave correctly.
"""

import io
import socket
import threading
import time
import unittest

from ttexalens.gdb.gdb_communication import ServerSocket, GdbInputStream


# ---------------------------------------------------------------------------
# RSP helpers
# ---------------------------------------------------------------------------

def _checksum(data: bytes) -> int:
    return sum(data) % 256


def _hex_digit(n: int) -> int:
    """Return ASCII code of a single uppercase hex digit 0-F."""
    return n + 48 if n < 10 else n + 55  # '0'-'9' or 'A'-'F'


def _build_packet(data: bytes, checksum_override: int | None = None) -> bytes:
    """
    Build a GDB RSP packet:  $<data>#<cc>

    checksum_override lets the caller inject a deliberately wrong checksum.
    """
    cs = checksum_override if checksum_override is not None else _checksum(data)
    return (
        b"$"
        + data
        + bytes([ord("#"), _hex_digit(cs // 16), _hex_digit(cs % 16)])
    )


# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

class _ServerThread(threading.Thread):
    """
    Runs ServerSocket.accept() + GdbInputStream.read() on a background thread.

    Results are stored in self.parsed and self.nacks so the test thread can
    inspect them after joining.
    """

    def __init__(self, server_socket: ServerSocket):
        super().__init__(daemon=True)
        self._server = server_socket
        self.parsed = None       # GdbMessageParser returned by read(), or None
        self.nacks: list[bytes] = []
        self._error_stream = io.StringIO()

    def run(self):
        client = self._server.accept(timeout=5.0)
        if client is None:
            return

        # Intercept writes so we can capture NACKs without a real GDB client
        _orig_write = client.write

        def _capture_write(data: bytes):
            self.nacks.append(data)
            _orig_write(data)

        client.write = _capture_write  # type: ignore[method-assign]

        stream = GdbInputStream(client, error_stream=self._error_stream)
        self.parsed = stream.read()


class TestGdbChecksumEndToEnd(unittest.TestCase):
    """
    End-to-end: real TCP socket pair, real ServerSocket, real GdbInputStream.
    """

    def _run(
        self,
        packet: bytes,
        read_timeout: float = 3.0,
    ) -> tuple[object, list[bytes]]:
        """
        Spin up a ServerSocket, connect a raw client socket, send *packet*,
        wait for GdbInputStream.read() to return, then return
        (parsed_message, nacks_sent).
        """
        server_sock = ServerSocket(port=None)
        server_sock.start()
        port = server_sock.port
        assert port is not None

        srv = _ServerThread(server_sock)
        srv.start()

        # Give the server thread a moment to call accept()
        time.sleep(0.05)

        with socket.create_connection(("localhost", port), timeout=read_timeout) as raw:
            raw.sendall(packet)
            # Keep the connection open long enough for the server to read
            time.sleep(0.2)

        srv.join(timeout=read_timeout + 1)
        server_sock.close()
        return srv.parsed, srv.nacks

    # ------------------------------------------------------------------
    # Acceptance cases
    # ------------------------------------------------------------------

    def test_e2e_valid_packet_accepted_no_nack(self):
        """
        A packet with the correct checksum must be parsed and returned;
        no NACK (b"-") must be sent.

        Regression: before the fix this always sent b"-" because != was used
        in the checksum comparison.
        """
        payload = b"qSupported"
        packet = _build_packet(payload)

        parsed, nacks = self._run(packet)

        self.assertIsNotNone(
            parsed,
            "GdbInputStream.read() returned None — valid packet was not accepted",
        )
        self.assertEqual(
            parsed.data,
            payload,
            f"Parsed data mismatch: expected {payload!r}, got {parsed.data!r}",
        )
        self.assertNotIn(
            b"-",
            nacks,
            "A NACK was sent for a valid packet — checksum comparison is still inverted",
        )

    def test_e2e_valid_ok_packet(self):
        """Minimal 'OK' payload — commonly the first reply in a GDB session."""
        payload = b"OK"
        packet = _build_packet(payload)

        parsed, nacks = self._run(packet)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.data, payload)
        self.assertNotIn(b"-", nacks)

    def test_e2e_checksum_wrap_around(self):
        """Payload whose checksum wraps mod 256 is still handled correctly."""
        # 256 × 0xFF → checksum = 0
        payload = bytes([0xFF] * 256)
        packet = _build_packet(payload)

        parsed, nacks = self._run(packet)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.data, payload)
        self.assertNotIn(b"-", nacks)

    # ------------------------------------------------------------------
    # Rejection cases
    # ------------------------------------------------------------------

    def test_e2e_wrong_checksum_sends_nack(self):
        """
        A packet with a wrong checksum must cause GdbInputStream.read() to
        send b"-" and not return the corrupted payload to the caller.

        Regression: before the fix, a packet where both nibbles were wrong
        was silently accepted (correct_checksum=True with !=).
        """
        payload = b"OK"
        correct_cs = _checksum(payload)
        # XOR with 0xFF flips all bits — both nibbles are wrong
        wrong_cs = correct_cs ^ 0xFF
        packet = _build_packet(payload, checksum_override=wrong_cs)

        parsed, nacks = self._run(packet)

        # The server sends NACK then tries to read again; the connection
        # closes, so read() returns None.
        self.assertIsNone(
            parsed,
            "GdbInputStream.read() returned a result for a corrupted packet — "
            "checksum rejection is broken",
        )
        self.assertIn(
            b"-",
            nacks,
            "No NACK was sent for a corrupted packet",
        )

    def test_e2e_single_nibble_wrong_sends_nack(self):
        """
        A packet with only the low nibble wrong must also be rejected.

        This catches the edge case where the old `and` operator would have
        accepted the packet if only one nibble was wrong (correct_checksum
        would be False because the first != was satisfied but the second was
        not, making `and` False — then `if not False` triggered the NACK).
        This test confirms the fix preserves that behaviour while the
        acceptance case confirms the inversion is corrected.
        """
        payload = b"g"
        correct_cs = _checksum(payload)
        wrong_cs = (correct_cs ^ 0x01) % 256  # flip only low nibble
        packet = _build_packet(payload, checksum_override=wrong_cs)

        parsed, nacks = self._run(packet)

        self.assertIsNone(parsed)
        self.assertIn(b"-", nacks)

    # ------------------------------------------------------------------
    # Explicit regression labels (named so CI history is self-documenting)
    # ------------------------------------------------------------------

    def test_regression_valid_packet_must_not_be_nacked(self):
        """
        REGRESSION: before the fix every valid packet was NACKed because
        `correct_checksum = checksum1 != buffer[pos]` evaluated to True
        on a mismatch, making correct_checksum=False on a match, so the
        `if not correct_checksum` branch always fired for valid packets.
        """
        payload = b"vCont;c:p1.1"
        packet = _build_packet(payload)

        parsed, nacks = self._run(packet)

        self.assertNotIn(
            b"-",
            nacks,
            "REGRESSION: valid packet was NACKed — != comparison is still present",
        )
        self.assertIsNotNone(parsed)

    def test_regression_doubly_corrupted_packet_must_be_nacked(self):
        """
        REGRESSION: before the fix a packet where both checksum nibbles were
        wrong was silently accepted because `!=` on both nibbles returned True,
        making correct_checksum=True, and `if not True` never fired.
        """
        payload = b"OK"
        correct_cs = _checksum(payload)
        wrong_cs = correct_cs ^ 0xFF  # both nibbles differ
        packet = _build_packet(payload, checksum_override=wrong_cs)

        parsed, nacks = self._run(packet)

        self.assertIsNone(
            parsed,
            "REGRESSION: doubly-corrupted packet was silently accepted",
        )
        self.assertIn(b"-", nacks)


if __name__ == "__main__":
    unittest.main()
