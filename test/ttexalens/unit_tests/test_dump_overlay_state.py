# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import importlib
import unittest
from unittest.mock import MagicMock, patch

from ttexalens.hardware.quasar.functional_overlay_registers_description import overlay_registers_description

dump_overlay_state = importlib.import_module("ttexalens.cli_commands.dump-overlay-state")


class TestDumpPlic(unittest.TestCase):
    """The PLIC dump must not change interrupt state and must label priorities with the interrupt source ID."""

    def dump_plic(self) -> tuple[list[str], dict[str, list]]:
        read_registers: list[str] = []

        def read_register(name: str) -> int:
            read_registers.append(name)
            return 0x7 if name == "TT_CLUSTER_PLIC_PRIORITY_0_" else 0

        register_store = MagicMock()
        register_store.read_register.side_effect = read_register
        tables: dict[str, list] = {}

        def print_styled_table(title, header, rows):
            tables[title] = rows

        with patch.object(
            dump_overlay_state.formatter, "print_styled_table", side_effect=print_styled_table
        ), patch.object(dump_overlay_state.console, "print"):
            dump_overlay_state.dump_plic(register_store, True, list(range(8)), overlay_registers_description)
        return read_registers, tables

    def test_does_not_read_claim_complete(self):
        read_registers, _ = self.dump_plic()
        self.assertTrue(read_registers, "PLIC dump should read registers.")
        self.assertEqual([name for name in read_registers if name.endswith("CLAIM_COMPLETE")], [])

    def test_priority_labels_are_source_ids(self):
        _, tables = self.dump_plic()
        priorities = next(rows for title, rows in tables.items() if "priorities" in title)
        self.assertEqual(priorities[0], (1, "0x7"))
        self.assertEqual(priorities[-1][0], len(overlay_registers_description.plic_priorities))
