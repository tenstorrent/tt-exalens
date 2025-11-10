# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest

from test.ttexalens.unit_tests.test_base import init_default_test_context
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.util import FirmwareVersion


class TestRemoteCommunication(unittest.TestCase):
    context: Context  # TTExaLens context
    local_device: Device  # Local (PCIE) device

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()
        cls.local_device = cls.context.devices[0]
        cls.remote_devices = [cls.context.devices[i] for i in range(1, len(cls.context.devices))]

    def test_remote_communication(self):

        if len(self.remote_devices) == 0:
            self.skipTest("There are no remote devices to test")

        fw_versions1: list[FirmwareVersion] = []
        for remote_device in self.remote_devices:
            fw_versions1.append(FirmwareVersion(self.context.server_ifc.get_firmware_version(remote_device._id)))
            eth_core = self.context.server_ifc.get_remote_transfer_eth_core(remote_device._id)
            coord_str = f"e{eth_core[0]},{eth_core[1]}"
            loc = OnChipCoordinate.create(coord_str, self.local_device)
            noc_block = self.local_device.get_block(loc)
            risc_debug = noc_block.get_risc_debug(noc_block.risc_names[0])
            risc_debug.halt()

        fw_versions2: list[FirmwareVersion] = []
        for remote_device in self.remote_devices:
            fw_versions2.append(FirmwareVersion(self.context.server_ifc.get_firmware_version(remote_device._id)))

        for i in range(len(self.remote_devices)):
            self.assertEqual(fw_versions1[i], fw_versions2[i])

    def tearDown(self) -> None:
        self.context.server_ifc.warm_reset()
        self.context = init_default_test_context()
