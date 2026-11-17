# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import dataclasses
import os
import re
import subprocess
import tempfile
import textwrap
import time
import unittest
from unittest.mock import Mock

from parameterized import parameterized

from test.ttexalens.unit_tests.test_base import (
    init_cached_test_context,
    get_core_location,
    is_simulation,
)

from ttexalens import util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.gdb.gdb_client import get_gdb_client_path, get_process_ids
from ttexalens.gdb.gdb_server import GdbServer
from ttexalens.gdb.gdb_communication import (
    ClientSocket,
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


def run_gdb_script(gdb_bin: str, script_path: str, timeout: float) -> tuple[int, str]:
    """
    Run GDB in batch mode with the given script and return (returncode, decoded_output).
    We capture raw bytes and decode with errors='replace' so that binary
    remote protocol logs don't break the test.
    """
    proc = subprocess.run(
        [gdb_bin, "-q", "-x", script_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=False,  # capture raw bytes
        timeout=timeout,
    )
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

    def _run_gdb_script(self, script_path: str) -> tuple[int, str]:
        return run_gdb_script(self.gdb_bin, script_path, timeout=2)

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


_HALTED = RiscDebugStatus(
    is_halted=True,
    is_pc_watchpoint_hit=False,
    is_memory_watchpoint_hit=False,
    is_ebreak_hit=False,
    watchpoints_hit=[False] * 8,
)
_HALTED_ON_EBREAK = dataclasses.replace(_HALTED, is_ebreak_hit=True)
_HALTED_ON_PC_WATCHPOINT = dataclasses.replace(_HALTED, is_pc_watchpoint_hit=True, watchpoints_hit=[True] + [False] * 7)
_HALTED_ON_MEMORY_WATCHPOINT = dataclasses.replace(
    _HALTED, is_memory_watchpoint_hit=True, watchpoints_hit=[True] + [False] * 7
)


class ScriptedRiscDebug:
    def __init__(self, risc_location: RiscLocation):
        self.risc_location = risc_location
        self.pc = 0
        self.status = _HALTED
        self.script: list[tuple[int, RiscDebugStatus]] = []
        self.watchpoints = [
            RiscDebugWatchpointState(is_enabled=False, is_memory=False, is_read=False, is_write=False) for _ in range(8)
        ]
        self.watchpoint_addresses = [0] * 8
        self.cont_calls = 0
        self.step_calls = 0

    def is_in_reset(self) -> bool:
        return False

    def is_halted(self) -> bool:
        return self.status.is_halted

    def halt(self) -> None:
        self.status = dataclasses.replace(self.status, is_halted=True)

    def cont(self) -> None:
        self.cont_calls += 1
        self.pc, self.status = self.script.pop(0)

    def step(self) -> None:
        self.step_calls += 1
        self.pc, self.status = self.script.pop(0)

    def read_status(self) -> RiscDebugStatus:
        return dataclasses.replace(self.status, watchpoints_hit=list(self.status.watchpoints_hit))

    def read_gpr(self, register_index: int) -> int:
        return self.pc if register_index == 32 else 0

    def read_watchpoints_state(self) -> list[RiscDebugWatchpointState]:
        return [dataclasses.replace(watchpoint) for watchpoint in self.watchpoints]

    def read_watchpoint_address(self, watchpoint_index: int) -> int:
        return self.watchpoint_addresses[watchpoint_index]

    def set_watchpoint_on_pc_address(self, watchpoint_index: int, address: int) -> None:
        self.watchpoints[watchpoint_index] = RiscDebugWatchpointState(
            is_enabled=True, is_memory=False, is_read=False, is_write=False
        )
        self.watchpoint_addresses[watchpoint_index] = address

    def set_watchpoint_on_memory_write(self, watchpoint_index: int, address: int) -> None:
        self.watchpoints[watchpoint_index] = RiscDebugWatchpointState(
            is_enabled=True, is_memory=True, is_read=False, is_write=True
        )
        self.watchpoint_addresses[watchpoint_index] = address

    def disable_watchpoint(self, watchpoint_index: int) -> None:
        self.watchpoints[watchpoint_index] = RiscDebugWatchpointState(
            is_enabled=False, is_memory=False, is_read=False, is_write=False
        )


class TestGdbServerBreakpointPackets(unittest.TestCase):
    risc_debug: ScriptedRiscDebug
    gdb_server: GdbServer

    def setUp(self) -> None:
        location = Mock()
        risc_location = RiscLocation(location, None, "brisc")
        self.risc_debug = ScriptedRiscDebug(risc_location)
        location.noc_block.get_risc_debug.return_value = self.risc_debug
        location.device.get_block_type.return_value = "functional_workers"
        context = Mock()
        context.get_loaded_elfs.return_value = [(risc_location, "sample.debug.brisc.elf")]
        self.gdb_server = GdbServer(context, ServerSocket(), skip_detach=True, debug_only_with_elfs=True)

    def _send(self, payload: bytes) -> bytes:
        writer = GdbMessageWriter(ClientSocket())
        self.assertTrue(self.gdb_server.process_message(GdbMessageParser(payload), writer))
        return bytes(writer.data[1:])

    def _attach(self, script: list[tuple[int, RiscDebugStatus]]) -> None:
        self.risc_debug.script = list(script)
        self.assertEqual(self._send(b"vAttach;1"), b"T00;thread:p1.1;core:1;")

    def _pc_in_g_reply(self) -> bytes:
        return self._send(b"g")[-8:]

    def test_resume_after_reported_stop_runs_core(self) -> None:
        self._attach([(0xBC4, _HALTED_ON_EBREAK), (0xBC4, _HALTED_ON_EBREAK)])

        self.assertEqual(self._send(b"vCont;c"), b"T05swbreak:;thread:p1.1;core:1;")
        self.assertEqual(self._pc_in_g_reply(), b"C00B0000")
        self.assertEqual(self._send(b"vCont;c"), b"T05swbreak:;thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.cont_calls, 2)

    def test_breakpoint_stop_reports_breakpoint_address(self) -> None:
        self._attach([(0xC014, _HALTED_ON_PC_WATCHPOINT)])

        self.assertEqual(self._send(b"Z0,c010,4"), b"OK")
        self.assertEqual(self._send(b"vCont;c"), b"T05swbreak:;thread:p1.1;core:1;")
        self.assertEqual(self._pc_in_g_reply(), b"10C00000")

    def test_step_from_breakpoint_stop_does_not_run_core(self) -> None:
        self._attach([(0xC014, _HALTED_ON_PC_WATCHPOINT), (0xC014, _HALTED_ON_PC_WATCHPOINT)])

        self._send(b"Z0,c010,4")
        self._send(b"vCont;c")
        self._send(b"z0,c010,4")
        self.assertEqual(self._send(b"vCont;s:p1.1"), b"T05thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.step_calls, 0)
        self.assertEqual(self._pc_in_g_reply(), b"14C00000")
        self._send(b"Z0,c010,4")
        self.assertEqual(self._send(b"vCont;c:p1.-1"), b"T05swbreak:;thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.cont_calls, 2)
        self.assertEqual(self._pc_in_g_reply(), b"10C00000")

    def test_continue_from_breakpoint_stop(self) -> None:
        self._attach([(0xC014, _HALTED_ON_PC_WATCHPOINT), (0xBC4, _HALTED_ON_EBREAK)])

        self._send(b"Z0,c010,4")
        self._send(b"vCont;c")
        self.assertEqual(self._send(b"vCont;c"), b"T05swbreak:;thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.cont_calls, 2)
        self.assertEqual(self._pc_in_g_reply(), b"C00B0000")

    def test_hardware_step_is_not_a_breakpoint_stop(self) -> None:
        self.risc_debug.pc = 0xC014
        self.risc_debug.status = _HALTED_ON_PC_WATCHPOINT
        self.risc_debug.set_watchpoint_on_pc_address(0, 0xC010)
        self._attach([(0xC018, _HALTED_ON_PC_WATCHPOINT)])

        self.assertEqual(self._send(b"vCont;s:p1.1"), b"T05thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.step_calls, 1)
        self.assertEqual(self._pc_in_g_reply(), b"18C00000")

    def test_breakpoint_stop_at_hardware_pc_steps_core(self) -> None:
        self._attach([(0xC010, _HALTED_ON_PC_WATCHPOINT), (0xC014, _HALTED)])

        self._send(b"Z0,c010,4")
        self._send(b"vCont;c")
        self.assertEqual(self._pc_in_g_reply(), b"10C00000")
        self.assertEqual(self._send(b"vCont;s:p1.1"), b"T05thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.step_calls, 1)

    def test_attach_forgets_breakpoint_stop(self) -> None:
        self._attach([(0xC014, _HALTED_ON_PC_WATCHPOINT)])

        self._send(b"Z0,c010,4")
        self._send(b"vCont;c")
        self.assertEqual(self._pc_in_g_reply(), b"10C00000")
        self.assertEqual(self._send(b"D;1"), b"OK")
        self.assertEqual(self._send(b"vAttach;1"), b"T00;thread:p1.1;core:1;")
        self.assertEqual(self._pc_in_g_reply(), b"14C00000")

    def test_step_from_watchpoint_stop_does_not_run_core(self) -> None:
        self._attach([(0xC014, _HALTED_ON_MEMORY_WATCHPOINT), (0xBC4, _HALTED_ON_EBREAK)])

        self.assertEqual(self._send(b"Z2,d000,4"), b"OK")
        self.assertEqual(self._send(b"vCont;c"), b"T05watch:d000;thread:p1.1;core:1;")
        self.assertEqual(self._send(b"z2,d000,4"), b"OK")
        self.assertEqual(self._send(b"vCont;s:p1.1"), b"T05thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.step_calls, 0)
        self.assertEqual(self._send(b"Z2,d000,4"), b"OK")
        self.assertEqual(self._send(b"vCont;c:p1.-1"), b"T05swbreak:;thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.cont_calls, 2)

    def test_hardware_step_skips_removed_watchpoint(self) -> None:
        self.risc_debug.pc = 0xC014
        self.risc_debug.status = _HALTED_ON_MEMORY_WATCHPOINT
        self._attach([(0xC018, _HALTED_ON_MEMORY_WATCHPOINT)])

        self.assertEqual(self._send(b"vCont;s:p1.1"), b"T05thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.step_calls, 1)
        self.assertEqual(self._pc_in_g_reply(), b"18C00000")

    def test_continue_from_watchpoint_stop_steps_core(self) -> None:
        self._attach([(0xC014, _HALTED_ON_MEMORY_WATCHPOINT), (0xBC4, _HALTED_ON_EBREAK), (0xBC8, _HALTED)])

        self._send(b"Z2,d000,4")
        self._send(b"vCont;c")
        self._send(b"vCont;c")
        self.assertEqual(self._send(b"vCont;s:p1.1"), b"T05thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.step_calls, 1)

    def test_attach_forgets_watchpoint_stop(self) -> None:
        self._attach([(0xC014, _HALTED_ON_MEMORY_WATCHPOINT), (0xC018, _HALTED)])

        self._send(b"Z2,d000,4")
        self._send(b"vCont;c")
        self._send(b"D;1")
        self._send(b"vAttach;1")
        self.assertEqual(self._send(b"vCont;s:p1.1"), b"T05thread:p1.1;core:1;")
        self.assertEqual(self.risc_debug.step_calls, 1)

    def test_breakpoint_address_is_read_from_hit_slot(self) -> None:
        status = dataclasses.replace(_HALTED, is_pc_watchpoint_hit=True, watchpoints_hit=[False, True] + [False] * 6)
        self._attach([(0xC014, status)])

        self._send(b"Z2,d000,4")
        self._send(b"Z0,c010,4")
        self._send(b"vCont;c")
        self.assertEqual(self._pc_in_g_reply(), b"10C00000")


_SAMPLE_CORES = ["brisc", "trisc0", "trisc1", "trisc2"]


class TestGdbBreakpointsFromClient(unittest.TestCase):
    context: Context
    device: Device
    arch: str
    location: OnChipCoordinate
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
            raise unittest.SkipTest("GDB breakpoint tests run on Wormhole and Blackhole only")
        if is_simulation(cls.device):
            raise unittest.SkipTest("GDB breakpoint tests do not run on simulators")

        cls.location = get_core_location("FW0", cls.device)
        cls.gdb_bin = get_gdb_client_path()

    def _run_gdb_on_sample(self, core: str, commands: list[str]) -> tuple[int, str]:
        elf_path = os.path.join("build", "riscv-src", self.arch, f"sample.debug.{core}.elf")
        risc_debug = self.location.noc_block.get_risc_debug(core)
        self.addCleanup(risc_debug.set_reset_signal, True)
        run_elf(elf_path, self.location.to_str(), core, context=self.context)

        server_socket = ServerSocket(port=None)
        self.addCleanup(server_socket.close)
        server_socket.start()
        gdb_server = GdbServer(self.context, server_socket, skip_detach=True, debug_only_with_elfs=True)
        self.addCleanup(gdb_server.stop)
        gdb_server.start()
        time.sleep(0.2)

        pid = get_process_ids(gdb_server)[risc_debug.risc_location]
        port = server_socket.port
        assert port is not None

        script = [
            "set pagination off",
            "set confirm off",
            "set verbose off",
            f"target extended-remote localhost:{port}",
            f"attach {pid}",
            f"add-symbol-file {elf_path}",
            "set variable g_MAILBOX = 0x1234",
            "continue",
            "print/x g_MAILBOX",
            *commands,
            "quit",
        ]
        with tempfile.TemporaryDirectory(prefix="gdb_breakpoints_") as tmpdir:
            script_path = os.path.join(tmpdir, "commands.gdb")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write("\n".join(script) + "\n")
            return run_gdb_script(self.gdb_bin, script_path, timeout=60)

    def _assert_breakpoint_stops(self, rc: int, output: str, stops: int, mailbox_values: list[int]) -> None:
        lines = output.splitlines()
        self.assertEqual(rc, 0, f"GDB exited with non-zero code {rc}\nOutput:\n{output}")
        self.assertTrue(
            any(re.match(r"^\$\d+ = 0xffb12080$", line) for line in lines),
            f"Expected GDB to print g_MAILBOX as 0xffb12080 at the ebreak stop\nOutput:\n{output}",
        )
        self.assertEqual(
            sum(bool(re.search(r"Breakpoint 1(\.\d+)?, decrement_mailbox", line)) for line in lines),
            stops,
            f"Expected {stops} lines with 'Breakpoint 1[.<location>], decrement_mailbox'\nOutput:\n{output}",
        )
        self.assertEqual(
            [int(match.group(1)) for line in lines if (match := re.match(r"^\$\d+ = (\d+)$", line))],
            mailbox_values,
            f"Expected GDB to print g_MAILBOX as {mailbox_values}\nOutput:\n{output}",
        )
        _, breakpoint_set, after_breakpoint_set = output.partition("Breakpoint 1 at ")
        self.assertTrue(breakpoint_set, f"Expected GDB to set breakpoint 1\nOutput:\n{output}")
        self.assertNotIn(
            "Program received signal",
            after_breakpoint_set,
            f"Expected no signal stop after breakpoint 1 was set\nOutput:\n{output}",
        )

    @parameterized.expand(_SAMPLE_CORES)
    def test_breakpoint_stops_on_every_call(self, core: str) -> None:
        if self.arch == "blackhole" and core == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        rc, output = self._run_gdb_on_sample(
            core,
            [
                "break decrement_mailbox",
                "continue",
                "print g_MAILBOX",
                "continue",
                "print g_MAILBOX",
                "continue",
                "print g_MAILBOX",
            ],
        )

        self._assert_breakpoint_stops(rc, output, stops=3, mailbox_values=[3, 2, 1])

    @parameterized.expand(_SAMPLE_CORES)
    def test_conditional_breakpoint_evaluated_by_gdb(self, core: str) -> None:
        if self.arch == "blackhole" and core == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        rc, output = self._run_gdb_on_sample(
            core,
            [
                "set breakpoint condition-evaluation host",
                "break decrement_mailbox if g_MAILBOX == 1",
                "continue",
                "print g_MAILBOX",
            ],
        )

        self._assert_breakpoint_stops(rc, output, stops=1, mailbox_values=[1])
