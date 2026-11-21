# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import contextlib
import importlib
import io
import unittest

from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.register_store import RegisterStore
from ttexalens.uistate import UIState

dump_tensix_state = importlib.import_module("ttexalens.cli_commands.dump-tensix-state")


class TestDumpTensixState(unittest.TestCase):
    context: Context
    ui_state: UIState
    location: OnChipCoordinate
    register_store: RegisterStore
    location_str = "0,0"

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.ui_state = UIState(cls.context)

    def setUp(self):
        device = self.context.devices[0]
        if device.is_quasar():
            self.skipTest("Test uses Wormhole and Blackhole register names.")
        self.location = OnChipCoordinate.create(self.location_str, device=device)
        self.register_store = self.location.noc_block.get_register_store()

    def _write_registers(self, values: dict[str, int]):
        """Writes the registers and restores their old values when the test ends."""
        for register_name, value in values.items():
            self.addCleanup(
                self.register_store.write_register, register_name, self.register_store.read_register(register_name)
            )
            self.register_store.write_register(register_name, value)

    def _dump(self, arguments: str) -> dict[str, str]:
        """Runs the command and returns the first value printed next to each row name."""
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            dump_tensix_state.run(f"tensix {arguments} -l {self.location_str}", self.context, self.ui_state)
        rows: dict[str, str] = {}
        for line in output.getvalue().splitlines():
            cells = [cell.strip() for cell in line.split("│")]
            for name, value in zip(cells, cells[1:]):
                if name and name not in rows:
                    rows[name] = value
        return rows

    def test_general_purpose_register_pairs(self):
        """Merged rows combine the halves of a value; registers that are not halves of one value get no merged row."""
        self._write_registers(
            {
                "TMP_HI_T0": 0x12340000,
                "TMP_LO_T0": 0x5678,
                "PERF_FIRST_UNP_HI_T0": 0x1,
                "PERF_FIRST_UNP_LO_T0": 0x12345678,
            }
        )
        rows = self._dump("gpr -t 0,2")
        self.assertEqual(rows["tmp"], str(0x12345678))
        self.assertEqual(rows["perf_first_unp"], str(0x112345678))
        self.assertIn("dest_offset_lo", rows)
        self.assertIn("dest_offset_hi", rows)
        self.assertNotIn("dest_offset", rows)

    def test_tile_descriptor_blobs_y_start(self):
        """blobs_y_start_lo holds the low 16 bits of blobs_y_start and blobs_y_start_hi the high 16 bits."""
        for low, high in [(0x1, 0x0), (0x0, 0x1), (0x5678, 0x1234)]:
            self._write_registers(
                {
                    "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_lo": low,
                    "UNPACK_TILE_DESCRIPTOR0_blobs_y_start_hi": high,
                }
            )
            rows = self._dump("unpack")
            self.assertEqual(rows["blobs_y_start"], str((high << 16) | low), f"lo=0x{low:x}, hi=0x{high:x}")
