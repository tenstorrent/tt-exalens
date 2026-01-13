# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for DWARF frame unwinding with real compiled RISC-V code.

These tests use 3 focused test programs to validate frame unwinding:

1. frame_unwinding_test.cc - Basic multi-frame unwinding
   - Tests: OFFSET (debug), SAME_VALUE (release)
   - 3-frame callstack: main → caller → callee

2. frame_unwinding_test_aliasing.cc - Register aliasing
   - Tests: REGISTER rules (release)
   - Focus on register-to-register value transfers

3. frame_unwinding_test_deep.cc - Deep callstack
   - Tests: Recursive frame state caching
   - 5-frame deep callstack stress test
"""

import unittest
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.context import Context


class TestFrameUnwindingBasic(unittest.TestCase):
    """Basic frame unwinding test with 3-frame callstack.

    Tests fundamental multi-frame unwinding with:
    - Debug builds (-O0): OFFSET rules (variables saved to stack)
    - Release builds (-O3): SAME_VALUE rules (variables kept in registers)
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

        This validates SAME_VALUE rules where variables stay in registers.
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


class TestFrameUnwindingAliasing(unittest.TestCase):
    """Register aliasing test - validates REGISTER rules in optimized builds.

    In release builds, the compiler may move register values around (REGISTER rule).
    This test focuses on scenarios that create register aliasing.
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

    def test_release_register_aliasing(self):
        """Test REGISTER rules with release build."""
        # Load release ELF
        self.core_sim.load_elf("frame_unwinding_test_aliasing.release")
        parsed_elf = self.core_sim.parse_elf("frame_unwinding_test_aliasing.release")

        # Take core out of reset - runs until ebreak
        self.core_sim.set_reset(False)

        # Verify halted at ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted at ebreak")

        # Get callstack
        callstack = self.core_sim.risc_debug.get_callstack([parsed_elf])

        # Verify we have frames
        self.assertGreaterEqual(len(callstack), 1, "Should have at least 1 frame")

        # Main test: verify we can read the callstack without errors
        # If REGISTER rules work, unwinding succeeds even with register aliasing
        frame0 = callstack[0]
        self.assertIsNotNone(frame0.function_name)

        print(f"\n[ALIASING] Successfully unwound {len(callstack)} frames with REGISTER rules:")
        for i, frame in enumerate(callstack):
            print(f"  Frame {i}: {frame.function_name} (args: {len(frame.arguments)}, locals: {len(frame.locals)})")

        if len(frame0.arguments) > 0:
            print(f"[ALIASING] Frame 0 arguments readable:")
            for arg in frame0.arguments:
                print(f"  - {arg.name}: {arg.value}")

        # Reset for next test
        self.core_sim.set_reset(True)


class TestFrameUnwindingDeep(unittest.TestCase):
    """Deep callstack test - validates recursive frame state caching.

    Tests unwinding through 5 frames to stress-test the frame state caching
    and recursive register resolution implementation.
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

    def test_debug_deep_stack(self):
        """Test deep callstack unwinding with debug build."""
        # Load debug ELF
        self.core_sim.load_elf("frame_unwinding_test_deep.debug")
        parsed_elf = self.core_sim.parse_elf("frame_unwinding_test_deep.debug")

        # Take core out of reset - runs until ebreak
        self.core_sim.set_reset(False)

        # Verify halted at ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted at ebreak")

        # Get callstack
        callstack = self.core_sim.risc_debug.get_callstack([parsed_elf])

        # Verify 5 frames: level1, level2, level3, level4, main
        self.assertGreaterEqual(len(callstack), 5, "Should have at least 5 frames")

        # Verify we can read all frames
        for i, frame in enumerate(callstack[:5]):
            self.assertIsNotNone(frame.function_name, f"Frame {i} should have function name")

        print(f"\n[DEEP DEBUG] Successfully unwound {len(callstack)} frames:")
        for i, frame in enumerate(callstack[:5]):
            print(f"  Frame {i}: {frame.function_name} (args: {len(frame.arguments)}, locals: {len(frame.locals)})")

        # Reset for next test
        self.core_sim.set_reset(True)

    def test_release_deep_stack(self):
        """Test deep callstack unwinding with release build.

        This validates that SAME_VALUE chains work correctly across many frames.
        """
        # Load release ELF
        self.core_sim.load_elf("frame_unwinding_test_deep.release")
        parsed_elf = self.core_sim.parse_elf("frame_unwinding_test_deep.release")

        # Take core out of reset - runs until ebreak
        self.core_sim.set_reset(False)

        # Verify halted at ebreak
        self.assertTrue(self.core_sim.is_halted(), "Core should be halted at ebreak")

        # Get callstack
        callstack = self.core_sim.risc_debug.get_callstack([parsed_elf])

        # Verify we have frames (may be fewer due to inlining)
        self.assertGreaterEqual(len(callstack), 1, "Should have at least 1 frame")

        # Main test: verify we can unwind without errors
        frame0 = callstack[0]
        self.assertIsNotNone(frame0.function_name)

        print(f"\n[DEEP RELEASE] Successfully unwound {len(callstack)} frames:")
        for i, frame in enumerate(callstack):
            print(f"  Frame {i}: {frame.function_name} (args: {len(frame.arguments)}, locals: {len(frame.locals)})")

        # Reset for next test
        self.core_sim.set_reset(True)


if __name__ == "__main__":
    unittest.main()
