# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import os
import re
import subprocess
import tempfile
import textwrap
import time
import unittest
from unittest.mock import MagicMock, PropertyMock, patch

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
from ttexalens.gdb.gdb_data import GdbProcess
from ttexalens.gdb.gdb_server import GdbServer
from ttexalens.gdb.gdb_communication import (
    GdbMessageParser,
    GdbMessageWriter,
    ServerSocket,
)
from ttexalens.hardware.risc_debug import RiscDebugStatus, RiscDebugWatchpointState, RiscLocation
from ttexalens.tt_exalens_lib import parse_elf, run_elf

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


def _run_gdb_script(gdb_bin: str, script_path: str, timeout: float = 2) -> tuple[int, str]:
    """
    Run GDB in batch mode with the given script and return (returncode, decoded_output).
    We capture raw bytes and decode with errors='replace' so that binary
    remote protocol logs don't break the test.
    """
    try:
        proc = subprocess.run(
            [gdb_bin, "-q", "-x", script_path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=False,  # capture raw bytes
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        partial_output = (e.output or b"").decode("utf-8", errors="replace")
        raise AssertionError(f"GDB did not finish within {timeout} s\nOutput:\n{partial_output}") from e
    output = proc.stdout.decode("utf-8", errors="replace")
    return proc.returncode, output


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

            rc, output = _run_gdb_script(self.gdb_bin, script_path)
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

            rc, output = _run_gdb_script(self.gdb_bin, script_path)
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


class TestGdbBreakpointsFromClient(unittest.TestCase):
    context: Context
    device: Device
    arch: str
    location: OnChipCoordinate
    location_str: str
    elf_path: str
    gdb_bin: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

        arch_str = str(cls.device._arch).lower()
        if arch_str.startswith("wormhole"):
            cls.arch = "wormhole"
        elif arch_str.startswith("blackhole"):
            cls.arch = "blackhole"
        else:
            raise unittest.SkipTest(f"Unsupported architecture for this test: {cls.device._arch}")

        cls.location = get_core_location("FW0", cls.device)
        cls.location_str = cls.location.to_str()

        cls.elf_path = os.path.join("build", "riscv-src", cls.arch, "gdb_breakpoint_test.debug.brisc.elf")
        if not os.path.exists(cls.elf_path):
            raise unittest.SkipTest(f"{cls.elf_path} does not exist; build gdb_breakpoint_test first.")

        cls.gdb_bin = get_gdb_client_path()

    def setUp(self) -> None:
        run_elf(self.elf_path, self.location_str, "brisc", context=self.context)
        self.server_socket = ServerSocket(port=None)
        self.server_socket.start()
        self.gdb_server = GdbServer(self.context, self.server_socket, skip_detach=True, debug_only_with_elfs=True)
        self.gdb_server.start()
        self.pid = get_process_ids(self.gdb_server)[RiscLocation(self.location, None, "brisc")]

    def tearDown(self) -> None:
        try:
            self.gdb_server.stop()
        finally:
            self.server_socket.close()
            risc_debug = self.location.noc_block.get_risc_debug("brisc")
            for i in range(len(risc_debug.read_watchpoints_state())):
                risc_debug.disable_watchpoint(i)
            risc_debug.set_reset_signal(True)

    def _run_gdb_commands(self, commands: list[str]) -> str:
        port = self.server_socket.port
        assert port is not None
        script = "\n".join(
            [
                "set pagination off",
                "set confirm off",
                "set debug remote 1",
                f"target extended-remote localhost:{port}",
                f"attach {self.pid}",
                f"add-symbol-file {self.elf_path}",
                *commands,
                "quit",
            ]
        )
        with tempfile.TemporaryDirectory(prefix="gdb_breakpoints_") as tmpdir:
            script_path = os.path.join(tmpdir, "commands.gdb")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script + "\n")
            rc, output = _run_gdb_script(self.gdb_bin, script_path, timeout=60)
        self.assertEqual(rc, 0, f"GDB exited with non-zero code {rc}\nOutput:\n{output}")
        self.assertNotIn("Program received signal", output, output)
        return output

    @staticmethod
    def _printed_values(output: str) -> dict[int, str]:
        return {int(number): value.strip() for number, value in re.findall(r"^\$(\d+) = (.*)$", output, re.MULTILINE)}

    def test_conditional_breakpoint_stops_on_each_true_hit(self) -> None:
        output = self._run_gdb_commands(
            [
                "break add_element if g_index == 5",
                "continue",
                "print g_index",
                "print g_round",
                "continue",
                "print g_index",
                "print g_round",
            ]
        )
        values = self._printed_values(output)
        self.assertEqual(output.count("Breakpoint 1, add_element"), 2, output)
        self.assertEqual(values.get(1), "5", output)
        self.assertEqual(values.get(3), "5", output)
        self.assertIn(2, values, output)
        self.assertIn(4, values, output)
        self.assertEqual(int(values[4]), int(values[2]) + 1, output)

    def test_never_true_condition_runs_to_later_breakpoint(self) -> None:
        output = self._run_gdb_commands(
            [
                "break add_element if g_index == 100",
                "break round_done",
                "continue",
                "print g_sum",
            ]
        )
        values = self._printed_values(output)
        self.assertIn("Breakpoint 2, round_done", output)
        self.assertNotIn("Breakpoint 1,", output)
        self.assertEqual(values.get(1), "98", output)

    def test_condition_set_changed_and_removed(self) -> None:
        output = self._run_gdb_commands(
            [
                "break add_element",
                "condition 1 g_index == 6",
                "continue",
                "print g_index",
                "condition 1 g_index == 2",
                "continue",
                "print g_index",
                "condition 1",
                "continue",
                "print g_index",
            ]
        )
        values = self._printed_values(output)
        self.assertEqual(values.get(1), "6", output)
        self.assertEqual(values.get(2), "2", output)
        self.assertEqual(values.get(3), "3", output)

    @parameterized.expand(
        [
            ("with_false_condition_breakpoint", True),
            ("without_breakpoint", False),
        ]
    )
    def test_false_condition_breakpoint_keeps_loop_result(self, _label: str, with_false_condition: bool) -> None:
        commands = ["break add_element if g_index == 100"] if with_false_condition else []
        commands += [
            "break round_done",
            "continue",
            "print g_sum",
            "continue",
            "print g_sum",
        ]
        output = self._run_gdb_commands(commands)
        values = self._printed_values(output)
        self.assertEqual(len(re.findall(r"Breakpoint \d+, round_done", output)), 2, output)
        self.assertEqual(values.get(1), "98", output)
        self.assertEqual(values.get(2), "98", output)

    def test_stepi_after_breakpoint_stop(self) -> None:
        output = self._run_gdb_commands(
            [
                "break add_element",
                "continue",
                "x/2i $pc",
                "stepi",
                "print/x $pc",
                "stepi",
                "print/x $pc",
            ]
        )
        values = self._printed_values(output)
        addresses = re.findall(r"^(?:=>)?\s*(0x[0-9a-fA-F]+)(?:\s+<[^>]*>)?:\s", output, re.MULTILINE)
        self.assertEqual(len(addresses), 2, output)
        self.assertIn(1, values, output)
        self.assertIn(2, values, output)
        self.assertEqual(int(values[1], 16), int(addresses[1], 16), output)
        self.assertNotEqual(int(values[2], 16), int(values[1], 16), output)
        self.assertEqual(output.count("Breakpoint 1,"), 1, output)


class TestGdbServerBreakpointPackets(unittest.TestCase):
    def setUp(self) -> None:
        self.risc_debug = MagicMock()
        self.risc_debug.is_halted.return_value = True
        self.risc_debug.is_in_reset.return_value = False
        self.risc_debug.read_gpr.side_effect = lambda i: 0x1238 if i == 32 else 0
        self.risc_debug.read_watchpoint_address.side_effect = lambda i: {1: 0x1234, 2: 0x5678}[i]
        self.risc_debug.read_watchpoints_state.return_value = self._watchpoints({1: self._breakpoint_slot()})
        self.risc_debug.read_status.return_value = self._status()

        self.process = GdbProcess(1, "test.elf", self.risc_debug, 1, "worker")
        self.server = GdbServer(MagicMock(), MagicMock())
        self.server.current_process = self.process
        self.server.debugging_threads = {1: self.process.thread_id}
        available_processes = patch.object(
            GdbServer, "available_processes", new_callable=PropertyMock, return_value={1: self.process}
        )
        available_processes.start()
        self.addCleanup(available_processes.stop)

        sock = MagicMock()
        sock.input_ready.return_value = False
        sock.packet_size = 2048
        self.writer = GdbMessageWriter(sock)

    @staticmethod
    def _status(
        is_pc_watchpoint_hit: bool = False,
        is_memory_watchpoint_hit: bool = False,
        hit_slots: tuple[int, ...] = (),
    ) -> RiscDebugStatus:
        return RiscDebugStatus(
            is_halted=True,
            is_pc_watchpoint_hit=is_pc_watchpoint_hit,
            is_memory_watchpoint_hit=is_memory_watchpoint_hit,
            is_ebreak_hit=False,
            watchpoints_hit=[slot in hit_slots for slot in range(8)],
        )

    @staticmethod
    def _breakpoint_slot() -> RiscDebugWatchpointState:
        return RiscDebugWatchpointState(is_enabled=True, is_memory=False, is_read=False, is_write=False)

    @staticmethod
    def _watchpoints(enabled: dict[int, RiscDebugWatchpointState]) -> list[RiscDebugWatchpointState]:
        disabled = RiscDebugWatchpointState(is_enabled=False, is_memory=False, is_read=False, is_write=False)
        return [enabled.get(slot, disabled) for slot in range(8)]

    def _send(self, packet: bytes) -> str:
        self.server.process_message(GdbMessageParser(packet), self.writer)
        reply = bytes(self.writer.data).decode()
        self.writer.clear()
        return reply

    def _read_pc(self) -> str:
        return self._send(b"g")[1 + 32 * 8 : 1 + 33 * 8]

    def _stop_at_breakpoint(self) -> str:
        self.risc_debug.read_status.return_value = self._status(is_pc_watchpoint_hit=True, hit_slots=(1,))
        return self._send(b"vCont;c:p1.-1")

    def test_breakpoint_stop_reports_swbreak_and_breakpoint_address_as_pc(self) -> None:
        reply = self._stop_at_breakpoint()
        self.assertEqual(reply, "$T05swbreak:;thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.cont.call_count, 1)
        self.assertEqual(self._read_pc(), "34120000")

    def test_step_after_breakpoint_stop_completes_without_hardware_step(self) -> None:
        self._stop_at_breakpoint()
        reply = self._send(b"vCont;s:p1.1;c")
        self.assertEqual(reply, "$T05thread:p1.1;core:1;")
        self.risc_debug.step.assert_not_called()
        self.assertEqual(self._read_pc(), "38120000")

    def test_continue_after_breakpoint_stop_resumes_core(self) -> None:
        self._stop_at_breakpoint()
        self.risc_debug.read_status.return_value = self._status()
        self._send(b"vCont;c:p1.-1")
        self.assertEqual(self.risc_debug.cont.call_count, 2)
        self.assertEqual(self._read_pc(), "38120000")

    def test_step_without_earlier_stop_steps_core(self) -> None:
        reply = self._send(b"vCont;s:p1.1;c")
        self.assertEqual(self.risc_debug.step.call_count, 1)
        self.assertEqual(reply, "$T05thread:p1.1;core:1;")

    def test_breakpoint_stop_reports_address_of_hit_slot(self) -> None:
        self.risc_debug.read_watchpoints_state.return_value = self._watchpoints(
            {1: self._breakpoint_slot(), 2: self._breakpoint_slot()}
        )
        self.risc_debug.read_status.return_value = self._status(is_pc_watchpoint_hit=True, hit_slots=(2,))
        self._send(b"vCont;c:p1.-1")
        self.assertEqual(self._read_pc(), "78560000")

    def test_step_after_memory_watchpoint_stop_completes_without_hardware_step(self) -> None:
        self.risc_debug.read_watchpoints_state.return_value = self._watchpoints(
            {1: RiscDebugWatchpointState(is_enabled=True, is_memory=True, is_read=False, is_write=True)}
        )
        self.risc_debug.read_status.return_value = self._status(is_memory_watchpoint_hit=True, hit_slots=(1,))
        reply = self._send(b"vCont;c:p1.-1")
        self.assertEqual(reply, "$T05watch:1234;thread:p1.1;core:1;")
        self.assertEqual(self._read_pc(), "38120000")

        reply = self._send(b"vCont;s:p1.1;c")
        self.risc_debug.step.assert_not_called()
        self.assertEqual(reply, "$T05thread:p1.1;core:1;")

        self.risc_debug.read_status.return_value = self._status()
        self._send(b"vCont;s:p1.1;c")
        self.assertEqual(self.risc_debug.step.call_count, 1)

    def test_attach_clears_breakpoint_stop_state(self) -> None:
        self._stop_at_breakpoint()
        self.server.debugging_threads.clear()
        self.risc_debug.read_status.return_value = self._status()
        self._send(b"vAttach;1")
        self.assertEqual(self._read_pc(), "38120000")
        self._send(b"vCont;s:p1.1;c")
        self.assertEqual(self.risc_debug.step.call_count, 1)
