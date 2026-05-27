// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "dwarf_attribute.hpp"
#include "dwarf_handle.hpp"
#include "dwarf_info.hpp"  // for NativeDwarfInfo::Impl + NativeDwarfDiePtr
#include "dwarf_string.hpp"

namespace ttexalens::native_elf {

class NativeDwarfCompileUnit;

// DIE tags - DW_TAG_*
enum class NativeDwarfDieTag : Dwarf_Half {
    array_type = DW_TAG_array_type,
    atomic_type = DW_TAG_atomic_type,
    base_type = DW_TAG_base_type,
    call_site = DW_TAG_call_site,
    class_type = DW_TAG_class_type,
    coarray_type = DW_TAG_coarray_type,
    compile_unit = DW_TAG_compile_unit,
    const_type = DW_TAG_const_type,
    dynamic_type = DW_TAG_dynamic_type,
    enumeration_type = DW_TAG_enumeration_type,
    enumerator = DW_TAG_enumerator,
    formal_parameter = DW_TAG_formal_parameter,
    GNU_call_site = DW_TAG_GNU_call_site,
    GNU_formal_parameter_pack = DW_TAG_GNU_formal_parameter_pack,
    GNU_template_parameter_pack = DW_TAG_GNU_template_parameter_pack,
    immutable_type = DW_TAG_immutable_type,
    imported_declaration = DW_TAG_imported_declaration,
    imported_module = DW_TAG_imported_module,
    inheritance = DW_TAG_inheritance,
    inlined_subroutine = DW_TAG_inlined_subroutine,
    interface_type = DW_TAG_interface_type,
    label = DW_TAG_label,
    lexical_block = DW_TAG_lexical_block,
    member = DW_TAG_member,
    namespace_ = DW_TAG_namespace,
    packed_type = DW_TAG_packed_type,
    pointer_type = DW_TAG_pointer_type,
    ptr_to_member_type = DW_TAG_ptr_to_member_type,
    reference_type = DW_TAG_reference_type,
    restrict_type = DW_TAG_restrict_type,
    rvalue_reference_type = DW_TAG_rvalue_reference_type,
    set_type = DW_TAG_set_type,
    shared_type = DW_TAG_shared_type,
    string_type = DW_TAG_string_type,
    structure_type = DW_TAG_structure_type,
    subprogram = DW_TAG_subprogram,
    subrange_type = DW_TAG_subrange_type,
    subroutine_type = DW_TAG_subroutine_type,
    template_type_parameter = DW_TAG_template_type_parameter,
    template_value_parameter = DW_TAG_template_value_parameter,
    thrown_type = DW_TAG_thrown_type,
    typedef_ = DW_TAG_typedef,
    union_type = DW_TAG_union_type,
    unspecified_parameters = DW_TAG_unspecified_parameters,
    unspecified_type = DW_TAG_unspecified_type,
    variable = DW_TAG_variable,
    volatile_type = DW_TAG_volatile_type,
};

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

    // Reads DW_AT_linkage_name off this DIE, if present. This is the
    // (typically Itanium-ABI mangled) name the linker put in .symtab —
    // distinct from get_name() for any C++ symbol that needs mangling.
    // Returns an empty view when the attribute is absent.
    std::string_view get_linkage_name() const;

    // Fully-qualified path through enclosing scopes, joined with "::".
    // Follows DW_AT_abstract_origin / DW_AT_specification for subprograms
    // so a concrete subprogram instance returns the source-level name.
    // Returns std::nullopt when the DIE has no resolvable name.
    std::optional<std::string> get_path() const;

    // .debug_info offset of this DIE — stable id, used as the cache key.
    Dwarf_Off get_offset() const;

    // DWARF tag (DW_TAG_*). Always asks libdwarf — the call is just a
    // field read. Compare against NativeDwarfDieTag enumerators directly
    // (e.g. die.get_tag() == NativeDwarfDieTag::subprogram).
    NativeDwarfDieTag get_tag() const;

