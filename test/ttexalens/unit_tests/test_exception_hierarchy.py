# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest

from ttexalens.util import TTException, TTFatalException, HardwareError, DebugSymbolError, CoordinateError
from ttexalens.elf.exceptions import (
    SymbolNotFoundError,
    TypeMismatchError,
    InvalidArrayAccessError,
    DataLossError,
    MemoryLayoutError,
)
from ttexalens.coordinate import CoordinateTranslationError, UnknownCoordinateSystemError
from ttexalens.memory_access import RestrictedMemoryAccessError, ReadOnlyMemoryError


class TestHardwareErrorHierarchy(unittest.TestCase):
    def test_restricted_memory_access_is_hardware_error(self):
        self.assertTrue(issubclass(RestrictedMemoryAccessError, HardwareError))

    def test_restricted_memory_access_is_ttexception(self):
        self.assertTrue(issubclass(RestrictedMemoryAccessError, TTException))

    def test_read_only_memory_is_hardware_error(self):
        self.assertTrue(issubclass(ReadOnlyMemoryError, HardwareError))

    def test_read_only_memory_is_ttexception(self):
        self.assertTrue(issubclass(ReadOnlyMemoryError, TTException))

    def test_hardware_error_is_ttexception(self):
        self.assertTrue(issubclass(HardwareError, TTException))

    def test_ttfatalexception_is_not_ttexception(self):
        self.assertFalse(issubclass(TTFatalException, TTException))

    def test_read_only_memory_error_message(self):
        err = ReadOnlyMemoryError("FixedMemoryAccess is read-only")
        self.assertIn("read-only", str(err))


class TestDebugSymbolErrorHierarchy(unittest.TestCase):
    def test_symbol_not_found_is_debug_symbol_error(self):
        self.assertTrue(issubclass(SymbolNotFoundError, DebugSymbolError))

    def test_symbol_not_found_is_ttexception(self):
        self.assertTrue(issubclass(SymbolNotFoundError, TTException))

    def test_type_mismatch_is_debug_symbol_error(self):
        self.assertTrue(issubclass(TypeMismatchError, DebugSymbolError))

    def test_invalid_array_access_is_debug_symbol_error(self):
        self.assertTrue(issubclass(InvalidArrayAccessError, DebugSymbolError))

    def test_data_loss_is_debug_symbol_error(self):
        self.assertTrue(issubclass(DataLossError, DebugSymbolError))

    def test_memory_layout_is_debug_symbol_error(self):
        self.assertTrue(issubclass(MemoryLayoutError, DebugSymbolError))

    def test_symbol_not_found_attributes(self):
        err = SymbolNotFoundError("MyStruct::field")
        self.assertEqual(err.member_path, "MyStruct::field")
        self.assertIn("MyStruct::field", str(err))

    def test_type_mismatch_attributes(self):
        err = TypeMismatchError("index", "uint32_t")
        self.assertEqual(err.operation, "index")
        self.assertEqual(err.actual_type, "uint32_t")
        self.assertIn("index", str(err))
        self.assertIn("uint32_t", str(err))

    def test_invalid_array_access_attributes(self):
        err = InvalidArrayAccessError(5, 4)
        self.assertEqual(err.index, 5)
        self.assertEqual(err.length, 4)
        self.assertIn("5", str(err))

    def test_invalid_array_access_unknown_length(self):
        err = InvalidArrayAccessError(0, None)
        self.assertIsNone(err.length)

    def test_data_loss_attributes(self):
        err = DataLossError(3.14, "float")
        self.assertEqual(err.value, 3.14)
        self.assertEqual(err.type_name, "float")
        self.assertIn("float", str(err))


class TestCoordinateErrorHierarchy(unittest.TestCase):
    def test_coordinate_translation_error_is_coordinate_error(self):
        self.assertTrue(issubclass(CoordinateTranslationError, CoordinateError))

    def test_coordinate_translation_error_is_ttexception(self):
        self.assertTrue(issubclass(CoordinateTranslationError, TTException))

    def test_unknown_coordinate_system_is_coordinate_error(self):
        self.assertTrue(issubclass(UnknownCoordinateSystemError, CoordinateError))

    def test_unknown_coordinate_system_is_ttexception(self):
        self.assertTrue(issubclass(UnknownCoordinateSystemError, TTException))

    def test_unknown_coordinate_system_attributes(self):
        err = UnknownCoordinateSystemError("noc99")
        self.assertEqual(err.coord_system, "noc99")
        self.assertIn("noc99", str(err))


class TestExceptionCatchability(unittest.TestCase):
    """Verify that all new exceptions are still caught by broad except clauses."""

    def test_symbol_not_found_caught_as_ttexception(self):
        with self.assertRaises(TTException):
            raise SymbolNotFoundError("x::y")

    def test_symbol_not_found_caught_as_exception(self):
        with self.assertRaises(Exception):
            raise SymbolNotFoundError("x::y")

    def test_hardware_error_caught_as_ttexception(self):
        with self.assertRaises(TTException):
            raise ReadOnlyMemoryError("test")

    def test_coordinate_error_caught_as_ttexception(self):
        with self.assertRaises(TTException):
            raise UnknownCoordinateSystemError("bad")

    def test_no_circular_import(self):
        # Simply importing all modules in combination verifies no import-time circular dependency
        from ttexalens.elf.exceptions import SymbolNotFoundError as SNF
        from ttexalens.elf.exceptions import MemoryLayoutError as MLErr
        from ttexalens.coordinate import UnknownCoordinateSystemError as UCSE
        self.assertTrue(issubclass(SNF, DebugSymbolError))
        self.assertTrue(issubclass(MLErr, DebugSymbolError))
        self.assertTrue(issubclass(UCSE, CoordinateError))


if __name__ == "__main__":
    unittest.main()
