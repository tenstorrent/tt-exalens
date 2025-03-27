# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import unittest
import time
from test.ttexalens.unit_tests.test_base import init_default_test_context
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from ttexalens.debug_risc import RiscLoader, RiscDebug, RiscLoc, get_register_index, get_risc_id

class TestMulticore(unittest.TestCase):
    """Test class for multi-core scenarios."""

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()

    def setUp(self):
        # Initialize cores
        self.brisc = RiscvCoreSimulator(self.context, "FW0", "BRISC")
        self.trisc0 = RiscvCoreSimulator(self.context, "FW0", "TRISC0")
    def tearDown(self):
        # Reset both cores
        self.trisc0.set_reset(True)
        self.brisc.set_reset(True)

    def test_mailbox_communication_lockup(self):
        """Test mailbox communication between BRISC and TRISC0 is locked up for a specific scenario.

        BRISC program:
            li t0, 0xFFEC1000  # T0 -> B mailbox (when reading on RISCV B)
            li t3, 0           # T3 -> Counter
        b_loop:
            addi t3, t3, 1     # Counter increment
            lw t1, 0(t0)       # Mailbox pop
            j b_loop           # Loop back

        TRISC0 program:
            li t0, 0xFFEC0000  # T0 -> B mailbox (when writing on RISCV T0)
            li t3, 0           # T3 -> Counter
        t0_loop:
            addi t3, t3, 1     # Counter increment
            slli t1, t3, 20    # Shift left by 20 to control mailbox write frequency
            bne t1, x0, t0_loop
            sw t3, 0(t0)       # Mailbox push
            j t0_loop          # Loop back
        """
        self.trisc0.set_branch_prediction(False)
        # Write BRISC program
        self.brisc.write_program(0, 0xffec12b7)  # li t0, 0xFFEC1000
        self.brisc.write_program(4, 0x00000e37)  # li t3, 0
        self.brisc.write_program(8, 0x001e0e13)  # addi t3, t3, 1
        self.brisc.write_program(12, 0x00002303)  # lw t1, 0(t0)
        self.brisc.write_program(16, self.brisc.loader.get_jump_to_offset_instruction(-8)) # j b_loop (-8)

        # # Write TRISC0 program
        self.trisc0.write_program(0, 0xffec02b7)  # li t0, 0xFFEC0000
        self.trisc0.write_program(4, 0x00000e37)  # li t3, 0
        self.trisc0.write_program(8, 0x001e0e13)  # addi t3, t3, 1
        self.trisc0.write_program(12, 0x014e1313) # slli t1, t3, 20
        self.trisc0.write_program(16, 0xfe031ce3) # bne t1, x0, t0_loop
        self.trisc0.write_program(20, 0x01c2a023) # sw t3, 0(t0)
        self.trisc0.write_program(24, 0xff1ff06f) # j t0_loop

        # Take cores out of reset
        self.brisc.set_reset(False)
        self.trisc0.set_reset(False)

        # delay 1 second
        time.sleep(1)
        try:
            self.trisc0.halt()
        except Exception as e:
            # Expected exception when halt is called
            print(f"Exception: {e}")

            # Print final PC values
            print("\nFinal PC values after halt:")
            brisc_pc = self.brisc.get_pc_and_print()
            trisc0_pc = self.trisc0.get_pc_and_print()
            self.trisc0.set_reset(True)
            self.trisc0.set_branch_prediction(True)
            return

        self.trisc0.set_branch_prediction(False)

        self.assertFalse(True, "Exception not raised")

if __name__ == '__main__':
    unittest.main()