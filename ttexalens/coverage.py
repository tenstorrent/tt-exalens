# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

import shutil
import tempfile
from pathlib import Path

from ttexalens import util
from ttexalens.tt_exalens_lib import read_word_from_device, read_from_device, parse_elf, check_context
from ttexalens.tt_exalens_lib import TTException, ParsedElfFile
from ttexalens.context import Context

"""
Extract the coverage data from the device into a .gcda file.
Optionally get the gcno path from struct gcov_info from the ELF
and copy it to the specified output path.

Note that the ELF is needed for knowing the offset in L1 where coverage data resides and
for finding the gcno. As the L1 offset is the same for all ELFs for a given baby RISC core
on a given architecture, this script can be adjusted to take the arch and RISC type instead
of the ELF, should that be necessary. That is, however, less flexible, as it requires
hardcoding offsets, which would break in case of linker script changes.
"""

def dump_coverage(
    core_loc: str, elf_path: Path, gcda_path: Path, gcno_copy_path: Path | None = None, context: Context | None = None
) -> None:
    context = check_context(context)
    elf = parse_elf(str(elf_path), context)

    #util.INFO(f"1: {core_loc} 2: {elf_path} 3: {gcda_path} 4: {gcno_copy_path} 5: {context}")
    # Coverage region layout:
    # The first word at the __coverage_start symbol tells us the length of the whole segment.
    # The second word is a pointer to the filename, which we use to reach the gcno, if required.
    # The third is the length of the filename string.
    # Onward, it's *__coverage_start - 12 bytes of data.
    coverage_start = elf.symbols["__coverage_start"].value
    if not coverage_start:
        raise TTException("__coverage_start not found")

    length = read_word_from_device(core_loc, addr=coverage_start, context=context)

    # 0xDEADBEEF will be written in place of length if overflow occurred.
    if length == 0xDEADBEEF:
        raise TTException("Coverage region overflowed")

    if gcno_copy_path:
        filename_addr = read_word_from_device(core_loc, addr=coverage_start+4, context=context)
        filename_len = read_word_from_device(core_loc, addr=coverage_start+8, context=context)
        filename: str = read_from_device(core_loc, filename_addr, num_bytes=filename_len, context=context).decode("ascii")
        # This points to the expected gcda file, but it's in the same directory where the compiler placed the gcno,
        # so we just replace the extension and get the gcno path.
        gcno_path = filename[:-4] + "gcno"
        if not Path.exists(Path(gcno_path).resolve()):
            # Warn, but don't raise; we still extract the gcda.
            util.WARN(f"{gcno_path}: file does not exist")
        shutil.copy2(gcno_path, gcno_copy_path)

    data = read_from_device(core_loc, coverage_start+12, num_bytes=length-12, context=context)
    with open(gcda_path, "wb") as f:
        f.write(data)
