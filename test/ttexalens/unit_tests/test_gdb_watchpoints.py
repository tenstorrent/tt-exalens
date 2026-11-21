# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Device tests for GDB watchpoints and stop replies. A small RSP client sends packets to GdbServer over its TCP
# socket, so each test controls the exact packet sequence, while the watchpoints and stops happen on a real core.

import socket
import time
import unittest

from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.program_writer import RiscvProgramWriter
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.gdb.gdb_client import get_process_ids
from ttexalens.gdb.gdb_communication import ServerSocket
from ttexalens.gdb.gdb_server import GdbServer
from ttexalens.hardware.risc_debug import RiscLocation


class RspClient:
    """Minimal GDB remote protocol client: sends one packet and returns the reply payload."""

    def __init__(self, port: int):
        self.socket = socket.create_connection(("localhost", port), timeout=10)
        self.buffer = b""

    def close(self):
        self.socket.close()

    def _read_byte(self) -> int:
        if not self.buffer:
            self.buffer = self.socket.recv(4096)
            if not self.buffer:
                raise ConnectionError("GDB server closed the connection")
        byte = self.buffer[0]
        self.buffer = self.buffer[1:]
        return byte

    def send(self, payload: str) -> str:
        data = payload.encode()
        self.socket.sendall(b"$" + data + b"#" + f"{sum(data) % 256:02x}".encode())
        ack = self._read_byte()
        if ack != ord("+"):
            raise ConnectionError(f"GDB server did not acknowledge {payload!r}: {chr(ack)!r}")
        while self._read_byte() != ord("$"):
            pass
        reply = bytearray()
        while (byte := self._read_byte()) != ord("#"):
            reply.append(byte)
        self._read_byte()
        self._read_byte()
        self.socket.sendall(b"+")
        return reply.decode()


class TestGdbWatchpoints(unittest.TestCase):
    context: Context
    device: Device

    READ_ADDRESS = 0x10000  # The program loads a word from here
    WRITE_ADDRESS = 0x11000  # and then stores a word here

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]
        if cls.device.is_quasar():
            raise unittest.SkipTest("Needs a Wormhole or Blackhole device")

    def setUp(self):
        self.core_sim = RiscvCoreSimulator(self.context, "FW0", "BRISC")
        if self.core_sim.risc_debug.baby_risc_info.max_watchpoints < 2:
            self.skipTest("Needs at least two watchpoints")
        write_noc_address = self.core_sim.risc_debug.baby_risc_info.l1.translate_to_noc_address(self.WRITE_ADDRESS)
        assert write_noc_address is not None
        self.write_noc_address: int = write_noc_address
        self.core_sim.write_data_checked(self.write_noc_address, 0)
        program_writer = RiscvProgramWriter(self.core_sim)
        # C++:
        #   asm volatile ("ebreak");
        #   int d = *(int*)READ_ADDRESS;
        #   *(int*)WRITE_ADDRESS = 0x87654000;
        #   while (true);
        program_writer.append_ebreak()
        program_writer.append_load_word_from_memory_to_register(12, self.READ_ADDRESS, 10)
        program_writer.append_store_word_to_memory(self.WRITE_ADDRESS, 0x87654000, 10, 11)
        program_writer.append_while_true()
        program_writer.write_program()
        self.core_sim.set_reset(False)
        self.assertTrue(self.core_sim.is_halted() and self.core_sim.is_ebreak_hit())
        # Watchpoint slots can only be changed while the core is halted
        for watchpoint in range(self.core_sim.risc_debug.baby_risc_info.max_watchpoints):
            self.core_sim.debug_hardware.disable_watchpoint(watchpoint)

        # Expose the core to the GDB server as a process
        risc_location = RiscLocation(self.core_sim.location, None, "brisc")
        self.previous_elf = self.context.loaded_elfs.get(risc_location)
        self.context.elf_loaded(risc_location, "generated_watchpoint_program")
        self.server_socket = ServerSocket()
        self.server_socket.start()
        self.gdb_server = GdbServer(self.context, self.server_socket, skip_detach=True, debug_only_with_elfs=True)
        self.gdb_server.start()
        self.pid = get_process_ids(self.gdb_server)[risc_location]
        self.risc_location = risc_location

    def tearDown(self):
        self.gdb_server.stop()
        if self.previous_elf is None:
            self.context.loaded_elfs.pop(self.risc_location, None)
        else:
            self.context.loaded_elfs[self.risc_location] = self.previous_elf
        for watchpoint in range(self.core_sim.risc_debug.baby_risc_info.max_watchpoints):
            self.core_sim.debug_hardware.disable_watchpoint(watchpoint)
        self.core_sim.set_reset(True)

    def connect(self) -> RspClient:
        assert self.server_socket.port is not None
        client = RspClient(self.server_socket.port)
        self.assertEqual(client.send("!"), "OK")
        self.assertTrue(client.send(f"vAttach;{self.pid:x}").startswith("T00"))
        return client

    def wait_disconnected(self):
        deadline = time.time() + 5
        while self.gdb_server.is_connected and time.time() < deadline:
            time.sleep(0.01)

    def test_access_watchpoint_stop_is_reported_as_awatch(self):
        client = self.connect()
        try:
            self.assertEqual(client.send(f"Z4,{self.READ_ADDRESS:x},4"), "OK")
            reply = client.send("vCont;c")
            self.assertTrue(self.core_sim.read_status().is_memory_watchpoint_hit, reply)
            self.assertTrue(reply.startswith(f"T05awatch:{self.READ_ADDRESS:x};thread:"), reply)
        finally:
            client.close()

    def test_removing_write_watchpoint_keeps_access_watchpoint(self):
        client = self.connect()
        try:
            self.assertEqual(client.send(f"Z4,{self.WRITE_ADDRESS:x},4"), "OK")
            self.assertEqual(client.send(f"Z2,{self.WRITE_ADDRESS:x},4"), "OK")
            self.assertEqual(client.send(f"z2,{self.WRITE_ADDRESS:x},4"), "OK")
            states = self.core_sim.risc_debug.read_watchpoints_state()
            access_slots = [
                i
                for i, state in enumerate(states)
                if state.is_enabled
                and state.is_access
                and self.core_sim.debug_hardware.read_watchpoint_address(i) == self.WRITE_ADDRESS
            ]
            self.assertEqual(len(access_slots), 1, f"Access watchpoint was removed by z2: {states}")
            self.assertEqual(client.send(f"z4,{self.WRITE_ADDRESS:x},4"), "OK")
        finally:
            client.close()

    def test_new_session_does_not_get_previous_session_stop(self):
        # First session stops on a watchpoint and disconnects
        client = self.connect()
        try:
            self.assertEqual(client.send(f"Z3,{self.READ_ADDRESS:x},4"), "OK")
            self.assertTrue(client.send("vCont;c").startswith(f"T05rwatch:{self.READ_ADDRESS:x};"))
            self.assertEqual(client.send(f"z3,{self.READ_ADDRESS:x},4"), "OK")
            self.assertEqual(client.send("D"), "OK")
        finally:
            client.close()
        self.wait_disconnected()

        # Second session: its first resume must run the core to the next stop, not return the earlier one
        client = self.connect()
        try:
            self.assertEqual(client.send(f"Z2,{self.WRITE_ADDRESS:x},4"), "OK")
            reply = client.send("vCont;c")
            self.assertTrue(reply.startswith(f"T05watch:{self.WRITE_ADDRESS:x};thread:"), reply)
            self.assertEqual(self.core_sim.read_data(self.write_noc_address), 0x87654000)
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
