# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
import unittest
from test.ttexalens.unit_tests.test_base import init_default_test_context
from parameterized import parameterized, parameterized_class

import tempfile
import itertools
from pathlib import Path

from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.elf_loader import ElfLoader
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.tt_exalens_lib import run_elf
from ttexalens.coverage import dump_coverage

ELFS = ["run_elf_test.coverage", "cov_test.coverage"] # We only run ELFs that don't halt.

@parameterized_class(
    [
        # {"core_desc": "ETH0", "risc_name": "ERISC"},
        # {"core_desc": "ETH0", "risc_name": "ERISC0"},
        # {"core_desc": "ETH0", "risc_name": "ERISC1"},
        {"core_desc": "FW0", "risc_name": "BRISC"},
        {"core_desc": "FW0", "risc_name": "TRISC0"},
        {"core_desc": "FW0", "risc_name": "TRISC1"},
        {"core_desc": "FW0", "risc_name": "TRISC2"},
        {"core_desc": "FW0", "risc_name": "NCRISC"}
    ]
)
class TestCoverage(unittest.TestCase):
    context: Context
    elf_root: Path
    risc_name: str
    risc_id: str
    core_desc: str
    location: OnChipCoordinate
    device: Device
    loader: ElfLoader
    risc_debug: RiscDebug

    def setUp(self):
        self.context = init_default_test_context()
        self.device = self.context.devices[0]

        # Arch is needed to know the ELF path
        if not self.context.arch:
            self.skipTest(f"Undefined architecture")
        if self.context.arch.startswith("wormhole"):
            arch = "wormhole"
        elif self.context.arch.startswith("blackhole"):
            arch = "blackhole"
        else:
            self.skipTest(f"Unsupported architecture: {self.context.arch}")

        self.elf_root = Path("build/riscv-src/") / arch

        # Convert core_desc to core_loc
        if self.core_desc.startswith("ETH"):
            # Ask device for all ETH cores and get first one
            eth_blocks = self.device.idle_eth_blocks
            core_index = int(self.core_desc[3:])
            if len(eth_blocks) > core_index:
                self.core_loc = eth_blocks[core_index].location.to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("ETH core is not available on this platform")
        elif self.core_desc.startswith("FW"):
            # Ask device for all ETH cores and get first one
            eth_cores = self.device.get_block_locations(block_type="functional_workers")
            core_index = int(self.core_desc[2:])
            if len(eth_cores) > core_index:
                self.core_loc = eth_cores[core_index].to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("FW core is not available on this platform")
        else:
            self.fail(f"Unknown core description {self.core_desc}")
        
        self.location = OnChipCoordinate.create(self.core_loc, device=self.device)
        noc_block = self.location._device.get_block(self.location)
        try:
            self.risc_debug = noc_block.get_risc_debug(self.risc_name)
        except ValueError as e:
            self.skipTest(f"{self.risc_name} core is not available in this block on this platform")

        self.loader = ElfLoader(self.risc_debug)

    def get_elf_name(self, elf: str):
        # We can use BRISC elf for ERISCs
        if self.risc_name.lower().startswith("erisc"):
            return f"{elf}.brisc.elf"
        else:
            return f"{elf}.{self.risc_name.lower()}.elf"


    @parameterized.expand(ELFS)
    def test_coverage(self, elf):
        with tempfile.TemporaryDirectory(prefix = "cov_test_") as temp:
            temp_root = Path(temp)
            
            # Run the ELF and save its coverage data.
            elf_path = self.elf_root / self.get_elf_name(elf)
            self.loader.run_elf(str(elf_path))
            basename = elf_path.stem
            gcda = temp_root / f"{basename}.gcda"
            gcno = temp_root / f"{basename}.gcno"

            dump_coverage(elf_path, self.device, self.location, gcda, gcno, context=self.context)

            # Check if the files match expectations.
            self.assertTrue(gcda.exists(), f"{gcda}: file does not exist")
            self.assertTrue(gcno.exists(), f"{gcno}: file does not exist")

            gcda_bytes = gcda.read_bytes()
            gcno_bytes = gcno.read_bytes()

            # First four bytes of gcno and gcda contain their magic numbers (mind the endianness).
            self.assertEqual(gcno_bytes[0:4], b"oncg", "f{gcno}: incorrect magic")
            self.assertEqual(gcda_bytes[0:4], b"adcg", "f{gcda}: incorrect magic")

            # Test if versions match.
            self.assertEqual(gcda_bytes[4:8], gcno_bytes[4:8], f"{gcda}: version mismatch with {gcno}")

            # Most important test: checksum. It's very unlikely that a gcda is malformed if its checksum matches the gcno.
            self.assertEqual(gcda_bytes[8:12], gcno_bytes[8:12], f"{gcda}: checksum mismatch with {gcno}")
