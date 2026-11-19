# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import Mock
from parameterized import parameterized
from test.ttexalens.unit_tests.test_base import get_core_location, init_cached_test_context
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.exceptions import TTException
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.perf_counters import (
    list_perf_counters,
    read_perf_counter,
    read_perf_counters,
    reset_perf_counters,
    start_perf_counters,
    stop_perf_counters,
)

BLOCK_FUNCTIONS = {
    "read_perf_counters": read_perf_counters,
    "reset_perf_counters": reset_perf_counters,
    "start_perf_counters": start_perf_counters,
    "stop_perf_counters": stop_perf_counters,
}

NEO_ID_CASES = [(name, neo_id) for name in BLOCK_FUNCTIONS for neo_id in (0, 1)]


class TestPerfCountersNeoId(unittest.TestCase):
    def setUp(self):
        self.location = Mock()
        self.location.to_user_str.return_value = "0,0"
        self.perf = Mock()
        self.location.noc_block = NocBlock(  # type: ignore[abstract]
            self.location, "functional_workers", perf_counters=self.perf
        )

    def test_get_perf_counters_without_neo_id_returns_perf_counters(self):
        self.assertIs(self.location.noc_block.get_perf_counters(), self.perf)
        self.assertIs(self.location.noc_block.get_perf_counters(None), self.perf)

    @parameterized.expand([0, 1])
    def test_get_perf_counters_with_neo_id_returns_none(self, neo_id: int):
        self.assertIsNone(self.location.noc_block.get_perf_counters(neo_id))

    @parameterized.expand(NEO_ID_CASES)
    def test_block_function_with_neo_id_raises(self, function_name: str, neo_id: int):
        with self.assertRaises(TTException):
            BLOCK_FUNCTIONS[function_name](self.location, neo_id=neo_id)
        self.assertEqual(self.perf.mock_calls, [])

    @parameterized.expand([0, 1])
    def test_read_perf_counter_with_neo_id_raises(self, neo_id: int):
        with self.assertRaises(TTException):
            read_perf_counter(self.location, "FPU", 2, neo_id=neo_id)
        self.assertEqual(self.perf.mock_calls, [])

    @parameterized.expand([-1, 512, 600])
    def test_read_perf_counter_out_of_range_raises(self, counter: int):
        with self.assertRaises(TTException) as cm:
            read_perf_counter(self.location, "FPU", counter)
        self.assertIn("out of range", str(cm.exception))
        self.assertEqual(self.perf.mock_calls, [])

    def test_list_perf_counters_with_neo_id_returns_empty(self):
        self.assertEqual(list_perf_counters(self.location, neo_id=1), {})


class TestPerfCounters(unittest.TestCase):
    context: Context
    device: Device
    location: OnChipCoordinate
    neo_id: int | None

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

    def setUp(self):
        try:
            self.location = get_core_location("FW0", self.device)
        except ValueError as e:
            self.skipTest(f"Core FW0 not available on this platform: {e}")
        neo_ids = self.location.noc_block.neo_ids
        self.neo_id = neo_ids[0] if neo_ids else None
        if self.location.noc_block.get_perf_counters(self.neo_id) is None:
            self.skipTest(f"Perf counters not available on FW0[neo={self.neo_id}]")

    def test_read_unnamed_counter_id(self):
        fpu_ids = [cid for cid, _name in list_perf_counters(self.location, neo_id=self.neo_id).get("FPU", [])]
        if 2 in fpu_ids:
            self.skipTest("Counter 2 is named in the FPU block on this architecture")
        value = read_perf_counter(self.location, "FPU", 2, neo_id=self.neo_id)
        self.assertIsInstance(value, int)
        self.assertGreaterEqual(value, 0)
        self.assertLessEqual(value, 0xFFFFFFFF)

    def test_read_named_counter_by_id_and_by_name(self):
        cid, name = list_perf_counters(self.location, neo_id=self.neo_id)["FPU"][0]
        self.assertIsInstance(read_perf_counter(self.location, "FPU", cid, neo_id=self.neo_id), int)
        self.assertIsInstance(read_perf_counter(self.location, "FPU", name, neo_id=self.neo_id), int)

    def test_read_out_of_range_counter_id_raises(self):
        with self.assertRaises(TTException) as cm:
            read_perf_counter(self.location, "FPU", 600, neo_id=self.neo_id)
        self.assertIn("out of range", str(cm.exception))

    def test_read_unknown_counter_name_raises(self):
        with self.assertRaises(TTException):
            read_perf_counter(self.location, "FPU", "no_such_counter", neo_id=self.neo_id)

    @parameterized.expand(NEO_ID_CASES)
    def test_block_function_with_neo_id_raises_without_neos(self, function_name: str, neo_id: int):
        if self.neo_id is not None:
            self.skipTest("This architecture has NEOs")
        with self.assertRaises(TTException):
            BLOCK_FUNCTIONS[function_name](self.location, neo_id=neo_id)

    def test_block_functions_without_neo_id(self):
        if self.neo_id is not None:
            self.skipTest("This architecture has NEOs")
        self.assertIsNone(reset_perf_counters(self.location))
        self.assertIsNone(start_perf_counters(self.location))
        self.assertIsNone(stop_perf_counters(self.location))
        result = read_perf_counters(self.location)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        expected_keys = {
            (block_name, cid, name)
            for block_name, counters in list_perf_counters(self.location).items()
            for cid, name in counters
        }
        self.assertEqual(set(result.keys()), expected_keys)
        for value in result.values():
            self.assertIsInstance(value, tuple)
            self.assertEqual(len(value), 2)
            self.assertIsInstance(value[0], int)
            self.assertIsInstance(value[1], int)

    def test_read_perf_counters_with_neo_id(self):
        if self.neo_id is None:
            self.skipTest("This architecture has no NEOs")
        result = read_perf_counters(self.location, neo_id=self.neo_id)
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        with self.assertRaises(TTException):
            read_perf_counters(self.location, neo_id=99)


if __name__ == "__main__":
    unittest.main()
