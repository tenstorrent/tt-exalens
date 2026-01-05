# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest

from test.ttexalens.unit_tests.test_base import init_default_test_context
from ttexalens import Context, OnChipCoordinate, Device, read_word_from_device, write_words_to_device


class TestRemoteCommunication(unittest.TestCase):
    context: Context  # TTExaLens context
    local_devices: Device  # Local (PCIE) devices
    remote_device_id: int | None
    tensix_core: "0,0"

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()

        # We need to reset the board until #691 is fixed
        cls.context.umd_api.warm_reset()
        cls.context = init_default_test_context()

        cls.local_device = cls.context.devices[0]
        assert cls.local_device._has_mmio, "Could not find local device"
        cls.remote_device_id = cls.context.devices[1]._id if len(cls.context.devices) > 1 else None
        cls.tensix_loc = "0,0"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.context.umd_api.warm_reset()
        cls.context = init_default_test_context()

    def test_remote_communication(self):
        data = 0x12345678
        address = 0x100

        if self.remote_device_id is None:
            self.skipTest("There are no remote devices to test")

        # Initial testing of writing to/reading from remote device
        write_words_to_device(self.tensix_loc, address, data, self.remote_device_id)
        ret = read_word_from_device(self.tensix_loc, address, self.remote_device_id)
        self.assertEqual(ret, data)
        # Find eth core used for remote communication and halt it
        eth_core = self.context.umd_api.get_remote_transfer_eth_core(self.remote_device_id)
        self.assertIsNotNone(eth_core, "Could not find ETH core used for remote communication")
        coord_str = f"e{eth_core[0]},{eth_core[1]}"
        loc = OnChipCoordinate.create(coord_str, self.local_device)
        noc_block = self.local_device.get_block(loc)
        risc_debug = noc_block.get_default_risc_debug()
        risc_debug.halt()

        self.assertTrue(risc_debug.is_halted(), "RISC debug is not halted")

        # Test writing to/reading from remote device again (after halting default eth core)
        write_words_to_device(self.tensix_loc, address, data, self.remote_device_id)
        ret = read_word_from_device(self.tensix_loc, address, self.remote_device_id)
        eth_core_after = self.context.umd_api.get_remote_transfer_eth_core(self.remote_device_id)
        self.assertNotEqual(eth_core, eth_core_after, "ETH core used for remote communication has not changed")
        self.assertEqual(ret, data)
