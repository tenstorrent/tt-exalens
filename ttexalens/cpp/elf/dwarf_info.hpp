// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>

#include "dwarf_die.hpp"
#include "dwarf_frame.hpp"
#include "variable.hpp"

namespace ttexalens::native_elf {

namespace details {
class NativeElfFileImpl;
class NativeDwarfInfoImpl;
}  // namespace details

class NativeDwarfInfo {
   public:
    NativeDwarfInfo(std::weak_ptr<details::NativeElfFileImpl> elf_impl);

    ~NativeDwarfInfo();
    NativeDwarfInfo(const NativeDwarfInfo&) = delete;
    NativeDwarfInfo& operator=(const NativeDwarfInfo&) = delete;
    NativeDwarfInfo(NativeDwarfInfo&& other) noexcept;
    NativeDwarfInfo& operator=(NativeDwarfInfo&& other) noexcept;

    // Maps a PC to its source location via the .debug_line program. Returns
    // std::nullopt if no line entry covers the address.
    std::optional<NativeDwarfFileLine> find_file_line_by_address(uint64_t address) const;

    // Resolves a "Foo::Bar::baz" path against every CU's DIE tree and returns
    // the first non-declaration match (or a declaration as fallback). Follows
    // DW_AT_abstract_origin / DW_AT_specification one hop when present.
    NativeDwarfDiePtr get_die_by_name(std::string_view name) const;

    // Walks every CU and recursively drills into children to find the DIE
    // whose address range contains `address`. When multiple CUs match (e.g.
    // overlapping subprograms from inlining), the DIE with the narrowest
    // range wins. Returns nullptr if no DIE covers the address.
    NativeDwarfDiePtr find_function_by_address(uint64_t address) const;

    // Locates the FDE covering `pc` in .debug_frame (falling back to
    // .eh_frame) and returns a NativeFrameDescription bound to `memory_access`.
    // Returns nullopt if no FDE covers `pc`.
    std::optional<NativeFrameDescription> get_frame_description(uint64_t pc,
                                                                std::shared_ptr<MemoryAccess> memory_access) const;

    // Finds a symbol in the ELF symbol table by its exact name. Returns nullptr
    // when no match is found. Returned pointer is valid for the NativeDwarfInfo's
    // lifetime. Don't change fields of the returned read-only symbol to avoid
    // internal state corruption.
    const NativeElfSymbol* find_symbol_by_name(std::string_view name) const;

    // Looks up `name` as an enumerator / constexpr int constant. Returns
    // nullopt when the DIE doesn't exist or doesn't carry a numeric constant
    // value.
    std::optional<uint64_t> get_enum_value(std::string_view name) const;

    // Looks up the constant value of `name` (must be a DW_TAG_constant /
    // constexpr-style DIE backed by a base type).
    NativeDwarfDie::ConstantValue get_constant(std::string_view name) const;

    // Locates `name` as a global variable and builds a NativeElfVariable
    // bound to `memory_access`.
    NativeElfVariable get_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const;

    // Convenience: get_global() followed by .read() — snapshots the current
    // bytes of the variable so subsequent member / index / dereference
    // chains reuse the cached copy.
    NativeElfVariable read_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const;

   private:
    std::shared_ptr<details::NativeDwarfInfoImpl> impl;
};

}  // namespace ttexalens::native_elf
