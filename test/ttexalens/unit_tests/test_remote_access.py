# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class


from test.ttexalens.unit_tests.test_base import init_default_test_context
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.util import FirmwareVersion


class TestRemoteAccess(unittest.TestCase):
    context: Context  # TTExaLens context
    local_device: Device  # Local (PCIE) device

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()
        cls.local_device = cls.context.devices[0]

    def test_remote_access(self):
        if len(self.context.devices) < 2:
            self.skipTest("There are no remote devices to test")

        remote_devices = [self.context.devices[i] for i in range(1, len(self.context.devices))]

        fw_versions1: list[FirmwareVersion] = []
        for remote_device in remote_devices:
            fw_versions1.append(FirmwareVersion(self.context.server_ifc.get_firmware_version(remote_device._id)))
            eth_core = self.context.server_ifc.get_currently_active_eth_core(remote_device._id)
            coord_str = f"e{eth_core[0]},{eth_core[1]}"
            loc = OnChipCoordinate.create(coord_str, self.local_device)
            noc_block = self.local_device.get_block(loc)
            risc_debug = noc_block.get_risc_debug(noc_block.risc_names[0])
            risc_debug.halt()

        self.context.server_ifc.warm_reset()
        self.context = init_default_test_context()

        fw_versions2: list[FirmwareVersion] = []
        for remote_device in remote_devices:
            fw_versions2.append(FirmwareVersion(self.context.server_ifc.get_firmware_version(remote_device._id)))

        for i in range(len(remote_devices)):
            self.assertEqual(fw_versions1[i], fw_versions2[i])
