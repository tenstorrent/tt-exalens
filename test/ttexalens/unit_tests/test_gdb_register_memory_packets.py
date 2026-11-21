# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Host-only tests for the GDB server's register and memory packets ('g', 'G', 'p', 'P', 'm').
# They feed packets straight into GdbServer.process_message with a stubbed core, so no device is needed.
# GDB sends and expects register values in target byte order (little-endian on RISC-V), and memory
# bytes in address order.

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from ttexalens.gdb.gdb_communication import GdbMessageParser, GdbMessageWriter
from ttexalens.gdb.gdb_server import GdbServer


class _FakeClientSocket:
    packet_size = 2048

    def write(self, data):
        pass


class TestGdbRegisterMemoryPackets(unittest.TestCase):
    def setUp(self):
        self.server = GdbServer(MagicMock(), MagicMock())
        self.registers = [0] * GdbServer.REGISTER_COUNT
        self.ebreak_hit = False
        self.memory = bytes()

        risc_debug = MagicMock()
        risc_debug.read_gpr.side_effect = self._read_gpr
        risc_debug.write_gpr.side_effect = self._write_gpr
        risc_debug.read_status.side_effect = lambda: SimpleNamespace(is_ebreak_hit=self.ebreak_hit)
        mem_access = MagicMock()
        mem_access.read.side_effect = lambda address, buffer: buffer.__setitem__(
            slice(0, len(buffer)), self.memory[: len(buffer)]
        )
        self.risc_debug = risc_debug
        self.server.current_process = SimpleNamespace(risc_debug=risc_debug, mem_access=mem_access)  # type: ignore

    # Out-of-range indices are tolerated here so that the tests check the server's own range check.
    def _read_gpr(self, index: int) -> int:
        return self.registers[index] if 0 <= index < len(self.registers) else 0

    def _write_gpr(self, index: int, value: int) -> None:
        if 0 <= index < len(self.registers):
            self.registers[index] = value

    def send(self, packet: bytes) -> bytes:
        writer = GdbMessageWriter(_FakeClientSocket())  # type: ignore
        self.assertTrue(self.server.process_message(GdbMessageParser(packet), writer))
        return bytes(writer.data[1:])  # drop the leading '$'

    def test_read_hex_field_at_end_of_packet(self):
        parser = GdbMessageParser(b"12345678")
        self.assertEqual(parser.read_hex(8), 0x12345678)

    def test_p_replies_in_target_byte_order(self):
        self.registers[2] = 0x0000FFF0
        self.assertEqual(self.send(b"p2"), b"F0FF0000")

    def test_p_matches_g_for_every_register(self):
        self.registers = [0x01020300 + i for i in range(GdbServer.REGISTER_COUNT)]
        g_reply = self.send(b"g")
        for i in range(GdbServer.REGISTER_COUNT):
            self.assertEqual(self.send(b"p%x" % i), g_reply[8 * i : 8 * i + 8], f"register {i}")

    def test_p_pc_after_ebreak_matches_g(self):
        self.registers[32] = 0x1004
        self.ebreak_hit = True
        g_reply = self.send(b"g")
        self.assertEqual(g_reply[8 * 32 : 8 * 33], b"00100000")
        self.assertEqual(self.send(b"p20"), b"00100000")

    def test_p_out_of_range_register_is_rejected(self):
        self.assertEqual(self.send(b"p21"), b"E01")
        self.risc_debug.read_gpr.assert_not_called()

    def test_P_decodes_target_byte_order(self):
        self.assertEqual(self.send(b"P20=34120000"), b"OK")
        self.assertEqual(self.registers[32], 0x1234)
        self.assertEqual(self.send(b"Pa=F0FF0000"), b"OK")
        self.assertEqual(self.registers[10], 0x0000FFF0)

    def test_P_out_of_range_register_is_rejected(self):
        self.assertEqual(self.send(b"P21=00000000"), b"E01")
        self.risc_debug.write_gpr.assert_not_called()

    def test_G_writes_all_registers(self):
        values = [0x11223300 + i for i in range(GdbServer.REGISTER_COUNT)]
        payload = b"".join(value.to_bytes(4, "little").hex().encode() for value in values)
        self.assertEqual(self.send(b"G" + payload), b"OK")
        self.assertEqual(self.registers, values)

    def test_m_replies_bytes_in_address_order(self):
        self.memory = bytes([0x01, 0x02, 0x03, 0x04, 0xAA])
        self.assertEqual(self.send(b"m100,4"), b"01020304")
        self.assertEqual(self.send(b"m100,5"), b"01020304AA")


if __name__ == "__main__":
    unittest.main()
