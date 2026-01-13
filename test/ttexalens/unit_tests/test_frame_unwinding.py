# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for DWARF frame unwinding with real compiled RISC-V code.

These tests use 2 test programs to validate frame unwinding:

1. frame_unwinding_test.cc - Basic multi-frame unwinding
   - Tests: OFFSET rules (both debug and release)
   - 3-frame callstack: main → caller → callee
   - Compiler-generated CFI (only OFFSET rules)

2. frame_unwinding_test_cfi_directives.S - Explicit CFI directives
   - Tests: SAME_VALUE and REGISTER rules
   - Hand-written assembly with explicit .cfi_same_value and .cfi_register
   - Only way to test these rules (compilers don't generate them automatically)
"""

import unittest
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.context import Context


class TestFrameUnwindingBasic(unittest.TestCase):
    """Basic frame unwinding test with 3-frame callstack.

    Tests fundamental multi-frame unwinding with:
    - Debug builds (-O0): OFFSET rules (variables saved to stack)
    - Release builds (-O3): OFFSET rules (compiler always generates OFFSET for saved registers)
    """

    context: Context
    core_sim: RiscvCoreSimulator

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        risc_debug = cls.context.devices[0].get_blocks()[0].all_riscs[0]
        cls.core_sim = RiscvCoreSimulator(
            cls.context,
            risc_debug.risc_location.location.to_str(),
            risc_debug.risc_location.risc_name,
            risc_debug.risc_location.neo_id,
        )

    @classmethod
    def tearDownClass(cls):
        cls.core_sim.set_reset(True)

    def test_debug_build(self):
        """Test basic frame unwinding with debug build (-O0)."""
        # Load debug ELF
        self.core_sim.load_elf("frame_unwinding_test.debug")
        parsed_elf = self.core_sim.parse_elf("frame_unwinding_test.debug")

        # Take core out of reset - runs until ebreak
        self.core_sim.set_reset(False)

        # Verify halted at ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted at ebreak")
        self.assertTrue(self.core_sim.is_ebreak_hit(), "Should have hit ebreak")

        # Get callstack
        callstack = self.core_sim.risc_debug.get_callstack([parsed_elf])

        # Verify 3 frames: callee, caller, main
        self.assertGreaterEqual(len(callstack), 3, "Should have at least 3 frames")

        # Frame 0 (callee) - deepest frame
        frame0 = callstack[0]
        self.assertIsNotNone(frame0.function_name)
        self.assertIn("callee", frame0.function_name.lower())
        self.assertGreaterEqual(len(frame0.arguments), 3, "callee should have 3+ arguments")
        self.assertGreater(len(frame0.locals), 0, "callee should have local variables")

        # Frame 1 (caller)
        frame1 = callstack[1]
        self.assertIsNotNone(frame1.function_name)
        self.assertIn("caller", frame1.function_name.lower())

        print(f"\n[BASIC DEBUG] Successfully unwound {len(callstack)} frames:")
        for i, frame in enumerate(callstack[:3]):
            print(f"  Frame {i}: {frame.function_name} (args: {len(frame.arguments)}, locals: {len(frame.locals)})")

        # Reset for next test
        self.core_sim.set_reset(True)

    def test_release_build(self):
        """Test basic frame unwinding with release build (-O3).

        Note: Compiler still generates OFFSET rules even in release mode.
        """
        # Load release ELF
        self.core_sim.load_elf("frame_unwinding_test.release")
        parsed_elf = self.core_sim.parse_elf("frame_unwinding_test.release")

        # Take core out of reset - runs until ebreak
        self.core_sim.set_reset(False)

        # Verify halted at ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted at ebreak")

        # Get callstack
        callstack = self.core_sim.risc_debug.get_callstack([parsed_elf])

        # Verify we have frames (may be fewer due to inlining)
        self.assertGreaterEqual(len(callstack), 1, "Should have at least 1 frame")

        # Verify frame 0 is readable
        frame0 = callstack[0]
        self.assertIsNotNone(frame0.function_name)

        # Try to read arguments/locals (some may be optimized away)
        if len(frame0.arguments) > 0:
            print(f"\n[BASIC RELEASE] Frame 0 arguments: {len(frame0.arguments)}")
            for arg in frame0.arguments:
                print(f"  - {arg.name}: {arg.value}")

        if len(frame0.locals) > 0:
            print(f"[BASIC RELEASE] Frame 0 locals: {len(frame0.locals)}")
            for local in frame0.locals:
                print(f"  - {local.name}: {local.value}")

        print(f"\n[BASIC RELEASE] Successfully unwound {len(callstack)} frames:")
        for i, frame in enumerate(callstack):
            print(f"  Frame {i}: {frame.function_name} (args: {len(frame.arguments)}, locals: {len(frame.locals)})")

        # Reset for next test
        self.core_sim.set_reset(True)


class TestFrameUnwindingCFIDirectives(unittest.TestCase):
    """CFI directives test - validates SAME_VALUE and REGISTER rules.

    This test uses hand-written assembly with explicit CFI directives to test
    SAME_VALUE and REGISTER DWARF rules, which compilers don't generate automatically.
    """

    context: Context
    core_sim: RiscvCoreSimulator

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        risc_debug = cls.context.devices[0].get_blocks()[0].all_riscs[0]
        cls.core_sim = RiscvCoreSimulator(
            cls.context,
            risc_debug.risc_location.location.to_str(),
            risc_debug.risc_location.risc_name,
            risc_debug.risc_location.neo_id,
        )

    @classmethod
    def tearDownClass(cls):
        cls.core_sim.set_reset(True)

    def test_cfi_directives_present(self):
        """Test that CFI directives work correctly for SAME_VALUE and REGISTER rules.

        This test verifies full callstack unwinding through:
        - leaf_function (ebreak location)
        - middle_with_same_value (12 SAME_VALUE rules for s0-s11, plus VAL_OFFSET for gp)
        - function_with_register_rule (REGISTER rule: s1 value in s2, SAME_VALUE for s3-s11)
        - top_level_asm (sets up initial register values)
        - main (entry point)
        """
        # Load debug ELF
        self.core_sim.load_elf("frame_unwinding_test_cfi_asm.debug")
        parsed_elf = self.core_sim.parse_elf("frame_unwinding_test_cfi_asm.debug")

        # Take core out of reset - runs until ebreak
        self.core_sim.set_reset(False)

        # Verify halted at ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted at ebreak")

        # Get callstack - should successfully unwind through all 5 frames
        callstack = self.core_sim.risc_debug.get_callstack([parsed_elf])
        self.assertGreaterEqual(len(callstack), 5, "Should unwind through all 5 frames")

        # Verify expected function names
        function_names = [frame.function_name.lower() if frame.function_name else "" for frame in callstack[:5]]
        self.assertTrue(any("leaf" in name for name in function_names), "Should find leaf_function")
        self.assertTrue(any("middle" in name for name in function_names), "Should find middle_with_same_value")
        self.assertTrue(
            any("function_with_register" in name or "register_rule" in name for name in function_names),
            "Should find function_with_register_rule",
        )
        self.assertTrue(any("top_level" in name for name in function_names), "Should find top_level_asm")
        self.assertTrue(any("main" in name for name in function_names), "Should find main")

        # Verify frame order
        self.assertIn("leaf", callstack[0].function_name.lower())
        self.assertIn("middle", callstack[1].function_name.lower())

        # Verify all functions DID execute by checking register values
        # top_level_asm sets s0-s4 to known values
        s0 = self.core_sim.risc_debug.read_gpr(8)
        s3 = self.core_sim.risc_debug.read_gpr(19)
        s4 = self.core_sim.risc_debug.read_gpr(20)
        self.assertEqual(s0, 0x1000, "s0 should be 0x1000 (set by top_level_asm)")
        self.assertEqual(s3, 0x4000, "s3 should be 0x4000 (set by top_level_asm)")
        self.assertEqual(s4, 0x5000, "s4 should be 0x5000 (set by top_level_asm)")

        # function_with_register_rule modifies s1 to 0x9999, saves original (0x2000) in s2
        s1 = self.core_sim.risc_debug.read_gpr(9)
        s2 = self.core_sim.risc_debug.read_gpr(18)
        self.assertEqual(s1, 0x9999, "s1 should be 0x9999 (modified by function_with_register_rule)")
        self.assertEqual(s2, 0x2000, "s2 should be 0x2000 (original s1, saved by REGISTER rule)")

        print(f"\n[CFI DIRECTIVES] Successfully unwound through {len(callstack)} frames:")
        for i, frame in enumerate(callstack[:5]):
            name = frame.function_name if frame.function_name else "(none)"
            print(f"  Frame {i}: {name}")
        print(f"\n  Register verification:")
        print(f"    top_level_asm: s0=0x{s0:x}, s3=0x{s3:x}, s4=0x{s4:x}")
        print(f"    function_with_register_rule: s1=0x{s1:x} (modified), s2=0x{s2:x} (saved)")

        # Reset for next test
        self.core_sim.set_reset(True)


if __name__ == "__main__":
    unittest.main()
