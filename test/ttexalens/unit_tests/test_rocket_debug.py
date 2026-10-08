# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class, parameterized

from test.ttexalens.unit_tests.test_base import get_core_location, init_cached_test_context
from test.ttexalens.unit_tests.program_writer import RiscvProgramWriter
from ttexalens import Context, OnChipCoordinate, read_word_from_device, write_words_to_device
from ttexalens.device import Device
from ttexalens.hardware.rocket_core_debug import RocketCoreDebug

PROGRAM_BASE_ADDRESS = 0x0
BREAKPOINT_REGISTER = 31  # t6
L1_UNCACHED_BASE = 0x400000  # Core stores through this alias bypass its caches, so they are visible over NOC


class RocketProgramWriter(RiscvProgramWriter):
    """Program writer for rocket cores that reuses instruction encoding from RiscvProgramWriter."""

    def __init__(self, rocket_debug: RocketCoreDebug, start_address: int):
        self.rocket_debug = rocket_debug
        self.start_address = start_address
        self.instructions: list[int] = []

    def write_program(self):
        # Rocket cores don't execute code written to L1 over NOC, so program is written over debug module system bus
        data = b"".join(instruction.to_bytes(4, byteorder="little") for instruction in self.instructions)
        self.rocket_debug.write_memory_bytes(self.start_address, data)

    def append_ebreak(self):
        raise NotImplementedError("ebreak is not fully investigated on rocket cores, use append_breakpoint instead.")

    def append_breakpoint(self) -> int:
        """Append loop that simulates ebreak instruction and return address of the loop.

        Core spins in the loop until breakpoint register is cleared (see TestDebugging.continue_from_breakpoint).
        Unlike ebreak, core doesn't halt by itself, but once halted its PC is equal to returned address.
        """
        # C++:
        #   t6 = 1;
        #   while (t6 != 0);
        self.append_load_constant_to_register(BREAKPOINT_REGISTER, 1)
        breakpoint_address = self.current_address
        self.append_bne(0, BREAKPOINT_REGISTER, 0)
        return breakpoint_address


