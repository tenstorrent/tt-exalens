# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from unittest.mock import Mock, patch
from parameterized import parameterized
import tt_umd
from ttexalens.context import Context
from ttexalens.device import Device, NocUnavailableError
from ttexalens.umd_device import TimeoutDeviceRegisterError
from ttexalens.coordinate import OnChipCoordinate


def create_timeout_error(chip_id=0, is_read=True):
    """Helper to create a properly initialized TimeoutDeviceRegisterError."""
    coord = tt_umd.CoreCoord(1, 1, tt_umd.CoreType.TENSIX, tt_umd.CoordSystem.NOC0)
    return TimeoutDeviceRegisterError(
        chip_id=chip_id, coord=coord, address=0x1000, size=4, is_read=is_read, duration=1.0
    )


class TestNocFailoverDisabled(unittest.TestCase):
    """Test NOC behavior when failover is disabled."""

    def setUp(self):
        # Create mock context with failover disabled
        self.mock_context = Mock(spec=Context)
        self.mock_context.use_noc1 = False
        self.mock_context.noc_failover = False
        self.mock_context.use_4B_mode = True
        self.mock_context.dma_read_threshold = 24
        self.mock_context.dma_write_threshold = 56

        # Create mock UMD device
        self.mock_umd_device = Mock()
        self.mock_umd_device.arch = Mock()
        self.mock_umd_device.unique_id = 0
        self.mock_umd_device.is_jtag_capable = False
        self.mock_umd_device.is_mmio_capable = True
        self.mock_umd_device.soc_descriptor = Mock()
        self.mock_umd_device.soc_descriptor.get_cores.return_value = []
        self.mock_umd_device.soc_descriptor.get_harvested_cores.return_value = []

        # Create test location
        self.test_location = Mock(spec=OnChipCoordinate)
        self.test_location._noc0_coord = (1, 1)

    def create_test_device(self):
        """Helper to create a test device with mocked dependencies."""
        with patch.object(Device, "_init_coordinate_systems"), patch.object(Device, "get_block"), patch.object(
            Device, "get_tensix_registers_description"
        ), patch.object(Device, "get_tensix_debug_bus_description"):
            device = Device(0, self.mock_umd_device, self.mock_context)  # type: ignore[abstract]
            return device

    def test_noc_read_timeout_no_failover(self):
        """Test that timeout raises immediately when failover is disabled."""
        device = self.create_test_device()
        initial_noc = device._active_noc
        self.mock_umd_device.noc_read.side_effect = create_timeout_error()

        with self.assertRaises(TimeoutDeviceRegisterError):
            device.noc_read(self.test_location, 0x1000, 4)

        # Should only try once (no failover)
        self.assertEqual(self.mock_umd_device.noc_read.call_count, 1)
        # Active NOC should still be initial NOC
        self.assertEqual(device._active_noc, initial_noc)
        # Nothing marked as hung
        self.assertFalse(device._noc_hung[0])
        self.assertFalse(device._noc_hung[1])

    def test_noc_write_timeout_no_failover(self):
        """Test that write timeout raises immediately when failover is disabled."""
        device = self.create_test_device()
        initial_noc = device._active_noc
        self.mock_umd_device.noc_write.side_effect = create_timeout_error(is_read=False)

        with self.assertRaises(TimeoutDeviceRegisterError):
            device.noc_write(self.test_location, 0x1000, b"\x00\x01\x02\x03")

        # Should only try once (no failover)
        self.assertEqual(self.mock_umd_device.noc_write.call_count, 1)
        # Active NOC should still be initial NOC
        self.assertEqual(device._active_noc, initial_noc)


