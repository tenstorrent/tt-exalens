# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Host-only tests for the GDB server's watchpoint packets and stop replies. The core is a stub that keeps
# watchpoint slots in memory, so no device is needed.

import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from ttexalens.gdb.gdb_communication import GdbMessageParser, GdbMessageWriter
from ttexalens.gdb.gdb_data import GdbThreadId
from ttexalens.gdb.gdb_server import GdbServer
from ttexalens.hardware.risc_debug import RiscDebugStatus, RiscDebugWatchpointState


class _FakeClientSocket:
    packet_size = 2048

    def input_ready(self, timeout: float = 0):
        return False

    def read(self, packet_size=None):
        return b""  # Client disconnected

    def write(self, data):
        pass


class _FakeRiscDebug:
    """Keeps watchpoint slots the way the debug hardware reports them: an access slot is both read and write."""

    def __init__(self, slots: int = 4):
        self.states = [RiscDebugWatchpointState(False, False, False, False) for _ in range(slots)]
        self.addresses = [0] * slots
        self.halted = True
        self.hit: list[bool] = [False] * slots

    def _set(self, index: int, address: int, is_read: bool, is_write: bool):
        self.states[index] = RiscDebugWatchpointState(True, True, is_read, is_write)
        self.addresses[index] = address

    def set_watchpoint_on_memory_read(self, index, address):
        self._set(index, address, True, False)

    def set_watchpoint_on_memory_write(self, index, address):
        self._set(index, address, False, True)

    def set_watchpoint_on_memory_access(self, index, address):
        self._set(index, address, True, True)

    def disable_watchpoint(self, index):
        self.states[index] = RiscDebugWatchpointState(False, False, False, False)

    def read_watchpoints_state(self):
        return list(self.states)

    def read_watchpoint_address(self, index):
        return self.addresses[index]

    def is_halted(self):
        return self.halted

    def is_in_reset(self):
        return False

    def cont(self):
        # The core runs and stops on the watchpoint marked as hit
        self.halted = True

    def halt(self):
        self.halted = True

    def read_status(self):
        return RiscDebugStatus(
            is_halted=self.halted,
            is_pc_watchpoint_hit=False,
            is_memory_watchpoint_hit=any(self.hit),
            is_ebreak_hit=False,
            watchpoints_hit=list(self.hit),
        )


class TestGdbStopReplies(unittest.TestCase):
    def setUp(self):
        self.server = GdbServer(MagicMock(), MagicMock())
        self.risc_debug = _FakeRiscDebug()
        self.process = MagicMock()
        self.process.process_id = 1
        self.process.virtual_core_id = 1
        self.process.thread_id = GdbThreadId(1, 1)
        self.process.risc_debug = self.risc_debug
        self.server.current_process = self.process
        self.server.debugging_threads[1] = self.process.thread_id
        patcher = patch.object(GdbServer, "available_processes", new_callable=PropertyMock)
        patcher.start().return_value = {1: self.process}
        self.addCleanup(patcher.stop)

    def send(self, packet: bytes) -> bytes:
        writer = GdbMessageWriter(_FakeClientSocket())  # type: ignore
        self.assertTrue(self.server.process_message(GdbMessageParser(packet), writer))
        return bytes(writer.data[1:])  # drop the leading '$'

    def test_access_watchpoint_hit_is_reported_as_awatch(self):
        self.assertEqual(self.send(b"Z4,100,4"), b"OK")
        self.risc_debug.hit[0] = True
        self.assertEqual(self.send(b"vCont;c"), b"T05awatch:100;thread:p1.1;core:1;")

    def test_read_and_write_watchpoint_hits(self):
        self.assertEqual(self.send(b"Z3,100,4"), b"OK")
        self.risc_debug.hit[0] = True
        self.assertEqual(self.send(b"vCont;c"), b"T05rwatch:100;thread:p1.1;core:1;")
        self.server.vCont_pending_statuses.clear()
        self.assertEqual(self.send(b"z3,100,4"), b"OK")
        self.assertEqual(self.send(b"Z2,100,4"), b"OK")
        self.assertEqual(self.send(b"vCont;c"), b"T05watch:100;thread:p1.1;core:1;")

    def test_write_and_read_watchpoints_do_not_match_access_watchpoint(self):
        self.assertEqual(self.send(b"Z4,100,4"), b"OK")
        # Setting a write and a read watchpoint at the same address takes their own slots
        self.assertEqual(self.send(b"Z2,100,4"), b"OK")
        self.assertEqual(self.send(b"Z3,100,4"), b"OK")
        self.assertEqual([state.is_enabled for state in self.risc_debug.states], [True, True, True, False])
        # Removing them leaves the access watchpoint in place
        self.assertEqual(self.send(b"z2,100,4"), b"OK")
        self.assertEqual(self.send(b"z3,100,4"), b"OK")
        self.assertTrue(self.risc_debug.states[0].is_access)
        self.assertEqual([state.is_enabled for state in self.risc_debug.states], [True, False, False, False])
        self.assertEqual(self.send(b"z4,100,4"), b"OK")

    def test_new_session_starts_without_pending_stop_replies(self):
        self.server.vCont_pending_statuses.append("T05thread:p1.1;core:1;")
        self.server.process_client(_FakeClientSocket())  # type: ignore
        self.assertEqual(self.server.vCont_pending_statuses, [])


if __name__ == "__main__":
    unittest.main()
