#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Integration test for register definition loading functionality using real device access.
Tests both PCI and JTAG access methods.
"""

import os
import unittest
from ttexalens import tt_exalens_init
from ttexalens.reg_access_yaml import YamlRegisterMap
from ttexalens.reg_access_json import JsonRegisterMap
from ttexalens.reg_access_common import set_verbose, get_regdef_file_type, get_regdef_family

# Logging functions
def log_stage(stage_name):
    print(f"\033[92m=== {stage_name} ===\033[0m")

class TestRegDefRealAccess(unittest.TestCase):
    def setUp(self):
        self.regdef_path = os.getenv('REGDEF')
        if not self.regdef_path:
            raise RuntimeError("REGDEF environment variable not set")
        if not os.path.exists(self.regdef_path):
            raise FileNotFoundError(f"Register definition file not found: {self.regdef_path}")

        # Choose appropriate loader based on file extension
        file_type = get_regdef_file_type(self.regdef_path)
        if file_type == 'json':
            self.RegisterMap = JsonRegisterMap
        elif file_type == 'yaml':
            self.RegisterMap = YamlRegisterMap
        else:
            self.skipTest(f"Unsupported file extension: {self.regdef_path}")

    def _test_access_patterns_common(self, init_jtag: bool, test_name: str):
        """Common test logic for both PCI and JTAG access patterns."""
        log_stage(f"{test_name}")

        # Initialize context with specified access method
        self.context = tt_exalens_init.init_ttexalens(
            wanted_devices=[0],
            cache_path=None,
            init_jtag=init_jtag,
            use_noc1=False
        )
        self.assertIsNotNone(self.context)

        # Create register map with verbose output and custom access functions
        set_verbose(True)
        if init_jtag:
            # TODO: Add JTAG access functions when available
            self.reg_map = self.RegisterMap(self.regdef_path,
                reg_read_func=self._jtag_arc_reg_read,
                reg_write_func=self._jtag_arc_reg_write
            )
        else:
            # Use PCI access functions
            self.reg_map = self.RegisterMap(
                self.regdef_path,
                reg_read_func=self._pci_arc_reg_read,
                reg_write_func=self._pci_arc_reg_write
            )

        # Verify register access requires explicit read/write
        family = get_regdef_family(self.regdef_path)
        if family == 'WH':
            reg = self.reg_map.ARC_RESET.SCRATCH[0]
        else:
            reg = self.reg_map.reset_unit.SCRATCH_0

        print(f"Value of ARC post code: 0x{reg.read():X}")

        # Assert that the upper 16 bits are 0xC0DE
        self.assertEqual(reg.read() & 0xFFFF0000, 0xC0DE0000)

    def _pci_arc_reg_read(self, addr: int) -> int:
        """Read ARC register using PCI->NOC->ARC."""
        device_id = 0
        arc_core_loc = self.context.devices[device_id].get_arc_block_location()
        print(f"arc_core_loc: {type(arc_core_loc)}")
        old_way_off_addr = self.context.devices[device_id].get_arc_register_addr('ARC_RESET_SCRATCH0')
        # Get the register address from the register map
        print(f"_pci_arc_reg_read:\n  old_way_off_addr: 0x{old_way_off_addr:X}\n  addr: 0x{addr:X}\n  arc_core_loc: {arc_core_loc}")
        value = self.context.server_ifc.pci_read32(device_id, *self.context.convert_loc_to_umd(arc_core_loc), addr)
        return value

    def _pci_arc_reg_write(self, addr: int, data: int) -> None:
        """Write ARC register using PCI->NOC->ARC."""
        device_id = 0
        print(f"Writing ARC register at address 0x{addr:X} with value 0x{data:X}")
        # Mask data to 64 bits before storing
        masked_data = data & 0xFFFFFFFFFFFFFFFF
        arc_core_loc = self.context.devices[device_id].get_arc_block_location()
        print(f"ARC core location: {arc_core_loc}")
        self.context.server_ifc.pci_write32(device_id, *self.context.convert_loc_to_umd(arc_core_loc), addr, masked_data)

    def _jtag_arc_reg_read(self, addr: int) -> int:
        """Read ARC register using JTAG->NOC->ARC."""
        device_id = 0
        arc_core_loc = self.context.devices[device_id].get_arc_block_location()
        print(f"arc_core_loc: {type(arc_core_loc)}")
        old_way_off_addr = self.context.devices[device_id].get_arc_register_addr('ARC_RESET_SCRATCH0')
        # Get the register address from the register map
        print(f"_jtag_arc_reg_read:\n  old_way_off_addr: 0x{old_way_off_addr:X}\n  addr: 0x{addr:X}\n  arc_core_loc: {arc_core_loc}")
        print(f"New addr: 0x{addr:X}")
        value = self.context.server_ifc.jtag_read32(device_id, *self.context.convert_loc_to_umd(arc_core_loc), addr)
        return value

    def _jtag_arc_reg_write(self, addr: int, data: int) -> None:
        """Write ARC register using JTAG->NOC->ARC."""
        device_id = 0
        print(f"Writing ARC register at address 0x{addr:X} with value 0x{data:X}")
        # Mask data to 64 bits before storing
        masked_data = data & 0xFFFFFFFFFFFFFFFF
        arc_core_loc = self.context.devices[device_id].get_arc_block_location()
        print(f"ARC core location: {arc_core_loc}")
        self.context.server_ifc.jtag_write32(device_id, *self.context.convert_loc_to_umd(arc_core_loc), addr, masked_data)

    # def test_access_patterns_pci(self):
    #     """Test register and field access patterns using PCI access."""
    #     self._test_access_patterns_common(init_jtag=False, test_name=self.test_access_patterns_pci.__doc__)

    def test_access_patterns_jtag(self):
        """Test register and field access patterns using JTAG access."""
        self._test_access_patterns_common(init_jtag=True, test_name=self.test_access_patterns_jtag.__doc__)

if __name__ == "__main__":
    unittest.main() 