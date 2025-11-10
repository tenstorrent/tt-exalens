# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest

from test.ttexalens.unit_tests.test_base import init_default_test_context
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device


class TestRemoteCommunication(unittest.TestCase):
    context: Context  # TTExaLens context
    local_device: Device  # Local (PCIE) device
    remote_devices: list[Device]  # Remote devices
    tensix_core: OnChipCoordinate

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()
        cls.local_device = cls.context.devices[0]
        cls.remote_devices = [cls.context.devices[i] for i in range(1, len(cls.context.devices))]
        cls.tensix_core = OnChipCoordinate.create("0,0", cls.local_device)

    def test_remote_communication(self):

        data = 0x12345678
        address = 0x100

        if len(self.remote_devices) == 0:
            self.skipTest("There are no remote devices to test")

        for remote_device in self.remote_devices:
            write_words_to_device(self.tensix_core, address, data, remote_device._id)
            ret = read_word_from_device(self.tensix_core, address, remote_device._id)
            self.assertEqual(ret, data)
            eth_core = self.context.server_ifc.get_remote_transfer_eth_core(remote_device._id)
            coord_str = f"e{eth_core[0]},{eth_core[1]}"
            loc = OnChipCoordinate.create(coord_str, self.local_device)
            noc_block = self.local_device.get_block(loc)
            risc_debug = noc_block.get_default_risc_debug()
            risc_debug.halt()

        for remote_device in self.remote_devices:
            write_words_to_device(self.tensix_core, address, data, remote_device._id)
            ret = read_word_from_device(self.tensix_core, address, remote_device._id)
            self.assertEqual(ret, data)

    def tearDown(self) -> None:
        self.context.server_ifc.warm_reset()
        self.context = init_default_test_context()
