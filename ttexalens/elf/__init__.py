# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Re-export the native C++ types under their Native-less names so client
# code reads naturally (e.g. `from ttexalens.elf import ElfFile, DwarfDie`)
# while the implementation lives in the `_native_ttexalens` module.
from ttexalens._native_ttexalens import (
    NativeDwarfAttribute as DwarfAttribute,
    NativeDwarfAttributeForm as DwarfAttributeForm,
    NativeDwarfAttributeTag as DwarfAttributeTag,
    NativeDwarfDie as DwarfDie,
    NativeDwarfDieTag as DwarfDieTag,
    NativeDwarfFileLine as DwarfFileLine,
    NativeDwarfInfo as DwarfInfo,
    NativeElfFile as ElfFile,
    NativeElfSection as ElfSection,
    NativeElfSymbol as ElfSymbol,
    NativeElfSymbolBinding as ElfSymbolBinding,
    NativeElfSymbolType as ElfSymbolType,
    NativeElfVariable as ElfVariable,
    NativeFrameDescription as FrameDescription,
    NativeFrameInspection as FrameInspection,
)
from .parsed import ParsedElfFile, read_elf

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
    "ParsedElfFile",
    "read_elf",
]
