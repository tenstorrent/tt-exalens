#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Unit test for register definition loading functionality.
"""

import os
import unittest
from ttexalens.reg_access_yaml import create_register_map as create_yaml_register_map
from ttexalens.reg_access_json import create_register_map as create_json_register_map

class TestRegDefLoad(unittest.TestCase):
    def setUp(self):
        self.regdef_path = os.getenv('REGDEF')
        if not self.regdef_path:
            self.skipTest("REGDEF environment variable not set")
        if not os.path.exists(self.regdef_path):
            self.skipTest(f"Register definition file not found: {self.regdef_path}")

        # Choose appropriate loader based on file extension
        _, ext = os.path.splitext(self.regdef_path)
        if ext.lower() == '.json':
            self.create_register_map = create_json_register_map
        elif ext.lower() in ['.yaml', '.yml']:
            self.create_register_map = create_yaml_register_map
        else:
            self.skipTest(f"Unsupported file extension: {ext}")

    def test_regdef_load(self):
        """Test loading register definitions from file."""
        # Create register map with verbose output
        reg_map = self.create_register_map(self.regdef_path, verbose=True)

        # Verify top level register map
        self.assertIsNotNone(reg_map)
        print("\n=== Top Level Register Map ===")
        print(reg_map)

        # Try to access some common registers to verify functionality
        # Note: These might not exist in all register maps, but we'll try them
        try:
            print("\n=== Testing register access ===")
            # Try to access a reset register if it exists
            if hasattr(reg_map, 'ARC_RESET'):
                print(reg_map.ARC_RESET)
                print(reg_map.ARC_RESET.GLOBAL_RESET)
                print(reg_map.ARC_RESET.SCRATCH[4])
            elif hasattr(reg_map, 'reset_unit'):
                print(reg_map.reset_unit)
                print(reg_map.reset_unit.GLOBAL_RESET)
                print(reg_map.reset_unit.SCRATCH_4)
            
            # Try to access memory block if it exists
            if hasattr(reg_map, 'ARC_ICCM'):
                print(reg_map.ARC_ICCM)
            elif hasattr(reg_map, 'iccm_memory'):
                print(reg_map.iccm_memory)
        except AttributeError as e:
            print(f"Note: Some registers not found: {e}")

if __name__ == "__main__":
    unittest.main() 