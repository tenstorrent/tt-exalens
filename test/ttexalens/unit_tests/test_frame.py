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


if __name__ == "__main__":
    unittest.main()
