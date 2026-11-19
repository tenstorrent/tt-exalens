# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import contextlib
import importlib
import io
import unittest

from parameterized import parameterized
from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens import tt_exalens_lib as lib
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.debug_tensix import TensixDebug
from ttexalens.uistate import UIState

dump_tensix_state = importlib.import_module("ttexalens.cli_commands.dump-tensix-state")


class TestRegisterWindowCounters(unittest.TestCase):
    """The thread 0 Dst register window counter as shown by get_tensix_state and dump-tensix-state."""

    context: Context
    location: OnChipCoordinate
    tensix_debug: TensixDebug
    debug_bus: DebugBusSignalStore
    location_str = "0,0"

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()

    def setUp(self):
        device = self.context.devices[0]
        if device.is_quasar():
            self.skipTest("Test uses Wormhole and Blackhole instructions.")
        self.location = OnChipCoordinate.create(self.location_str, device=device)
        self.tensix_debug = TensixDebug(self.location)
        debug_bus = self.location.noc_block.get_debug_bus()
        assert debug_bus is not None
        self.debug_bus = debug_bus
        self.addCleanup(self._set_dst_counter, 0)

    def _set_dst_counter(self, value: int):
        ops = self.context.devices[0].instructions
        # 0xF sets SrcA, SrcB, Dst and the fidelity phase of thread 0 to 0
        self.tensix_debug.inject_instruction(ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF), 0)
        while value > 0:
            step = min(value, 0xF)
            self.tensix_debug.inject_instruction(ops.TT_OP_INCRWC(0, step, 0, 0), 0)
            value -= step

    def test_split_signals_are_left_out_of_groups(self):
        """A signal whose parts sit in two groups cannot be read from either group."""
        for base_name in {name.split("/")[0] for name in self.debug_bus.signal_names if "/" in name}:
            parts = [desc for name, desc in self.debug_bus.signals.items() if name.startswith(base_name + "/")]
            if len({(desc.daisy_sel, desc.sig_sel) for desc in parts}) > 1:
                self.assertTrue(all(desc.across_groups for desc in parts), base_name)
                for group_name, group_signals in self.debug_bus.signal_groups.items():
                    self.assertNotIn(base_name, group_signals, group_name)

    @parameterized.expand([0x5, 0x100, 0x105, 0x3FF])
    def test_get_tensix_state_dst_counter(self, value: int):
        self._set_dst_counter(value)
        state = lib.get_tensix_state(self.location, context=self.context)
        self.assertEqual(state.register_window_counters["rwc0_dst"], value)

    @parameterized.expand([0x5, 0x100, 0x105, 0x3FF])
    def test_dump_tensix_state_dst_counter(self, value: int):
        self._set_dst_counter(value)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            dump_tensix_state.run(f"tensix rwc -l {self.location_str}", self.context, UIState(self.context))
        values = [
            cells[cells.index("rwc0_dst") + 1]
            for cells in ([cell.strip() for cell in line.split("│")] for line in output.getvalue().splitlines())
            if "rwc0_dst" in cells
        ]
        self.assertEqual(values, [hex(value)])
