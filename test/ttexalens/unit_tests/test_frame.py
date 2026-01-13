# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for ttexalens.elf.frame.FrameDescription.try_read_register

These tests verify the implementation of the try_read_register method which handles
different DWARF register rule types for reading saved register values from the stack.

To run these tests, first install the project dependencies from ttexalens/requirements.txt,
then run:
    python3 -m unittest test.ttexalens.unit_tests.test_frame

Or run all tests with:
    make test
"""

import unittest
from unittest.mock import Mock, patch


class MockRegisterRule:
    """Mock class for DWARF register rules."""

    def __init__(self, rule_type: str, arg: int | None = None):
        self.type = rule_type
        self.arg = arg


class TestFrameDescriptionTryReadRegister(unittest.TestCase):
    """Test suite for FrameDescription.try_read_register method.

    This test suite validates the implementation of try_read_register for all
    supported DWARF register rule types:
    - UNDEFINED: Register value is undefined
    - SAME_VALUE: Register value unchanged from previous frame
    - OFFSET: Register value stored at memory address CFA + offset
    - REGISTER: Register value copied to another register
    - VAL_OFFSET: Register value equals CFA + offset
    - EXPRESSION/VAL_EXPRESSION: Not yet implemented (returns None)
    """

    def setUp(self):
        """Set up test fixtures."""
        # Mock FDE (Frame Description Entry)
        self.mock_fde = Mock()
        self.mock_fde.get_decoded = Mock()

        # Mock CIE
        self.mock_cie = Mock()
        self.mock_fde.cie = self.mock_cie

        # Mock RiscDebug
        self.mock_risc_debug = Mock()
        self.mock_risc_debug.read_gpr = Mock()

        # Mock MemoryAccess
        self.mock_mem_access = Mock()

        # PC for testing
        self.test_pc = 0x1000

    def _create_frame_description(self, fde_entry: dict | None = None):
        """Helper to create FrameDescription with mocked dependencies."""
        # Import here to avoid issues during test discovery
        from ttexalens.elf.frame import FrameDescription
        from ttexalens.memory_access import RestrictedMemoryAccessError

        # Store the exception for use in tests
        self.RestrictedMemoryAccessError = RestrictedMemoryAccessError

        # Mock the decoded FDE table
        decoded = Mock()
        if fde_entry is None:
            fde_entry = {}
        decoded.table = [{"pc": 0x100, **fde_entry}]
        self.mock_fde.get_decoded.return_value = decoded

        # Create FrameDescription with mocked MemoryAccess
        with patch("ttexalens.elf.frame.MemoryAccess.create", return_value=self.mock_mem_access):
            frame_desc = FrameDescription(self.test_pc, self.mock_fde, self.mock_risc_debug)

        return frame_desc

    def test_try_read_register_undefined_rule(self):
        """Test UNDEFINED rule returns None."""
        fde_entry = {5: MockRegisterRule("UNDEFINED")}
        frame_desc = self._create_frame_description(fde_entry)

        result = frame_desc.try_read_register(5, 0x2000)
        self.assertIsNone(result, "UNDEFINED rule should return None")

    def test_try_read_register_same_value_rule(self):
        """Test SAME_VALUE rule reads from previous frame."""
        fde_entry = {7: MockRegisterRule("SAME_VALUE")}
        frame_desc = self._create_frame_description(fde_entry)

        # Create a mock previous frame
        mock_previous_frame = Mock()
        mock_previous_frame.read_register.return_value = 0x12345678

        result = frame_desc.try_read_register(7, 0x2000, mock_previous_frame)

        self.assertEqual(result, 0x12345678, "SAME_VALUE should read from previous frame")
        mock_previous_frame.read_register.assert_called_once_with(7)

    def test_try_read_register_same_value_rule_no_previous_frame(self):
        """Test SAME_VALUE rule returns None without previous frame."""
        fde_entry = {7: MockRegisterRule("SAME_VALUE")}
        frame_desc = self._create_frame_description(fde_entry)

        result = frame_desc.try_read_register(7, 0x2000, previous_frame=None)

        self.assertIsNone(result, "SAME_VALUE without previous frame should return None")

    def test_try_read_register_offset_rule(self):
        """Test OFFSET rule reads from memory at CFA + offset."""
        offset = -8
        fde_entry = {3: MockRegisterRule("OFFSET", offset)}
        frame_desc = self._create_frame_description(fde_entry)

        # Mock memory access to return a specific value
        self.mock_mem_access.read_word.return_value = 0xABCDEF01

        cfa = 0x2000
        result = frame_desc.try_read_register(3, cfa)

        self.assertEqual(result, 0xABCDEF01, "OFFSET should read from memory at CFA + offset")
        self.mock_mem_access.read_word.assert_called_once_with(cfa + offset)

    def test_try_read_register_offset_rule_no_cfa(self):
        """Test OFFSET rule returns None when CFA is None."""
        fde_entry = {3: MockRegisterRule("OFFSET", -8)}
        frame_desc = self._create_frame_description(fde_entry)

        result = frame_desc.try_read_register(3, None)

        self.assertIsNone(result, "OFFSET with None CFA should return None")
        self.mock_mem_access.read_word.assert_not_called()

    def test_try_read_register_offset_rule_restricted_memory(self):
        """Test OFFSET rule returns None on RestrictedMemoryAccessError."""
        fde_entry = {3: MockRegisterRule("OFFSET", -8)}
        frame_desc = self._create_frame_description(fde_entry)

        # Mock memory access to raise RestrictedMemoryAccessError
        # RestrictedMemoryAccessError requires access_start, access_end, and location parameters
        from unittest.mock import Mock

        mock_location = Mock()
        self.mock_mem_access.read_word.side_effect = self.RestrictedMemoryAccessError(0x1000, 0x1004, mock_location)

        result = frame_desc.try_read_register(3, 0x2000)

        self.assertIsNone(result, "OFFSET with restricted memory should return None")

    def test_try_read_register_register_rule(self):
        """Test REGISTER rule reads from another register in previous frame."""
        other_reg = 10
        fde_entry = {5: MockRegisterRule("REGISTER", other_reg)}
        frame_desc = self._create_frame_description(fde_entry)

        # Create a mock previous frame
        mock_previous_frame = Mock()
        mock_previous_frame.read_register.return_value = 0x99887766

        result = frame_desc.try_read_register(5, 0x2000, mock_previous_frame)

        self.assertEqual(result, 0x99887766, "REGISTER should read from previous frame")
        mock_previous_frame.read_register.assert_called_once_with(other_reg)

    def test_try_read_register_register_rule_no_previous_frame(self):
        """Test REGISTER rule returns None without previous frame."""
        other_reg = 10
        fde_entry = {5: MockRegisterRule("REGISTER", other_reg)}
        frame_desc = self._create_frame_description(fde_entry)

        result = frame_desc.try_read_register(5, 0x2000, previous_frame=None)

        self.assertIsNone(result, "REGISTER without previous frame should return None")

    def test_try_read_register_val_offset_rule(self):
        """Test VAL_OFFSET rule returns CFA + offset directly."""
        offset = 16
        fde_entry = {8: MockRegisterRule("VAL_OFFSET", offset)}
        frame_desc = self._create_frame_description(fde_entry)

        cfa = 0x3000
        result = frame_desc.try_read_register(8, cfa)

        self.assertEqual(result, cfa + offset, "VAL_OFFSET should return CFA + offset")

    def test_try_read_register_val_offset_rule_no_cfa(self):
        """Test VAL_OFFSET rule returns None when CFA is None."""
        fde_entry = {8: MockRegisterRule("VAL_OFFSET", 16)}
        frame_desc = self._create_frame_description(fde_entry)

        result = frame_desc.try_read_register(8, None)

        self.assertIsNone(result, "VAL_OFFSET with None CFA should return None")

    def test_try_read_register_expression_rule(self):
        """Test EXPRESSION rule returns None (not implemented)."""
        fde_entry = {9: MockRegisterRule("EXPRESSION")}
        frame_desc = self._create_frame_description(fde_entry)

        result = frame_desc.try_read_register(9, 0x2000)

        self.assertIsNone(result, "EXPRESSION should return None (not implemented)")

    def test_try_read_register_val_expression_rule(self):
        """Test VAL_EXPRESSION rule returns None (not implemented)."""
        fde_entry = {9: MockRegisterRule("VAL_EXPRESSION")}
        frame_desc = self._create_frame_description(fde_entry)

        result = frame_desc.try_read_register(9, 0x2000)

        self.assertIsNone(result, "VAL_EXPRESSION should return None (not implemented)")

    def test_try_read_register_no_rule(self):
        """Test returns None when no rule exists for the register."""
        fde_entry = {5: MockRegisterRule("OFFSET", -8)}
        frame_desc = self._create_frame_description(fde_entry)

        # Request a different register that has no rule
        result = frame_desc.try_read_register(10, 0x2000)

        self.assertIsNone(result, "Should return None when no rule exists")

    def test_try_read_register_no_fde_entry(self):
        """Test returns None when no FDE entry exists."""
        # Create frame description with no FDE entries
        from ttexalens.elf.frame import FrameDescription

        decoded = Mock()
        decoded.table = []
        self.mock_fde.get_decoded.return_value = decoded

        with patch("ttexalens.elf.frame.MemoryAccess.create", return_value=self.mock_mem_access):
            frame_desc = FrameDescription(self.test_pc, self.mock_fde, self.mock_risc_debug)

        result = frame_desc.try_read_register(5, 0x2000)

        self.assertIsNone(result, "Should return None when no FDE entry exists")

    def test_read_register_uses_try_read_register(self):
        """Test read_register delegates to try_read_register."""
        fde_entry = {3: MockRegisterRule("OFFSET", -8)}
        frame_desc = self._create_frame_description(fde_entry)

        # Mock memory access to return a specific value
        self.mock_mem_access.read_word.return_value = 0x11223344

        result = frame_desc.read_register(3, 0x2000)

        # Should return the value from try_read_register (via OFFSET rule)
        self.assertEqual(result, 0x11223344, "read_register should use try_read_register")

    def test_read_register_fallback_to_risc_debug(self):
        """Test read_register falls back to risc_debug when try_read_register returns None."""
        fde_entry: dict = {}  # No rules
        frame_desc = self._create_frame_description(fde_entry)

        # Mock risc_debug to return a fallback value
        self.mock_risc_debug.read_gpr.return_value = 0xFEEDBEEF

        result = frame_desc.read_register(10, 0x2000)

        # Should return the fallback value from risc_debug
        self.assertEqual(result, 0xFEEDBEEF, "read_register should fall back to risc_debug.read_gpr")
        self.mock_risc_debug.read_gpr.assert_called_once_with(10)


class TestMultiFrameUnwinding(unittest.TestCase):
    """Integration tests for frame unwinding across multiple frames.

    These tests verify that DWARF register rules work correctly across
    multiple stack frames, including recursive resolution of SAME_VALUE
    and REGISTER rules through the frame chain.
    """

    def setUp(self):
        """Set up test fixtures."""
        from ttexalens.elf.frame import FrameInspection

        self.FrameInspection = FrameInspection
        self.mock_risc_debug = Mock()
        self.mock_mem_access = Mock()

    def _create_mock_frame_description(self, register_rules: dict):
        """Create a mock FrameDescription with specified register rules."""
        mock_frame_desc = Mock()

        def mock_try_read_register(reg_index, cfa, previous_frame=None):
            if reg_index not in register_rules:
                return None

            rule = register_rules[reg_index]
            rule_type = rule["type"]

            if rule_type == "OFFSET":
                # Read from mock memory
                if cfa is None:
                    return None
                # In real code, would read from address = cfa + rule["offset"]
                # For tests, we just return the mocked value
                return rule.get("value", 0xDEADBEEF)

            elif rule_type == "SAME_VALUE":
                if previous_frame is not None:
                    return previous_frame.read_register(reg_index)
                return None

            elif rule_type == "REGISTER":
                other_reg = rule["other_reg"]
                if previous_frame is not None:
                    return previous_frame.read_register(other_reg)
                return None

            elif rule_type == "VAL_OFFSET":
                if cfa is None:
                    return None
                return cfa + rule["offset"]

            elif rule_type == "UNDEFINED":
                return None

            return None

        mock_frame_desc.try_read_register = Mock(side_effect=mock_try_read_register)
        return mock_frame_desc

    def test_mixed_rules_complex_unwinding(self):
        """Test complex unwinding with mix of rule types."""
        # Frame 3: R5=SAME_VALUE, R6=REGISTER(R7)
        # Frame 2: R5=REGISTER(R8), R7=OFFSET
        # Frame 1: R8=OFFSET
        # Frame 0: top frame

        # Frame 0 (top)
        frame0 = self.FrameInspection(
            self.mock_risc_debug, loaded_offset=0, frame_description=None, cfa=None, previous_frame=None
        )

        # Frame 1 - R8 has OFFSET
        frame1_desc = self._create_mock_frame_description({8: {"type": "OFFSET", "offset": -24, "value": 0x11111111}})
        frame1 = self.FrameInspection(
            self.mock_risc_debug, loaded_offset=0, frame_description=frame1_desc, cfa=0x2000, previous_frame=frame0
        )

        # Frame 2 - R5=REGISTER(R8), R7=OFFSET
        frame2_desc = self._create_mock_frame_description(
            {5: {"type": "REGISTER", "other_reg": 8}, 7: {"type": "OFFSET", "offset": -32, "value": 0x22222222}}
        )
        frame2 = self.FrameInspection(
            self.mock_risc_debug, loaded_offset=0, frame_description=frame2_desc, cfa=0x3000, previous_frame=frame1
        )

        # Frame 3 - R5=SAME_VALUE, R6=REGISTER(R7)
        frame3_desc = self._create_mock_frame_description(
            {5: {"type": "SAME_VALUE"}, 6: {"type": "REGISTER", "other_reg": 7}}
        )
        frame3 = self.FrameInspection(
            self.mock_risc_debug, loaded_offset=0, frame_description=frame3_desc, cfa=0x4000, previous_frame=frame2
        )

        # Read R5 from Frame 3: SAME_VALUE → Frame 2: REGISTER(R8) → Frame 1: OFFSET → 0x11111111
        result_r5 = frame3.read_register(5)
        self.assertEqual(result_r5, 0x11111111, "R5 should resolve through complex chain")

        # Read R6 from Frame 3: REGISTER(R7) → Frame 2: OFFSET → 0x22222222
        result_r6 = frame3.read_register(6)
        self.assertEqual(result_r6, 0x22222222, "R6 should resolve to R7 in Frame 2")

    def test_register_rule_to_undefined_register(self):
        """Test REGISTER rule pointing to register with no value."""
        # Frame 1: R5 has REGISTER(R10)
        # Frame 0: R10 has UNDEFINED (no rule, returns None)

        # Frame 0 (top) - no rule for R10, will return None
        frame0_desc = self._create_mock_frame_description({10: {"type": "UNDEFINED"}})
        frame0 = self.FrameInspection(
            self.mock_risc_debug, loaded_offset=0, frame_description=frame0_desc, cfa=None, previous_frame=None
        )

        # Frame 1 - R5 has REGISTER(R10)
        frame1_desc = self._create_mock_frame_description({5: {"type": "REGISTER", "other_reg": 10}})
        frame1 = self.FrameInspection(
            self.mock_risc_debug, loaded_offset=0, frame_description=frame1_desc, cfa=0x2000, previous_frame=frame0
        )

        # Read R5 from Frame 1 - should return None (R10 is undefined)
        result = frame1.read_register(5)

        self.assertIsNone(result, "REGISTER to UNDEFINED should return None")

    def test_deeply_nested_same_value_chain(self):
        """Test many frames all with SAME_VALUE (stress test recursion)."""
        # Create 10 frames, all with SAME_VALUE for R5
        # Final top frame has R5 = 0xDEADC0DE

        self.mock_risc_debug.read_gpr.return_value = 0xDEADC0DE

        # Build frame chain from bottom up
        frames = []

        # Frame 0 (top)
        frames.append(
            self.FrameInspection(
                self.mock_risc_debug, loaded_offset=0, frame_description=None, cfa=None, previous_frame=None
            )
        )

        # Frames 1-9 (all with SAME_VALUE)
        for i in range(1, 10):
            frame_desc = self._create_mock_frame_description({5: {"type": "SAME_VALUE"}})
            frames.append(
                self.FrameInspection(
                    self.mock_risc_debug,
                    loaded_offset=0,
                    frame_description=frame_desc,
                    cfa=0x1000 + (i * 0x1000),
                    previous_frame=frames[i - 1],
                )
            )

        # Read R5 from deepest frame (Frame 9)
        result = frames[9].read_register(5)

        self.assertEqual(result, 0xDEADC0DE, "Deep SAME_VALUE chain should resolve to top frame")
        self.mock_risc_debug.read_gpr.assert_called_once_with(5)


if __name__ == "__main__":
    unittest.main()
