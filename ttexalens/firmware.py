# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
This module is used to represent the firmware
"""

import time
from typing import Callable
from ttexalens.elf import ParsedElfFile, read_elf
from ttexalens import util as util

import re
from fuzzywuzzy import process, fuzz
from sys import getsizeof

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.risc_debug import RiscDebug


class FAKE_DIE(object):
    """
    Some pointers are hard-coded in the source with #defines. These names do not make
    it to the DWARF info. We add them here. To keep the rest of code consistent, we create
    fake DIEs for these names, with minimal required configuration.
    """

    def __init__(self, var_name, addr, resolved_type):
        self.name = var_name
        self.address = addr
        self.resolved_type = resolved_type
        self.size = self.resolved_type.size
        self.value = None


class ELF:
    """
    This class wraps around a list of ELF files and provides a unified interface to them.
    """

    def __init__(self, file_ifc, filemap, extra_vars=None) -> None:
        """
        Given a filemap "prefix" -> "filename", load all the ELF files and store them in
        self.names. For example, if filemap is { "brisc" : "./build/riscv-src/wormhole/sample.brisc.elf" },
        the parsed content of "./build/riscv-src/wormhole/sample.brisc.elf" will be stored in self.names["brisc"].
        """
        self.names: dict[str, ParsedElfFile] = dict()
        self.filemap = filemap
        self._file_ifc = file_ifc
        self.name_word_pattern = re.compile(r"[_@.a-zA-Z]+")
        for prefix, filename in filemap.items():
            util.INFO(f"Loading ELF file: '{filename}'", end="")
            start_time = time.time()
            self.names[prefix] = read_elf(self._file_ifc, filename)
            util.INFO(f" ({getsizeof(self.names[prefix])} bytes loaded in {time.time() - start_time:.2f}s)")

            # Inject the variables that are not in the ELF
            if extra_vars:
                self._process_extra_vars(prefix, extra_vars)

    def _process_extra_vars(self, prefix, extra_vars):
        """
        Given a prefix, inject the variables that are not in the ELF
        """
        for var_name, var in extra_vars.items():
            if var_name in self.names[prefix].variables:
                util.INFO(f"Variable '{var_name}' already in ELF. Skipping")
                continue
            offset_var = var["offset"]
            if offset_var not in self.names[prefix].variables:
                raise util.TTException(f"Variable '{offset_var}' not found in ELF. Cannot add '{var_name}'")
            ov = self.names[prefix].variables[offset_var]
            addr = addr = ov.value if ov.value else ov.address
            resolved_type = self.names[prefix].types[var["type"]].resolved_type
            self.names[prefix].variables[var_name] = FAKE_DIE(var_name, addr=addr, resolved_type=resolved_type)

    def _get_prefix_and_suffix(self, path_str) -> tuple[str, str]:
        dot_pos = path_str.find(".")
        if dot_pos == -1:
            return "", path_str  # just the suffix
        return path_str[:dot_pos], path_str[dot_pos + 1 :]

    def fuzzy_find_multiple(self, path, limit):
        """
        Given a path, return a list of all symbols that match the path. This is used for auto-completion.
        """
        at_prefix = False
        if path.startswith("@"):
            path = path[1:]
            at_prefix = True
        elf_name, suffix = self._get_prefix_and_suffix(path)

        if elf_name not in self.names:
            elf = None
            choices = self.names.keys()
        else:
            elf = self.names[elf_name]
            choices = elf.variables.keys()

        # Uses Levenshtein distance to find the best match for a query in a list of keys
        matches = process.extract(suffix, choices, scorer=fuzz.QRatio, limit=limit)

        sorted_matches = sorted(matches, key=lambda x: x[1], reverse=True)

        if elf:
            filtered_matches = [f"{'@' if at_prefix else ''}{elf_name}.{match}" for match, score in sorted_matches]
        else:
            filtered_matches = [match for match, score in sorted_matches]
        return filtered_matches

    def get_enum_mapping(self, enum_path):
        """
        Given a path, return the enum mapping for it. Example: get_enum_mapping("erisc_app.epoch_queue.EpochQueueCmd")
        will return a dict of {1: "EpochCmdValid", 2: "EpochCmdNotValid...", ...}
        """
        ret_val = {}
        elf_name, enum_path = self._get_prefix_and_suffix(enum_path)
        names = self.names[elf_name]
        for name, data in names.enumerators.items():
            if name.startswith(enum_path):
                val = data.value

                ret_val[val] = name[name.rfind("::") + 2 :]
        return ret_val

    @staticmethod
    def get_mem_reader(
        location: OnChipCoordinate, risc_name: str | None = None, neo_id: int | None = None
    ) -> Callable[[int, int, int], list[int]]:
        """
        Returns a simple memory reader function that reads from a given device and a given core.
        """
        from ttexalens.tt_exalens_lib import read_from_device

        # Initialization
        device = location._device
        private_memory: MemoryBlock | None = None
        risc_debug: RiscDebug | None = None
        word_size = 4
        if risc_name is not None:
            noc_block = device.get_block(location)
            risc_debug = noc_block.get_risc_debug(risc_name, neo_id)
            private_memory = risc_debug.get_data_private_memory()

        def mem_reader(addr: int, size_bytes: int, elements_to_read: int) -> list[int]:
            if elements_to_read == 0:
                return []
            element_size = size_bytes // elements_to_read
            assert element_size * elements_to_read == size_bytes, "Size must be divisible by number of elements"

            bytes_data: bytes | None = None
            if risc_name is not None:
                # Check if address is in private memory
                if (
                    private_memory is not None
                    and risc_debug is not None
                    and private_memory.contains_private_address(addr)
                ):
                    # We need to read aligned to 4 bytes
                    aligned_start = addr - (addr % word_size)
                    aligned_end = ((addr + size_bytes + word_size - 1) // word_size) * word_size

                    # Figure out how many words to read
                    words_to_read = (aligned_end - aligned_start) // word_size

                    with risc_debug.ensure_private_memory_access():
                        words = [risc_debug.read_memory(aligned_start + i * word_size) for i in range(words_to_read)]

                    # Convert words to bytes and remove extra bytes
                    bytes_data = b"".join(word.to_bytes(4, byteorder="little") for word in words)
                    bytes_data = bytes_data[addr - aligned_start : addr - aligned_start + size_bytes]

            if bytes_data is None:
                bytes_data = read_from_device(location=location, addr=addr, num_bytes=size_bytes)

            return [
                int.from_bytes(bytes_data[i * element_size : (i + 1) * element_size], byteorder="little")
                for i in range(elements_to_read)
            ]

        return mem_reader
