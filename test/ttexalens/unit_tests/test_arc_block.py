# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from unittest.mock import MagicMock, patch
from parameterized import parameterized

from ttexalens.hardware.blackhole.arc_block import BlackholeArcBlock
from ttexalens.memory_map import MemoryMap


class TestBlackholeArcBlockMemoryMap(unittest.TestCase):
    """The ARC NOC memory map is valid on local and remote Blackhole devices, whichever is built first."""

    @parameterized.expand([([True, False],), ([False, True],)])
    def test_noc_register_blocks(self, is_local_order: list[bool]):
        with patch.dict(MemoryMap._MemoryMap__cache_of_memory_maps, clear=True):  # type: ignore[attr-defined]
            for is_local in is_local_order:
                location = MagicMock()
                location.device.is_local = is_local
                arc_block = BlackholeArcBlock(location)
                for address, name in [
                    (0x80050000, "noc0_regs"),
                    (0x80057FFC, "noc0_regs"),
                    (0x80058000, "noc1_regs"),
                    (0x8005FFFC, "noc1_regs"),
                ]:
                    block_info = arc_block.noc_memory_map.find_by_noc_address(address)
                    self.assertIsNotNone(block_info, f"0x{address:08x} is not mapped (is_local={is_local})")
                    assert block_info is not None
                    self.assertEqual(block_info.name, name)
