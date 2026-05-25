// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <optional>
#include <string_view>
#include <utility>
#include <vector>

#include "dwarf_handle.hpp"
#include "dwarf_string.hpp"

namespace ttexalens::native_elf {

// Owning DIE wrapper. The only way to construct one is by handing it a
// populated DwarfDieHandle — the wrapper itself never serves as a libdwarf
// out-parameter, so we don't need (and don't define) operator&() or an
// out_ptr() slot. This rules out the failure mode where nanobind takes
// `&value` and unintentionally invokes a side-effectful operator&.
//
// DIE-level accessors live here.
class NativeDwarfDie {
   public:
    explicit NativeDwarfDie(DwarfDieHandle die) : die(std::move(die)) {}

    operator Dwarf_Die() const { return die; }
    explicit operator bool() const { return static_cast<bool>(die); }
    Dwarf_Debug get_state() const { return die.get_state(); }

    // Walks the direct children of this DIE and returns the first whose
    // DW_AT_name matches `name`. Returns std::nullopt on miss.
    std::optional<NativeDwarfDie> find_child_by_name(std::string_view name) const;

    // Lazily reads DW_AT_name off this DIE. First call invokes dwarf_diename
    // and caches the result; later calls return the cached view. Returns an
    // empty view when the DIE has no name attribute. The returned view is
    // valid for the lifetime of this NativeDwarfDie.
    std::string_view get_name() const;

    // Resolves a DIE-valued attribute (e.g. DW_AT_abstract_origin,
    // DW_AT_specification) to the referenced DIE. Returns std::nullopt when
    // the attribute is absent OR when the reference can't be followed.
    std::optional<NativeDwarfDie> get_die_from_attribute(Dwarf_Half attribute_tag) const;

    // True iff this DIE carries the given attribute. Each call hits libdwarf;
    // caching can come later if it shows up in profiles.
    bool has_attribute(Dwarf_Half attribute_tag) const;

    // True iff DW_AT_declaration is present and set — i.e. the DIE is only a
    // declaration, not a definition.
    bool is_declaration() const;

    // Returns the address ranges this DIE covers, as (start, end) pairs.
    // Mirrors the existing Python ElfDie.address_ranges:
    //   1. DW_AT_low_pc + DW_AT_high_pc → one absolute range.
    //   2. DW_AT_ranges → parsed range list (DWARF 5 .debug_rnglists; DWARF
    //      <=4 .debug_ranges is not wired up yet, returns empty).
    //   3. Otherwise → union of every child DIE's address_ranges.
    std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>> get_address_ranges() const;

    // .debug_info offset of this DIE. Stable identifier — useful as a cache
    // key for per-DIE state on either side of the binding.
    Dwarf_Off get_offset() const;

    // Walk this DIE's children one at a time:
    //
    //   for (auto child = die.get_first_child(); child;
    //        child = child->get_next_sibling()) { ... }
    //
    // Beats a materialized iter_children() vector when we don't need to keep
    // every child around at once — and it doesn't run into nanobind's
    // can't-weak-reference-a-list limitation.
    std::optional<NativeDwarfDie> get_first_child() const;
    std::optional<NativeDwarfDie> get_next_sibling() const;

   private:
    DwarfDieHandle die;
    mutable std::optional<NativeDwarfString> name;
};

}  // namespace ttexalens::native_elf
