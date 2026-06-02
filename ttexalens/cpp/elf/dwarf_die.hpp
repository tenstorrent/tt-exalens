// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "dwarf_attribute.hpp"
#include "dwarf_handle.hpp"
#include "dwarf_string.hpp"
#include "variable.hpp"

namespace ttexalens::native_elf {

namespace details {
class NativeDwarfInfoImpl;
}  // namespace details

class NativeElfSymbol;
class NativeDwarfCompileUnit;
class NativeFrameInspection;

class NativeDwarfDie;
using NativeDwarfDiePtr = std::shared_ptr<NativeDwarfDie>;

// DIE tags - DW_TAG_*
enum class NativeDwarfDieTag : Dwarf_Half {
    access_declaration = DW_TAG_access_declaration,
    ALTIUM_circ_type = DW_TAG_ALTIUM_circ_type,
    ALTIUM_mwa_circ_type = DW_TAG_ALTIUM_mwa_circ_type,
    ALTIUM_rev_carry_type = DW_TAG_ALTIUM_rev_carry_type,
    ALTIUM_rom = DW_TAG_ALTIUM_rom,
    array_type = DW_TAG_array_type,
    atomic_type = DW_TAG_atomic_type,
    base_type = DW_TAG_base_type,
    BORLAND_Delphi_dynamic_array = DW_TAG_BORLAND_Delphi_dynamic_array,
    BORLAND_Delphi_set = DW_TAG_BORLAND_Delphi_set,
    BORLAND_Delphi_string = DW_TAG_BORLAND_Delphi_string,
    BORLAND_Delphi_variant = DW_TAG_BORLAND_Delphi_variant,
    BORLAND_property = DW_TAG_BORLAND_property,
    call_site = DW_TAG_call_site,
    call_site_parameter = DW_TAG_call_site_parameter,
    catch_block = DW_TAG_catch_block,
    class_template = DW_TAG_class_template,
    class_type = DW_TAG_class_type,
    coarray_type = DW_TAG_coarray_type,
    common_block = DW_TAG_common_block,
    common_inclusion = DW_TAG_common_inclusion,
    compile_unit = DW_TAG_compile_unit,
    condition = DW_TAG_condition,
    const_type = DW_TAG_const_type,
    constant = DW_TAG_constant,
    dwarf_procedure = DW_TAG_dwarf_procedure,
    dynamic_type = DW_TAG_dynamic_type,
    entry_point = DW_TAG_entry_point,
    enumeration_type = DW_TAG_enumeration_type,
    enumerator = DW_TAG_enumerator,
    file_type = DW_TAG_file_type,
    formal_parameter = DW_TAG_formal_parameter,
    format_label = DW_TAG_format_label,
    friend_ = DW_TAG_friend,
    function_template = DW_TAG_function_template,
    generic_subrange = DW_TAG_generic_subrange,
    ghs_namespace = DW_TAG_ghs_namespace,
    ghs_template_templ_param = DW_TAG_ghs_template_templ_param,
    ghs_using_declaration = DW_TAG_ghs_using_declaration,
    ghs_using_namespace = DW_TAG_ghs_using_namespace,
    GNU_BINCL = DW_TAG_GNU_BINCL,
    GNU_call_site = DW_TAG_GNU_call_site,
    GNU_call_site_parameter = DW_TAG_GNU_call_site_parameter,
    GNU_EINCL = DW_TAG_GNU_EINCL,
    GNU_formal_parameter_pack = DW_TAG_GNU_formal_parameter_pack,
    GNU_template_parameter_pack = DW_TAG_GNU_template_parameter_pack,
    GNU_template_template_parameter = DW_TAG_GNU_template_template_parameter,
    HP_array_descriptor = DW_TAG_HP_array_descriptor,
    immutable_type = DW_TAG_immutable_type,
    imported_declaration = DW_TAG_imported_declaration,
    imported_module = DW_TAG_imported_module,
    imported_unit = DW_TAG_imported_unit,
    inheritance = DW_TAG_inheritance,
    inlined_subroutine = DW_TAG_inlined_subroutine,
    interface_type = DW_TAG_interface_type,
    label = DW_TAG_label,
    lexical_block = DW_TAG_lexical_block,
    LLVM_annotation = DW_TAG_LLVM_annotation,
    member = DW_TAG_member,
    MIPS_loop = DW_TAG_MIPS_loop,
    module = DW_TAG_module,
    mutable_type = DW_TAG_mutable_type,
    namelist = DW_TAG_namelist,
    namelist_item = DW_TAG_namelist_item,
    namespace_ = DW_TAG_namespace,
    packed_type = DW_TAG_packed_type,
    partial_unit = DW_TAG_partial_unit,
    PGI_interface_block = DW_TAG_PGI_interface_block,
    PGI_kanji_type = DW_TAG_PGI_kanji_type,
    pointer_type = DW_TAG_pointer_type,
    ptr_to_member_type = DW_TAG_ptr_to_member_type,
    reference_type = DW_TAG_reference_type,
    restrict_type = DW_TAG_restrict_type,
    rvalue_reference_type = DW_TAG_rvalue_reference_type,
    set_type = DW_TAG_set_type,
    shared_type = DW_TAG_shared_type,
    skeleton_unit = DW_TAG_skeleton_unit,
    string_type = DW_TAG_string_type,
    structure_type = DW_TAG_structure_type,
    subprogram = DW_TAG_subprogram,
    subrange_type = DW_TAG_subrange_type,
    subroutine_type = DW_TAG_subroutine_type,
    SUN_class_template = DW_TAG_SUN_class_template,
    SUN_codeflags = DW_TAG_SUN_codeflags,
    SUN_dtor = DW_TAG_SUN_dtor,
    SUN_dtor_info = DW_TAG_SUN_dtor_info,
    SUN_f90_interface = DW_TAG_SUN_f90_interface,
    SUN_fortran_vax_structure = DW_TAG_SUN_fortran_vax_structure,
    SUN_function_template = DW_TAG_SUN_function_template,
    SUN_hi = DW_TAG_SUN_hi,
    SUN_indirect_inheritance = DW_TAG_SUN_indirect_inheritance,
    SUN_memop_info = DW_TAG_SUN_memop_info,
    SUN_omp_child_func = DW_TAG_SUN_omp_child_func,
    SUN_rtti_descriptor = DW_TAG_SUN_rtti_descriptor,
    SUN_struct_template = DW_TAG_SUN_struct_template,
    SUN_union_template = DW_TAG_SUN_union_template,
    template_alias = DW_TAG_template_alias,
    template_type_parameter = DW_TAG_template_type_parameter,
    template_value_parameter = DW_TAG_template_value_parameter,
    thrown_type = DW_TAG_thrown_type,
    TI_assign_register = DW_TAG_TI_assign_register,
    TI_far_type = DW_TAG_TI_far_type,
    TI_ioport_type = DW_TAG_TI_ioport_type,
    TI_near_type = DW_TAG_TI_near_type,
    TI_onchip_type = DW_TAG_TI_onchip_type,
    TI_restrict_type = DW_TAG_TI_restrict_type,
    try_block = DW_TAG_try_block,
    type_unit = DW_TAG_type_unit,
    typedef_ = DW_TAG_typedef,
    union_type = DW_TAG_union_type,
    unspecified_parameters = DW_TAG_unspecified_parameters,
    unspecified_type = DW_TAG_unspecified_type,
    upc_relaxed_type = DW_TAG_upc_relaxed_type,
    upc_shared_type = DW_TAG_upc_shared_type,
    upc_strict_type = DW_TAG_upc_strict_type,
    variable = DW_TAG_variable,
    variant = DW_TAG_variant,
    variant_part = DW_TAG_variant_part,
    volatile_type = DW_TAG_volatile_type,
    with_stmt = DW_TAG_with_stmt,
};

// Source location for a particular program counter — returned by
// NativeDwarfInfo::find_file_line_by_address.
struct NativeDwarfFileLine {
    std::string file;
    uint32_t line;
    uint32_t column;
};

class NativeDwarfDie : public std::enable_shared_from_this<NativeDwarfDie> {
   public:
    NativeDwarfDie(DwarfDieHandle die, std::weak_ptr<details::NativeDwarfInfoImpl> info);
    ~NativeDwarfDie();

