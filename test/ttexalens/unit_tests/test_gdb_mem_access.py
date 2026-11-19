# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import os
import subprocess
import tempfile
import textwrap
import time
import unittest

from parameterized import parameterized

from test.ttexalens.unit_tests.test_base import (
    init_cached_test_context,
    get_core_location,
)

from ttexalens import util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.gdb.gdb_client import get_gdb_client_path, get_process_ids
from ttexalens.gdb.gdb_server import GdbServer
from ttexalens.gdb.gdb_communication import (
    ServerSocket,
)
from ttexalens.hardware.risc_debug import RiscDebug, RiscLocation
from ttexalens.tt_exalens_lib import parse_elf, read_from_device, run_elf, write_to_device

_MAINTENANCE_CASES: list[tuple[str, str, int | None, bool]] = [
    # Wormhole L1: [0x00000000, 0x0016E000)
    ("wormhole_inside", "wormhole", None, False),
    ("wormhole_partial", "wormhole", 0x0016DFF8, True),
    ("wormhole_outside", "wormhole", 0x0016E000, True),
    # Blackhole L1: [0x00000000, 0x00180000)
    ("blackhole_inside", "blackhole", None, False),
    ("blackhole_partial", "blackhole", 0x0017FFF8, True),
    ("blackhole_outside", "blackhole", 0x00180000, True),
]


