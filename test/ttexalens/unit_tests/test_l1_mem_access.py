# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from parameterized import parameterized_class, parameterized
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.program_writer import RiscvProgramWriter
from ttexalens.context import Context


@parameterized_class(
    [
        {"core_desc": "ETH0", "risc_name": "ERISC", "neo_id": None},
        {"core_desc": "ETH0", "risc_name": "ERISC0", "neo_id": None},
        {"core_desc": "ETH0", "risc_name": "ERISC1", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "BRISC", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "NCRISC", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "BRISC", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "TRISC0", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "TRISC1", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "TRISC2", "neo_id": None},
        {"core_desc": "FW1", "risc_name": "NCRISC", "neo_id": None},
        # {"core_desc": "DRAM0", "risc_name": "DRISC", "neo_id": None},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": 0},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": 0},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": 0},
        {"core_desc": "FW0", "risc_name": "TRISC3", "neo_id": 0},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": 1},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": 1},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": 1},
        {"core_desc": "FW0", "risc_name": "TRISC3", "neo_id": 1},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": 2},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": 2},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": 2},
        {"core_desc": "FW0", "risc_name": "TRISC3", "neo_id": 2},
        {"core_desc": "FW0", "risc_name": "TRISC0", "neo_id": 3},
        {"core_desc": "FW0", "risc_name": "TRISC1", "neo_id": 3},
        {"core_desc": "FW0", "risc_name": "TRISC2", "neo_id": 3},
        {"core_desc": "FW0", "risc_name": "TRISC3", "neo_id": 3},
    ]
)
class TestL1MemoryAccessFromRiscs(unittest.TestCase):
    risc_name: str  # Risc name
    neo_id: int | None  # NEO ID
    context: Context  # TTExaLens context
    core_desc: str  # Core description ETH0, FW0, FW1 - being parametrized
    core_sim: RiscvCoreSimulator  # RISC-V core simulator instance

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

    def setUp(self):
        try:
            self.core_sim = RiscvCoreSimulator(self.context, self.core_desc, self.risc_name, self.neo_id)
            self.program_writer = RiscvProgramWriter(self.core_sim)
        except ValueError as e:
            if self.risc_name.lower() in e.__str__().lower():
                self.skipTest(f"Core {self.risc_name} not available on this platform: {e}")
            elif "ETH core" in e.__str__() or "FW core" in e.__str__():
                self.skipTest(f"Core {self.core_desc}:{self.risc_name} not available on this platform: {e}")
            else:
                raise e
        except AssertionError as e:
            if self.neo_id is not None and "NEO ID" in e.__str__():
                self.skipTest(f"Test requires NEO ID, but is not supported on this platform: {e}")
            else:
                raise e

        # Stop risc with reset
        self.core_sim.set_reset(True)
        self.assertTrue(self.core_sim.is_in_reset())
        if self.device.is_wormhole() and self.risc_name.lower() == "ncrisc":
            self.core_sim.set_code_start_address(0x2000)

    def tearDown(self):
        # Stop risc with reset
        self.core_sim.set_reset(True)
        self.assertTrue(self.core_sim.is_in_reset())

    @parameterized.expand(
        [
            (0, 0x12345678),
            (4, 0x9ABCDEF0),
            (8, 0x0FEDCBA9),
            (12, 0x87654321),
        ]
    )
    def test_word_aligned_writes(self, offset: int, value: int):
        base_address = 0x20000
        address = base_address + offset
        pattern = 0xDEADBEEF

        self.core_sim.write_data_checked(base_address, [pattern] * 16)
        program_writer = RiscvProgramWriter(self.core_sim)
        program_writer.append_store_word_to_memory(address, value, 10, 11)
        program_writer.append_while_true()
        program_writer.write_program()

        self.core_sim.set_reset(False)
        read_data = self.core_sim.read_data(address)
        self.assertEqual(
            read_data, value, f"Data mismatch at address {address:x}: expected 0x{value:x}, got 0x{read_data:x}"
        )

    @parameterized.expand(
        [
            (1, 0x11223344),
            (2, 0x55667788),
            (3, 0x99AABBCC),
            (5, 0xDDEEFF00),
            (6, 0xA1B2C3D4),
            (7, 0xE5F6A7B8),
            (9, 0x10203040),
            (10, 0x50607080),
            (11, 0x90A0B0C0),
            (13, 0xD0E0F000),
            (14, 0x1A2B3C4D),
            (15, 0x12345967),
            (17, 0x89ABCDEF),
            (18, 0x0FEDCBA9),
            (19, 0x76543210),
        ]
    )
    def test_word_unaligned_writes(self, offset: int, value: int):
        base_address = 0x20000
        address = base_address + offset
        pattern = 0xDEADBEEF

        self.core_sim.write_data_checked(base_address, [pattern] * 16)
        program_writer = RiscvProgramWriter(self.core_sim)
        program_writer.append_store_word_to_memory(address, value, 10, 11)
        program_writer.append_while_true()
        program_writer.write_program()

        self.core_sim.set_reset(False)
        read_data = self.core_sim.read_data(address)

        # Unaligned writes should not match the value
        self.assertNotEqual(
            read_data, value, f"Data mismatch at address {address:x}: expected 0x{value:x}, got 0x{read_data:x}"
        )

        # Unaligned write behaves as if writing to the aligned word rounded down
        # Read two adjacent words to verify write
        aligned_address = address & ~0x3
        word0 = self.core_sim.read_data(aligned_address)
        word1 = self.core_sim.read_data(aligned_address + 4)

        # Reconstruct expected value based on alignment and architecture
        if self.device.is_wormhole():
            expected_value0 = value
            expected_value1 = pattern
        elif self.device.is_blackhole():
            high_mask = ((1 << ((4 - (address & 0x3)) * 8)) - 1) << ((address & 0x3) * 8)
            if address % 16 > 12:
                # If writing to the last word in the cache line, upper word is not updated
                low_mask = 0
            else:
                low_mask = ~high_mask & 0xFFFFFFFF
            expected_value0 = (pattern & ~(high_mask)) | (value & high_mask)
            expected_value1 = (pattern & ~(low_mask)) | (value & low_mask)
        else:
            raise NotImplementedError("Unhandled device type for unaligned word write verification")
        self.assertEqual(
            word0,
            expected_value0,
            f"Data mismatch at address {address:x}: expected 0x{expected_value0:x}, got 0x{word0:x}",
        )
        self.assertEqual(
            word1,
            expected_value1,
            f"Data mismatch at address {address:x}: expected 0x{expected_value1:x}, got 0x{word1:x}",
        )

    def test_half_word_aligned_writes(self):
        base_address = 0x20000
        value = 0xCC69
        pattern = 0xDEADBEEF

        self.core_sim.write_data_checked(base_address, [pattern] * 16)
        for offset in range(0, 20, 2):
            address = base_address + offset
            aligned_address = address & ~0x3

            self.core_sim.write_data_checked(aligned_address, pattern)

            program_writer = RiscvProgramWriter(self.core_sim)
            program_writer.append_store_half_word_to_memory(address, value, 10, 11)
            program_writer.append_while_true()
            program_writer.write_program()

            self.core_sim.set_reset(True)
            self.core_sim.set_reset(False)
            read_data = self.core_sim.read_data(aligned_address)
            expected_value = (pattern & ~(0xFFFF << ((address & 0x3) * 8))) | (value << ((address & 0x3) * 8))
            self.assertEqual(
                read_data,
                expected_value,
                f"Data mismatch at offset {offset}: expected 0x{expected_value:x}, got 0x{read_data:x}",
            )

    def test_half_word_unaligned_writes(self):
        base_address = 0x20000
        value = 0xCC69
        pattern = 0xDEADBEEF

        self.core_sim.write_data_checked(base_address, [pattern] * 16)
        for offset in range(1, 60, 2):
            address = base_address + offset
            aligned_address = address & ~0x3

            self.core_sim.write_data_checked(aligned_address, pattern)

            program_writer = RiscvProgramWriter(self.core_sim)
            program_writer.append_store_half_word_to_memory(address, value, 10, 11)
            program_writer.append_while_true()
            program_writer.write_program()

            self.core_sim.set_reset(True)
            self.core_sim.set_reset(False)

            test_value = value
            test_value_mask = 0xFFFF
            if self.device.is_wormhole():
                # It behaves as if addressing the previous aligned half-word
                address = address - 1
            elif self.device.is_blackhole():
                # Value gets flipped on Blackhole devices
                test_value = ((value & 0xFF00) >> 8) | ((value & 0x00FF) << 8)
                if offset % 16 == 15:
                    # Also, upper word is not updated
                    test_value = test_value & 0xFF
                    test_value_mask = 0xFF

            read_data0 = self.core_sim.read_data(aligned_address)
            read_data1 = self.core_sim.read_data(aligned_address + 4)
            read_data = read_data0 | (read_data1 << 32)
            expected_value = ((pattern | (pattern << 32)) & ~(test_value_mask << ((address & 0x3) * 8))) | (
                test_value << ((address & 0x3) * 8)
            )
            self.assertEqual(
                read_data,
                expected_value,
                f"Data mismatch at offset {offset}: expected 0x{expected_value:x}, got 0x{read_data:x}",
            )

    def test_byte_writes(self):
        base_address = 0x20000
        value = 0x42
        pattern = 0xDEADBEEF

        self.core_sim.write_data_checked(base_address, [pattern] * 16)
        for offset in range(20):
            address = base_address + offset
            aligned_address = address & ~0x3

            self.core_sim.write_data_checked(aligned_address, pattern)

            program_writer = RiscvProgramWriter(self.core_sim)
            program_writer.append_store_byte_to_memory(address, value, 10, 11)
            program_writer.append_while_true()
            program_writer.write_program()

            self.core_sim.set_reset(True)
            self.core_sim.set_reset(False)
            read_data = self.core_sim.read_data(aligned_address)

            expected_value = (pattern & ~(0xFF << ((address & 0x3) * 8))) | (value << ((address & 0x3) * 8))
            self.assertEqual(
                read_data,
                expected_value,
                f"Data mismatch at offset {offset}: expected 0x{expected_value:x}, got 0x{read_data:x}",
            )
