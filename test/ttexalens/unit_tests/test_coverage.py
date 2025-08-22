# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
import unittest
from test.ttexalens.unit_tests.test_base import init_default_test_context

import tempfile
from pathlib import Path

from ttexalens.context import Context
from ttexalens.tt_exalens_lib import run_elf
from ttexalens.coverage import dump_coverage

RISC_NAMES = ["brisc", "trisc0", "trisc1", "trisc2", "ncrisc"]
BASE_NAMES = ["run_elf_test.coverage", "cov_test.coverage"] # We only run ELFs that don't halt.

class TestCoverage(unittest.TestCase):
    context: Context
    elf_root: Path
    core_loc: str = "0,0"

    def setUp(self):
        self.context = init_default_test_context()

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

    def test_coverage(self):
        with tempfile.TemporaryDirectory(prefix = "cov_test_") as temp:
            temp_root = Path(temp)
            
            for risc in RISC_NAMES:
                for base in BASE_NAMES:
                    # Run the ELF and save its coverage data.
                    elf_path = self.elf_root / f"{base}.{risc}.elf"
                    run_elf(str(elf_path), self.core_loc, risc, context=self.context)
                    dump_coverage(self.core_loc, elf_path, temp_root, context=self.context)

                    # Check if the files match expectations.
                    basename = elf_path.stem
                    gcda = temp_root / f"{basename}.gcda"
                    gcno = temp_root / f"{basename}.gcno"

                    self.assertTrue(gcda.exists(), f"{gcda}: file does not exist")
                    self.assertTrue(gcno.exists(), f"{gcno}: file does not exist")

                    gcda_bytes = gcda.read_bytes()
                    gcno_bytes = gcno.read_bytes()

                    # First four bytes of gcno and gcda contain their magic numbers.
                    # In little-endian:
                    # 6F6E6367 = "gcno"
                    # 61646367 = "gcda"
                    self.assertEqual(gcno_bytes[0:4], bytes.fromhex("6F6E6367"), "f{gcno}: incorrect magic")
                    self.assertEqual(gcda_bytes[0:4], bytes.fromhex("61646367"), "f{gcda}: incorrect magic")

                    # Test if versions match.
                    self.assertEqual(gcda_bytes[4:8], gcno_bytes[4:8], f"{gcda}: version mismatch with {gcno}")

                    # Most important test: checksum. It's very unlikely that a gcda is malformed if its checksum matches the gcno.
                    self.assertEqual(gcda_bytes[8:12], gcno_bytes[8:12], f"{gcda}: checksum mismatch with {gcno}")
