# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import unittest
from unittest.mock import MagicMock, patch
from parameterized import parameterized

import tt_umd
from ttexalens import init_ttexalens, NocId
from ttexalens import umd_api
from ttexalens.umd_device import UmdDevice


class TestUmdDeviceNocSelection(unittest.TestCase):
    @parameterized.expand([(NocId.NOC0,), (NocId.NOC1,)])
    def test_init_keeps_selected_noc(self, noc_id: NocId):
        """After initialization the thread still uses the NOC the session was initialized with."""
        if os.getenv("TTEXALENS_TESTS_REMOTE") or os.getenv("TTEXALENS_SIMULATOR"):
            self.skipTest("Test needs a local device.")
        context = init_ttexalens(noc_id=noc_id, noc_failover=False)
        if context.devices[0].is_quasar():
            self.skipTest("Quasar uses NOC0 and the system NOC.")
        self.assertEqual(getattr(umd_api.TLS_FOR_NOC_ID, "noc_id", None), noc_id)


class TestUmdDeviceEthernetRetry(unittest.TestCase):
    """Only remote devices retry a failed read over another active Ethernet core."""

    def create_device(self, is_mmio_capable: bool) -> tuple[UmdDevice, MagicMock]:
        device = UmdDevice.__new__(UmdDevice)
        umd_device = MagicMock()
        device._UmdDevice__device = umd_device  # type: ignore[attr-defined]
        device._arch = tt_umd.ARCH.BLACKHOLE
        device._device_id = 0
        device._is_mmio_capable = is_mmio_capable
        device._simulation_backend_type = None
        device._active_eth_coords_on_mmio_chip = [] if is_mmio_capable else [MagicMock(), MagicMock()]
        return device, umd_device

    def run_with_failing_first_read(self, is_mmio_capable: bool, read, set_failure):
        device, umd_device = self.create_device(is_mmio_capable)
        set_failure(umd_device, [RuntimeError("first read failed"), 42])
        with patch.object(umd_api.UmdApi, "select_noc_id"), patch.object(
            UmdDevice, "_UmdDevice__configure_working_active_eth"
        ) as configure_eth:
            if is_mmio_capable:
                with self.assertRaisesRegex(RuntimeError, "first read failed"):
                    read(device)
                configure_eth.assert_not_called()
            else:
                self.assertEqual(read(device), 42)
                configure_eth.assert_called_once()

    @staticmethod
    def fail_telemetry(umd_device: MagicMock, results):
        reader = umd_device.get_firmware_telemetry_reader.return_value
        reader.is_entry_available.return_value = True
        reader.read_entry.side_effect = results

    @staticmethod
    def fail_firmware_version(umd_device: MagicMock, results):
        umd_device.get_firmware_info_provider.return_value.get_firmware_version.side_effect = results

    @parameterized.expand([(True,), (False,)])
    def test_read_firmware_telemetry_entry(self, is_mmio_capable: bool):
        self.run_with_failing_first_read(
            is_mmio_capable,
            lambda device: device.read_firmware_telemetry_entry(NocId.NOC0, 1),
            self.fail_telemetry,
        )

    @parameterized.expand([(True,), (False,)])
    def test_get_firmware_version(self, is_mmio_capable: bool):
        self.run_with_failing_first_read(
            is_mmio_capable,
            lambda device: device.get_firmware_version(NocId.NOC0),
            self.fail_firmware_version,
        )

    def test_unavailable_telemetry_tag_on_local_device(self):
        """On a local device, the real error of an unavailable telemetry tag is reported."""
        device, umd_device = self.create_device(is_mmio_capable=True)
        umd_device.get_firmware_telemetry_reader.return_value.is_entry_available.return_value = False
        with patch.object(umd_api.UmdApi, "select_noc_id"):
            with self.assertRaisesRegex(RuntimeError, "is not available"):
                device.read_firmware_telemetry_entry(NocId.NOC0, 1)
