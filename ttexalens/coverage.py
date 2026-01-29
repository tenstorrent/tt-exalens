# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.exceptions import TTException
from ttexalens.elf import ParsedElfFile
from ttexalens.memory_access import MemoryAccess

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
    elf: ParsedElfFile,
    location: OnChipCoordinate,
    gcda_path: str,
    gcno_copy_path: str | None = None,
) -> None:

    # Find coverage region in ELF.
    coverage_start = elf.symbols["__coverage_start"].value
    if not coverage_start:
        raise TTException("__coverage_start not found")
    coverage_end = elf.symbols["__coverage_end"].value
    if not coverage_end:
        raise TTException("__coverage_end not found")

    # Find coverage header in device memory.
    coverage_header = elf.get_global("coverage_header", MemoryAccess.create_l1(location))
    if coverage_header is None:
        raise TTException("coverage_header not found")
    coverage_header = coverage_header.dereference()
    if coverage_header.get_address() != coverage_start:
        raise TTException("coverage_header address does not match __coverage_start")

    # Check magic number.
    magic_number = elf.get_constant("COVERAGE_MAGIC_NUMBER")
    if magic_number is None or coverage_header.magic_number != magic_number:
        raise TTException("COVERAGE_MAGIC_NUMBER not found in ELF")

    header_size = coverage_header.get_size()
    length = coverage_header.bytes_written

    # 0xDEADBEEF will be written in place of length if overflow occurred.
    if length == 0xDEADBEEF:
        raise TTException("Coverage region overflowed")
    if length > coverage_end - coverage_start:
        raise TTException("Coverage length is larger than coverage region")
    if length < header_size:
        raise TTException("Kernel did not finish writing coverage data")

    if gcno_copy_path:
        filename_len = coverage_header.filename_length.read_value()
        assert isinstance(filename_len, int)
        filename_addr = coverage_header.filename.dereference().get_address()
        filename: str = location.noc_read(filename_addr, filename_len).decode("ascii")

        # This points to the expected gcda file, which is in the same directory where the compiler placed the gcno,
        # so we just replace the extension and get the gcno path.
        # We fetch it through context.file_api.get_binary in case this is a remote debugging session.
        gcno_path = filename[:-4] + "gcno"
        with location.context.file_api.get_binary(gcno_path) as gcno_reader:
            with open(gcno_copy_path, "wb") as f:
                f.write(gcno_reader.read())

    data = location.noc_read(coverage_start + header_size, length - header_size)
    with open(gcda_path, "wb") as f:
        f.write(data)
