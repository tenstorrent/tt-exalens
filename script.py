# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.tt_exalens_init import init_ttexalens

context = init_ttexalens()
device = context.devices[0]
noc_block = device.get_block(device.get_block_locations(block_type="functional_workers")[0])
risc_debug = noc_block.get_risc_debug("brisc")

addr = 0x10000
noc_addr = risc_debug.baby_risc_info.l1.translate_to_noc_address(addr)
assert noc_addr is not None, "Translated NOC address should not be None."

# Write our data to memory
self.core_sim.write_data_checked(noc_addr, 0x12345678)

# Write code for brisc core at address 0
# C++:
#   while (true);
self.program_writer.append_while_true()
self.program_writer.write_program()

# Take risc out of reset
self.core_sim.set_reset(False)
self.assertFalse(self.core_sim.is_in_reset())

# Halt core
self.core_sim.halt()

# Value should not be changed and should stay the same since core is in halt
self.assertTrue(self.core_sim.is_halted(), "Core should be halted.")

# Test read and write memory
self.assertEqual(self.core_sim.risc_debug.read_memory(addr), 0x12345678, "Memory value should be 0x12345678.")
self.core_sim.risc_debug.write_memory(addr, 0x87654321)
self.assertEqual(self.core_sim.risc_debug.read_memory(addr), 0x87654321, "Memory value should be 0x87654321.")
self.assertEqual(self.core_sim.read_data(noc_addr), 0x87654321, "Memory value read over NOC should be 0x87654321.")
