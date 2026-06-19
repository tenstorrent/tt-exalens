# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
import unittest
from test.ttexalens.unit_tests.test_base import get_parsed_elf_file, init_cached_test_context
from parameterized import parameterized, parameterized_class

import os
import struct
import tempfile

from ttexalens import Context, OnChipCoordinate, Device, TTException
from ttexalens.elf_loader import ElfLoader
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.coverage import dump_coverage

ELFS = ["run_elf_test.coverage", "cov_test.coverage"]  # We only run ELFs that don't halt.

# gcda record tags (see GCC's gcov-io.h).
GCOV_TAG_FUNCTION = 0x01000000
GCOV_TAG_COUNTER_BASE = 0x01A10000


def summarize_gcda(data: bytes) -> tuple[int, int, int]:
    """Walk a gcda byte stream and return (function_records, counters, nonzero_counters).

    The stream (as written on-device by libgcov's __gcov_info_to_gcda) is a 16-byte
    header (magic, version, stamp, checksum) followed by tag/length records. Each
    record is a 4-byte tag, a 4-byte length in bytes, and that many body bytes. Counter
    records use a negative length when every counter is zero (the body is then omitted).
    """

    def is_counter_tag(tag: int) -> bool:
        # GCOV_TAG_FOR_COUNTER(n) == GCOV_TAG_COUNTER_BASE + (n << 17), low 16 bits zero.
        return GCOV_TAG_COUNTER_BASE <= tag < 0x02000000 and (tag & 0xFFFF) == 0

    functions = counters = nonzero = 0
    off, end = 16, len(data)
    while off + 4 <= end:
        (tag,) = struct.unpack_from("<I", data, off)
        off += 4
        if tag == 0:  # trailing terminator, if present
            break
        (length,) = struct.unpack_from("<I", data, off)
        off += 4
        slen = length - 0x100000000 if length & 0x80000000 else length  # length is signed
        if tag == GCOV_TAG_FUNCTION:
            functions += 1
            off += slen  # 12-byte body, or 0 for a function not in this TU
        elif is_counter_tag(tag):
            if slen < 0:
                counters += (-slen) // 8  # all-zero counters: body omitted
            else:
                count = slen // 8  # each counter is a 64-bit value (two words)
                counters += count
                for i in range(count):
                    lo, hi = struct.unpack_from("<II", data, off + i * 8)
                    if lo or hi:
                        nonzero += 1
                off += slen
        else:
            off += slen  # skip any other record by its length
    return functions, counters, nonzero


