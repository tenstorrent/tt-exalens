# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Re-export the C++ types from the `_native_ttexalens` extension module.
from ttexalens._native_ttexalens import (
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
)
from ttexalens.server import FileAccessApi


def read_elf(
    file_ifc: FileAccessApi, elf_file_path: str, load_address: int | None = None, require_debug_symbols: bool = True
) -> ElfFile:
    """Read an ELF binary through `file_ifc` and return an `ElfFile` view
    anchored at `load_address` (when given) so subsequent live-PC lookups
    map back to the static ELF address space."""
    # The file_ifc indirection is what redirects to the tmp folder for
    # remote runs.
    with file_ifc.get_binary(elf_file_path) as f:
        data = f.read()
        elf = ElfFile.from_bytes(data, elf_file_path, load_address)
        if require_debug_symbols and not elf.has_dwarf_info():
            raise ValueError(f"{elf_file_path} does not have DWARF info. Source file must be compiled with -g")
        return elf


__all__ = [
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
    "read_elf",
]
