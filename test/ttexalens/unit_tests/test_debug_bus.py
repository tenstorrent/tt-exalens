# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from parameterized import parameterized_class, parameterized
from test.ttexalens.unit_tests.core_simulator import RiscvCoreSimulator
from test.ttexalens.unit_tests.program_writer import RiscvProgramWriter
from test.ttexalens.unit_tests.test_base import get_core_location, init_cached_test_context
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription, DebugBusSignalStore
from ttexalens.context import Context
from ttexalens.cli_commands.debug_bus import parse_string


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
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

    def setUp(self):
        try:
            self.location = get_core_location(self.core_desc, self.device)
        except ValueError as e:
            if "ETH core" in e.__str__() or "FW core" in e.__str__():
                self.skipTest(f"Core {self.core_desc} not available on this platform: {e}")
            else:
                raise e

        debug_bus = self.location.noc_block.get_debug_bus(self.neo_id)
        if debug_bus is None:
            self.skipTest(f"Debug bus not available on core {self.core_desc}[neo={self.neo_id}]")
        self.debug_bus = debug_bus

        for risc_name in self.location.noc_block.risc_names:
            if self.device.is_wormhole() and risc_name.lower() == "ncrisc":
                self.location.noc_block.get_risc_debug(risc_name, self.neo_id).set_code_start_address(0x2000)
            self.location.noc_block.get_risc_debug(risc_name, self.neo_id).set_reset_signal(True)
            self.assertTrue(self.location.noc_block.get_risc_debug(risc_name, self.neo_id).is_in_reset())

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
        if self.device.is_quasar():
            self.skipTest("This test does not work on quasar.")

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
        if self.device.is_quasar():
            self.skipTest("This test does not work on quasar.")

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
        if self.device.is_quasar():
            self.skipTest("This test does not work on quasar.")

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
        if self.device.is_quasar():
            self.skipTest("This test does not work on quasar.")

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
        if self.device.is_quasar():
            self.skipTest("This test does not work on quasar.")

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
        if self.device.is_quasar():
            self.skipTest("This test does not work on quasar.")

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

    def _get_group_for_signal(self, signal_store: DebugBusSignalStore, signal: str) -> str:
        """Get the group name for a given signal name."""
        for group_name, group_dict in signal_store.signal_groups.items():
            if signal_store.get_base_signal_name(signal) in group_dict:
                return group_name
        return ""

    def test_debug_bus_command_signal_name_parser(self):
        """Test the parse_string function for all signal names in the signal store."""
        signal_names = self.debug_bus.signal_names

        for name in signal_names:
            input_string = name
            parsed_result = parse_string(input_string)

            # Check that the parsing returned exactly one item
            self.assertEqual(
                len(parsed_result), 1, f"Parsing returned {len(parsed_result)} results for '{name}'. Expected: 1."
            )

            # Check that the result is a string (a signal name, not a list of numbers)
            self.assertIsInstance(
                parsed_result[0],
                str,
                f"Parsed result for '{name}' is not a string. Type: {type(parsed_result[0]).__name__}.",
            )

            # Check that the parsed string matches the original signal name
            self.assertEqual(
                parsed_result[0],
                name,
                f"Parsed name does not match original. Original: '{name}', Parsed: '{parsed_result[0]}'.",
            )

    @parameterized.expand(
        [
            # input_string, expected_result
            ("{7,0,12,0x3ffffff}", [[7, 0, 12, 0x3FFFFFF]]),
            ("{10,20,30}", [[10, 20, 30, 0xFFFFFFFF]]),
            ("SigA,{1,2,3},SigB,{10,20,30,40},End", ["SigA", [1, 2, 3, 0xFFFFFFFF], "SigB", [10, 20, 30, 40], "End"]),
            ("signal1", ["signal1"]),
            ("", []),
            ("signal1,signal2", ["signal1", "signal2"]),
            ("{1,2,3,4}", [[1, 2, 3, 4]]),
        ]
    )
    def test_debug_bus_command_parse_string(self, input_string, expected_result):
        """Test various cases of the parse_string function."""
        parsed_result = parse_string(input_string)
        self.assertEqual(
            parsed_result,
            expected_result,
            f"Failed parsing input '{input_string}': expected {expected_result}, got {parsed_result}",
        )
        self.assertIsInstance(parsed_result, list, f"Result should be a list, got {type(parsed_result).__name__}")

    def test_debug_bus_signal_store_pc(self):
        if not self.device.is_wormhole():
            self.skipTest("This test only works on Wormhole devices.")

        for risc_name in self.location.noc_block.risc_names:
            core_sim = RiscvCoreSimulator(self.context, self.core_desc, risc_name, self.neo_id)
            program_writer = RiscvProgramWriter(core_sim)

            pc_signal_name = risc_name.lower() + "_pc"

            # ebreak
            program_writer.append_ebreak()
            program_writer.write_program()

            # Take risc out of reset
            core_sim.set_reset(False)
            if not risc_name.lower() == "ncrisc":
                assert core_sim.is_halted(), f"Core {risc_name} should be halted after ebreak."

            # simple test for pc signal
            pc_value_32 = self.debug_bus.read_signal(pc_signal_name)

            group_name = self._get_group_for_signal(self.debug_bus, pc_signal_name)
            group_values = self.debug_bus.read_signal_group(group_name, l1_address=0x1000)
            assert (
                pc_signal_name in group_values.keys()
            ), f"PC signal '{pc_signal_name}' not found in group for {risc_name}"
            assert (
                group_values[pc_signal_name] == pc_value_32
            ), f"PC signal value mismatch for {risc_name}: group={group_values[pc_signal_name]}, direct={pc_value_32}"

    @parameterized.expand(
        [
            (1, 2),  # samples, sampling_interval
            (11, 50),
            (25, 100),
            (40, 5),
        ]
    )
    def test_debug_bus_signal_store_sample_signal_group(self, samples, sampling_interval):
        """Validate signal group readings for all groups on this core."""
        if not self.device.is_wormhole():
            self.skipTest("This test only works on Wormhole devices.")

        WORD_SIZE_BITS = 32
        l1_addr = 0x1000

        for risc_name in self.location.noc_block.risc_names:
            core_sim = RiscvCoreSimulator(self.context, self.core_desc, risc_name, self.neo_id)
            program_writer = RiscvProgramWriter(core_sim)

            # ebreak
            program_writer.append_ebreak()
            program_writer.write_program()

            # Take risc out of reset
            core_sim.set_reset(False)
            if not risc_name.lower() == "ncrisc":
                assert core_sim.is_halted(), f"Core {risc_name} should be halted after ebreak."

            for group in self.debug_bus.group_names:
                if not group.startswith(risc_name.lower() + "_"):
                    continue

                sampled_group = self.debug_bus._read_signal_group_samples(group, l1_addr, samples, sampling_interval)
                if not isinstance(sampled_group, list):
                    sampled_group = [sampled_group]

                # check number of samples taken
                self.assertEqual(len(sampled_group), samples, f"Expected {samples} samples, got {len(sampled_group)}")

                for signal_name in self.debug_bus.get_signal_names_in_group(group):
                    # all samples should be equal
                    first_val = sampled_group[0][signal_name]
                    self.assertTrue(
                        all(v[signal_name] == first_val for v in sampled_group),
                        f"{signal_name}: Inconsistent sampled values: {sampled_group}",
                    )

                    # get all signal parts
                    parts = self.debug_bus.get_signal_part_names(signal_name)

                    if self.debug_bus.is_combined_signal(signal_name):
                        # combined signal
                        combined_value = 0

                        # Find the lowest part of combined signal, which has minimum rd_sel among all parts
                        min_part = min(parts, key=lambda part: self.debug_bus.get_signal_description(part).rd_sel)
                        min_part_desc = self.debug_bus.get_signal_description(min_part)

                        # calculate combined value from all parts using read_signal
                        for part in parts:
                            part_value = self.debug_bus.read_signal(part)
                            part_desc = self.debug_bus.get_signal_description(part)
                            shift = (part_desc.mask & -part_desc.mask).bit_length() - 1
                            combined_value |= part_value << (shift + part_desc.rd_sel * WORD_SIZE_BITS)

                        min_shift = (min_part_desc.mask & -min_part_desc.mask).bit_length() - 1
                        combined_value >>= min_shift + min_part_desc.rd_sel * WORD_SIZE_BITS
                        self.assertEqual(first_val, combined_value, f"Combined signal {signal_name} value mismatch.")
                    else:
                        # single signal
                        single_value = self.debug_bus.read_signal(signal_name)
                        self.assertEqual(first_val, single_value, f"Signal {signal_name} value mismatch.")
