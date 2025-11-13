# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from parameterized import parameterized_class, parameterized
from test.ttexalens.unit_tests.test_base import get_core_location, init_default_test_context
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.context import Context


@parameterized_class(
    [
        {"core_desc": "ETH0", "neo_id": None},
        {"core_desc": "FW0", "neo_id": None},
        {"core_desc": "FW1", "neo_id": None},
        # {"core_desc": "DRAM0", "neo_id": None},
        {"core_desc": "FW0", "neo_id": 0},
        {"core_desc": "FW0", "neo_id": 1},
        {"core_desc": "FW0", "neo_id": 2},
        {"core_desc": "FW0", "neo_id": 3},
    ]
)
class TestDebugBus(unittest.TestCase):
    neo_id: int | None  # NEO ID
    context: Context  # TTExaLens context
    core_desc: str  # Core description ETH0, FW0, FW1 - being parametrized
    debug_bus: DebugBusSignalStore  # Debug bus signal store

    @classmethod
    def setUpClass(cls):
        cls.context = init_default_test_context()
        cls.device = cls.context.devices[0]

    def setUp(self):
        self.location = get_core_location(self.core_desc, self.device)
        debug_bus = self.location.noc_block.get_debug_bus(self.neo_id)
        if debug_bus is None:
            self.skipTest(f"Debug bus not available on core {self.core_desc}[neo={self.neo_id}]")
        self.debug_bus = debug_bus

    def test_invalid_rd_sel(self):
        sig = DebugBusSignalDescription(rd_sel=4, daisy_sel=0, sig_sel=0)
        with self.assertRaises(ValueError) as cm:
            self.debug_bus.read_signal(sig)
        self.assertIn("rd_sel must be between 0 and 3", str(cm.exception))

    def test_invalid_daisy_sel(self):
        sig = DebugBusSignalDescription(rd_sel=0, daisy_sel=256, sig_sel=0)
        with self.assertRaises(ValueError) as cm:
            self.debug_bus.read_signal(sig)
        self.assertIn("daisy_sel must be between 0 and 255", str(cm.exception))

    def test_invalid_sig_sel(self):
        sig = DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=65536)
        with self.assertRaises(ValueError) as cm:
            self.debug_bus.read_signal(sig)
        self.assertIn("sig_sel must be between 0 and 65535", str(cm.exception))

    def test_invalid_mask(self):
        sig = DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFFF)
        with self.assertRaises(ValueError) as cm:
            self.debug_bus.read_signal(sig)
        self.assertIn("mask must be a valid 32-bit integer", str(cm.exception))

    def test_sample_signal_group_invalid_samples(self):
        if not self.device.is_wormhole():
            self.skipTest("This test only works on wormhole.")

        group_name = next(iter(self.debug_bus.group_map.keys()))
        with self.assertRaises(ValueError) as cm:
            self.debug_bus.sample_signal_group(
                signal_group=group_name,
                l1_address=0x1000,
                samples=0,
                sampling_interval=2,
            )
        self.assertIn("samples count must be at least 1", str(cm.exception))

    def test_signal_group_invalid_l1_address(self):
        if not self.device.is_wormhole():
            self.skipTest("This test only works on wormhole.")

        # test sample_signal_group
        group_name = next(iter(self.debug_bus.group_map.keys()))
        with self.assertRaises(ValueError) as cm:
            self.debug_bus._read_signal_group_samples(
                signal_group=group_name,
                l1_address=0x1001,
                samples=1,
                sampling_interval=2,
            )
        self.assertIn("L1 address must be 16-byte aligned", str(cm.exception))

    def test_sample_signal_group_invalid_sampling_interval(self):
        if not self.device.is_wormhole():
            self.skipTest("This test only works on wormhole.")

        group_name = next(iter(self.debug_bus.group_map.keys()))
        with self.assertRaises(ValueError) as cm:
            self.debug_bus.sample_signal_group(
                signal_group=group_name,
                l1_address=0x1000,
                samples=2,
                sampling_interval=1,
            )
        self.assertIn("When sampling groups, sampling_interval must be between 2 and 256", str(cm.exception))

    @parameterized.expand(
        [
            (1, 0x100000),  # samples, l1_address
            (4, 0x100000 - 16),
            (25, 0x100000 - 32),
            (40, 0x100000 - 160),
        ]
    )
    def test_signal_group_exceeds_memory(self, samples, l1_address):
        if not self.device.is_wormhole():
            self.skipTest("This test only works on wormhole.")

        # test sample_signal_group
        group_name = next(iter(self.debug_bus.group_map.keys()))
        with self.assertRaises(ValueError) as cm:
            self.debug_bus._read_signal_group_samples(
                signal_group=group_name,
                l1_address=l1_address,
                samples=samples,
            )
        end_address = l1_address + (samples * self.debug_bus.L1_SAMPLE_SIZE_BYTES) - 1
        self.assertIn(f"L1 sampling range 0x{l1_address:x}-0x{end_address:x} exceeds 1 MiB limit", str(cm.exception))

    def test_read_signal_group_invalid_signal_name(self):
        if not self.device.is_wormhole():
            self.skipTest("This test only works on wormhole.")

        signal_name = "invalid_signal_name"
        group_name = next(iter(self.debug_bus.group_map.keys()))
        with self.assertRaises(ValueError) as cm:
            group_sample = self.debug_bus.read_signal_group(
                signal_group=group_name,
                l1_address=0x1000,
            )
            group_sample[signal_name]
        self.assertIn(f"Signal '{signal_name}' does not exist in group.", str(cm.exception))

    def test_invalid_group_name(self):
        if not self.device.is_wormhole():
            self.skipTest("This test only works on wormhole.")

        group_name = "invalid_group_name"
        with self.assertRaises(ValueError) as cm:
            self.debug_bus.get_signal_names_in_group(group_name)
        self.assertIn(f"Unknown group name '{group_name}'.", str(cm.exception))

    def test_get_signal_description_invalid_signal_name(self):
        signal_name = "invalid_signal_name"
        with self.assertRaises(ValueError) as cm:
            self.debug_bus.get_signal_description(signal_name)
        self.assertIn(
            f"Unknown signal name '{signal_name}' on {self.location.to_user_str()} for device {self.device._id}.",
            str(cm.exception),
        )
