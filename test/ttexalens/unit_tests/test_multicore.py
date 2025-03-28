# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import unittest
import time
from test.ttexalens.unit_tests.test_base import init_default_test_context
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator


class TestMulticore(unittest.TestCase):
    """Test class for multi-core scenarios."""

    def setUp(self):
        self.context = init_default_test_context()
        self.brisc = RiscvCoreSimulator(self.context, "FW0", "BRISC")
        self.trisc0 = RiscvCoreSimulator(self.context, "FW0", "TRISC0")

    def tearDown(self):
        for core in [self.brisc, self.trisc0]:
            core.set_reset(True)
            core.set_branch_prediction(True)

    def _write_program_sequence(self, core, instructions):
        """Helper to write a sequence of instructions."""
        for i, instruction in enumerate(instructions):
            core.write_program(i * 4, instruction)

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
        # Constants
        MAILBOX_READ_ADDR = 0xFFEC1000
        MAILBOX_WRITE_ADDR = 0xFFEC0000

        # Configure cores
        self.trisc0.set_branch_prediction(False)

        # Write BRISC program (Reader)
        brisc_program = [
            0xFFEC12B7,  # lui t0, 0xffec1 - Load upper immediate: t0 = 0xFFEC1000 (mailbox read address)
            0x00000E37,  # lui t3, 0x0    - Load upper immediate: t3 = 0 (initialize counter)
            0x001E0E13,  # addi t3, t3, 1 - Add immediate: t3 += 1 (increment counter)
            0x0002A303,  # lw t1, 0(t0)   - Load word: t1 = MEM[t0 + 0] (read from mailbox)
            self.brisc.loader.get_jump_to_offset_instruction(-8),  # Jump back 8 bytes (2 instructions) to addi
        ]
        self._write_program_sequence(self.brisc, brisc_program)

        # Write TRISC0 program (Writer)
        trisc0_program = [
            0xFFEC02B7,  # lui t0, 0xffec0 - Load upper immediate: t0 = 0xFFEC0000 (mailbox write address)
            0x00000E37,  # lui t3, 0x0     - Load upper immediate: t3 = 0 (initialize counter)
            0x001E0E13,  # addi t3, t3, 1  - Add immediate: t3 += 1 (increment counter)
            0x014E1313,  # slli t1, t3, 20 - Shift left logical immediate: t1 = t3 << 20 (delay write frequency)
            0xFE031CE3,  # bne t1, x0, -8  - Branch if not equal: if(t1 != 0) goto t0_loop (branch to addi)
            0x01C2A023,  # sw t3, 0(t0)    - Store word: MEM[t0 + 0] = t3 (write counter to mailbox)
            0xFF1FF06F,  # jal x0, -16     - Jump and link: jump back to addi (loop)
        ]
        self._write_program_sequence(self.trisc0, trisc0_program)

        try:
            # Start execution
            self.brisc.set_reset(False)
            self.trisc0.set_reset(False)
            time.sleep(1)

            # Attempt to halt - should raise exception
            self.trisc0.halt()
            self.fail("Expected exception when halting locked core")

        except Exception as e:
            print(f"\nExpected exception occurred: {e}")
            self._verify_core_states()


if __name__ == "__main__":
    unittest.main()
