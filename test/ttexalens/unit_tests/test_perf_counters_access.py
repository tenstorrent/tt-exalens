# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import contextlib
import importlib
import io
import unittest
from unittest import mock

from parameterized import parameterized

from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.exceptions import TTException
from ttexalens.perf_counters import read_perf_counters, reset_perf_counters, start_perf_counters, stop_perf_counters
from ttexalens.uistate import UIState

perf_counters_command = importlib.import_module("ttexalens.cli_commands.perf_counters")


class TestPerfCountersCommand(unittest.TestCase):
    context: Context
    ui_state: UIState

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.ui_state = UIState(cls.context)
        location = OnChipCoordinate.create("0,0", device=cls.context.devices[0])
        if location.noc_block.get_perf_counters() is None:
            raise unittest.SkipTest("No perf counters on this core.")

    def run_command(self, command: str) -> tuple[list[str], list[str]]:
        """Runs the command and returns its printed lines and its warnings."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output), mock.patch.object(perf_counters_command.util, "WARN") as warn:
            perf_counters_command.run(command, self.context, self.ui_state)
        return output.getvalue().splitlines(), [str(call.args[0]) for call in warn.call_args_list]

    @parameterized.expand(
        [
            ("unnamed request id", "2"),  # FPU names only ids 0, 1 and 257
            ("unnamed grant id", "0x100"),
            ("named id", "257"),
            ("name", "fpu_or_sfpu_instrn"),
        ]
    )
    def test_read_one_counter(self, _description: str, counter: str):
        """``read --counter`` prints the value of any counter id in [0, 512), not only of ids that have a name."""
        lines, warnings = self.run_command(f"perf-counters read --block=FPU --counter={counter} -l 0,0")
        self.assertEqual(warnings, [])
        self.assertEqual(len(lines), 1, lines)
        self.assertTrue(lines[0].isdigit(), lines)

    @parameterized.expand([("unknown name", "no_such_counter"), ("id out of range", "512")])
    def test_read_unknown_counter(self, _description: str, counter: str):
        lines, warnings = self.run_command(f"perf-counters read --block=FPU --counter={counter} -l 0,0")
        self.assertEqual(lines, [])
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("not found in block FPU", warnings[0])


class TestPerfCountersNeoId(unittest.TestCase):
    """A core without NEOs has no counters for a NEO id: asking for one must fail, not return the core's counters."""

    context: Context
    location: OnChipCoordinate

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.location = OnChipCoordinate.create("0,0", device=cls.context.devices[0])
        if cls.location.noc_block.neo_ids:
            raise unittest.SkipTest("This core has NEOs.")
        if cls.location.noc_block.get_perf_counters() is None:
            raise unittest.SkipTest("No perf counters on this core.")

    def test_without_neo_id(self):
        self.assertTrue(read_perf_counters(self.location, block_name="FPU"))

    @parameterized.expand(
        [
            ("read", read_perf_counters),
            ("reset", reset_perf_counters),
            ("start", start_perf_counters),
            ("stop", stop_perf_counters),
        ]
    )
    def test_neo_id_is_rejected(self, _name: str, function):
        with self.assertRaises(TTException):
            function(self.location, "FPU", neo_id=3)


if __name__ == "__main__":
    unittest.main()