    // Lazily walks every attribute on this DIE, decodes each into a
    // NativeDwarfAttribute, and caches the result. DIEs typically carry a
    // handful of attributes, so a flat vector + linear scan beats a hash
    // map. Reference is stable for the lifetime of this NativeDwarfDie.
    // Pair with get_attribute() for tag-keyed lookup.
    const std::vector<NativeDwarfAttribute>& get_attributes() const;

    // Returns the cached attribute with the given DW_AT_* tag, or nullptr.
    const NativeDwarfAttribute* get_attribute(NativeDwarfAttributeTag attribute_tag) const;

    // Convenience: looks up the attribute by tag and returns its value if the
    // active variant alternative is T. nullptr when the attribute is absent
    // or stored under a different form.
    template <typename T>
    const T* get_attribute_value(NativeDwarfAttributeTag attribute_tag) const {
        if (const NativeDwarfAttribute* attr = get_attribute(attribute_tag)) {
            return std::get_if<T>(&attr->get_value());
        }
        return nullptr;
    }

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

    // True iff this DIE is a base type with a signed integer encoding
    // (DW_AT_encoding ∈ {DW_ATE_signed, DW_ATE_signed_char, DW_ATE_signed_fixed}).
    bool is_signed_type() const;

    // Size in bytes for this DIE's type. Returns std::nullopt when no size
    // can be determined.
    std::optional<uint64_t> get_size() const;

    // TODO: member location should be extracted out!!!
    // Address for variable / member DIEs. Walks DW_AT_data_member_location,
    // then DW_AT_low_pc, then a DW_OP_addr-only DW_AT_location expression,
    // then follows DW_AT_specification / DW_AT_abstract_origin once. Returns
    // 0 for union members, falls back to DW_AT_const_value when present.
    // (Skipped vs Python: full location expression evaluation, symbol table
    // lookup, and the global find-DIE-that-specifies search.)
    std::optional<uint64_t> get_address() const;

    // Walks the direct children of this DIE and returns the first whose
    // DW_AT_name matches `name`. nullptr on miss.
    NativeDwarfDiePtr find_child_by_name(std::string_view name) const;

    // Resolves a DIE-valued attribute (e.g. DW_AT_abstract_origin,
    // DW_AT_specification) to the referenced DIE. nullptr when the attribute
    // is absent OR the reference can't be followed.
    NativeDwarfDiePtr get_die_from_attribute(NativeDwarfAttributeTag attribute_tag) const;

    // True iff this DIE carries the given attribute.
    bool has_attribute(NativeDwarfAttributeTag attribute_tag) const;

    // True iff DW_AT_declaration is present and set.
    bool is_declaration() const;

    // Returns the address ranges this DIE covers, as (start, end) pairs.
    // Walks DW_AT_low_pc + DW_AT_high_pc, then DW_AT_ranges (DWARF 5
    // .debug_rnglists), then a union of children's ranges, mirroring the
    // existing Python ElfDie.address_ranges algorithm. Cached after the
    // first call — find_function_by_address calls this repeatedly during
    // descent.
    const std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>>& get_address_ranges() const;

    // Source location associated with DW_AT_decl_* / DW_AT_call_* attributes,
    // packaged as (file_path, line, column). Resolves DW_AT_*_file (an index
    // into the CU's line-table file table) to a fully-qualified path via
    // libdwarf's dwarf_srcfiles. Returns std::nullopt when the relevant
    // attribute is absent or the file index can't be resolved.
    std::optional<NativeDwarfFileLine> get_decl_file_info() const;
    std::optional<NativeDwarfFileLine> get_call_file_info() const;

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
    static const NativeElfSymbol* find_symbol(std::shared_ptr<NativeDwarfInfo::Impl> info, std::string_view name);
    static NativeDwarfCompileUnit* get_die_cu(std::shared_ptr<NativeDwarfInfo::Impl> info, Dwarf_Off target_offset);

    // Resolves this DIE to its .symtab entry. Returns nullptr on miss.
    const NativeElfSymbol* find_symbol() const;

    std::optional<NativeDwarfFileLine> resolve_file_info(NativeDwarfAttributeTag file_tag,
                                                         NativeDwarfAttributeTag line_tag,
                                                         NativeDwarfAttributeTag column_tag) const;

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
