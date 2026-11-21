# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import ast
import os
import unittest

from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore

HARDWARE_DIRECTORY = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ttexalens", "hardware")


class TestDebugBusSignalMapSource(unittest.TestCase):
    def test_signal_names_are_unique(self):
        """A signal name written twice in a map silently replaces the first signal."""
        for root, _, file_names in os.walk(HARDWARE_DIRECTORY):
            for file_name in file_names:
                if not file_name.endswith(".py"):
                    continue
                path = os.path.join(root, file_name)
                with open(path) as file:
                    tree = ast.parse(file.read(), path)
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Dict):
                        continue
                    keys = [
                        key.value for key in node.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)
                    ]
                    duplicates = sorted({key for key in keys if keys.count(key) > 1})
                    self.assertEqual(duplicates, [], f"{path}:{node.lineno}")


class TestBlackholeDebugBusSignals(unittest.TestCase):
    debug_bus: DebugBusSignalStore

    def setUp(self):
        device = init_cached_test_context().devices[0]
        if not device.is_blackhole():
            self.skipTest("Checks the Blackhole signal map.")
        location = OnChipCoordinate.create("0,0", device=device)
        debug_bus = location.noc_block.get_debug_bus()
        assert debug_bus is not None
        self.debug_bus = debug_bus

    def test_frontend_target_cfg_space(self):
        """Each thread's target_cfg_space is one signal made of two parts, read whole from its group."""
        for thread_id in range(3):
            signal_name = f"tensix_frontend_t{thread_id}_rq_head_rsrcs_target_cfg_space"
            self.assertTrue(self.debug_bus.is_combined_signal(signal_name), signal_name)
            self.assertIn(signal_name, self.debug_bus.get_signal_names_in_group(f"tensix_frontend_t{thread_id}"))
            self.assertEqual(self.debug_bus.signal_groups[f"tensix_frontend_t{thread_id}"][signal_name].mask, 0x7 << 95)

    def test_brisc_icache_req_fifo_signals(self):
        """The BRISC instruction cache request queue flags are read from the instruction cache controller group."""
        group = self.debug_bus.read_signal_group_unsafe("tensix_icache_ctrl")
        for signal_name in ["brisc_icache_req_fifo_empty", "brisc_icache_req_fifo_full"]:
            self.assertIn(signal_name, group.keys())
            self.assertEqual(self.debug_bus.get_signal_description(signal_name).sig_sel, 26)
            self.assertEqual(group[signal_name], self.debug_bus.read_signal(signal_name), signal_name)
