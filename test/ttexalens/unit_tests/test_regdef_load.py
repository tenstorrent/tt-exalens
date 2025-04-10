#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Unit test for register definition loading functionality. Uses mock memory to test register access.
"""

import os
import unittest
from ttexalens.reg_access_yaml import YamlRegisterMap
from ttexalens.reg_access_json import JsonRegisterMap
from ttexalens.reg_access_common import set_verbose

# Logging funcions

def log_stage(stage_name):
    print(f"\033[92m=== {stage_name} ===\033[0m")

class TestRegDefLoad(unittest.TestCase):
    def file_type(self):
        if self.regdef_path.endswith('.json'):
            return 'json'
        elif self.regdef_path.endswith('.yaml') or self.regdef_path.endswith('.yml'):
            return 'yaml'
        else:
            raise ValueError(f"Unsupported file extension: {self.regdef_path}")

    def family(self):
        if self.file_type() == 'yaml':
            return 'WH' # Wormhole
        elif self.file_type() == 'json':
            return 'BH' # Blackhole
        else:
            raise ValueError(f"Unsupported family for file: {self.regdef_path}")

    def setUp(self):
        self.regdef_path = os.getenv('REGDEF')
        if not self.regdef_path:
            self.skipTest("REGDEF environment variable not set")
        if not os.path.exists(self.regdef_path):
            self.skipTest(f"Register definition file not found: {self.regdef_path}")

        # Choose appropriate loader based on file extension
        _, ext = os.path.splitext(self.regdef_path)
        if ext.lower() == '.json':
            self.RegisterMap = JsonRegisterMap
        elif ext.lower() in ['.yaml', '.yml']:
            self.RegisterMap = YamlRegisterMap
        else:
            self.skipTest(f"Unsupported file extension: {ext}")

    def test_regdef_load(self):
        """Test loading register definitions from file."""
        log_stage(f"{self.test_regdef_load.__doc__}")

        # Create register map with verbose output
        set_verbose(True)
        reg_map = self.RegisterMap(self.regdef_path)

        # Verify top level register map
        self.assertIsNotNone(reg_map)

        # Try to access some common registers to verify functionality
        # Note: These might not exist in all register maps, but we'll try them
        log_stage("Testing register print")
        # Try to access a reset register if it exists
        if self.family() == 'WH':
            log_stage("Printing ARC_RESET")
            print(reg_map.ARC_RESET)
            log_stage("Printing GLOBAL_RESET")
            print(reg_map.ARC_RESET.GLOBAL_RESET)
            log_stage("Printing SCRATCH[0]")
            print(reg_map.ARC_RESET.SCRATCH[0])
        elif self.family() == 'BH':
            log_stage("Printing reset_unit")
            print(reg_map.reset_unit)
            log_stage("Printing GLOBAL_RESET")
            print(reg_map.reset_unit.GLOBAL_RESET)
            log_stage("Printing SCRATCH_0")
            print(reg_map.reset_unit.SCRATCH_0)

        # Try to access memory block if it exists
        log_stage("Testing register array print")
        if self.family() == 'WH':
            log_stage("Printing CSM")
            print(reg_map.ARC_CSM)
            log_stage("Printing CSM[10]")
            print(reg_map.ARC_CSM.DATA[10])
        elif self.family() == 'BH':
            log_stage("Printing csm_memory")
            print(reg_map.csm_memory)
            log_stage("Printing CSM_memory[10]")
            print(reg_map.csm_memory.csm_memory[10].read())

    @unittest.skip("Skipping field access test")
    def test_regdef_field_access(self):
        """Test field access to registers."""
        log_stage(f"{self.test_regdef_field_access.__doc__}")

        # Create register map with verbose output
        set_verbose(True)
        reg_map = self.RegisterMap(self.regdef_path)

        # Verify top level register map
        self.assertIsNotNone(reg_map)

        # Try to read/write a register field (NOC reset in GLOBAL_RESETS)
        # Check that the bit is properly read back
        log_stage("Testing register field read/write")
        if self.family() == 'WH':
            # Read initial register value
            initial_val = reg_map.ARC_RESET.GLOBAL_RESET.read()
            # Get field info directly from the register
            noc_reset_field = reg_map.ARC_RESET.GLOBAL_RESET._fields['noc_reset']
            print(f"Field info: {noc_reset_field}")
            # Field info is [offset, width]
            noc_reset_mask = (1 << noc_reset_field[1]) - 1 << noc_reset_field[0]
            print(f"initial_val: {initial_val:X}, noc_reset_mask: {noc_reset_mask:X}")
            
            # Write 1 to NOC reset
            reg_map.ARC_RESET.GLOBAL_RESET.write_field('noc_reset', 1)
            # Read full register and verify only noc_reset bit changed
            new_val = reg_map.ARC_RESET.GLOBAL_RESET.read()
            self.assertEqual(new_val & noc_reset_mask, noc_reset_mask, "noc_reset bit not set")
            self.assertEqual(new_val & ~noc_reset_mask, initial_val & ~noc_reset_mask, "Other bits changed")
            
            # Write 0 to NOC reset
            reg_map.ARC_RESET.GLOBAL_RESET.write_field('noc_reset', 0)
            # Read full register and verify only noc_reset bit changed back
            final_val = reg_map.ARC_RESET.GLOBAL_RESET.read()
            self.assertEqual(final_val & noc_reset_mask, 0, "NOC_RESET bit not cleared")
            self.assertEqual(final_val & ~noc_reset_mask, initial_val & ~noc_reset_mask, "Other bits changed")
        
        elif self.family() == 'BH':
            # Read initial register value
            initial_val = reg_map.reset_unit.GLOBAL_RESET.read()
            # Get field info directly from the register
            noc_reset_field = reg_map.reset_unit.GLOBAL_RESET._fields['noc_reset']
            print(f"Field info: {noc_reset_field}")
            # Field info is [offset, width]
            noc_reset_mask = (1 << noc_reset_field[1]) - 1 << noc_reset_field[0]
            print(f"initial_val: {initial_val:X}, noc_reset_mask: {noc_reset_mask:X}")
            
            # Write 1 to NOC reset
            reg_map.reset_unit.GLOBAL_RESET.write_field('noc_reset', 1)
            # Read full register and verify only NOC_RESET bit changed
            new_val = reg_map.reset_unit.GLOBAL_RESET.read()
            self.assertEqual(new_val & noc_reset_mask, noc_reset_mask, "NOC_RESET bit not set")
            self.assertEqual(new_val & ~noc_reset_mask, initial_val & ~noc_reset_mask, "Other bits changed")
            
            # Write 0 to NOC reset
            reg_map.reset_unit.GLOBAL_RESET.write_field('noc_reset', 0)
            # Read full register and verify only NOC_RESET bit changed back
            final_val = reg_map.reset_unit.GLOBAL_RESET.read()
            self.assertEqual(final_val & noc_reset_mask, 0, "NOC_RESET bit not cleared")
            self.assertEqual(final_val & ~noc_reset_mask, initial_val & ~noc_reset_mask, "Other bits changed")

    def test_access_patterns(self):
        """Test register and field access patterns."""
        log_stage(f"{self.test_access_patterns.__doc__}")

        # Create register map with verbose output
        set_verbose(True)
        reg_map = self.RegisterMap(self.regdef_path)

        # Verify register access requires explicit read/write
        if self.family() == 'WH':
            reg = reg_map.ARC_RESET.GLOBAL_RESET
            self.assertIsNotNone(reg)  # Register object exists
            self.assertNotIsInstance(reg, int)  # Not an integer value

            # Read and write register
            initial_val = reg.read()
            reg.write(0x12345678)
            new_val = reg.read()
            self.assertEqual(new_val, 0x12345678)

            # Field access
            reg.noc_reset = 1
            self.assertEqual(reg.noc_reset, 1)

            # Array access
            array_reg = reg_map.ARC_RESET.SCRATCH[0]
            array_reg.write(0x87654321)
            self.assertEqual(array_reg.read(), 0x87654321)

        elif self.family() == 'BH':
            reg = reg_map.reset_unit.GLOBAL_RESET
            self.assertIsNotNone(reg)  # Register object exists
            self.assertNotIsInstance(reg, int)  # Not an integer value

            # Read and write register
            initial_val = reg.read()
            reg.write(0x12345678)
            new_val = reg.read()
            self.assertEqual(new_val, 0x12345678)

            # Field access
            reg.noc_reset_n = 1
            self.assertEqual(reg.noc_reset_n, 1)

            # Array access
            array_reg = reg_map.reset_unit.SCRATCH_0
            array_reg.write(0x87654321)
            self.assertEqual(array_reg.read(), 0x87654321)

if __name__ == "__main__":
    unittest.main() 