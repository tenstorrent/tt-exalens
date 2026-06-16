# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import unittest
import time
from test.ttexalens.unit_tests.program_writer import RiscvProgramWriter
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from ttexalens.exceptions import RiscHaltError


class TestMulticore(unittest.TestCase):
    """Test class for multi-core scenarios."""

    def setUp(self):
        self.context = init_cached_test_context()
        self.brisc = RiscvCoreSimulator(self.context, "FW0", "BRISC")
        self.trisc0 = RiscvCoreSimulator(self.context, "FW0", "TRISC0")

    def tearDown(self):
        for core in [self.brisc, self.trisc0]:
            core.set_reset(True)
            core.set_branch_prediction(True)

    def _verify_core_states(self):
        """Helper to print and verify core states."""
        print("\nCore states:")
        self.brisc.get_pc_and_print()
        self.trisc0.get_pc_and_print()

    def test_mailbox_communication_lockup(self):
        """Test mailbox communication between BRISC and TRISC0 is locked up.

        BRISC Program (Reader):
        - Sets up mailbox read address in t0 (0xFFEC1000)
        - Initializes counter t3 to 0
        - Enters loop:
            - Increments counter
            - Reads from mailbox
            - Jumps back to increment

        TRISC0 Program (Writer):
        - Sets up mailbox write address in t0 (0xFFEC0000)
        - Initializes counter t3 to 0
        - Enters loop:
            - Increments counter
            - Shifts counter left by 20 to create delay
            - If shifted value is not 0, skips write
            - Writes counter to mailbox
            - Jumps back to increment
        """
        # Register numbers (RISC-V ABI): t0 = x5, t1 = x6, t3 = x28
        t0, t1, t3 = 5, 6, 28
        MAILBOX_READ_ADDRESS = 0xFFEC1000
        MAILBOX_WRITE_ADDRESS = 0xFFEC0000

        # Configure cores
        self.trisc0.set_branch_prediction(False)

        # Write BRISC program (Reader)
        brisc_writer = RiscvProgramWriter(self.brisc)
        brisc_writer.append_load_constant_to_register(t0, MAILBOX_READ_ADDRESS)  # t0 = mailbox read address
        brisc_writer.append_load_constant_to_register(t3, 0)  # t3 = 0 (initialize counter)
        brisc_loop = brisc_writer.current_address
        brisc_writer.append_addi(t3, t3, 1)  # t3 += 1 (increment counter)
        brisc_writer.append_lw(t1, t0, 0)  # t1 = MEM[t0 + 0] (read from mailbox)
        brisc_writer.append_loop(brisc_loop)  # jump back to the increment
        brisc_writer.write_program()

        # Write TRISC0 program (Writer)
        trisc0_writer = RiscvProgramWriter(self.trisc0)
        trisc0_writer.append_load_constant_to_register(t0, MAILBOX_WRITE_ADDRESS)  # t0 = mailbox write address
        trisc0_writer.append_load_constant_to_register(t3, 0)  # t3 = 0 (initialize counter)
        trisc0_loop = trisc0_writer.current_address
        trisc0_writer.append_addi(t3, t3, 1)  # t3 += 1 (increment counter)
        trisc0_writer.append_slli(t1, t3, 20)  # t1 = t3 << 20 (delay write frequency)
        trisc0_writer.append_bne(trisc0_loop - trisc0_writer.current_address, t1, 0)  # if(t1 != 0) goto increment
        trisc0_writer.append_sw(t3, t0, 0)  # MEM[t0 + 0] = t3 (write counter to mailbox)
        trisc0_writer.append_loop(trisc0_loop)  # jump back to the increment
        trisc0_writer.write_program()

        try:
            # Start execution
            self.brisc.set_reset(False)
            self.trisc0.set_reset(False)
            time.sleep(1)

            # Attempt to halt - should raise exception
            self.trisc0.halt()
            self.fail("Expected exception when halting locked core")

        except RiscHaltError as he:
            print(f"\nCore was locked up. {he}")
            self._verify_core_states()
        except Exception as e:
            print(f"\nExpected exception occurred: {e}")
            self._verify_core_states()


if __name__ == "__main__":
    unittest.main()
