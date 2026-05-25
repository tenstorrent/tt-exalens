// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <optional>
#include <string_view>
#include <utility>

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

   private:
    DwarfDieHandle die;
    mutable std::optional<NativeDwarfString> name;
};

}  // namespace ttexalens::native_elf