    operator Dwarf_Die() const { return die; }
    explicit operator bool() const { return static_cast<bool>(die); }
    Dwarf_Debug get_state() const { return die.get_state(); }

    // Returns the compile unit that owns this DIE, or nullptr if the
    // owning NativeDwarfInfo has been destroyed. The pointer is valid only
    // while the owning ElfFile is alive — do not store it.
    const NativeDwarfCompileUnit* get_cu() const;

    // Lazily reads DW_AT_name off this DIE. First call invokes dwarf_diename
    // and caches the result; later calls return the cached view. Returns an
    // empty view when the DIE has no name attribute.
    std::string_view get_name() const;

    // Reads DW_AT_linkage_name off this DIE, if present. This is the
    // (typically Itanium-ABI mangled) name the linker put in .symtab —
    // distinct from get_name() for any C++ symbol that needs mangling.
    // Returns an empty view when the attribute is absent.
    std::string_view get_linkage_name() const;

    // Tries to create human-friendly names for this DIE.
    std::string get_readable_name() const;

    // Fully-qualified path through enclosing scopes, joined with "::".
    // Follows DW_AT_abstract_origin / DW_AT_specification for subprograms
    // so a concrete subprogram instance returns the source-level name.
    std::string get_path() const;

    // Like get_path(), but appends `(t1, t2, ...)` after every subprogram
    // segment so the result matches the form `__cxa_demangle` emits.
    std::string get_search_path() const;

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

