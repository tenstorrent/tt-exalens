// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <memory>
#include <optional>
#include <string_view>
#include <utility>
#include <vector>

#include "dwarf_attribute.hpp"
#include "dwarf_handle.hpp"
#include "dwarf_info.hpp"  // for NativeDwarfInfo::Impl + NativeDwarfDiePtr
#include "dwarf_string.hpp"

namespace ttexalens::native_elf {

class NativeDwarfDie : public std::enable_shared_from_this<NativeDwarfDie> {
   public:
    NativeDwarfDie(DwarfDieHandle die, std::weak_ptr<NativeDwarfInfo::Impl> info);

    operator Dwarf_Die() const { return die; }
    explicit operator bool() const { return static_cast<bool>(die); }
    Dwarf_Debug get_state() const { return die.get_state(); }

    // Lazily reads DW_AT_name off this DIE. First call invokes dwarf_diename
    // and caches the result; later calls return the cached view. Returns an
    // empty view when the DIE has no name attribute.
    std::string_view get_name() const;

    // .debug_info offset of this DIE — stable id, used as the cache key.
    Dwarf_Off get_offset() const;

    // DWARF tag (DW_TAG_*). Always asks libdwarf — the call is just a
    // field read. Compare against DW_TAG_* constants directly (e.g.
    // die.get_tag() == DW_TAG_subprogram). The nanobind layer exposes it
    // alongside the NativeDwarfDieTag namespace of named constants.
    Dwarf_Half get_tag() const;

    // Lazily walks every attribute on this DIE, decodes each into a
    // NativeDwarfAttribute, and caches the result. DIEs typically carry a
    // handful of attributes, so a flat vector + linear scan beats a hash
    // map. Reference is stable for the lifetime of this NativeDwarfDie.
    // Pair with get_attribute() for tag-keyed lookup.
    const std::vector<NativeDwarfAttribute>& get_attributes() const;

    // Returns the cached attribute with the given DW_AT_* tag, or nullptr.
    const NativeDwarfAttribute* get_attribute(Dwarf_Half attribute_tag) const;

    // Compile-time constant value for this DIE (e.g. constexpr globals,
    // enumerators). Walks DW_AT_const_value, then DW_AT_const_expr, and
    // finally follows DW_AT_abstract_origin one hop if neither is present.
    // Returns std::monostate when no constant value is found.
    //
    // When the DIE's resolved type is a base type named "bool" / "float" /
    // "double" the raw DWARF encoding (often packed integer or bytes) is
    // reinterpreted so callers get a usable bool / float / double instead
    // of the underlying bit pattern.
    using ConstantValue = std::variant<std::monostate, bool, int64_t, uint64_t, float, double>;
    ConstantValue get_constant_value() const;

    // Peels typedef / const_type / volatile_type wrappers off a type, or
    // follows DW_AT_type from a non-type DIE (variable, member, …) to its
    // type and then peels. Also follows DW_AT_specification /
    // DW_AT_abstract_origin when present. Returns the original DIE if
    // nothing more specific is reachable.
    NativeDwarfDiePtr get_resolved_type() const;

    // If this DIE is DW_TAG_pointer_type or DW_TAG_reference_type, follows
    // DW_AT_type and runs get_resolved_type on the result so callers see
    // the ultimate pointee type (not an intervening typedef). nullptr for
    // any other tag or when DW_AT_type is absent.
    NativeDwarfDiePtr get_dereference_type() const;

    // If this DIE is DW_TAG_array_type, follows DW_AT_type to the element
    // DIE and runs get_resolved_type on it. nullptr for any other tag.
    NativeDwarfDiePtr get_array_element_type() const;

    // Walks the direct children of this DIE and returns the first whose
    // DW_AT_name matches `name`. nullptr on miss.
    NativeDwarfDiePtr find_child_by_name(std::string_view name) const;

    // Resolves a DIE-valued attribute (e.g. DW_AT_abstract_origin,
    // DW_AT_specification) to the referenced DIE. nullptr when the attribute
    // is absent OR the reference can't be followed.
    NativeDwarfDiePtr get_die_from_attribute(Dwarf_Half attribute_tag) const;

    // True iff this DIE carries the given attribute.
    bool has_attribute(Dwarf_Half attribute_tag) const;

    // True iff DW_AT_declaration is present and set.
    bool is_declaration() const;

    // Returns the address ranges this DIE covers, as (start, end) pairs.
    // Walks DW_AT_low_pc + DW_AT_high_pc, then DW_AT_ranges (DWARF 5
    // .debug_rnglists), then a union of children's ranges, mirroring the
    // existing Python ElfDie.address_ranges algorithm. Cached after the
    // first call — find_function_by_address calls this repeatedly during
    // descent.
    const std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>>& get_address_ranges() const;

    // Walk this DIE's children:
    //   for (auto child = die->get_first_child(); child;
    //        child = child->get_next_sibling()) { ... }
    // Both calls are cached after the first invocation (including the "no
    // child / no sibling" outcome), so repeat traversals are free.
    NativeDwarfDiePtr get_first_child() const;
    NativeDwarfDiePtr get_next_sibling() const;

    // Returns this DIE's parent in the .debug_info tree, or nullptr for a CU
    // root (or if the DIE somehow isn't reachable from any CU).
    NativeDwarfDiePtr get_parent() const;

   private:
    // Cache-interaction helpers.
    static NativeDwarfDiePtr register_die(std::shared_ptr<NativeDwarfInfo::Impl> info, DwarfDieHandle handle);
    static NativeDwarfDiePtr get_or_create_die(std::shared_ptr<NativeDwarfInfo::Impl> info, Dwarf_Off offset);
    static NativeDwarfDiePtr find_parent(std::shared_ptr<NativeDwarfInfo::Impl> info, Dwarf_Off target_offset);

    friend class NativeDwarfInfo::Impl;

    DwarfDieHandle die;
    std::weak_ptr<NativeDwarfInfo::Impl> info;

    mutable std::optional<NativeDwarfString> name;
    mutable std::optional<std::vector<NativeDwarfAttribute>> attributes;
    mutable std::optional<NativeDwarfDiePtr> first_child;
    mutable std::optional<NativeDwarfDiePtr> next_sibling;
    mutable std::optional<std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>>> address_ranges;
    mutable std::optional<std::weak_ptr<NativeDwarfDie>> parent;
};

}  // namespace ttexalens::native_elf