@parameterized_class(
    [
        {"core_desc": "FW0", "risc_name": "ROCKET0"},
        {"core_desc": "FW0", "risc_name": "ROCKET1"},
        {"core_desc": "FW0", "risc_name": "ROCKET2"},
        {"core_desc": "FW0", "risc_name": "ROCKET3"},
        {"core_desc": "FW0", "risc_name": "ROCKET4"},
        {"core_desc": "FW0", "risc_name": "ROCKET5"},
        {"core_desc": "FW0", "risc_name": "ROCKET6"},
        {"core_desc": "FW0", "risc_name": "ROCKET7"},
    ]
)
class TestDebugging(unittest.TestCase):
    core_desc: str
    risc_name: str
    context: Context
    device: Device
    location: OnChipCoordinate
    rocket_debug: RocketCoreDebug  # Debug interface of tested rocket core
    program_writer: RocketProgramWriter

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]
        if cls.device.is_wormhole() or cls.device.is_blackhole():
            raise unittest.SkipTest("Rocket cores are not available on Wormhole or Blackhole devices.")

    def setUp(self):
        self.location = get_core_location(self.core_desc, self.device)
        rocket_debug = self.device.get_block(self.location).get_risc_debug(self.risc_name)
        assert isinstance(rocket_debug, RocketCoreDebug), f"Expected RocketCoreDebug, got {type(rocket_debug)}"
        self.rocket_debug = rocket_debug
        self.program_writer = RocketProgramWriter(self.rocket_debug, PROGRAM_BASE_ADDRESS)

        self.rocket_debug.set_reset_signal(True)
        self.assertTrue(self.rocket_debug.is_in_reset())
        self.rocket_debug.set_code_start_address(PROGRAM_BASE_ADDRESS)

    def tearDown(self):
        if self.rocket_debug.is_halted():
            self.rocket_debug.cont()
        self.rocket_debug.set_reset_signal(True)
        self.assertTrue(self.rocket_debug.is_in_reset())

    def assertPcEquals(self, expected: int):
        """Assert PC register equals to expected offset from program base address."""
        self.assertEqual(
            self.rocket_debug.get_pc(),
            PROGRAM_BASE_ADDRESS + expected,
            f"PC should be {expected} + program base address ({PROGRAM_BASE_ADDRESS + expected}).",
        )

    def continue_from_breakpoint(self):
        """Release halted core from breakpoint loop and continue its execution."""
        self.assertTrue(self.rocket_debug.is_halted(), "Core should be halted in breakpoint loop.")
        self.rocket_debug.write_gpr(BREAKPOINT_REGISTER, 0)
        self.rocket_debug.cont()

    def test_core_reset(self):
        """Test asserting and deasserting core reset."""
        addr = 0x10000
        pattern = 0xDEADBEEF

        write_words_to_device(self.location, addr, 0)
        self.assertEqual(
            read_word_from_device(self.location, addr), 0, "Memory should be cleared before running program."
        )

        # C++:
        #   *(int*)(L1_UNCACHED_BASE + 0x10000) = pattern;
        #   while (true);
        self.program_writer.append_store_word_to_memory(L1_UNCACHED_BASE + addr, pattern, 10, 11)
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        self.rocket_debug.set_reset_signal(False)
        self.assertFalse(self.rocket_debug.is_in_reset(), "Core should be out of reset.")

        self.assertEqual(read_word_from_device(self.location, addr), pattern, "Core should run program after reset.")

    def test_halt_continue(self):
        """Test halting core and continuing its execution."""
        addr = 0x10000
        pattern1 = 0x12345678
        pattern2 = 0xDEADBEEF

        write_words_to_device(self.location, addr, 0)
        self.assertEqual(
            read_word_from_device(self.location, addr), 0, "Memory should be cleared before running program."
        )

        # C++:
        #   *(int*)(L1_UNCACHED_BASE + 0x10000) = 0x12345678;
        #   t6 = 1;
        #   while (t6 != 0);
        #   *(int*)(L1_UNCACHED_BASE + 0x10000) = 0xDEADBEEF;
        #   while (true);
        self.program_writer.append_store_word_to_memory(L1_UNCACHED_BASE + addr, pattern1, 10, 11)
        self.program_writer.append_breakpoint()
        self.program_writer.append_store_word_to_memory(L1_UNCACHED_BASE + addr, pattern2, 10, 11)
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        self.rocket_debug.set_reset_signal(False)
        self.assertFalse(self.rocket_debug.is_in_reset(), "Core should be out of reset.")

        self.rocket_debug.halt()
        self.assertTrue(self.rocket_debug.is_halted(), "Core should be halted.")

        self.rocket_debug.write_gpr(BREAKPOINT_REGISTER, 0)
        self.assertEqual(
            read_word_from_device(self.location, addr), pattern1, "Core should be halted in breakpoint loop."
        )

        self.rocket_debug.cont()
        self.assertFalse(self.rocket_debug.is_halted(), "Core should be running.")
        self.assertEqual(
            read_word_from_device(self.location, addr), pattern2, "Core should continue past breakpoint loop."
        )

    def test_code_start_address(self):
        """Test that core starts executing from code start address."""
        addr = 0x10000
        start_address = 0x100
        pattern = 0xDEADBEEF

        write_words_to_device(self.location, addr, 0)
        self.assertEqual(
            read_word_from_device(self.location, addr), 0, "Memory should be cleared before running program."
        )

        # C++ (at 0x100):
        #   *(int*)(L1_UNCACHED_BASE + 0x10000) = pattern;
        #   while (true);
        program_writer = RocketProgramWriter(self.rocket_debug, start_address)
        program_writer.append_store_word_to_memory(L1_UNCACHED_BASE + addr, pattern, 10, 11)
        program_writer.append_while_true()
        program_writer.write_program()

        self.rocket_debug.set_code_start_address(start_address)
        self.rocket_debug.set_reset_signal(False)
        self.assertFalse(self.rocket_debug.is_in_reset(), "Core should be out of reset.")

        self.assertEqual(
            read_word_from_device(self.location, addr),
            pattern,
            "Core should start executing from code start address.",
        )

    def test_read_pc(self):
        """Test reading PC while core is running and while core is halted."""
        num_of_nops = 3
        # C++:
        #   asm volatile ("nop");
        #   asm volatile ("nop");
        #   asm volatile ("nop");
        #   while (true);
        for _ in range(num_of_nops):
            self.program_writer.append_nop()
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        self.rocket_debug.set_reset_signal(False)
        self.assertFalse(self.rocket_debug.is_in_reset(), "Core should be out of reset.")

        self.rocket_debug.halt()
        self.assertTrue(self.rocket_debug.is_halted(), "Core should be halted.")
        self.assertPcEquals(4 * num_of_nops)

        self.rocket_debug.cont()
        self.assertFalse(self.rocket_debug.is_halted(), "Core should be running.")
        self.assertPcEquals(4 * num_of_nops)

    def test_step(self):
        """Test executing single and multiple steps."""
        addr = 0x10000
        pattern = 0xDEADBEEF

        write_words_to_device(self.location, addr, 0)
        self.assertEqual(
            read_word_from_device(self.location, addr), 0, "Memory should be cleared before running program."
        )

        # C++:
        #   t6 = 1;
        #   while (t6 != 0);
        #   *(int*)(L1_UNCACHED_BASE + 0x10000) = pattern;
        #   while (true);
        breakpoint_offset = self.program_writer.append_breakpoint() - PROGRAM_BASE_ADDRESS
        store_address = self.program_writer.current_address
        self.program_writer.append_store_word_to_memory(L1_UNCACHED_BASE + addr, pattern, 10, 11)
        num_of_store_instructions = (self.program_writer.current_address - store_address) // 4
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        self.rocket_debug.set_reset_signal(False)
        self.assertFalse(self.rocket_debug.is_in_reset(), "Core should be out of reset.")

        self.rocket_debug.halt()
        self.assertTrue(self.rocket_debug.is_halted(), "Core should be halted.")
        self.assertEqual(read_word_from_device(self.location, addr), 0, "Memory should still be cleared.")
        self.assertPcEquals(breakpoint_offset)

        self.rocket_debug.write_gpr(BREAKPOINT_REGISTER, 0)

        # Step over branch of breakpoint loop
        pc = breakpoint_offset + 4
        self.rocket_debug.step()
        self.assertPcEquals(pc)

        for _ in range(num_of_store_instructions):
            self.rocket_debug.step()
            pc += 4
            self.assertPcEquals(pc)
        self.assertEqual(read_word_from_device(self.location, addr), pattern, "Memory should contain pattern.")

        for _ in range(3):
            self.rocket_debug.step()
            self.assertPcEquals(pc)

    @parameterized.expand(
        [
            (0, None),
            (1, 0x0123456789ABCDEF),
            (5, 0xFEDCBA9876543210),
            (16, 1),
            (31, 0x87654321),
        ]
    )
    def test_read_write_gpr(self, register_index: int, value: int | None):
        """Test writing and reading general purpose registers."""
        # C++:
        #   while (true);
        self.program_writer.append_while_true()
        self.program_writer.write_program()

        self.rocket_debug.set_reset_signal(False)
        self.assertFalse(self.rocket_debug.is_in_reset(), "Core should be out of reset.")

        self.rocket_debug.halt()
        self.assertTrue(self.rocket_debug.is_halted(), "Core should be halted.")

        if value is None:
            self.assertEqual(self.rocket_debug.read_gpr(register_index), 0, "zero should always be 0.")
        else:
            self.rocket_debug.write_gpr(register_index, value)
            self.assertEqual(
                self.rocket_debug.read_gpr(register_index), value, f"Register x{register_index} should be 0x{value:x}."
            )

    @parameterized.expand(
        [
            (-1, None),
            (33, None),
            (-1, 0),
            (33, 0),
            (1, -1),
            (1, 2**64),
        ]
    )
    def test_invalid_read_write_gpr(self, register_index: int, value: int | None):
        """Test invalid inputs for general purpose register read and write."""
        with self.assertRaises(ValueError):
            if value is None:
                self.rocket_debug.read_gpr(register_index)
            else:
                self.rocket_debug.write_gpr(register_index, value)

    @parameterized.expand(
        [
            # Aligned
            (0, b"\x10\x11\x12\x13"),
            (0, b"\x20\x21\x22\x23\x24\x25\x26\x27"),
            (0, bytes(range(0x30, 0x50))),
            # Unaligned
            (0, b"\x50\x51\x52"),
            (1, b"\x60"),
            (2, b"\x70\x71"),
            (3, b"\x80\x81"),
            (1, b"\x90\x91\x92\x93\x94\x95\x96"),
            (3, bytes(range(0xA0, 0xAD))),
        ]
    )
    def test_read_write_memory(self, offset: int, data: bytes):
        """Test reading and writing memory through debug module system bus (SBA)."""
        addr = 0x10000

        self.rocket_debug.write_memory_bytes(addr + offset, data)

        buffer = bytearray(len(data))
        self.rocket_debug.read_memory_bytes(addr + offset, buffer)
        self.assertEqual(buffer, data, f"Should read back {len(data)} bytes written at offset {offset}.")