class TestNocFailoverEnabled(unittest.TestCase):
    """Test NOC failover behavior when enabled, for both NOC0 and NOC1 as primary."""

    @parameterized.expand(
        [
            ("noc0", False, 0, 1, "NOC0", "NOC1"),
            ("noc1", True, 1, 0, "NOC1", "NOC0"),
        ]
    )
    def test_noc_read_success_no_failover_triggered(
        self, name, use_noc1, primary_noc, other_noc, primary_name, other_name
    ):
        """Test successful read doesn't trigger failover."""
        device = self._create_device(use_noc1)
        self.mock_umd_device.noc_read.return_value = b"\x00\x01\x02\x03"

        result = device.noc_read(self.test_location, 0x1000, 4)

        self.assertEqual(result, b"\x00\x01\x02\x03")
        self.assertEqual(self.mock_umd_device.noc_read.call_count, 1)
        self.assertEqual(device._active_noc, primary_noc)  # Still on primary
        self.assertFalse(device._noc_hung[0])
        self.assertFalse(device._noc_hung[1])

    @parameterized.expand(
        [
            ("noc0_to_noc1", False, 0, 1, "NOC0", "NOC1"),
            ("noc1_to_noc0", True, 1, 0, "NOC1", "NOC0"),
        ]
    )
    def test_noc_read_timeout_fails_over(self, name, use_noc1, primary_noc, other_noc, primary_name, other_name):
        """Test that timeout on primary NOC triggers failover to other NOC."""
        device = self._create_device(use_noc1)

        # First call (primary) times out, second call (other) succeeds
        self.mock_umd_device.noc_read.side_effect = [create_timeout_error(is_read=True), b"\x00\x01\x02\x03"]

        with patch("ttexalens.util.WARN") as mock_warn:
            result = device.noc_read(self.test_location, 0x1000, 4)

            # Verify warning was logged
            mock_warn.assert_called_once()
            self.assertIn(f"{primary_name} hung", str(mock_warn.call_args))
            self.assertIn(f"switching over to {other_name}", str(mock_warn.call_args))

        self.assertEqual(result, b"\x00\x01\x02\x03")
        self.assertEqual(self.mock_umd_device.noc_read.call_count, 2)

        # Verify state changes
        self.assertEqual(device._active_noc, other_noc)  # Switched to other NOC
        self.assertTrue(device._noc_hung[primary_noc])  # Primary marked as hung
        self.assertFalse(device._noc_hung[other_noc])  # Other still healthy
        self.assertTrue(device.noc_available)  # At least one NOC available

        # Verify the actual noc_id arguments used
        calls = self.mock_umd_device.noc_read.call_args_list
        self.assertEqual(calls[0][0][0], primary_noc)  # First call used primary
        self.assertEqual(calls[1][0][0], other_noc)  # Second call used other

    @parameterized.expand(
        [
            ("noc0", False),
            ("noc1", True),
        ]
    )
    def test_noc_read_both_nocs_timeout(self, name, use_noc1):
        """Test that both NOCs timing out raises NocUnavailableError."""
        device = self._create_device(use_noc1)

        # Both NOCs timeout
        self.mock_umd_device.noc_read.side_effect = [
            create_timeout_error(is_read=True),
            create_timeout_error(is_read=True),
        ]

        with self.assertRaises(NocUnavailableError) as ctx:
            device.noc_read(self.test_location, 0x1000, 4)

        self.assertIn("all NOCs are hung", str(ctx.exception))
        self.assertEqual(self.mock_umd_device.noc_read.call_count, 2)

        # Verify both NOCs marked as hung
        self.assertTrue(device._noc_hung[0])
        self.assertTrue(device._noc_hung[1])

    @parameterized.expand(
        [
            ("noc0", False, 0, 1),
            ("noc1", True, 1, 0),
        ]
    )
    def test_noc_write_timeout_fails_over(self, name, use_noc1, primary_noc, other_noc):
        """Test that write timeout triggers failover."""
        device = self._create_device(use_noc1)

        # First call (primary) times out, second call (other) succeeds
        self.mock_umd_device.noc_write.side_effect = [create_timeout_error(is_read=False), None]

        with patch("ttexalens.util.WARN") as mock_warn:
            device.noc_write(self.test_location, 0x1000, b"\x00\x01\x02\x03")

            # Verify warning was logged
            mock_warn.assert_called_once()

        self.assertEqual(self.mock_umd_device.noc_write.call_count, 2)
        self.assertEqual(device._active_noc, other_noc)
        self.assertTrue(device._noc_hung[primary_noc])

    @parameterized.expand(
        [
            ("noc0", False, 0),
            ("noc1", True, 1),
        ]
    )
    def test_explicit_noc_id_no_failover(self, name, use_noc1, expected_noc):
        """Test that explicit noc_id doesn't trigger failover."""
        device = self._create_device(use_noc1)
        self.mock_umd_device.noc_read.side_effect = create_timeout_error()

        with self.assertRaises(TimeoutDeviceRegisterError):
            device.noc_read(self.test_location, 0x1000, 4, noc_id=expected_noc)

        # Should only try once (no failover)
        self.assertEqual(self.mock_umd_device.noc_read.call_count, 1)
        # Active NOC should be unchanged
        self.assertEqual(device._active_noc, expected_noc)
        self.assertFalse(device._noc_hung[0])
        self.assertFalse(device._noc_hung[1])

    @parameterized.expand(
        [
            ("noc0", False, 0, 1),
            ("noc1", True, 1, 0),
        ]
    )
    def test_subsequent_reads_use_active_noc(self, name, use_noc1, primary_noc, other_noc):
        """Test that after failover, subsequent reads use the new active NOC."""
        device = self._create_device(use_noc1)

        # First call fails (primary), second succeeds (other)
        self.mock_umd_device.noc_read.side_effect = [
            create_timeout_error(is_read=True),
            b"\x00\x01\x02\x03",
        ]

        # First read triggers failover
        with patch("ttexalens.util.WARN"):
            device.noc_read(self.test_location, 0x1000, 4)

        # Reset side_effect for second read
        self.mock_umd_device.noc_read.side_effect = [b"\x04\x05\x06\x07"]

        # Second read should use other NOC directly
        result = device.noc_read(self.test_location, 0x2000, 4)

        self.assertEqual(result, b"\x04\x05\x06\x07")
        # Verify it's using the other NOC
        last_call_args = self.mock_umd_device.noc_read.call_args[0]
        self.assertEqual(last_call_args[0], other_noc)

    def setUp(self):
        """Set up mocks for each test."""
        # Create mock UMD device
        self.mock_umd_device = Mock()
        self.mock_umd_device.arch = Mock()
        self.mock_umd_device.unique_id = 0
        self.mock_umd_device.is_jtag_capable = False
        self.mock_umd_device.is_mmio_capable = True
        self.mock_umd_device.soc_descriptor = Mock()
        self.mock_umd_device.soc_descriptor.get_cores.return_value = []
        self.mock_umd_device.soc_descriptor.get_harvested_cores.return_value = []

        # Create test location
        self.test_location = Mock(spec=OnChipCoordinate)
        self.test_location._noc0_coord = (1, 1)

    def _create_device(self, use_noc1):
        """Helper to create a test device with specified NOC configuration."""
        mock_context = Mock(spec=Context)
        mock_context.use_noc1 = use_noc1
        mock_context.noc_failover = True
        mock_context.use_4B_mode = True
        mock_context.dma_read_threshold = 24
        mock_context.dma_write_threshold = 56

        with patch.object(Device, "_init_coordinate_systems"), patch.object(Device, "get_block"), patch.object(
            Device, "get_tensix_registers_description"
        ), patch.object(Device, "get_tensix_debug_bus_description"):
            return Device(0, self.mock_umd_device, mock_context)  # type: ignore[abstract]


if __name__ == "__main__":
    unittest.main()