@parameterized_class(
    [
        {"core_desc": "ETH0", "risc_name": "ERISC"},
        {"core_desc": "ETH0", "risc_name": "ERISC0"},
        {"core_desc": "ETH0", "risc_name": "ERISC1"},
        {"core_desc": "FW0", "risc_name": "BRISC"},
        {"core_desc": "FW0", "risc_name": "TRISC0"},
        {"core_desc": "FW0", "risc_name": "TRISC1"},
        {"core_desc": "FW0", "risc_name": "TRISC2"},
        {"core_desc": "FW0", "risc_name": "NCRISC"},
    ]
)
class TestCoverage(unittest.TestCase):
    context: Context
    elf_root: str
    risc_name: str
    risc_id: str
    core_desc: str
    location: OnChipCoordinate
    device: Device
    loader: ElfLoader
    risc_debug: RiscDebug

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

    def setUp(self):
        # Arch is needed to know the ELF path
        if not self.device._arch:
            self.skipTest(f"Undefined architecture")
        arch = str(self.device._arch).lower()
        if arch.startswith("wormhole"):
            arch = "wormhole"
        elif arch.startswith("blackhole"):
            arch = "blackhole"
        else:
            self.skipTest(f"Unsupported architecture: {arch}")

        self.elf_root = "build/riscv-src/" + arch + "/"

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
            fw_cores = self.device.get_block_locations(block_type="functional_workers")
            core_index = int(self.core_desc[2:])
            if len(fw_cores) > core_index:
                self.core_loc = fw_cores[core_index].to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("FW core is not available on this platform")
        else:
            self.fail(f"Unknown core description {self.core_desc}")

        self.location = OnChipCoordinate.create(self.core_loc, device=self.device)
        noc_block = self.location.device.get_block(self.location)
        try:
            self.risc_debug = noc_block.get_risc_debug(self.risc_name)
        except ValueError:
            self.skipTest(f"{self.risc_name} core is not available in this block on this platform")

        self.loader = ElfLoader(self.risc_debug)

    def get_elf_name(self, elf: str):
        return os.path.join(self.elf_root, f"{elf}.{self.risc_name.lower()}.elf")

    def test_no_coverage(self):
        elf_path = self.get_elf_name("callstack.release")
        elf = get_parsed_elf_file(elf_path)
        self.loader.run_elf(elf)
        with self.assertRaises(TTException) as cm:
            dump_coverage(elf, self.location, "/tmp/callstack.release.gcda", "/tmp/callstack.release.gcno")
            self.assertIn("__coverage_start not found", str(cm.exception))

    def test_coverage_not_finished(self):
        elf_path = self.get_elf_name("callstack.coverage")
        elf = get_parsed_elf_file(elf_path)
        self.loader.run_elf(elf)
        with self.assertRaises(TTException) as cm:
            dump_coverage(elf, self.location, "/tmp/callstack.release.gcda", "/tmp/callstack.release.gcno")
            self.assertIn("Kernel did not finish writing coverage data", str(cm.exception))

    @parameterized.expand(ELFS)
    def test_coverage(self, elf):
        with tempfile.TemporaryDirectory(prefix="cov_test_") as temp_root:

            # Run the ELF and save its coverage data.
            elf_path = self.get_elf_name(elf)
            elf = get_parsed_elf_file(elf_path)
            self.loader.run_elf(elf)

            basename, _ = os.path.splitext(os.path.basename(elf_path))
            gcda = os.path.join(temp_root, f"{basename}.gcda")
            gcno = os.path.join(temp_root, f"{basename}.gcno")

            dump_coverage(elf, self.location, gcda, gcno)

            # Check if the files match expectations: if they exist, and if the headers are well-formed.
            self.assertTrue(os.path.exists(gcda), f"{gcda}: file does not exist")
            self.assertTrue(os.path.exists(gcno), f"{gcno}: file does not exist")

            with open(gcda, "rb") as f:
                gcda_bytes = f.read()
            with open(gcno, "rb") as f:
                gcno_bytes = f.read()
            gcda_header = gcda_bytes[:16]
            gcno_header = gcno_bytes[:16]

            # First four bytes of gcno and gcda contain their magic numbers (mind the endianness).
            self.assertEqual(gcno_header[0:4], b"oncg", f"{gcno}: incorrect magic")
            self.assertEqual(gcda_header[0:4], b"adcg", f"{gcda}: incorrect magic")

            # Versions (bytes 4:8) must match. The gcda version is emitted by the
            # compiler-shipped libgcov and the gcno version by the same compiler, so the
            # two stay in lockstep across SFPI bumps (no hand-maintained constant).
            self.assertEqual(gcda_header[4:8], gcno_header[4:8], f"{gcda}: version mismatch with {gcno}")

            # The stamp (bytes 8:12) uniquely identifies a compilation; a matching stamp
            # means this gcda was produced from exactly this gcno.
            self.assertEqual(gcda_header[8:12], gcno_header[8:12], f"{gcda}: stamp mismatch with {gcno}")

            # Validate the gcda actually carries coverage: at least one function record and
            # at least one counter that was incremented while the kernel ran. Both ELFs
            # execute a main(), so its entry counter must be non-zero.
            functions, counters, nonzero = summarize_gcda(gcda_bytes)
            self.assertGreater(functions, 0, f"{gcda}: no function records in coverage data")
            self.assertGreater(counters, 0, f"{gcda}: no counters in coverage data")
            self.assertGreater(nonzero, 0, f"{gcda}: all counters are zero - kernel produced no coverage")
