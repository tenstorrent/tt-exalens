# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest

from ttexalens.util import HardwareError
from ttexalens.exceptions import SimulatorException, TTException


class TestHardwareErrorCatchability(unittest.TestCase):
    """HardwareError must not be swallowed by broad 'except Exception' blocks."""

    def test_not_caught_by_except_exception(self):
        with self.assertRaises(HardwareError):
            try:
                raise HardwareError("device failure")
            except Exception:
                self.fail("HardwareError must not be caught by 'except Exception'")


class TestSimulatorExceptionCatchability(unittest.TestCase):
    """SimulatorException must be catchable as both Exception and TTException."""

    def test_is_tt_exception(self):
        exc = SimulatorException("not implemented")
        self.assertIsInstance(exc, TTException)

    def test_caught_by_except_exception(self):
        """pytest and normal code can catch SimulatorException with 'except Exception'."""
        caught = False
        try:
            raise SimulatorException("simulator: not implemented")
        except Exception:
            caught = True
        self.assertTrue(caught, "SimulatorException must be caught by 'except Exception'")

    def test_caught_by_tt_exception(self):
        caught = False
        try:
            raise SimulatorException("simulator: not implemented")
        except TTException:
            caught = True
        self.assertTrue(caught, "SimulatorException must be caught by 'except TTException'")

    def test_message_preserved(self):
        msg = "unimplemented: some_feature"
        exc = SimulatorException(msg)
        self.assertEqual(str(exc), msg)

    def test_chained_cause_preserved(self):
        original = RuntimeError("C++ exception: not implemented")
        try:
            raise SimulatorException("wrapped") from original
        except SimulatorException as exc:
            self.assertIs(exc.__cause__, original)


if __name__ == "__main__":
    unittest.main()
