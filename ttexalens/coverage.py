# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import TTException
from ttexalens.elf import ElfFile
from ttexalens.memory_access import create_l1_memory_access

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
    elf: ElfFile,
    location: OnChipCoordinate,
    gcda_path: str,
    gcno_copy_path: str | None = None,
) -> None:

    # Find coverage region in ELF.
    start_sym = elf.find_symbol_by_name("__coverage_start")
    if start_sym is None or not start_sym.value:
        raise TTException("__coverage_start not found")
    coverage_start = start_sym.value
    end_sym = elf.find_symbol_by_name("__coverage_end")
    if end_sym is None or not end_sym.value:
        raise TTException("__coverage_end not found")
    coverage_end = end_sym.value

    # Find coverage header in device memory.
    coverage_header = elf.get_global("coverage_header", create_l1_memory_access(location))
    coverage_header = coverage_header.dereference()
    if coverage_header.get_address() != coverage_start:
        raise TTException("coverage_header address does not match __coverage_start")

    # Check magic number.
    magic_number = elf.get_constant("COVERAGE_MAGIC_NUMBER")
    if coverage_header.magic_number != magic_number:
        raise TTException("COVERAGE_MAGIC_NUMBER does not match in ELF")

    header_size = coverage_header.get_size()
    length = int(coverage_header.bytes_written)

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
        filename_buffer = bytearray(filename_len)
        location.noc_read(filename_addr, filename_buffer)
        filename: str = filename_buffer.decode("ascii")

        # This points to the expected gcda file, which is in the same directory where the compiler placed the gcno,
        # so we just replace the extension and get the gcno path.
        # We fetch it through context.file_api.get_binary in case this is a remote debugging session.
        gcno_path = filename[:-4] + "gcno"
        with location.context.file_api.get_binary(gcno_path) as gcno_reader:
            with open(gcno_copy_path, "wb") as f:
                f.write(gcno_reader.read())

    data = bytearray(length - header_size)
    location.noc_read(coverage_start + header_size, data)
    with open(gcda_path, "wb") as f:
        f.write(data)