def _run_gdb_script(gdb_bin: str, script: str) -> tuple[int, str]:
    """
    Run GDB in batch mode with the given script and return (returncode, decoded_output).
    """
    with tempfile.TemporaryDirectory(prefix="gdb_packets_") as tmpdir:
        script_path = os.path.join(tmpdir, "commands.gdb")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(script).strip() + "\n")
        proc = subprocess.run(
            [gdb_bin, "-q", "-x", script_path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,
            timeout=10,
        )
    return proc.returncode, proc.stdout.decode("utf-8", errors="replace")


def _maintenance_packet_replies(output: str) -> list[str]:
    """
    Return the replies printed by 'maintenance packet' commands, in order.
    GDB prints each one as: received: "<reply>"
    """
    replies = []
    for line in output.splitlines():
        line = line.strip()
        if line.startswith('received: "') and line.endswith('"'):
            replies.append(line[len('received: "') : -1])
    return replies


class TestGdbMemAccessFromClient(unittest.TestCase):
    """
    Integration tests: run a real GDB client against GdbServer and verify that
    L1/private restriction (E04) behaves sanely from the GDB user's perspective.
    """

    # Class attributes set in setUpClass
    context: Context
    device: Device
    arch: str
    location: OnChipCoordinate
    location_str: str
    elf_path: str
    gdb_edge_symbol: str
    edge_addr: int
    inside_addr: int
    server_socket: ServerSocket
    gdb_server: GdbServer
    gdb_bin: str

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

        # Edge ELF that defines g_p_* symbols and the g_scratch thread-local window
        cls.elf_path = os.path.join(
            "build",
            "riscv-src",
            cls.arch,
            "edge_mem_test.debug.brisc.elf",
        )
        if not os.path.exists(cls.elf_path):
            raise unittest.SkipTest(f"{cls.elf_path} does not exist; build edge_mem_test first.")

        # Resolve the kernel's thread-local scratch window as the "inside L1" probe address.
        tls_symbol = parse_elf(cls.elf_path, cls.context).find_symbol_by_name("__thread_local_start")
        assert tls_symbol is not None, "edge_mem_test ELF is missing __thread_local_start"
        cls.inside_addr = int(tls_symbol.value)

        # Arch-specific pointer symbol and edge address for the x/16xb test
        if cls.arch == "wormhole":
            cls.gdb_edge_symbol = "g_p_wormhole"
            cls.edge_addr = 0x0016DFF8
        else:  # blackhole
            cls.gdb_edge_symbol = "g_p_blackhole"
            cls.edge_addr = 0x0017FFF8

        # Run the ELF on BRISC so there is a live process to attach to
        run_elf(cls.elf_path, cls.location_str, "brisc", context=cls.context)

        # Start GdbServer on a free port
        cls.server_socket = ServerSocket(port=None)
        cls.server_socket.start()
        cls.gdb_server = GdbServer(cls.context, cls.server_socket, skip_detach=True, debug_only_with_elfs=True)
        cls.gdb_server.start()

        # Small delay to ensure the server is listening
        time.sleep(0.2)

        cls.gdb_bin = get_gdb_client_path()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.gdb_server.stop()
        finally:
            cls.server_socket.close()

    def _run_gdb_script(self, script_path: str) -> tuple[int, str]:
        """
        Run GDB in batch mode with the given script and return (returncode, decoded_output).
        We capture raw bytes and decode with errors='replace' so that binary
        remote protocol logs don't break the test.
        """
        proc = subprocess.run(
            [self.gdb_bin, "-q", "-x", script_path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,  # capture raw bytes
            timeout=2,
        )
        output = proc.stdout.decode("utf-8", errors="replace")
        return proc.returncode, output

    def _assert_packet_result(
        self,
        output: str,
        cmd_prefix: str,
        addr_hex: str,
        length_hex: str,
        expect_e04: bool,
    ) -> None:
        """
        Assert that a maintenance packet with the given cmd/addr/len
        produced (or did not produce) E04 in the immediate reply.
        """
        send_marker = f"Sending packet: ${cmd_prefix}{addr_hex},{length_hex}"
        self.assertIn(
            send_marker,
            output,
            f"Expected to see '{send_marker}' in GDB remote log.\nOutput:\n{output}",
        )

        idx = output.find(send_marker)
        self.assertNotEqual(idx, -1)
        sub = output[idx:]

        recv_prefix = "Packet received: "
        recv_idx = sub.find(recv_prefix)
        self.assertNotEqual(
            recv_idx,
            -1,
            f"Expected a 'Packet received' after '{send_marker}'.\nSub-output:\n{sub}",
        )

        recv_line = sub[recv_idx + len(recv_prefix) :].splitlines()[0]
        recv_val = recv_line.strip()

        if expect_e04:
            self.assertEqual(
                recv_val,
                "E04",
                f"Expected E04 for packet '{send_marker}', got '{recv_val}'\nSub-output:\n{sub}",
            )
        else:
            self.assertNotEqual(
                recv_val,
                "E04",
                f"Did not expect E04 for packet '{send_marker}', but got it.\nSub-output:\n{sub}",
            )

    def test_gdb_x_sees_l1_and_reports_error_past_l1(self) -> None:
        """
        Use 'print sym' / 'print *sym' and 'x/16xb sym' on the edge pointer and verify:
          - the pointer value (edge_addr) is printed correctly
          - dereferencing yields an error-like result (<incomplete type>)
          - x/16xb triggers a visible memory access error (E04/Can't access)
          - GDB exits cleanly
        """
        port = self.server_socket.port
        assert port is not None

        with tempfile.TemporaryDirectory(prefix="gdb_mem_access_") as tmpdir:
            script_path = os.path.join(tmpdir, "commands_x.gdb")

            sym = self.gdb_edge_symbol
            ptr_str = f"0x{self.edge_addr:x}"

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

                # 1) Inspect pointer value
                print {sym}

                # 2) Try to dereference the array at the edge of L1
                print *{sym}

                # 3) Also do a raw memory dump across the edge
                x/16xb {sym}

                quit
                """
            ).strip()

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(gdb_commands + "\n")

            rc, output = self._run_gdb_script(script_path)
            util.INFO("GDB integration test output (print/x on edge pointer):\n" + output)

            # 1) GDB should exit cleanly
            self.assertEqual(
                rc,
                0,
                f"GDB exited with non-zero code {rc}\nOutput:\n{output}",
            )

            # 2) Expect the pointer value (edge_addr) to be printed
            self.assertIn(
                ptr_str,
                output,
                f"Expected GDB to print pointer value {ptr_str} for {sym}\nOutput:\n{output}",
            )

            # 3) Expect some indication that the raw x/16xb hit a memory access error.
            error_signatures = [
                "Cannot access memory at address",
                "Remote failure reply: E04",
            ]
            self.assertTrue(
                any(sig in output for sig in error_signatures),
                f"Expected GDB/x to report restricted memory (E04) in a user-visible "
                f"or remote-log way.\nOutput:\n{output}",
            )

    @parameterized.expand(_MAINTENANCE_CASES)
    def test_gdb_maintenance_m_M_x_X(
        self,
        _label: str,
        arch: str,
        addr: int | None,
        expect_e04: bool,
    ) -> None:
        """
        For a given (arch, addr, expect_e04) case:

          - if arch != current device arch, skip.
          - send maintenance packet m/M/x/X for that addr/size.
          - assert that replies either all succeed or all E04.

        addr is None for the "inside L1" case; it is resolved to the kernel's
        thread-local scratch window (see setUpClass) so the write cannot corrupt
        code or data.
        """
        if arch != self.arch:
            self.skipTest(f"Case for arch={arch}, current arch={self.arch}")

        if addr is None:
            addr = self.inside_addr

        port = self.server_socket.port
        assert port is not None

        addr_hex = f"{addr:x}"
        length_hex = "10"  # 16 bytes

        with tempfile.TemporaryDirectory(prefix="gdb_mem_access_") as tmpdir:
            script_path = os.path.join(tmpdir, f"commands_packets_{arch}_{addr_hex}.gdb")

            gdb_commands = textwrap.dedent(
                f"""
                set pagination off
                set confirm off
                set verbose off
                set debug remote 1

                target extended-remote localhost:{port}
                attach 1
                add-symbol-file {self.elf_path}

                # m: hex read
                maintenance packet m{addr_hex},{length_hex}

                # M: hex write
                maintenance packet M{addr_hex},{length_hex}:00112233445566778899AABBCCDDEEFF

                # x: binary read
                maintenance packet x{addr_hex},{length_hex}

                # X: binary write
                maintenance packet X{addr_hex},{length_hex}:ABCDEFGHIJKLMNOP

                quit
                """
            ).strip()

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(gdb_commands + "\n")

            rc, output = self._run_gdb_script(script_path)
            util.INFO(f"GDB integration test output (maintenance {arch} addr=0x{addr:x}):\n" + output)

            # 1) GDB should exit cleanly
            self.assertEqual(
                rc,
                0,
                f"GDB exited with non-zero code {rc}\nOutput:\n{output}",
            )

            # For this addr, all four packets (m/M/x/X) should either all succeed or all E04.
            self._assert_packet_result(output, "m", addr_hex, length_hex, expect_e04=expect_e04)
            self._assert_packet_result(output, "M", addr_hex, length_hex, expect_e04=expect_e04)
            self._assert_packet_result(output, "x", addr_hex, length_hex, expect_e04=expect_e04)
            self._assert_packet_result(output, "X", addr_hex, length_hex, expect_e04=expect_e04)

    def test_gdb_m_reads_bytes_in_address_order(self) -> None:
        """
        Write 16 known bytes with 'M' and read them back with 'm': the 'm' reply must list the bytes in
        address order, the same order 'M' takes them and that the device holds them in.
        """
        port = self.server_socket.port
        assert port is not None
        pid = get_process_ids(self.gdb_server)[RiscLocation(self.location, None, "brisc")]
        pattern = "00112233445566778899AABBCCDDEEFF"
        addr_hex = f"{self.inside_addr:x}"

        rc, output = _run_gdb_script(
            self.gdb_bin,
            f"""
            set pagination off
            set confirm off
            target extended-remote localhost:{port}
            attach {pid}
            maintenance packet M{addr_hex},10:{pattern}
            maintenance packet m{addr_hex},10
            maintenance packet m{addr_hex},4
            quit
            """,
        )
        self.assertEqual(rc, 0, f"GDB exited with non-zero code {rc}\nOutput:\n{output}")
        self.assertEqual(_maintenance_packet_replies(output), ["OK", pattern, pattern[:8]], output)

        # The device holds the bytes in the same order
        device_bytes = read_from_device(self.location, self.inside_addr, num_bytes=16, context=self.context)
        self.assertEqual(bytes(device_bytes).hex().upper(), pattern)

    def test_gdb_p_P_use_target_byte_order(self) -> None:
        """
        'p' must reply with the same bytes as that register's slot in the 'g' reply (target byte order),
        and 'P' must take its value in the same order, so that 'P' followed by 'p' round-trips and the core
        holds the written value.
        """
        port = self.server_socket.port
        assert port is not None
        risc_location = RiscLocation(self.location, None, "brisc")
        pid = get_process_ids(self.gdb_server)[risc_location]
        risc_debug = self.location.noc_block.get_risc_debug("brisc", None)
        sp_register = 2  # holds a non-zero value whose four bytes differ, so a byte swap shows
        register = 31  # t6; the test kernel is a nop loop that does not use it
        value = 0x12345678
        value_hex = value.to_bytes(4, "little").hex().upper()

        rc, output = _run_gdb_script(
            self.gdb_bin,
            f"""
            set pagination off
            set confirm off
            target extended-remote localhost:{port}
            attach {pid}
            maintenance packet g
            maintenance packet p{sp_register:x}
            maintenance packet P{register:x}={value_hex}
            maintenance packet p{register:x}
            maintenance packet p{GdbServer.REGISTER_COUNT:x}
            quit
            """,
        )
        self.assertEqual(rc, 0, f"GDB exited with non-zero code {rc}\nOutput:\n{output}")
        replies = _maintenance_packet_replies(output)
        self.assertEqual(len(replies), 5, output)
        g_reply, p_sp, P_reply, p_after, p_out_of_range = replies
        original = int.from_bytes(bytes.fromhex(g_reply[8 * register : 8 * register + 8]), "little")
        try:
            self.assertEqual(p_sp, g_reply[8 * sp_register : 8 * sp_register + 8], output)
            self.assertEqual(int.from_bytes(bytes.fromhex(p_sp), "little"), risc_debug.read_gpr(sp_register))
            self.assertEqual(P_reply, "OK", output)
            self.assertEqual(p_after, value_hex, output)
            self.assertEqual(risc_debug.read_gpr(register), value)
            self.assertEqual(p_out_of_range, "E01", output)
        finally:
            # Leave the register as GDB found it
            risc_debug.write_gpr(register, original)


class TestGdbRegistersAtEbreak(unittest.TestCase):
    """
    Run a kernel that halts on an ebreak and check that GDB sees the same pc whether it reads all registers
    ('g') or only the pc ('p').
    """

    context: Context
    device: Device
    location: OnChipCoordinate
    risc_debug: RiscDebug
    server_socket: ServerSocket
    gdb_server: GdbServer
    gdb_bin: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]
        arch_str = str(cls.device._arch).lower()
        if arch_str.startswith("wormhole"):
            arch = "wormhole"
        elif arch_str.startswith("blackhole"):
            arch = "blackhole"
        else:
            raise unittest.SkipTest(f"Unsupported architecture for this test: {cls.device._arch}")
        cls.location = get_core_location("FW0", cls.device)
        elf_path = os.path.join("build", "riscv-src", arch, "callstack.release.brisc.elf")
        if not os.path.exists(elf_path):
            raise unittest.SkipTest(f"{elf_path} does not exist; build the callstack test kernel first.")

        # Recursion count 0 makes the kernel call halt(), which executes an ebreak
        parsed_elf = parse_elf(elf_path, cls.context)
        text_section = parsed_elf.get_section_by_name(".text")
        assert text_section is not None and text_section.address is not None
        write_to_device(
            cls.location, text_section.address + text_section.size, (0).to_bytes(4, "little"), context=cls.context
        )
        run_elf(elf_path, cls.location.to_str(), "brisc", context=cls.context)
        cls.risc_debug = cls.location.noc_block.get_risc_debug("brisc", None)
        deadline = time.time() + 2
        while not cls.risc_debug.is_halted() and time.time() < deadline:
            time.sleep(0.01)
        if not cls.risc_debug.read_status().is_ebreak_hit:
            raise unittest.SkipTest("Callstack kernel did not halt on its ebreak")

        cls.server_socket = ServerSocket(port=None)
        cls.server_socket.start()
        cls.gdb_server = GdbServer(cls.context, cls.server_socket, skip_detach=True, debug_only_with_elfs=True)
        cls.gdb_server.start()
        time.sleep(0.2)
        cls.gdb_bin = get_gdb_client_path()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.gdb_server.stop()
        finally:
            cls.server_socket.close()

    def test_gdb_p_pc_matches_g_at_ebreak(self) -> None:
        port = self.server_socket.port
        assert port is not None
        pid = get_process_ids(self.gdb_server)[RiscLocation(self.location, None, "brisc")]
        rc, output = _run_gdb_script(
            self.gdb_bin,
            f"""
            set pagination off
            set confirm off
            target extended-remote localhost:{port}
            attach {pid}
            maintenance packet g
            maintenance packet p20
            quit
            """,
        )
        self.assertEqual(rc, 0, f"GDB exited with non-zero code {rc}\nOutput:\n{output}")
        replies = _maintenance_packet_replies(output)
        self.assertEqual(len(replies), 2, output)
        g_pc = replies[0][8 * 32 : 8 * 33]
        self.assertEqual(replies[1], g_pc, output)
        # The pc GDB sees is the ebreak itself, 4 bytes before the hardware pc
        self.assertEqual(int.from_bytes(bytes.fromhex(g_pc), "little"), self.risc_debug.read_gpr(32) - 4)
