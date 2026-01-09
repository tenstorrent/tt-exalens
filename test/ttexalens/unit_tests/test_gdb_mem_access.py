# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import socket
import subprocess
import tempfile
import textwrap
import time
import unittest
from contextlib import contextmanager

from test.ttexalens.unit_tests.test_base import (  # type: ignore
    init_cached_test_context,
    get_core_location,
)

from ttexalens import util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.gdb.gdb_server import GdbServer
from ttexalens.gdb.gdb_communication import (
    ServerSocket,
    GDB_ASCII_DOLLAR,
    GDB_ASCII_HASH,
)
from ttexalens.gdb.gdb_data import GdbProcess
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.tt_exalens_lib import run_elf


class TestGdbServerMemAccess(unittest.TestCase):
    """
    Protocol-level tests for GdbServer memory access restrictions.

    These tests:
      - Start a real GdbServer on a free port.
      - Attach via the GDB remote protocol (vAttach).
      - Send raw x/m/M/X packets and verify:
          * full reads/writes inside L1 + data private,
          * E04 for any access that leaves allowed regions.
    """

    # Class attributes set in setUpClass
    context: Context
    device: Device
    risc_debug: RiscDebug
    location: OnChipCoordinate
    server_socket: ServerSocket
    gdb_server: GdbServer
    process: GdbProcess
    l1_start: int
    l1_end: int  # exclusive
    data_private_start: int | None
    data_private_end: int | None  # exclusive
    memory_regions: list[tuple[str, int, int]]
    pid: int

    @classmethod
    def setUpClass(cls) -> None:
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

        # Start GdbServer on a free port
        cls.server_socket = ServerSocket(port=None)
        cls.server_socket.start()
        cls.gdb_server = GdbServer(cls.context, cls.server_socket)
        cls.gdb_server.start()

        # Discover available processes via the regular GdbServer path
        available = cls.gdb_server.available_processes
        if not available:
            raise unittest.SkipTest("No debuggable RISC-V cores available for GdbServer tests")

        # For tests, just take the first process
        cls.pid, cls.process = next(iter(available.items()))
        cls.risc_debug = cls.process.risc_debug
        cls.location = cls.risc_debug.risc_location.location

        # L1 memory boundaries [start, end)
        l1 = cls.risc_debug.get_l1()
        assert l1.address.private_address is not None
        cls.l1_start = l1.address.private_address
        cls.l1_end = cls.l1_start + l1.size

        # Data private memory boundaries [start, end) (if present)
        data_private = cls.risc_debug.get_data_private_memory()
        if data_private is not None and data_private.address.private_address is not None:
            cls.data_private_start = data_private.address.private_address
            cls.data_private_end = cls.data_private_start + data_private.size
        else:
            cls.data_private_start = None
            cls.data_private_end = None

        # List of allowed regions ([start, end) ranges)
        cls.memory_regions: list[tuple[str, int, int]] = [
            ("l1", cls.l1_start, cls.l1_end),
        ]
        if cls.data_private_start is not None and cls.data_private_end is not None:
            cls.memory_regions.append(("data_private", cls.data_private_start, cls.data_private_end))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.gdb_server.stop()
        cls.server_socket.close()

    @contextmanager
    def _gdb_client(self) -> socket.socket:
        """
        Context manager that connects to GdbServer, attaches to the process via
        vAttach, and ensures socket cleanup.
        """
        sock = self._connect_client_and_attach()
        try:
            yield sock
        finally:
            sock.close()

    def _connect_client_and_attach(self) -> socket.socket:
        """
        Connect to the GdbServer and attach to the selected process using vAttach.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10.0)
        assert self.server_socket.port is not None
        s.connect(("localhost", self.server_socket.port))

        # Optional: initial handshake (matches real GDB behavior a bit closer)
        self._send_packet(s, b"qSupported")

        # Attach to the process the server reported as pid
        attach_cmd = f"vAttach;{self.pid:x}".encode()
        reply = self._send_packet(s, attach_cmd)

        # vAttach should return a stop reply packet (T.. or S..)
        self.assertTrue(
            reply.startswith(b"T") or reply.startswith(b"S"),
            f"Expected stop reply after vAttach, got: {reply!r}",
        )

        return s

    def _send_packet(self, sock: socket.socket, payload: bytes) -> bytes:
        """
        Send a single GDB remote serial protocol packet and return the reply body.

        - Builds: $<payload>#<checksum>
        - Expects a '+' ACK from the server.
        - Returns bytes between '$' and '#' of the reply packet.
        """
        checksum = sum(payload) % 256
        pkt = bytearray()
        pkt.append(GDB_ASCII_DOLLAR)
        pkt.extend(payload)
        pkt.append(GDB_ASCII_HASH)

        hi, lo = divmod(checksum, 16)
        hi_ch = (ord("0") + hi) if hi < 10 else (ord("A") + hi - 10)
        lo_ch = (ord("0") + lo) if lo < 10 else (ord("A") + lo - 10)
        pkt.append(hi_ch)
        pkt.append(lo_ch)

        sock.sendall(pkt)

        # Expect '+' ACK
        ack = sock.recv(1)
        self.assertEqual(ack, b"+", "Expected '+' ACK from GdbServer")

        # Reply must start with '$'
        ch = sock.recv(1)
        self.assertEqual(ch, b"$", "Expected '$' at start of reply")

        # Read until '#'
        data = bytearray()
        while True:
            ch = sock.recv(1)
            if ch == b"#":
                break
            data.extend(ch)

        # Skip checksum (2 hex digits)
        sock.recv(2)

        return bytes(data)

    def test_x_read_inside_allowed_memory_ok(self) -> None:
        """x: full-length binary read inside allowed regions must succeed."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                with self.subTest(memory_region=region_name):
                    length = 16
                    addr = start + 0x100
                    if addr + length > end:
                        # Region too small near the end; skip this subcase
                        continue

                    payload = f"x{addr:x},{length:x}".encode()
                    reply = self._send_packet(sock, payload)

                    self.assertGreaterEqual(len(reply), 1)
                    self.assertEqual(reply[0:1], b"b")
                    self.assertEqual(
                        len(reply) - 1,
                        length,
                        f"x inside {region_name} should return full {length} bytes, got {len(reply)-1}",
                    )

    def test_x_read_restricted_memory_e04(self) -> None:
        """x: any read that leaves allowed regions must return E04."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                test_cases: list[tuple[str, int, int]] = [
                    ("fully_outside", end, 4),  # entire range past region end
                    ("partial_end_after", end - 1, 8),  # start inside, end after
                ]
                # partial_start_before: start before region, end inside
                if start >= 4:
                    test_cases.append(("partial_start_before", start - 4, 8))

                for name, addr, length in test_cases:
                    with self.subTest(
                        memory_region=region_name,
                        scenario=name,
                        addr=hex(addr),
                        length=length,
                    ):
                        payload = f"x{addr:x},{length:x}".encode()
                        reply = self._send_packet(sock, payload)
                        self.assertEqual(
                            reply,
                            b"E04",
                            f"Expected E04 for {region_name} {name} scenario, got {reply!r}",
                        )

    def test_m_read_inside_allowed_memory_ok(self) -> None:
        """m: full-length hex read inside allowed regions must succeed."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                with self.subTest(memory_region=region_name):
                    length = 8
                    addr = start + 0x200
                    if addr + length > end:
                        continue

                    payload = f"m{addr:x},{length:x}".encode()
                    reply = self._send_packet(sock, payload)

                    # Each byte → 2 hex chars
                    self.assertEqual(
                        len(reply),
                        2 * length,
                        f"m inside {region_name} should return {2*length} hex chars, got {len(reply)}",
                    )

    def test_m_read_restricted_memory_e04(self) -> None:
        """m: any hex read that leaves allowed regions must return E04."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                test_cases: list[tuple[str, int, int]] = [
                    ("fully_outside", end, 8),
                    ("partial_end_after", end - 4, 8),
                ]
                if start >= 4:
                    test_cases.append(("partial_start_before", start - 4, 8))

                for name, addr, length in test_cases:
                    with self.subTest(
                        memory_region=region_name,
                        scenario=name,
                        addr=hex(addr),
                        length=length,
                    ):
                        payload = f"m{addr:x},{length:x}".encode()
                        reply = self._send_packet(sock, payload)
                        self.assertEqual(
                            reply,
                            b"E04",
                            f"Expected E04 for {region_name} {name} scenario, got {reply!r}",
                        )

    def test_M_write_inside_allowed_memory_ok(self) -> None:
        """M: hex write fully inside allowed regions must succeed with OK."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                with self.subTest(memory_region=region_name):
                    length = 4
                    addr = start + 0x300
                    if addr + length > end:
                        continue

                    data_hex = "aabbccdd"  # 4 bytes
                    payload = f"M{addr:x},{length:x}:{data_hex}".encode()
                    reply = self._send_packet(sock, payload)

                    self.assertEqual(reply, b"OK")

    def test_M_write_restricted_memory_e04(self) -> None:
        """M: any hex write that leaves allowed regions must return E04."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                test_cases: list[tuple[str, int, int, str]] = [
                    ("fully_outside", end, 4, "00112233"),
                    ("partial_end_after", end - 2, 8, "0011223344556677"),
                ]
                if start >= 4:
                    test_cases.append(("partial_start_before", start - 4, 8, "0011223344556677"))

                for name, addr, length, data_hex in test_cases:
                    with self.subTest(
                        memory_region=region_name,
                        scenario=name,
                        addr=hex(addr),
                        length=length,
                    ):
                        payload = f"M{addr:x},{length:x}:{data_hex}".encode()
                        reply = self._send_packet(sock, payload)
                        self.assertEqual(
                            reply,
                            b"E04",
                            f"Expected E04 for {region_name} {name} scenario, got {reply!r}",
                        )

    def test_X_write_inside_allowed_memory_ok(self) -> None:
        """X: binary write fully inside allowed regions must succeed with OK."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                with self.subTest(memory_region=region_name):
                    data = b"\x11\x22\x33\x44"
                    length = len(data)
                    addr = start + 0x400
                    if addr + length > end:
                        continue

                    payload = f"X{addr:x},{length:x}:".encode() + data
                    reply = self._send_packet(sock, payload)
                    self.assertEqual(reply, b"OK")

    def test_X_write_restricted_memory_e04(self) -> None:
        """X: any binary write that leaves allowed regions must return E04."""
        with self._gdb_client() as sock:
            for region_name, start, end in self.memory_regions:
                test_cases: list[tuple[str, int, bytes]] = [
                    ("fully_outside", end, b"\xAA\xBB\xCC\xDD"),
                    (
                        "partial_end_after",
                        end - 4,
                        b"\x00\x11\x22\x33\x44\x55\x66\x77\x88\x99\xAA\xBB\xCC\xDD\xEE\xFF",
                    ),
                ]
                if start >= 4:
                    test_cases.append(("partial_start_before", start - 4, b"\xFF\xEE\xDD\xCC\xBB\xAA\x99\x88"))

                for name, addr, data in test_cases:
                    with self.subTest(
                        memory_region=region_name,
                        scenario=name,
                        addr=hex(addr),
                        data_len=len(data),
                    ):
                        length = len(data)
                        payload = f"X{addr:x},{length:x}:".encode() + data
                        reply = self._send_packet(sock, payload)
                        self.assertEqual(
                            reply,
                            b"E04",
                            f"Expected E04 for {region_name} {name} scenario, got {reply!r}",
                        )


