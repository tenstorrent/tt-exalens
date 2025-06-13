# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from test.ttexalens.unit_tests.test_base import init_test_context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import write_words_to_device


class TestNOC(unittest.TestCase):
    def setUp(self):
        return

    def init_context(self, use_noc1: bool = False):
        self.context = init_test_context(use_noc1)
        self.device = self.context.devices[0]
        self.loc = OnChipCoordinate(1, 0, "logical", self.device, core_type="tensix")
        self.noc0_register_store = self.device.get_block(self.loc).get_register_store(0)
        self.noc1_register_store = self.device.get_block(self.loc).get_register_store(1)

    def test_noc0_context(self):
        self.init_context()
        # Read NOC0 and NOC1
        noc0_wr_req_before = self.noc0_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        noc1_wr_req_before = self.noc1_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        # Write different amounts through NOC0 and NOC1
        write_words_to_device(self.loc, 0x333, [1, 1, 1], noc_id=0)
        write_words_to_device(self.loc, 0x111, 3, noc_id=1)
        # Read again
        noc0_wr_req_after = self.noc0_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        noc1_wr_req_after = self.noc1_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")

        # NOC0 and NOC1 counters should've increased by at least 6 and 2, respectively
        self.assertGreaterEqual(noc0_wr_req_after, noc0_wr_req_before + 6)
        self.assertGreaterEqual(noc1_wr_req_after, noc1_wr_req_before + 2)

    def test_noc1_context(self):
        self.init_context(True)
        noc0_wr_req_before = self.noc0_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        noc1_wr_req_before = self.noc1_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        write_words_to_device(self.loc, 0x333, [1, 1, 1], noc_id=0)
        write_words_to_device(self.loc, 0x111, 3, noc_id=1)
        noc0_wr_req_after = self.noc0_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")
        noc1_wr_req_after = self.noc1_register_store.read_register("NIU_SLV_NONPOSTED_WR_REQ_RECEIVED")

        self.assertGreaterEqual(noc0_wr_req_after, noc0_wr_req_before + 6)
        self.assertGreaterEqual(noc1_wr_req_after, noc1_wr_req_before + 2)
