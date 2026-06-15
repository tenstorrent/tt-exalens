# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import os

# Re-export the C++ types from the `_native_ttexalens` extension module.
from ttexalens._native_ttexalens import (
    CallstackEntry,
    CallstackEntryVariable,
    DwarfAttribute,
    DwarfAttributeForm,
    DwarfAttributeTag,
    DwarfDie,
    DwarfDieTag,
    DwarfFileLine,
    DwarfInfo,
    ElfFile,
    ElfSection,
    ElfSymbol,
    ElfSymbolBinding,
    ElfSymbolType,
    ElfVariable,
    FrameDescription,
    FrameInspection,
    FrameSnapshot,
    get_callstack,
    get_frame_callstack,
)
from ttexalens.server import FileAccessApi


def read_elf(
    file_ifc: FileAccessApi, elf_file_path: str, load_address: int | None = None, require_debug_symbols: bool = True
) -> ElfFile:
    """Read an ELF binary through `file_ifc` and return an `ElfFile` view
    anchored at `load_address` (when given) so subsequent live-PC lookups
    map back to the static ELF address space."""
    if file_ifc.is_local():
        if not os.path.isfile(elf_file_path):
            raise FileNotFoundError(elf_file_path)
        elf = ElfFile(elf_file_path, load_address)
    else:
        with file_ifc.get_binary(elf_file_path) as f:
            elf = ElfFile.from_bytes(f.read(), elf_file_path, load_address)
    if require_debug_symbols and not elf.has_dwarf_info():
        raise ValueError(f"{elf_file_path} does not have DWARF info. Source file must be compiled with -g")
    return elf


__all__ = [
    "CallstackEntry",
    "CallstackEntryVariable",
    "DwarfAttribute",
    "DwarfAttributeForm",
    "DwarfAttributeTag",
    "DwarfDie",
    "DwarfDieTag",
    "DwarfFileLine",
    "DwarfInfo",
    "ElfFile",
    "ElfSection",
    "ElfSymbol",
    "ElfSymbolBinding",
    "ElfSymbolType",
    "ElfVariable",
    "FrameDescription",
    "FrameInspection",
    "FrameSnapshot",
    "get_callstack",
    "get_frame_callstack",
    "read_elf",
]
