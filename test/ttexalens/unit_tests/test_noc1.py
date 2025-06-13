# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from test.ttexalens.unit_tests.test_base import init_test_context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import write_words_to_device


class TestNOC1(unittest.TestCase):
    def setUp(self):
        self.context = init_test_context()  # Use NOC1
        self.device = self.context.devices[0]
        self.loc = OnChipCoordinate(1, 0, "logical", self.device, core_type="tensix")
        self.noc0_register_store = self.device.get_block(self.loc).get_register_store(0)
        self.noc1_register_store = self.device.get_block(self.loc).get_register_store(1)

    def test_noc1(self):
        # Read NOC0 and NOC1
        noc0_wr_req_before = self.noc0_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        noc1_wr_req_before = self.noc1_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        # Write through NOC1
        write_words_to_device(self.loc, 0x333, [1, 1, 1, 3], noc_id=1)
        # Read again
        noc0_wr_req_after = self.noc0_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        noc1_wr_req_after = self.noc1_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")

        # NOC1 counter should've increased by at least 8
        self.assertGreaterEqual(noc1_wr_req_after, noc1_wr_req_before + 8)
        # The difference on NOC1 should be strictly greater than the difference on NOC0
        self.assertGreater(noc1_wr_req_after - noc1_wr_req_before, noc0_wr_req_after - noc0_wr_req_before)
