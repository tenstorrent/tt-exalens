# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest

from ttexalens.util import HardwareError


class TestHardwareErrorCatchability(unittest.TestCase):
    """HardwareError must not be swallowed by broad 'except Exception' blocks."""

    def test_not_caught_by_except_exception(self):
        with self.assertRaises(HardwareError):
            try:
                raise HardwareError("device failure")
            except Exception:
                self.fail("HardwareError must not be caught by 'except Exception'")


if __name__ == "__main__":
    unittest.main()
