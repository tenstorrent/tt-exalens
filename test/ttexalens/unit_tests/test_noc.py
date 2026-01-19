# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from parameterized import parameterized_class
from test.ttexalens.unit_tests.test_base import init_test_context
from ttexalens import OnChipCoordinate, write_words_to_device


@parameterized_class(
    [
        {"use_noc1": False, "noc_id": 0},
        {"use_noc1": False, "noc_id": 1},
        # Disabled until issue #455 is resolved
        # {"use_noc1": True, "noc_id": 0},
        # {"use_noc1": True, "noc_id": 1},
    ]
)
class TestNOC(unittest.TestCase):
    use_noc1: bool
    noc_id: int

    def setUp(self):
        self.context = init_test_context(self.use_noc1)
        self.device = self.context.devices[0]
        self.loc = OnChipCoordinate(1, 0, "logical", self.device, core_type="tensix")
        self.register_store = self.device.get_block(self.loc).get_register_store(self.noc_id)

    def test_noc_write(self):
        # Read the counter, write 3 values through the NOC, and expect the counter to go up by at least 6
        before = self.register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        for _ in range(3):
            write_words_to_device(self.loc, 0x333, 1, noc_id=self.noc_id)
        after = self.register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        self.assertGreaterEqual(after, before + 6)
