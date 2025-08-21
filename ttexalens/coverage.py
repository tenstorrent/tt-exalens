# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

import shutil
from pathlib import Path
import subprocess

from ttexalens.tt_exalens_lib import read_word_from_device, read_from_device
from ttexalens.tt_exalens_lib import parse_elf
from ttexalens.tt_exalens_lib import TTException
from ttexalens.tt_exalens_lib import ParsedElfFile

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


from pathlib import Path
from ttexalens.tt_exalens_lib import TTException, parse_elf

from pathlib import Path
from ttexalens.tt_exalens_lib import TTException, parse_elf, ParsedElfFile

from pathlib import Path
from ttexalens.tt_exalens_lib import TTException, parse_elf, ParsedElfFile

def find_gcno(elf: ParsedElfFile) -> Path:
    """
    Look for the .gcda path in the ELF's .ldm_data section,
    then find the corresponding .gcno in the same directory.
    """

    # GCC's struct gcov_info is in .ldm_data, and it contains
    # the expected gcda path, which is where the gcno is also found.
    # We need to parse the strings in that section and find it.

    ldm_section = elf.elf.get_section_by_name(".ldm_data")
    if not ldm_section:
        raise TTException(".ldm_data section not found in ELF")

    # Read the raw bytes of the section.
    data = ldm_section.data()
    # Convert to string and split on null bytes.
    strings = []
    current = bytearray()
    for b in data:
        if b == 0:
            if current:
                try:
                    strings.append(current.decode("ascii"))
                except UnicodeDecodeError:
                    pass  # skip non-ASCII
                current.clear()
        else:
            current.append(b)

    # Look for something ending with gcda.
    gcda_paths = [Path(s) for s in strings if s.endswith(".gcda")]
    if not gcda_paths:
        raise TTException(f"Could not find .gcda in .ldm_data; tried: {strings}")

    # Take the first gcda path found.
    gcda_path = gcda_paths[0]
    gcno_path = gcda_path.with_suffix(".gcno")

    if not gcno_path.exists():
        raise TTException(f"Expected .gcno not found: {gcno_path}")

    return gcno_path

def dump_coverage(context, core_loc: str, elf_path: Path, outdir: Path, gcno: Path | None = None) -> None:

    if not elf_path.exists():
        raise TTException(f"{elf_path} does not exist")
    elf = parse_elf(str(elf_path))

    if gcno:
        if not gcno.exists():
            raise TTException(f"{gcno} does not exist")
    else:
        gcno = find_gcno(elf)

    # The first uint32_t at the __coverage_start symbol tells us the number of bytes that should be read.
    length_addr = elf.symbols["__coverage_start"].value
    if not length_addr:
        raise TTException("__coverage_start not found")
    data_addr = length_addr + 4 # Actual data starts right after the length.

    length = read_word_from_device(core_loc, addr=length_addr, context=context)

    # 0xDEADBEEF will be written in place of the length if overflow occurred.
    if length == 0xDEADBEEF:
        raise TTException("Coverage region overflowed")

    data = read_from_device(core_loc, data_addr, num_bytes=length, context=context)

    outdir.mkdir(parents=True, exist_ok=True)
    basename = elf_path.stem
    gcda_path = outdir / f"{basename}.gcda"
    gcno_copy_path = outdir / f"{basename}.gcno"

    shutil.copy2(gcno, gcno_copy_path)
    with open(gcda_path, "wb") as f:
        f.write(data)
