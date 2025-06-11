# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from test.ttexalens.unit_tests.test_base import init_test_context

class TestNOC1(unittest.TestCase):
    def setUp(self):
        self.context = init_test_context() # use noc1

    def test_noc1(self):
        # int write_words_to_device("0,0", 0x333, 111, noc_id=1)
        # probably use NIU_MST_RD_REQ_SENT/NIU_MST_WR_REQ_SENT
        # or NIU_MST_ATOMIC_RESP_RECEIVED/NIU_MST_WR_ACK_RECEIVED to see how many were actually done
        # there's also NIU_SLV_RD_RESP_SENT, NIU_SLV_WR_ACK_SENT etc

        # if I need to measure data flow then it's NIU_MST_RD_DATA_WORD_RECEIVED/NIU_SLV_NONPOSTED_WR_DATA_WORD_RECEIVED
