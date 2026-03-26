# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from parameterized import parameterized_class
from test.ttexalens.unit_tests.test_base import init_test_context
from ttexalens import OnChipCoordinate, write_words_to_device
from ttexalens.register_store import RegisterStore


@parameterized_class(
    [
        {"use_noc1": False, "noc_id": 0},
        {"use_noc1": False, "noc_id": 1},
        {"use_noc1": True, "noc_id": 0},
        {"use_noc1": True, "noc_id": 1},
    ]
)
class TestNOC(unittest.TestCase):
    use_noc1: bool
    noc_id: int

    def setUp(self):
        self.context = init_test_context(use_noc1=self.use_noc1)
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


@parameterized_class(
    [
        {"use_noc1": False},
        {"use_noc1": True},
    ]
)
class TestNOCLocations(unittest.TestCase):
    use_noc1: bool

    def setUp(self):
        self.context = init_test_context(use_noc1=self.use_noc1)

    @staticmethod
    def _read_noc_location(register_store: RegisterStore, register_name: str):
        data = register_store.read_register(register_name)
        x = data & 0x3F
        y = (data >> 6) & 0x3F
        return x, y

    def test_noc_locations(self):
        for device in self.context.devices.values():
            # TODO (944): Remove this check once UMD bug is fixed.
            if device.is_blackhole:
                continue
            for block_type in device.block_types:
                for block in device.get_blocks(block_type):
                    noc0_register_store = block.get_register_store(noc_id=0)
                    noc1_register_store = block.get_register_store(noc_id=1)
                    noc0_location = block.location.to("noc0")
                    noc0_id = TestNOCLocations._read_noc_location(noc0_register_store, "NOC_NODE_ID")
                    self.assertEqual(
                        noc0_location, noc0_id, f"NOC0 location mismatch for block at {block.location.to_user_str()}"
                    )
                    noc1_location = block.location.to("noc1")
                    noc1_id = TestNOCLocations._read_noc_location(noc1_register_store, "NOC_NODE_ID")
                    self.assertEqual(
                        noc1_location, noc1_id, f"NOC1 location mismatch for block at {block.location.to_user_str()}"
                    )
                    # Check that it doesn't raise exception when it reads logical IDs
                    noc0_logical_id = TestNOCLocations._read_noc_location(noc0_register_store, "NOC_ID_LOGICAL")
                    noc1_logical_id = TestNOCLocations._read_noc_location(noc1_register_store, "NOC_ID_LOGICAL")
