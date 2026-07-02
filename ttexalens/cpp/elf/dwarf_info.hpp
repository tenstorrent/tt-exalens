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
class ElfFileImpl;
class DwarfInfoImpl;
}  // namespace details

// Preference for the final component of a name when several DIEs share it
// (e.g. an `enum noc_mode` type shadowing a `constexpr uint8_t noc_mode`).
enum class DieNameFilter {
    Any,       // first name match, tag-agnostic (generic find-any-DIE lookups)
    Variable,  // prefer a DW_TAG_variable (value lookups: get_global/get_constant)
};

class DwarfInfo {
   public:
    DwarfInfo(std::weak_ptr<details::ElfFileImpl> elf_impl);

    ~DwarfInfo();
    DwarfInfo(const DwarfInfo&) = delete;
    DwarfInfo& operator=(const DwarfInfo&) = delete;
    DwarfInfo(DwarfInfo&& other) noexcept;
    DwarfInfo& operator=(DwarfInfo&& other) noexcept;

    // Maps a PC to its source location via the .debug_line program. Returns
    // std::nullopt if no line entry covers the address.
    std::optional<DwarfFileLine> find_file_line_by_address(uint64_t address) const;

    // Resolves a "Foo::Bar::baz" path against every CU's DIE tree and returns
    // the first non-declaration match (or a declaration as fallback). Follows
    // DW_AT_abstract_origin / DW_AT_specification one hop when present.
    DwarfDiePtr get_die_by_name(std::string_view name) const;

    // Walks every CU and recursively drills into children to find the DIE
    // whose address range contains `address`. When multiple CUs match (e.g.
    // overlapping subprograms from inlining), the DIE with the narrowest
    // range wins. Returns nullptr if no DIE covers the address.
    DwarfDiePtr find_function_by_address(uint64_t address) const;

    // Locates the FDE covering `pc` in .debug_frame (falling back to
    // .eh_frame) and returns a FrameDescription bound to `memory_access`.
    // Returns nullopt if no FDE covers `pc`.
    std::optional<FrameDescription> get_frame_description(uint64_t pc,
                                                          std::shared_ptr<MemoryAccess> memory_access) const;

    // Finds a symbol in the ELF symbol table by its exact name. Returns nullptr
    // when no match is found. Returned pointer is valid for the DwarfInfo's
    // lifetime. Don't change fields of the returned read-only symbol to avoid
    // internal state corruption.
    const ElfSymbol* find_symbol_by_name(std::string_view name) const;

    // Looks up `name` as an enumerator / constexpr int constant. Returns
    // nullopt when the DIE doesn't exist or doesn't carry a numeric constant
    // value.
    std::optional<uint64_t> get_enum_value(std::string_view name) const;

    // Looks up the constant value of `name` (must be a DW_TAG_constant /
    // constexpr-style DIE backed by a base type).
    DwarfDie::ConstantValue get_constant(std::string_view name) const;

    // Locates `name` as a global variable and builds a ElfVariable
    // bound to `memory_access`.
    ElfVariable get_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const;

    // Convenience: get_global() followed by .read() — snapshots the current
    // bytes of the variable so subsequent member / index / dereference
    // chains reuse the cached copy.
    ElfVariable read_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const;

   private:
    // Core name resolver for "Foo::Bar::baz" paths. With DieNameFilter::Variable
    // the final component prefers a DW_TAG_variable over a same-named type
    // (e.g. `constexpr uint8_t noc_mode` over `enum noc_mode`), scanning other
    // CUs before settling for a non-variable. Falls back to the first name
    // match, then to a declaration. get_die_by_name() passes DieNameFilter::Any.
    DwarfDiePtr resolve_die_by_name(std::string_view name, DieNameFilter filter) const;

    std::shared_ptr<details::DwarfInfoImpl> impl;
};

}  // namespace ttexalens::native_elf
