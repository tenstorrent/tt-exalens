# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class


from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.context import Context


@parameterized_class(
    [
        {"device_id": 0},
        {"device_id": 1},
        {"device_id": 2},
        {"device_id": 3},
    ]
)
class TestDevice(unittest.TestCase):

    device_id: int
    context: Context  # TTExaLens context

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()

    def setUp(self):
        if self.device_id not in self.context.device_ids:
            self.skipTest(f"Device {self.device_id} not found!")

        self.device = self.context.devices[self.device_id]

    def test_get_active_idle_eth_block_locations(self):
        set_eth = set(self.device.get_block_locations(block_type="eth"))
        set_active_eth = set(self.device.active_eth_block_locations)
        set_idle_eth = set(self.device.idle_eth_block_locations)

        self.assertTrue(set_active_eth.isdisjoint(set_idle_eth), "Active and idle ETH block locations must not overlap")
        self.assertTrue(
            (set_active_eth | set_idle_eth) == set_eth, "All eth block locations must be either idle or active"
        )

    def test_get_active_idle_eth_blocks(self):
        set_eth = set(self.device.get_blocks(block_type="eth"))
        set_active_eth = set(self.device.active_eth_blocks)
        set_idle_eth = set(self.device.idle_eth_blocks)

        self.assertTrue(set_active_eth.isdisjoint(set_idle_eth), "Active and idle ETH blocks must not overlap")
        self.assertTrue((set_active_eth | set_idle_eth) == set_eth, "All eth blocks must be either idle or active")
