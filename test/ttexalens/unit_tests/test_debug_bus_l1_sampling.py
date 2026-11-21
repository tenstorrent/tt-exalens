# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest

from test.ttexalens.unit_tests.test_base import init_cached_test_context


class TestDebugBusL1SamplingLimit(unittest.TestCase):
    def test_samples_must_fit_in_block_l1(self):
        """Samples must fit in the block's L1, also in blocks whose L1 is smaller than 1 MiB."""
        device = init_cached_test_context().devices[0]
        if device.is_quasar():
            self.skipTest("This test does not work on quasar.")

        checked_block_types = set()
        for block_type in ["dram", "eth", "functional_workers"]:
            for block in device.get_blocks(block_type):
                debug_bus = block.get_debug_bus()
                l1 = getattr(block, "l1", None)
                if debug_bus is None or l1 is None:
                    continue
                limit = min(l1.size, debug_bus.L1_LOW_MEMORY_SIZE)
                # Validation only: no sample is taken
                debug_bus._validate_l1_parameters(limit - 32, samples=2)
                for samples, l1_address in [(1, limit), (2, limit - 16)]:
                    with self.assertRaises(ValueError, msg=f"{block_type}, 0x{l1_address:x}") as cm:
                        debug_bus._validate_l1_parameters(l1_address, samples=samples)
                    self.assertIn(f"exceeds L1 sampling limit 0x{limit:x}", str(cm.exception))
                checked_block_types.add(block_type)
                break
        self.assertIn("functional_workers", checked_block_types)
