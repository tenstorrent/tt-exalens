# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

import shutil
from pathlib import Path
import subprocess

from ttexalens.tt_exalens_lib import read_words_from_device, read_from_device
from ttexalens.tt_exalens_lib import parse_elf
from ttexalens.tt_exalens_lib import TTException

"""
Extract the coverage data from the device into a .gcda file,
and find and copy its .gcno there such that it has the same name.
Debug info is parsed from the passed ELF to get the gcno.

You can supply the optional gcno argument, in which case debug info is not parsed.

Note that the ELF is needed for knowing the offset in L1 where coverage data resides and
for finding the gcno. As the L1 offset is the same for all ELFs for a given baby RISC core
on a given architecture, this script can be adjusted to take the arch and RISC type instead
of the ELF, should that be necessary. That is, however, less flexible, as it requires
hardcoding offsets, which would break in case of linker script changes.
"""


def find_gcno(elf_path: Path) -> Path:
    """
    Call strings and skim through its output for a .gcda path.
    Raise on failure.
    """
    try:
        res = subprocess.run(["strings", str(elf_path)], capture_output=True, text=True, check=True)
    except Exception as e:
        raise TTException(f"On strings invocation: {e}")

    gcda_paths = [line.strip() for line in res.stdout.splitlines() if line.strip().endswith(".gcda")]

    for gcda in gcda_paths:
        gcno = Path(gcda[:-4] + "gcno")
        if gcno.exists():
            return gcno

    raise TTException("Could not find gcno from debuginfo")


def dump_coverage(context, core_loc: str, elf_path: Path, outdir: Path, gcno: Path | None = None) -> None:

    if not elf_path.exists():
        raise TTException(f"{elf_path} does not exist")

    if gcno:
        if not gcno.exists():
            raise TTException(f"{gcno} does not exist")
    else:
        gcno_path = find_gcno(elf_path)

    elf = parse_elf(str(elf_path))
    length_addr = elf.symbols["__coverage_start"].value
    if not length_addr:
        raise TTException("__coverage_start not found")
    data_addr = length_addr + 4

    length = read_words_from_device(core_loc, addr=length_addr, word_count=1, context=context)
    n = length[0]

    if n == 0xDEADBEEF:
        raise TTException("Coverage region overflowed")

    data = read_from_device(core_loc, data_addr, num_bytes=n, context=context)

    outdir.mkdir(parents=True, exist_ok=True)
    basename = elf_path.stem
    gcda_path = outdir / f"{basename}.gcda"
    gcno_copy_path = outdir / f"{basename}.gcno"

    shutil.copy2(gcno_path, gcno_copy_path)
    with open(gcda_path, "wb") as f:
        f.write(data)