def _find_riscv_gdb() -> str | None:
    """
    Try to locate a suitable RISC-V GDB binary.

    Priority:
      1. TTEXALENS_RISCV_GDB env var
      2. build/sfpi/compiler/bin/riscv-tt-elf-gdb
      3. riscv-tt-elf-gdb in PATH
    """
    env_bin = os.getenv("TTEXALENS_RISCV_GDB")
    if env_bin and shutil.which(env_bin):
        return env_bin

    local_bin = os.path.join("build", "sfpi", "compiler", "bin", "riscv-tt-elf-gdb")
    if os.path.exists(local_bin):
        return local_bin

    which_bin = shutil.which("riscv-tt-elf-gdb")
    if which_bin:
        return which_bin

    return None


@unittest.skipUnless(
    _find_riscv_gdb() is not None,
    "RISC-V GDB not found (set TTEXALENS_RISCV_GDB or build/sfpi/compiler/bin/riscv-tt-elf-gdb)",
)
class TestGdbMemAccessIntegration(unittest.TestCase):
    """
    Integration test: run a real GDB client against GdbServer and verify that
    L1/private restriction (E04) behaves sanely from the GDB user's perspective.

    We use edge_mem_test.*.brisc.elf, which defines:
      - g_p_wormhole  -> 0x0016DFF8  (8B in Wormhole L1, 8B past)
      - g_p_blackhole -> 0x0017FFF8  (8B in Blackhole L1, 8B past)

    This test chooses which symbol to use based on the device arch.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

        # Determine architecture string for ELF path and symbol selection
        arch_str = str(cls.device._arch).lower()
        if arch_str.startswith("wormhole"):
            cls.arch = "wormhole"
        elif arch_str.startswith("blackhole"):
            cls.arch = "blackhole"
        else:
            raise unittest.SkipTest(f"Unsupported architecture for this test: {cls.device._arch}")

        # Use FW0 BRISC at 0,0 (same convention as other tests)
        cls.location = get_core_location("FW0", cls.device)
        cls.location_str = cls.location.to_str()

        # Edge ELF that defines g_p_wormhole / g_p_blackhole
        cls.elf_path = os.path.join(
            "build",
            "riscv-src",
            cls.arch,
            "edge_mem_test.debug.brisc.elf",
        )
        if not os.path.exists(cls.elf_path):
            raise unittest.SkipTest(f"{cls.elf_path} does not exist; build edge_mem_test first.")

        # Arch-specific pointer symbol and expected edge address
        if cls.arch == "wormhole":
            cls.gdb_symbol = "g_p_wormhole"
            cls.edge_addr = 0x0016DFF8
        else:  # blackhole
            cls.gdb_symbol = "g_p_blackhole"
            cls.edge_addr = 0x0017FFF8

        # Run the ELF on BRISC so there is a live process to attach to
        run_elf(cls.elf_path, cls.location_str, "brisc", context=cls.context)

        # Start GdbServer on a free port
        cls.server_socket = ServerSocket(port=None)
        cls.server_socket.start()
        cls.gdb_server = GdbServer(cls.context, cls.server_socket)
        cls.gdb_server.start()

        # Small delay to ensure the server is listening
        time.sleep(0.2)

        cls.gdb_bin = _find_riscv_gdb()
        assert cls.gdb_bin is not None

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.gdb_server.stop()
        finally:
            cls.server_socket.close()

    def test_gdb_x_sees_l1_and_reports_error_past_l1(self) -> None:
        """
        Scenario:

          - GdbServer has restricted m/x/M/X to L1 + private, returning E04 outside.
          - We run edge_mem_test on BRISC; g_p_wormhole / g_p_blackhole point near L1 end.
          - We run a real RISC-V GDB and execute: x/16xb <arch-specific pointer>

        Expectations:

          - GDB prints bytes at EDGE_ADDR (L1 part).
          - When it reaches out-of-L1 region, it shows a clear error:
              - e.g. 'Cannot access memory at address ...'
                or 'Remote failure reply: E04'
          - No crash/hang; GDB exits cleanly.
        """
        port = self.server_socket.port
        assert port is not None

        with tempfile.TemporaryDirectory(prefix="gdb_mem_access_") as tmpdir:
            script_path = os.path.join(tmpdir, "commands.gdb")

            sym = self.gdb_symbol
            expected_prefix = f"0x{self.edge_addr:x}:"

            gdb_commands = textwrap.dedent(
                f"""
                set pagination off
                set confirm off
                set verbose off
                set debug remote 1

                # Connect to TTExaLens GdbServer
                target extended-remote localhost:{port}

                # Attach to pid 1 (BRISC FW0)
                attach 1

                # Load symbols for our edge_mem_test
                add-symbol-file {self.elf_path}

                # Inspect pointer and then dump 16 bytes from it
                print {sym}
                x/16xb {sym}

                quit
                """
            ).strip()

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(gdb_commands + "\n")

            # Capture raw bytes from GDB, then decode with a tolerant codec so
            # binary remote debug output doesn't break the test.
            proc = subprocess.run(
                [self.gdb_bin, "-q", "-x", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,  # <-- raw bytes
                timeout=60,
            )

            output = proc.stdout.decode("utf-8", errors="replace")
            util.INFO("GDB integration test output:\n" + output)

            # 1) GDB should exit cleanly
            self.assertEqual(
                proc.returncode,
                0,
                f"GDB exited with non-zero code {proc.returncode}\nOutput:\n{output}",
            )

            # 2) Expect bytes at EDGE_ADDR (L1 part for the arch-specific pointer)
            self.assertIn(
                expected_prefix,
                output,
                f"Expected GDB to print bytes at {expected_prefix} from {sym}\nOutput:\n{output}",
            )

            # 3) Expect some indication that a memory access past L1 failed.
            #    Exact wording depends on GDB version; accept a couple of variants.
            error_signatures = [
                "Cannot access memory at address",
                "Remote failure reply: E04",
            ]
            self.assertTrue(
                any(sig in output for sig in error_signatures),
                f"Expected GDB to report restricted memory (E04) in a user-visible way.\nOutput:\n{output}",
            )
