# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
from ttexalens.memory_map import MemoryMap
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.device_address import DeviceAddress


class TestMemoryMap(unittest.TestCase):
    """Unit tests for MemoryMap class."""

    def setUp(self):
        """Set up test fixtures with sample memory blocks."""
        # Create sample memory blocks with different address ranges
        self.l1_block = MemoryBlock(
            size=1536 * 1024, address=DeviceAddress(private_address=0x00000000, noc_address=0x00000000)  # 1536 KB
        )

        self.dest_block = MemoryBlock(
            size=32 * 1024, address=DeviceAddress(private_address=0xFFBD8000, noc_address=0xFFBD8000)  # 32 KB
        )

        self.cfg_reg_block = MemoryBlock(
            size=64 * 1024, address=DeviceAddress(private_address=0xFFEF0000, noc_address=0xFFEF0000)  # 64 KB
        )

        self.gp_reg_block = MemoryBlock(
            size=64 * 1024, address=DeviceAddress(private_address=0xFFE00000, noc_address=0xFFE00000)  # 64 KB
        )

        # Create memory map with these blocks
        self.blocks_dict = {
            "L1": self.l1_block,
            "DEST": self.dest_block,
            "CFG_REG": self.cfg_reg_block,
            "GP_REG": self.gp_reg_block,
        }
        self.memory_map = MemoryMap(self.blocks_dict)

    def test_initialization(self):
        """Test that MemoryMap initializes correctly."""
        self.assertEqual(len(self.memory_map.blocks), 4)
        self.assertEqual(len(self.memory_map.sortedBlocks), 4)

        # Verify blocks are stored correctly
        self.assertIn("L1", self.memory_map.blocks)
        self.assertIn("DEST", self.memory_map.blocks)
        self.assertIn("CFG_REG", self.memory_map.blocks)
        self.assertIn("GP_REG", self.memory_map.blocks)

    def test_sorted_blocks_order(self):
        """Test that sortedBlocks are sorted by noc_address."""
        prev_address = -1
        for block, name in self.memory_map.sortedBlocks:
            current_address = block.address.noc_address
            self.assertGreater(
                current_address, prev_address, f"Block {name} at {hex(current_address)} is not in sorted order"
            )
            prev_address = current_address

    def test_sorted_blocks_tuple_structure(self):
        """Test that sortedBlocks contains tuples of (MemoryBlock, str)."""
        for item in self.memory_map.sortedBlocks:
            self.assertIsInstance(item, tuple, "sortedBlocks should contain tuples")
            self.assertEqual(len(item), 2, "Each tuple should have exactly 2 elements")
            block, name = item
            self.assertIsInstance(block, MemoryBlock, "First element should be MemoryBlock")
            self.assertIsInstance(name, str, "Second element should be string")

    def test_get_block_by_name_existing(self):
        """Test retrieving blocks by name for existing blocks."""
        l1 = self.memory_map.get_block_by_name("L1")
        self.assertIsNotNone(l1)
        self.assertEqual(l1.size, 1536 * 1024)
        self.assertEqual(l1.address.noc_address, 0x00000000)

        dest = self.memory_map.get_block_by_name("DEST")
        self.assertIsNotNone(dest)
        self.assertEqual(dest.size, 32 * 1024)
        self.assertEqual(dest.address.noc_address, 0xFFBD8000)

    def test_get_block_by_name_nonexistent(self):
        """Test retrieving blocks by name for non-existent blocks."""
        result = self.memory_map.get_block_by_name("NONEXISTENT")
        self.assertIsNone(result)

        result = self.memory_map.get_block_by_name("")
        self.assertIsNone(result)

    def test_get_block_by_address_start_of_block(self):
        """Test address lookup at the start of memory blocks."""
        # Start of L1
        name = self.memory_map.get_block_name_by_address(0x00000000)
        self.assertEqual(name, "L1")

        # Start of DEST
        name = self.memory_map.get_block_name_by_address(0xFFBD8000)
        self.assertEqual(name, "DEST")

        # Start of GP_REG
        name = self.memory_map.get_block_name_by_address(0xFFE00000)
        self.assertEqual(name, "GP_REG")

        # Start of CFG_REG
        name = self.memory_map.get_block_name_by_address(0xFFEF0000)
        self.assertEqual(name, "CFG_REG")

    def test_get_block_by_address_middle_of_block(self):
        """Test address lookup in the middle of memory blocks."""
        # Middle of L1 (0x00000000 + 768KB)
        name = self.memory_map.get_block_name_by_address(0x000C0000)
        self.assertEqual(name, "L1")

        # Middle of DEST
        name = self.memory_map.get_block_name_by_address(0xFFBDC000)
        self.assertEqual(name, "DEST")

        # Middle of GP_REG
        name = self.memory_map.get_block_name_by_address(0xFFE08000)
        self.assertEqual(name, "GP_REG")

    def test_get_block_by_address_end_of_block(self):
        """Test address lookup at the end boundary of memory blocks."""
        # Last byte of L1 (0x00000000 + 1536KB - 1)
        name = self.memory_map.get_block_name_by_address(0x0017FFFF)
        self.assertEqual(name, "L1")

        # One byte past L1 should not be in L1
        name = self.memory_map.get_block_name_by_address(0x00180000)
        self.assertNotEqual(name, "L1")

        # Last byte of DEST (0xFFBD8000 + 32KB - 1)
        name = self.memory_map.get_block_name_by_address(0xFFBDFFFF)
        self.assertEqual(name, "DEST")

        # One byte past DEST should not be in DEST
        name = self.memory_map.get_block_name_by_address(0xFFBE0000)
        self.assertNotEqual(name, "DEST")

    def test_get_block_by_address_unmapped_regions(self):
        """Test address lookup for unmapped memory regions."""
        # Between L1 and GP_REG
        name = self.memory_map.get_block_name_by_address(0x00200000)
        self.assertIsNone(name)

        # Between DEST and GP_REG
        name = self.memory_map.get_block_name_by_address(0xFFBE0000)
        self.assertIsNone(name)

        # Above all defined blocks
        name = self.memory_map.get_block_name_by_address(0xFFFFFFFF)
        self.assertIsNone(name)

        # Very low address if there's a gap
        name = self.memory_map.get_block_name_by_address(0x00180001)
        self.assertIsNone(name)

    def test_get_block_by_address_boundary_conditions(self):
        """Test edge cases and boundary conditions."""
        # Address 0
        name = self.memory_map.get_block_name_by_address(0)
        self.assertEqual(name, "L1")

        # Negative address (should not match anything)
        name = self.memory_map.get_block_name_by_address(-1)
        self.assertIsNone(name)

    def test_empty_memory_map(self):
        """Test behavior with an empty memory map."""
        empty_map = MemoryMap({})
        self.assertEqual(len(empty_map.blocks), 0)
        self.assertEqual(len(empty_map.sortedBlocks), 0)

        result = empty_map.get_block_name_by_address(0x00000000)
        self.assertIsNone(result)

        result = empty_map.get_block_by_name("ANYTHING")
        self.assertIsNone(result)

    def test_single_block_memory_map(self):
        """Test memory map with a single block."""
        single_block_map = MemoryMap({"ONLY_BLOCK": self.l1_block})

        self.assertEqual(len(single_block_map.blocks), 1)
        self.assertEqual(len(single_block_map.sortedBlocks), 1)

        name = single_block_map.get_block_name_by_address(0x00000000)
        self.assertEqual(name, "ONLY_BLOCK")

        name = single_block_map.get_block_name_by_address(0xFFFFFFFF)
        self.assertIsNone(name)

    def test_adjacent_blocks(self):
        """Test blocks that are adjacent to each other."""
        block1 = MemoryBlock(size=1024, address=DeviceAddress(noc_address=0x1000))
        block2 = MemoryBlock(size=1024, address=DeviceAddress(noc_address=0x1400))  # Starts right after block1

        adjacent_map = MemoryMap({"BLOCK1": block1, "BLOCK2": block2})

        # Last address of BLOCK1
        name = adjacent_map.get_block_name_by_address(0x13FF)
        self.assertEqual(name, "BLOCK1")

        # First address of BLOCK2
        name = adjacent_map.get_block_name_by_address(0x1400)
        self.assertEqual(name, "BLOCK2")


if __name__ == "__main__":
    unittest.main()
