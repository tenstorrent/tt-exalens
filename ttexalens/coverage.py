# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.tt_exalens_lib import read_word_from_device, read_from_device
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
    context: Context, elf: ParsedElfFile, device: Device, location: OnChipCoordinate, gcda_path: Path, gcno_copy_path: Path | None = None
) -> None:
    
    # Coverage region layout:
    # The first word at the __coverage_start symbol tells us the length of the whole segment.
    # The second word is a pointer to the filename, which we use to reach the gcno, if required.
    # The third is the length of the filename string.
    # Onward, it's *__coverage_start - 12 bytes of data.
    coverage_start = elf.symbols["__coverage_start"].value
    if not coverage_start:
        raise TTException("__coverage_start not found")

    length = read_word_from_device(location, addr=coverage_start, context=context, device_id=device._id)

    # 0xDEADBEEF will be written in place of length if overflow occurred.
    if length == 0xDEADBEEF:
        raise TTException("Coverage region overflowed")

    if gcno_copy_path:
        filename_addr = read_word_from_device(location, addr=coverage_start+4, context=context, device_id=device._id)
        filename_len = read_word_from_device(location, addr=coverage_start+8, context=context, device_id=device._id)
        filename: str = read_from_device(location, filename_addr, num_bytes=filename_len, context=context, device_id=device._id).decode("ascii")
        # This points to the expected gcda file, which is in the same directory where the compiler placed the gcno,
        # so we just replace the extension and get the gcno path.
        # We fetch it through context.server_ifc.get_binary in case this is a remote debugging session.
        gcno_path = filename[:-4] + "gcno"
        with context.server_ifc.get_binary(gcno_path) as gcno_reader:
            with open(gcno_copy_path, "wb") as f:
                f.write(gcno_reader.read())

    data = read_from_device(location, coverage_start+12, num_bytes=length-12, context=context, device_id=device._id)
    with open(gcda_path, "wb") as f:
        f.write(data)
