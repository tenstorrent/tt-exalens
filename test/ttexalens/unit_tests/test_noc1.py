# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from test.ttexalens.unit_tests.test_base import init_test_context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import write_words_to_device

class TestNOC1(unittest.TestCase):
    def setUp(self):
        self.context = init_test_context() # Use NOC1
        self.device = self.context.devices[0]
        self.loc = OnChipCoordinate(0, 0, "logical", self.device)
        self.register_store = self.device.get_block(self.loc).get_register_store(1) # NOC1 register store

    def test_noc1(self):
        # int write_words_to_device("0,0", 0x333, 111, noc_id=1)

        prev1 = self.register_store.read_register("NIU_MST_NONPOSTED_WR_REQ_SENT")
        prev2 = self.register_store.read_register("NIU_MST_POSTED_WR_REQ_SENT")
        prev3 = self.register_store.read_register("NIU_MST_WR_ACK_RECEIVED")
        prev4 = self.register_store.read_register("NIU_MST_RD_REQ_SENT")

        prev5 = self.register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        prev6 = self.register_store.read_register("NIU_SLV_POSTED_WR_REQ_RECEIVED")
        prev7 = self.register_store.read_register("NIU_SLV_WR_ACK_SENT")
        prev8 = self.register_store.read_register("NIU_SLV_RD_REQ_RECEIVED")

        write_words_to_device(self.loc, 0x333, 1, noc_id=1)
        self.assertLess(prev1, self.register_store.read_register("NIU_MST_NONPOSTED_WR_REQ_SENT"))