    // True iff this DIE is a base type with a character encoding
    // (DW_AT_encoding ∈ {DW_ATE_signed_char, DW_ATE_unsigned_char}). Used to
    // distinguish C strings (char[] / char*) from byte arrays.
    bool is_char_type() const;

    // True iff this DIE represents a C string: either an array of a char-
    // encoded base type, or a pointer to one. Used to decide whether
    // read_value() returns a Python str.
    bool is_string_type() const;

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

    // Reads this DIE's value from the given frame, if it's a variable or
    // member with a resolvable location. Returns std::nullopt if the DIE
    // has no location, the location is unsupported or can't be evaluated,
    // or the resolved type is unusably incomplete.
    std::optional<NativeElfVariable> read_value(const NativeFrameInspection& frame) const;

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

    // Collects every DW_TAG_template_value_parameter that applies to this
    // DIE: the DIE's own template params plus the enclosing scope's
    // (nested templates like `Class<3>::method<-1>` need both). Follows
    // DW_AT_specification / DW_AT_abstract_origin one hop first because
    // instance / inlined DIEs don't carry their template params directly.
    std::vector<NativeDwarfDiePtr> get_template_value_parameters() const;

   private:
    // Resolves this DIE to its .symtab entry. Returns nullptr on miss.
    const NativeElfSymbol* find_symbol() const;

    std::optional<NativeDwarfFileLine> resolve_file_info(NativeDwarfAttributeTag file_tag,
                                                         NativeDwarfAttributeTag line_tag,
                                                         NativeDwarfAttributeTag column_tag) const;

    friend class details::NativeDwarfInfoImpl;

    DwarfDieHandle die;
    std::weak_ptr<details::NativeDwarfInfoImpl> info;

    mutable std::optional<NativeDwarfString> name;
    mutable std::optional<std::vector<NativeDwarfAttribute>> attributes;
    mutable std::optional<NativeDwarfDiePtr> first_child;
    mutable std::optional<NativeDwarfDiePtr> next_sibling;
    mutable std::optional<std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>>> address_ranges;
    mutable std::optional<std::weak_ptr<NativeDwarfDie>> parent;
};

}  // namespace ttexalens::native_elf
