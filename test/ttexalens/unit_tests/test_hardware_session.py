# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest.mock import Mock

from ttexalens.context import Context, DebugSession, HardwareSession
from ttexalens.device import Device
from ttexalens.umd_api import UmdApi
from ttexalens.server import FileAccessApi


class TestHardwareSession(unittest.TestCase):

    def test_from_api_with_mock_umd(self):
        """from_api constructs with a mock UmdApi without FileAccessApi or Context."""
        mock_umd = Mock(spec=UmdApi)
        mock_umd.devices = {}
        session = HardwareSession.from_api(mock_umd)
        assert session.umd_api is mock_umd
        assert session.use_noc1 is False
        assert session.use_4B_mode is True

    def test_use_noc1_before_devices_cached_does_not_trigger_discovery(self):
        """use_noc1 setter does NOT trigger device discovery before devices are cached."""
        mock_umd = Mock(spec=UmdApi)
        mock_umd.devices = {}
        session = HardwareSession.from_api(mock_umd)

        session.use_noc1 = True

        # "devices" must not be in __dict__ — device discovery was not triggered
        assert "devices" not in session.__dict__
        assert session.use_noc1 is True

    def test_use_noc1_propagates_to_cached_devices(self):
        """use_noc1 setter propagates switch_noc() to already-cached devices."""
        mock_umd = Mock(spec=UmdApi)
        mock_device_0 = Mock()
        mock_device_1 = Mock()

        session = HardwareSession.from_api(mock_umd)
        # Manually populate the devices cache (bypass lazy construction)
        session.__dict__["devices"] = {0: mock_device_0, 1: mock_device_1}

        session.use_noc1 = True

        mock_device_0.switch_noc.assert_called_once_with(1)
        mock_device_1.switch_noc.assert_called_once_with(1)

    def test_device_constructs_from_hardware_session_without_context(self):
        """Device can be constructed from HardwareSession without Context or FileAccessApi."""
        mock_umd = Mock(spec=UmdApi)
        mock_umd_device = Mock()
        mock_umd_device.soc_descriptor = Mock()
        mock_umd_device.soc_descriptor.get_cores.return_value = []
        mock_umd_device.soc_descriptor.get_harvested_cores.return_value = []
        session = HardwareSession.from_api(mock_umd, short_name="wormhole")

        device = Device(0, mock_umd_device, session)
        assert device._session is session

    def test_debug_session_constructs_from_hardware_and_file_api(self):
        """DebugSession constructs from HardwareSession + FileAccessApi."""
        mock_umd = Mock(spec=UmdApi)
        mock_file_api = Mock(spec=FileAccessApi)
        session = HardwareSession.from_api(mock_umd)
        debug = DebugSession(hardware=session, file_api=mock_file_api)
        assert debug.hardware is session
        assert debug.file_api is mock_file_api
        assert debug._loaded_elfs == {}

    def test_elf_loaded_stores_and_retrieves_path(self):
        """elf_loaded and get_risc_elf_path round-trip."""
        mock_umd = Mock(spec=UmdApi)
        mock_file_api = Mock(spec=FileAccessApi)
        debug = DebugSession(
            hardware=HardwareSession.from_api(mock_umd),
            file_api=mock_file_api
        )
        loc = Mock()  # RiscLocation mock
        debug.elf_loaded(loc, "/path/to/fw.elf")
        assert debug.get_risc_elf_path(loc) == "/path/to/fw.elf"

    def test_context_is_debug_session(self):
        """isinstance(Context(...), DebugSession) is True; not HardwareSession."""
        mock_umd = Mock(spec=UmdApi)
        mock_file_api = Mock(spec=FileAccessApi)
        ctx = Context(umd_api=mock_umd, file_api=mock_file_api)
        assert isinstance(ctx, DebugSession)
        assert not isinstance(ctx, HardwareSession)

    def test_debug_session_use_noc1_delegates_to_hardware(self):
        """DebugSession.use_noc1 setter only delegates — no double switch_noc()."""
        mock_umd = Mock(spec=UmdApi)
        mock_file_api = Mock(spec=FileAccessApi)
        session = HardwareSession.from_api(mock_umd)
        debug = DebugSession(hardware=session, file_api=mock_file_api)

        mock_device = Mock()
        session.__dict__["devices"] = {0: mock_device}

        debug.use_noc1 = True

        # switch_noc must be called exactly once — not twice (no double-propagation)
        mock_device.switch_noc.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
