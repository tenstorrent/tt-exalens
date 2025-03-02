# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class, parameterized
from ttexalens import tt_exalens_init
from ttexalens import tt_exalens_lib as lib

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_risc import RiscLoader, RiscDebug, RiscLoc, get_risc_name, get_risc_id


@parameterized_class(
    [
        # { "core_desc": "ETH0", "risc_name": "BRISC" },
        {"core_desc": "FW0", "risc_name": "BRISC"},
        {"core_desc": "FW0", "risc_name": "TRISC0"},
        {"core_desc": "FW0", "risc_name": "TRISC1"},
        {"core_desc": "FW0", "risc_name": "TRISC2"},
    ]
)
class TestCallStack(unittest.TestCase):
    risc_name: str = None  # Risc name
    risc_id: int = None  # Risc ID - being parametrized
    context: Context = None  # TTExaLens context
    core_desc: str = None  # Core description ETH0, FW0, FW1 - being parametrized
    core_loc: str = None  # Core location
    rdbg: RiscDebug = None  # RiscDebug object
    loader: RiscLoader = None  # RiscLoader object
    pc_register_index: int = None  # PC register index

    @classmethod
    def setUpClass(cls):
        cls.context = tt_exalens_init.init_ttexalens()

    def setUp(self):
        # Convert core_desc to core_loc
        if self.core_desc.startswith("ETH"):
            # Ask device for all ETH cores and get first one
            eth_cores = self.context.devices[0].get_block_locations(block_type="eth")
            core_index = int(self.core_desc[3:])
            if len(eth_cores) > core_index:
                self.core_loc = eth_cores[core_index].to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("ETH core is not available on this platform")
        elif self.core_desc.startswith("FW"):
            # Ask device for all ETH cores and get first one
            eth_cores = self.context.devices[0].get_block_locations(block_type="functional_workers")
            core_index = int(self.core_desc[2:])
            if len(eth_cores) > core_index:
                self.core_loc = eth_cores[core_index].to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("FW core is not available on this platform")
        else:
            self.fail(f"Unknown core description {self.core_desc}")

        loc = OnChipCoordinate.create(self.core_loc, device=self.context.devices[0])
        self.risc_id = get_risc_id(self.risc_name)
        rloc = RiscLoc(loc, 0, self.risc_id)
        self.rdbg = RiscDebug(rloc, self.context)
        self.loader = RiscLoader(self.rdbg, self.context)

        # Stop risc with reset
        self.rdbg.set_reset_signal(True)
        self.assertTrue(self.rdbg.is_in_reset())

    def tearDown(self):
        # Stop risc with reset
        self.rdbg.set_reset_signal(True)
        self.assertTrue(self.rdbg.is_in_reset())

    def is_blackhole(self):
        """Check if the device is blackhole."""
        return self.context.devices[0]._arch == "blackhole"

    def get_elf_path(self, app_name):
        """Get the path to the ELF file."""
        arch = self.context.devices[0]._arch.lower()
        if arch == "wormhole_b0":
            arch = "wormhole"
        risc = get_risc_name(self.risc_id).lower()
        return f"build/riscv-src/{arch}/{app_name}.{risc}.elf"

    @parameterized.expand([1, 10, 50])
    def test_callstack(self, recursion_count):
        lib.write_words_to_device(self.core_loc, 0x4000, recursion_count, 0, self.context)
        elf_path = self.get_elf_path("callstack")
        self.loader.run_elf(elf_path)
        callstack = self.loader.get_callstack(elf_path)
        self.assertEqual(len(callstack), recursion_count + 3)
        self.assertEqual(callstack[0].function_name, "halt")
        for i in range(1, recursion_count + 1):
            self.assertEqual(callstack[i].function_name, "f1")
        self.assertEqual(callstack[recursion_count + 1].function_name, "recurse")
        self.assertEqual(callstack[recursion_count + 2].function_name, "main")

    @parameterized.expand([(1, 1), (10, 9), (50, 49)])
    def test_callstack_optimized(self, recursion_count, expected_f1_on_callstack_count):
        lib.write_words_to_device(self.core_loc, 0x4000, recursion_count, 0, self.context)
        elf_path = self.get_elf_path("callstack.optimized")
        self.loader.run_elf(elf_path)
        callstack = self.loader.get_callstack(elf_path)

        # Optimized version for non-blackhole doesn't have halt on callstack
        if self.is_blackhole():
            if recursion_count == 1:
                self.assertEqual(len(callstack), expected_f1_on_callstack_count + 3)
                self.assertEqual(callstack[0].function_name, "halt")
                for i in range(1, expected_f1_on_callstack_count + 1):
                    self.assertEqual(callstack[i].function_name, "f1")
                self.assertEqual(callstack[expected_f1_on_callstack_count + 1].function_name, "recurse")
                self.assertEqual(callstack[expected_f1_on_callstack_count + 2].function_name, "main")
            else:
                self.assertEqual(len(callstack), expected_f1_on_callstack_count + 4)
                self.assertEqual(callstack[0].function_name, "halt")
                for i in range(1, expected_f1_on_callstack_count + 2):
                    self.assertEqual(callstack[i].function_name, "f1")
                self.assertEqual(callstack[expected_f1_on_callstack_count + 2].function_name, "recurse")
                self.assertEqual(callstack[expected_f1_on_callstack_count + 3].function_name, "main")
        else:
            self.assertEqual(len(callstack), expected_f1_on_callstack_count + 2)
            for i in range(0, expected_f1_on_callstack_count):
                self.assertEqual(callstack[i].function_name, "f1")
            self.assertEqual(callstack[expected_f1_on_callstack_count + 0].function_name, "recurse")
            self.assertEqual(callstack[expected_f1_on_callstack_count + 1].function_name, "main")
