# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import socket
import unittest
from contextlib import contextmanager

from test.ttexalens.unit_tests.test_base import init_cached_test_context

from ttexalens.gdb.gdb_server import GdbServer
from ttexalens.gdb.gdb_communication import (
    ServerSocket,
    GDB_ASCII_DOLLAR,
    GDB_ASCII_HASH,
)
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.gdb.gdb_data import GdbProcess
from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.coordinate import OnChipCoordinate


class TestGdbServerMemAccess(unittest.TestCase):
    # Class attributes set in setUpClass
    context: Context
    device: Device
    risc_debug: RiscDebug
    location: OnChipCoordinate
    server_socket: ServerSocket
    gdb_server: GdbServer
    process: GdbProcess
    l1_start: int
    l1_end: int
    data_private_start: int
    data_private_end: int
    memory_regions: list[tuple[str, int, int]]
    pid: int

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]
        cls.risc_debug = cls.device.debuggable_cores[0]
        cls.location = cls.risc_debug.risc_location.location
        cls.server_socket = ServerSocket(port=None)
        cls.server_socket.start()

        cls.gdb_server = GdbServer(cls.context, cls.server_socket)
        cls.gdb_server.start()

        pid = 1
        elf_path = None
        core_type = "worker"
        virtual_core_id = 0
        cls.process = GdbProcess(
            process_id=pid,
            elf_path=elf_path,
            risc_debug=cls.risc_debug,
            virtual_core_id=virtual_core_id,
            core_type=core_type,
        )

        # Add process to debugging threads so it can be attached
        cls.gdb_server.debugging_threads[pid] = cls.process.thread_id
        cls.gdb_server._last_available_processes[cls.risc_debug.risc_location] = cls.process

        # Calculate L1 boundaries
        l1 = cls.risc_debug.get_l1()
        assert l1.address.private_address is not None
        cls.l1_start = l1.address.private_address
        cls.l1_end = cls.l1_start + l1.size - 1

        # Calculate data private memory boundaries
        data_private = cls.risc_debug.get_data_private_memory()
        assert data_private is not None
        assert data_private.address.private_address is not None
        cls.data_private_start = data_private.address.private_address
        cls.data_private_end = cls.data_private_start + data_private.size - 1

        cls.memory_regions = [
            ("l1", cls.l1_start, cls.l1_end),
            ("data_private", cls.data_private_start, cls.data_private_end),
        ]

        cls.pid = pid

    @classmethod
    def tearDownClass(cls):
        cls.gdb_server.stop()
        cls.server_socket.close()

    @contextmanager
    def _gdb_client(self):
        """Context manager that connects to GDB server and ensures socket cleanup."""
        sock = self._connect_client()
        try:
            yield sock
        finally:
            sock.close()

    def _connect_client(self) -> socket.socket:
        """Connect to GDB server and attach to the process."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10.0)  # 10 second timeout for all socket operations
        s.connect(("localhost", self.server_socket.port))

        # Send initial handshake - qSupported
        self._send_packet(s, b"qSupported")

        # Attach to process using vAttach
        attach_cmd = f"vAttach;{self.pid:x}".encode()
        reply = self._send_packet(s, attach_cmd)
        # Should get a stop reply packet (T05 or similar)
        self.assertTrue(
            reply.startswith(b"T") or reply.startswith(b"S"), f"Expected stop reply after vAttach, got: {reply!r}"
        )

        return s

    def _send_packet(self, sock: socket.socket, payload: bytes) -> bytes:
        """Send a GDB Remote Serial Protocol packet and return the response data.

        GDB packet format: $<data>#<checksum>
        - $ marks packet start
        - <data> is the command/response payload
        - # marks end of data
        - <checksum> is 2-digit hex sum of data bytes modulo 256

        Protocol flow:
        1. Client sends: $<command>#<checksum>
        2. Server sends: + (ACK) or - (NAK)
        3. Server sends: $<response>#<checksum>
        4. Client sends: + (ACK) - not implemented here as server doesn't wait for it
        """
        # Calculate checksum: sum of all payload bytes modulo 256
        checksum = sum(payload) % 256

        # Build packet: $<payload>#<checksum_hex>
        pkt = bytearray()
        pkt.append(GDB_ASCII_DOLLAR)  # '$'
        pkt.extend(payload)
        pkt.append(GDB_ASCII_HASH)  # '#'

        # Append 2-digit hex checksum
        hi = checksum // 16
        lo = checksum % 16
        hi_ch = (ord("0") + hi) if hi < 10 else (ord("A") + hi - 10)
        lo_ch = (ord("0") + lo) if lo < 10 else (ord("A") + lo - 10)
        pkt.append(hi_ch)
        pkt.append(lo_ch)

        # Send the packet
        sock.sendall(pkt)

        # Wait for ACK from server
        ack = sock.recv(1)
        self.assertEqual(ack, b"+", "Expected '+' ACK from GdbServer")

        # Read response packet start marker
        ch = sock.recv(1)
        self.assertEqual(ch, b"$", "Expected '$' at start of reply")

        # Read response data until '#'
        data = bytearray()
        while True:
            ch = sock.recv(1)
            if ch == b"#":
                break
            data.extend(ch)

        # Consume checksum (2 hex digits) but don't validate it
        sock.recv(2)

        return bytes(data)

    def test_x_read_inside_allowed_memory_ok(self):
        """Test x (binary read) command with address fully inside allowed memory regions."""
        with self._gdb_client() as sock:
            for region_name, start, _ in self.memory_regions:
                with self.subTest(memory_region=region_name):
                    addr = start + 0x100
                    length = 16

                    payload = f"x{addr:x},{length:x}".encode()
                    reply = self._send_packet(sock, payload)

                    self.assertGreaterEqual(len(reply), 1)
                    self.assertEqual(reply[0:1], b"b")
                    self.assertEqual(
                        len(reply) - 1,
                        length,
                        f"x inside {region_name} should return full {length} bytes, got {len(reply)-1}",
                    )

    def test_x_read_restricted_memory_e04(self):
        """Test x (binary read) returns E04 for various restricted memory scenarios."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                test_cases = [
                    ("fully_outside", end, 4),
                    ("partial_end_after", end - 1, 8),  # Starts inside, ends after
                ]
                test_cases.append(("partial_start_before", start - 4, 8)) if start >= 0x1000 else None

                for name, addr, length in test_cases:
                    with self.subTest(memory_region=region_name, scenario=name, addr=hex(addr), length=length):
                        payload = f"x{addr:x},{length:x}".encode()
                        reply = self._send_packet(sock, payload)
                        self.assertEqual(
                            reply, b"E04", f"Expected E04 for {region_name} {name} scenario, got {reply!r}"
                        )

    def test_m_read_inside_allowed_memory_ok(self):
        """Test m (hex read) command with address fully inside allowed memory regions."""
        with self._gdb_client() as sock:
            for region_name, start, _ in self.memory_regions:
                with self.subTest(memory_region=region_name):
                    addr = start + 0x200
                    length = 8

                    payload = f"m{addr:x},{length:x}".encode()
                    reply = self._send_packet(sock, payload)

                    # m reply: XX... (hex string)
                    # Each byte → 2 hex chars
                    self.assertEqual(
                        len(reply),
                        2 * length,
                        f"m inside {region_name} should return {2*length} hex chars, got {len(reply)}",
                    )

    def test_m_read_restricted_memory_e04(self):
        """Test m (hex read) returns E04 for various restricted memory scenarios."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                test_cases = [
                    ("fully_outside", end, 8),
                    ("partial_end_after", end - 4, 8),  # Starts inside, ends after
                ]
                test_cases.append(
                    ("partial_start_before", start - 4, 8)
                ) if start >= 0x1000 else None  # Starts before, ends inside

                for name, addr, length in test_cases:
                    with self.subTest(memory_region=region_name, scenario=name, addr=hex(addr), length=length):
                        payload = f"m{addr:x},{length:x}".encode()
                        reply = self._send_packet(sock, payload)
                        self.assertEqual(reply, b"E04", f"Expected E04 for {region_name} {name} scenario")

    def test_M_write_inside_allowed_memory_ok(self):
        """Test M (hex write) command with address fully inside allowed memory regions."""
        with self._gdb_client() as sock:
            for region_name, start, _ in self.memory_regions:
                with self.subTest(memory_region=region_name):
                    addr = start + 0x300
                    length = 4
                    data_hex = "aabbccdd"  # Proper hex string for 4 bytes (lowercase)
                    payload = f"M{addr:x},{length:x}:{data_hex}".encode()
                    reply = self._send_packet(sock, payload)
                    self.assertEqual(reply, b"OK")

    def test_M_write_restricted_memory_e04(self):
        """Test M (hex write) returns E04 for various restricted memory scenarios."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                test_cases = [
                    ("fully_outside", end, 4, "00112233"),
                    ("partial_end_after", end - 2, 8, "0011223344556677"),  # Starts inside, ends after
                ]
                test_cases.append(
                    ("partial_start_before", start - 4, 8, "0011223344556677")
                ) if start >= 0x1000 else None  # Starts before, ends inside

                for name, addr, length, data_hex in test_cases:
                    with self.subTest(memory_region=region_name, scenario=name, addr=hex(addr), length=length):
                        payload = f"M{addr:x},{length:x}:{data_hex}".encode()
                        reply = self._send_packet(sock, payload)
                        self.assertEqual(reply, b"E04", f"Expected E04 for {region_name} {name} scenario")

    def test_X_write_inside_allowed_memory_ok(self):
        """Test X (binary write) command with address fully inside allowed memory regions."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                with self.subTest(memory_region=region_name):
                    addr = start + 0x400
                    data = b"\x11\x22\x33\x44"
                    length = len(data)

                    payload = f"X{addr:x},{length:x}:".encode() + data
                    reply = self._send_packet(sock, payload)

                    self.assertEqual(reply, b"OK")

    def test_X_write_restricted_memory_e04(self):
        """Test X (binary write) returns E04 for various restricted memory scenarios."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                test_cases = [
                    ("fully_outside", end, b"\xAA\xBB\xCC\xDD"),
                    (
                        "partial_end_after",
                        end - 4,
                        b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xAA\xBB\xCC\xDD\xEE\xFF",
                    ),  # Starts inside, ends after
                ]
                test_cases.append(
                    ("partial_start_before", start - 4, b"\xFF\xEE\xDD\xCC\xBB\xAA\x99\x88")
                ) if start >= 0x1000 else None

                for name, addr, data in test_cases:
                    with self.subTest(memory_region=region_name, scenario=name, addr=hex(addr), data_len=len(data)):
                        length = len(data)
                        payload = f"X{addr:x},{length:x}:".encode() + data
                        reply = self._send_packet(sock, payload)
                        self.assertEqual(reply, b"E04", f"Expected E04 for {region_name} {name} scenario")
