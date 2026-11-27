# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import threading
import unittest

from parameterized import parameterized

from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.program_writer import RiscvProgramWriter
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens import Context
from ttexalens.gdb.gdb_communication import ClientSocket, GdbMessageParser, GdbMessageWriter, ServerSocket
from ttexalens.gdb.gdb_server import GdbServer


class SilentClientSocket(ClientSocket):
    def read(self, packet_size=None):
        return b""


def send_packet(server: GdbServer, packet: bytes) -> bytes:
    writer = GdbMessageWriter(SilentClientSocket())
    server.process_message(GdbMessageParser(packet), writer)
    return bytes(writer.data)


class TestGdbServerWatchpoints(unittest.TestCase):
    context: Context
    core_sim: RiscvCoreSimulator
    server: GdbServer

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        if cls.context.devices[0].is_quasar():
            raise unittest.SkipTest("GDB server watchpoint tests do not run on Quasar.")

    def setUp(self):
        self.core_sim = RiscvCoreSimulator(self.context, "FW0", "BRISC")
        program_writer = RiscvProgramWriter(self.core_sim)
        program_writer.append_ebreak()
        program_writer.append_store_word_to_memory(0x10000, 0x45678000, 10, 11)
        program_writer.append_load_word_from_memory_to_register(12, 0x11000, 10)
        program_writer.append_store_word_to_memory(0x12000, 0x87654000, 10, 11)
        program_writer.append_while_true()
        program_writer.write_program()
        self.core_sim.set_reset(False)
        self.disable_watchpoints()
        self.server = GdbServer(self.context, ServerSocket())
        self.new_session()

    def tearDown(self):
        self.disable_watchpoints()
        self.core_sim.set_reset(True)

    def disable_watchpoints(self) -> None:
        for i in range(self.core_sim.risc_debug.baby_risc_info.max_watchpoints):
            self.core_sim.risc_debug.disable_watchpoint(i)

    def new_session(self) -> None:
        self.server.process_client(SilentClientSocket())
        risc_location = self.core_sim.risc_debug.risc_location
        pid = next(
            process.process_id
            for process in self.server.available_processes.values()
            if process.risc_debug.risc_location == risc_location
        )
        send_packet(self.server, f"vAttach;{pid:x}".encode())

    def resume(self) -> bytes:
        timer = threading.Timer(10, self.server.stop_event.set)
        timer.start()
        try:
            return send_packet(self.server, b"vCont;c").split(b";")[0]
        finally:
            timer.cancel()

    def test_gdb_watchpoint_stop_replies(self):
        send_packet(self.server, b"Z2,10000,4")
        send_packet(self.server, b"Z3,11000,4")
        send_packet(self.server, b"Z4,12000,4")
        self.assertEqual(self.resume(), b"$T05watch:10000")
        self.new_session()
        self.assertEqual(self.resume(), b"$T05rwatch:11000")
        self.new_session()
        self.assertEqual(self.resume(), b"$T05awatch:12000")

    @parameterized.expand(
        [
            ("access_after_z2", [b"Z4,10000,4", b"Z2,10000,4", b"z2,10000,4"], b"$T05awatch:10000"),
            ("access_after_z3", [b"Z4,11000,4", b"Z3,11000,4", b"z3,11000,4"], b"$T05awatch:11000"),
            ("write_after_z4", [b"Z4,10000,4", b"Z2,10000,4", b"z4,10000,4"], b"$T05watch:10000"),
        ]
    )
    def test_gdb_watchpoint_survives_removal_at_same_address(self, _name, packets, expected):
        for packet in packets:
            self.assertEqual(send_packet(self.server, packet), b"$OK")
        self.assertEqual(self.resume(), expected)
