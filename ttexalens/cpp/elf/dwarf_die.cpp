// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_die.hpp"

#include <dwarf.h>  // DW_AT_* / DW_RLE_* / DW_FORM_* constants

#include <bit>
#include <cstring>
#include <utility>

#include "dwarf_cu.hpp"
#include "dwarf_location.hpp"
#include "elf_file.hpp"
#include "private/dwarf_info_impl.hpp"
#include "variable.hpp"

namespace ttexalens::native_elf {

namespace {

bool is_type_wrapper(DwarfDieTag tag) {
    return tag == DwarfDieTag::typedef_ || tag == DwarfDieTag::const_type || tag == DwarfDieTag::volatile_type;
}

// Pulls an integer attribute value out of the variant for the case where
// we accept both signed and unsigned representations.
std::optional<uint64_t> attr_as_uint(const DwarfAttribute* attr) {
    if (attr == nullptr) {
        return std::nullopt;
    }
    if (const auto* u = std::get_if<uint64_t>(&attr->get_value())) {
        return *u;
    }
    if (const auto* s = std::get_if<int64_t>(&attr->get_value())) {
        return static_cast<uint64_t>(*s);
    }
    return std::nullopt;
}

}  // namespace

DwarfDie::DwarfDie(DwarfDieHandle die, std::weak_ptr<details::DwarfInfoImpl> info)
    : die(std::move(die)), info(std::move(info)) {}

DwarfDie::~DwarfDie() {
    // If the parent DwarfInfoImpl was already destroyed,
    // dwarf_object_finish has invalidated the Dwarf_Debug. Calling
    // dwarf_dealloc on any libdwarf-owned handle in that state would
    // corrupt the heap. Detach every cached handle so their destructors
    // skip cleanup.
    if (info.expired()) {
        (void)die.release();
        if (name) {
            name->release();
        }
    }
}

std::string_view DwarfDie::get_name() const {
    if (!name) {
        Dwarf_Debug dbg = die.get_state();
        DwarfErrorHandle error(dbg);
        DwarfString s(dbg);
        dwarf_diename(die, &s, &error);
        name = std::move(s);
    }
    if (!name->empty()) {
        return *name;
    }
    // Follow DW_AT_abstract_origin / DW_AT_specification one hop. Inlined
    // and abstract-instance DIEs typically don't carry their own DW_AT_name
    // — the name lives on the declaration this DIE points at.
    if (auto origin = get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
        return origin->get_name();
    }
    if (auto spec = get_die_from_attribute(DwarfAttributeTag::specification)) {
        return spec->get_name();
    }
    return *name;
}

std::string_view DwarfDie::get_linkage_name() const {
    if (const auto* s = get_attribute_value<std::string>(DwarfAttributeTag::linkage_name)) {
        return *s;
    }
    return {};
}

const ElfSymbol* DwarfDie::find_symbol() const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return nullptr;
    }
    if (std::string_view linkage = get_linkage_name(); !linkage.empty()) {
        if (const ElfSymbol* sym = info_ptr->find_symbol_by_name(linkage)) {
            return sym;
        }
    }
    if (std::string_view die_name = get_name(); !die_name.empty()) {
        if (const ElfSymbol* sym = info_ptr->find_symbol_by_name(die_name)) {
            return sym;
        }
    }
    std::string path = get_search_path();
    if (!path.empty()) {
        if (const ElfSymbol* sym = info_ptr->find_symbol_by_demangled_name(path)) {
            return sym;
        }
    }
    return nullptr;
}

// Tries to create human-friendly names for this DIE.
std::string DwarfDie::get_readable_name() const {
    if (auto name_attribute = get_attribute(DwarfAttributeTag::name)) {
        if (const auto* s = std::get_if<std::string>(&name_attribute->get_value())) {
            return *s;
        }
    } else if (auto specification = get_die_from_attribute(DwarfAttributeTag::specification)) {
        return specification->get_readable_name();
    }
    // The pointer / reference / const / volatile cases follow DW_AT_type
    // directly (no get_resolved_type() — that would strip the cv-qualifiers
    // we're trying to render). The recursion preserves the DWARF chain
    // order, which for GCC mirrors the Itanium ABI mangling, so the output
    // matches `__cxa_demangle` (e.g. `int const volatile*`).
    else if (get_tag() == DwarfDieTag::pointer_type) {
        if (auto pointee = get_die_from_attribute(DwarfAttributeTag::type)) {
            return pointee->get_readable_name() + "*";
        }
        return "<pointer to unknown type>";
    } else if (get_tag() == DwarfDieTag::reference_type) {
        if (auto pointee = get_die_from_attribute(DwarfAttributeTag::type)) {
            return pointee->get_readable_name() + "&";
        }
        return "<reference to unknown type>";
    } else if (get_tag() == DwarfDieTag::rvalue_reference_type) {
        if (auto pointee = get_die_from_attribute(DwarfAttributeTag::type); pointee) {
            return pointee->get_readable_name() + "&&";
        }
        return "<rvalue reference to unknown type>";
    } else if (get_tag() == DwarfDieTag::const_type) {
        if (auto inner = get_die_from_attribute(DwarfAttributeTag::type)) {
            return inner->get_readable_name() + " const";
        }
        return "<const unknown>";
    } else if (get_tag() == DwarfDieTag::volatile_type) {
        if (auto inner = get_die_from_attribute(DwarfAttributeTag::type)) {
            return inner->get_readable_name() + " volatile";
        }
        return "<volatile unknown>";
    } else if (get_tag() == DwarfDieTag::mutable_type) {
        if (auto inner = get_die_from_attribute(DwarfAttributeTag::type)) {
            return inner->get_readable_name() + " mutable";
        }
        return "<mutable unknown>";
    } else if (auto origin = get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
        if (get_tag() == DwarfDieTag::inlined_subroutine) {
            return origin->get_path();
        }
        return origin->get_readable_name();
    } else {
        return "tag (" + std::to_string(static_cast<uint64_t>(get_tag())) + ") at offset " +
               std::to_string(get_offset());
    }
    return std::string(get_name());
}

std::string DwarfDie::get_path() const {
    // Follow DW_AT_abstract_origin / DW_AT_specification when present.
    if (auto origin = get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
        return origin->get_path();
    }
    if (auto spec = get_die_from_attribute(DwarfAttributeTag::specification)) {
        return spec->get_path();
    }

    auto name = get_readable_name();
    auto parent = get_parent();
    if (parent && parent->get_tag() != DwarfDieTag::compile_unit) {
        return parent->get_path() + "::" + name;
    }
    return name;
}

// Like get_path(), but emits the parameter list `(t1, t2, ...)` after every
// subprogram segment so the result matches the form `__cxa_demangle`
// produces. Used to look up `.symtab` entries by their demangled name —
// notably function-local statics, whose linker symbol's demangled form
// spells out the enclosing function's signature.
std::string DwarfDie::get_search_path() const {
    if (auto origin = get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
        return origin->get_search_path();
    }
    if (auto spec = get_die_from_attribute(DwarfAttributeTag::specification)) {
        return spec->get_search_path();
    }

    auto name = get_readable_name();
    if (get_tag() == DwarfDieTag::subprogram) {
        std::string params = "(";
        bool first = true;
        for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
            if (child->get_tag() != DwarfDieTag::formal_parameter) {
                continue;
            }
            if (!first) {
                params += ", ";
            }
            first = false;
            if (auto type_die = child->get_die_from_attribute(DwarfAttributeTag::type)) {
                params += type_die->get_readable_name();
            }
        }
        params += ")";
        name += params;
    }
    auto parent = get_parent();
    if (parent && parent->get_tag() != DwarfDieTag::compile_unit) {
        return parent->get_search_path() + "::" + name;
    }
    return name;
}

Dwarf_Off DwarfDie::get_offset() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    Dwarf_Off offset = 0;
    dwarf_dieoffset(die, &offset, &error);
    return offset;
}

DwarfDieTag DwarfDie::get_tag() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    Dwarf_Half value = 0;
    dwarf_tag(die, &value, &error);
    return static_cast<DwarfDieTag>(value);
}

const std::vector<DwarfAttribute>& DwarfDie::get_attributes() const {
    if (attributes) {
        return *attributes;
    }
    auto& vec = attributes.emplace();
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfAttributeListHandle attrs(dbg);
    if (dwarf_attrlist(die, &attrs, attrs.count_ptr(), &error) != DW_DLV_OK) {
        return *attributes;
    }
    vec.reserve(static_cast<size_t>(attrs.size()));
    for (Dwarf_Signed i = 0; i < attrs.size(); ++i) {
        if (auto a = DwarfAttribute::from_libdwarf(dbg, attrs[i])) {
            vec.push_back(std::move(*a));
        }
    }
    return *attributes;
}

const DwarfAttribute* DwarfDie::get_attribute(DwarfAttributeTag attribute_tag) const {
    for (const auto& attr : get_attributes()) {
        if (attr.get_tag() == attribute_tag) {
            return &attr;
        }
    }
    return nullptr;
}

bool DwarfDie::has_attribute(DwarfAttributeTag attribute_tag) const { return get_attribute(attribute_tag) != nullptr; }

DwarfDie::ConstantValue DwarfDie::get_constant_value() const {
    const DwarfAttribute* attr = get_attribute(DwarfAttributeTag::const_value);
    if (attr == nullptr) {
        attr = get_attribute(DwarfAttributeTag::const_expr);
    }
    if (attr == nullptr) {
        if (auto origin = get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
            return origin->get_constant_value();
        }
        return std::monostate{};
    }

    // For base_type DIEs, reinterpret the raw DW_FORM_data{4,8} / DW_FORM_block*
    // bit pattern as the underlying scalar type. Same bits in either encoding;
    // we just need to fish out the right width.
    const auto& raw = attr->get_value();

    if (auto type_die = get_resolved_type(); type_die && type_die->get_tag() == DwarfDieTag::base_type) {
        const auto type_name = type_die->get_name();
        if (type_name == "bool") {
            if (const auto* u = std::get_if<uint64_t>(&raw)) return *u != 0;
            if (const auto* s = std::get_if<int64_t>(&raw)) return *s != 0;
            if (const auto* b = std::get_if<bool>(&raw)) return *b;
            if (const auto* bytes = std::get_if<std::vector<uint8_t>>(&raw)) return !bytes->empty() && (*bytes)[0] != 0;
            return std::monostate{};
        }
        if (type_name == "float") {
            if (const auto* u = std::get_if<uint64_t>(&raw)) return std::bit_cast<float>(static_cast<uint32_t>(*u));
            if (const auto* bytes = std::get_if<std::vector<uint8_t>>(&raw)) {
                uint32_t bits = 0;
                if (bytes->size() >= sizeof(bits)) {
                    std::memcpy(&bits, bytes->data(), sizeof(bits));
                }
                return std::bit_cast<float>(bits);
            }
            return std::monostate{};
        }
        if (type_name == "double") {
            if (const auto* u = std::get_if<uint64_t>(&raw)) return std::bit_cast<double>(*u);
            if (const auto* bytes = std::get_if<std::vector<uint8_t>>(&raw)) {
                uint64_t bits = 0;
                if (bytes->size() >= sizeof(bits)) {
                    std::memcpy(&bits, bytes->data(), sizeof(bits));
                }
                return std::bit_cast<double>(bits);
            }
            return std::monostate{};
        }
    }
    if (const auto* b = std::get_if<bool>(&raw)) return *b;
    if (const auto* s = std::get_if<int64_t>(&raw)) return *s;
    if (const auto* u = std::get_if<uint64_t>(&raw)) return *u;
    return std::monostate{};
}

const DwarfCompileUnit* DwarfDie::get_cu() const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return nullptr;
    }
    return info_ptr->get_die_cu(get_offset());
}

DwarfDiePtr DwarfDie::get_resolved_type() const {
    auto current = std::const_pointer_cast<DwarfDie>(shared_from_this());
    while (current) {
        const DwarfDieTag tag = current->get_tag();

        if (is_type_wrapper(tag)) {
            auto next = current->get_die_from_attribute(DwarfAttributeTag::type);
            if (!next) {
                break;
            }
            if (is_type_wrapper(next->get_tag())) {
                current = std::move(next);
                continue;
            }
            return next;
        }

        // Check DwarfAttributeTag::type for non-type DIEs
        if (!current->is_type() && current->has_attribute(DwarfAttributeTag::type)) {
            auto next = current->get_die_from_attribute(DwarfAttributeTag::type);
            if (!next) {
                break;
            }
            if (is_type_wrapper(next->get_tag())) {
                current = std::move(next);
                continue;
            }
            return next;
        }

        // Check DwarfAttributeTag::specification
        if (auto spec = current->get_die_from_attribute(DwarfAttributeTag::specification)) {
            current = std::move(spec);
            continue;
        }

        // Check DwarfAttributeTag::abstract_origin
        if (auto origin = current->get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
            current = std::move(origin);
            continue;
        }

        // Check DwarfAttributeTag::type for enumeration_type
        if (tag == DwarfDieTag::enumeration_type) {
            if (auto next = current->get_die_from_attribute(DwarfAttributeTag::type)) {
                current = std::move(next);
                continue;
            }
        }

        break;
    }
    // Only meaningful stuck case is a wrapper that ran out of DwarfAttributeTag::type;
    // hand it back. Anything else means we couldn't reach a type at all.
    return is_type_wrapper(current->get_tag()) ? current : nullptr;
}

DwarfDiePtr DwarfDie::get_dereference_type() const {
    const DwarfDieTag tag = get_tag();
    if (tag != DwarfDieTag::pointer_type && tag != DwarfDieTag::reference_type) {
        return nullptr;
    }
    auto pointee = get_die_from_attribute(DwarfAttributeTag::type);
    if (!pointee) {
        return nullptr;
    }
    auto resolved = pointee->get_resolved_type();
    return resolved ? resolved : pointee;
}

DwarfDiePtr DwarfDie::get_array_element_type() const {
    if (get_tag() != DwarfDieTag::array_type) {
        return nullptr;
    }
    auto element = get_die_from_attribute(DwarfAttributeTag::type);
    if (!element) {
        return nullptr;
    }
    auto resolved = element->get_resolved_type();
    return resolved ? resolved : element;
}

bool DwarfDie::is_declaration() const {
    const auto* flag = get_attribute_value<bool>(DwarfAttributeTag::declaration);
    return flag != nullptr && *flag;
}

DwarfDiePtr DwarfDie::get_die_from_attribute(DwarfAttributeTag attribute_tag) const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return nullptr;
    }
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(die, static_cast<Dwarf_Half>(attribute_tag), &attr, &error) != DW_DLV_OK) {
        return nullptr;
    }
    Dwarf_Off offset = 0;
    if (dwarf_global_formref(attr, &offset, &error) != DW_DLV_OK) {
        return nullptr;
    }
    return info_ptr->get_or_create_die(offset);
}

DwarfDiePtr DwarfDie::get_first_child() const {
    if (first_child) {
        return *first_child;
    }
    DwarfDiePtr result;
    if (auto info_ptr = info.lock()) {
        Dwarf_Debug dbg = die.get_state();
        DwarfErrorHandle error(dbg);
        DwarfDieHandle handle(dbg);
        if (dwarf_child(die, &handle, &error) == DW_DLV_OK) {
            result = info_ptr->register_die(std::move(handle));
            if (result) {
                result->parent = std::const_pointer_cast<DwarfDie>(shared_from_this());
            }
        }
    }
    first_child = result;
    return result;
}

DwarfDiePtr DwarfDie::get_next_sibling() const {
    if (next_sibling) {
        return *next_sibling;
    }
    DwarfDiePtr result;
    if (auto info_ptr = info.lock()) {
        Dwarf_Debug dbg = die.get_state();
        DwarfErrorHandle error(dbg);
        DwarfDieHandle handle(dbg);
        if (dwarf_siblingof_b(dbg, die, /*is_info=*/true, &handle, &error) == DW_DLV_OK) {
            result = info_ptr->register_die(std::move(handle));
            if (result && parent) {
                result->parent = *parent;
            }
        }
    }
    next_sibling = result;
    return result;
}

DwarfDiePtr DwarfDie::get_parent() const {
    if (parent) {
        return parent->lock();
    }
    DwarfDiePtr result;
    if (auto info_ptr = info.lock()) {
        result = info_ptr->find_parent(get_offset());
    }
    // The descent in find_parent typically sets `parent` on us via the
    // get_first_child / get_next_sibling side effect — but if it didn't (e.g.
    // target wasn't found), cache the result explicitly so future calls don't
    // re-walk.
    if (!parent) {
        parent = result ? std::weak_ptr<DwarfDie>(result) : std::weak_ptr<DwarfDie>();
    }
    return parent->lock();
}

std::vector<DwarfDiePtr> DwarfDie::get_template_value_parameters() const {
    // Instance / inlined DIEs don't carry their template params directly —
    // follow specification or abstract_origin one hop and recurse.
    if (auto spec = get_die_from_attribute(DwarfAttributeTag::specification)) {
        return spec->get_template_value_parameters();
    }
    if (auto origin = get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
        return origin->get_template_value_parameters();
    }

    std::vector<DwarfDiePtr> result;
    for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
        if (child->get_tag() == DwarfDieTag::template_value_parameter) {
            result.push_back(child);
        }
    }
    // Walk up to pick up template params from enclosing scopes (e.g.
    // Class<3>::method<-1>: the class's params live on the class DIE).
    if (auto p = get_parent()) {
        auto parent_params = p->get_template_value_parameters();
        result.insert(result.end(), parent_params.begin(), parent_params.end());
    }
    return result;
}

const std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>>& DwarfDie::get_address_ranges() const {
    if (address_ranges) {
        return *address_ranges;
    }
    auto& ranges = address_ranges.emplace();
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);

    // DW_AT_low_pc + DW_AT_high_pc = one absolute range.
    Dwarf_Addr low_pc = 0;
    if (dwarf_lowpc(die, &low_pc, &error) == DW_DLV_OK) {
        Dwarf_Half hp_form = 0;
        enum Dwarf_Form_Class hp_class = DW_FORM_CLASS_UNKNOWN;
        Dwarf_Addr high_pc = 0;
        if (dwarf_highpc_b(die, &high_pc, &hp_form, &hp_class, &error) == DW_DLV_OK) {
            Dwarf_Addr end = (hp_class == DW_FORM_CLASS_ADDRESS) ? high_pc : (low_pc + high_pc);
            ranges.emplace_back(low_pc, end);
            return ranges;
        }
    }

    // DW_AT_ranges (DWARF 5 .debug_rnglists). Use libdwarf's "cooked"
    // addresses so base-address selection is applied for us.
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(die, static_cast<Dwarf_Half>(DwarfAttributeTag::ranges), &attr, &error) == DW_DLV_OK) {
        Dwarf_Half version = 0;
        Dwarf_Half offset_size = 0;
        if (dwarf_get_version_of_die(die, &version, &offset_size) == DW_DLV_OK && version >= 5) {
            Dwarf_Half form = 0;
            if (dwarf_whatform(attr, &form, &error) == DW_DLV_OK) {
                Dwarf_Unsigned attr_value = 0;
                bool have_value = false;
                if (static_cast<DwarfAttributeForm>(form) == DwarfAttributeForm::rnglistx) {
                    if (dwarf_formudata(attr, &attr_value, &error) == DW_DLV_OK) {
                        have_value = true;
                    }
                } else {
                    Dwarf_Off off = 0;
                    if (dwarf_global_formref(attr, &off, &error) == DW_DLV_OK) {
                        attr_value = off;
                        have_value = true;
                    }
                }
                if (have_value) {
                    Dwarf_Rnglists_Head head = nullptr;
                    Dwarf_Unsigned entries_count = 0;
                    Dwarf_Unsigned rle_global_offset = 0;
                    if (dwarf_rnglists_get_rle_head(attr, form, attr_value, &head, &entries_count, &rle_global_offset,
                                                    &error) == DW_DLV_OK) {
                        for (Dwarf_Unsigned i = 0; i < entries_count; ++i) {
                            unsigned int entrylen = 0;
                            unsigned int rle_code = 0;
                            Dwarf_Unsigned raw1 = 0;
                            Dwarf_Unsigned raw2 = 0;
                            Dwarf_Bool addr_unavailable = false;
                            Dwarf_Unsigned cooked1 = 0;
                            Dwarf_Unsigned cooked2 = 0;
                            if (dwarf_get_rnglists_entry_fields_a(head, i, &entrylen, &rle_code, &raw1, &raw2,
                                                                  &addr_unavailable, &cooked1, &cooked2,
                                                                  &error) != DW_DLV_OK) {
                                continue;
                            }
                            if (addr_unavailable) continue;
                            if (rle_code == DW_RLE_end_of_list) break;
                            if (rle_code == DW_RLE_base_address || rle_code == DW_RLE_base_addressx) {
                                continue;
                            }
                            ranges.emplace_back(cooked1, cooked2);
                        }
                        dwarf_dealloc_rnglists_head(head);
                    }
                }
            }
        } else {
            // DWARF 2/3/4: raw .debug_ranges. Entries are relative to a base
            // address that starts at the CU's DW_AT_low_pc and is updated by
            // any DW_RANGES_ADDRESS_SELECTION entries along the way.
            Dwarf_Off ranges_offset = 0;
            if (dwarf_global_formref(attr, &ranges_offset, &error) == DW_DLV_OK) {
                Dwarf_Bool known_base = 0;
                Dwarf_Unsigned base_address = 0;
                Dwarf_Bool ranges_present = 0;
                Dwarf_Unsigned ranges_attr_offset = 0;
                dwarf_get_ranges_baseaddress(dbg, die, &known_base, &base_address, &ranges_present, &ranges_attr_offset,
                                             &error);
                if (!known_base) {
                    base_address = 0;
                }

                DwarfRangesHandle raw(dbg);
                Dwarf_Off real_offset = 0;
                Dwarf_Unsigned byte_count = 0;
                if (dwarf_get_ranges_b(dbg, ranges_offset, die, &real_offset, &raw, raw.count_ptr(), &byte_count,
                                       &error) == DW_DLV_OK) {
                    for (Dwarf_Signed i = 0; i < raw.size(); ++i) {
                        const Dwarf_Ranges& entry = raw[i];
                        if (entry.dwr_type == DW_RANGES_END) {
                            break;
                        }
                        if (entry.dwr_type == DW_RANGES_ADDRESS_SELECTION) {
                            base_address = entry.dwr_addr2;
                            continue;
                        }
                        // DW_RANGES_ENTRY: addresses are relative to base.
                        ranges.emplace_back(base_address + entry.dwr_addr1, base_address + entry.dwr_addr2);
                    }
                }
            }
        }
        return ranges;
    }

    // No address attributes on this DIE — union of children's ranges.
    for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
        const auto& child_ranges = child->get_address_ranges();
        ranges.insert(ranges.end(), child_ranges.begin(), child_ranges.end());
    }
    return ranges;
}

DwarfDiePtr DwarfDie::find_child_by_name(std::string_view target) const {
    for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
        if (child->get_name() == target) {
            return child;
        }
    }
    return nullptr;
}

bool DwarfDie::is_type() const {
    switch (get_tag()) {
        case DwarfDieTag::typedef_:
        case DwarfDieTag::namespace_:
        case DwarfDieTag::array_type:
        case DwarfDieTag::base_type:
        case DwarfDieTag::class_type:
        case DwarfDieTag::const_type:
        case DwarfDieTag::enumeration_type:
        case DwarfDieTag::pointer_type:
        case DwarfDieTag::ptr_to_member_type:
        case DwarfDieTag::reference_type:
        case DwarfDieTag::rvalue_reference_type:
        case DwarfDieTag::string_type:
        case DwarfDieTag::structure_type:
        case DwarfDieTag::subrange_type:
        case DwarfDieTag::subroutine_type:
        case DwarfDieTag::thrown_type:
        case DwarfDieTag::union_type:
        case DwarfDieTag::unspecified_type:
        case DwarfDieTag::volatile_type:
        case DwarfDieTag::packed_type:
        case DwarfDieTag::restrict_type:
        case DwarfDieTag::atomic_type:
        case DwarfDieTag::immutable_type:
        case DwarfDieTag::shared_type:
        case DwarfDieTag::interface_type:
        case DwarfDieTag::set_type:
        case DwarfDieTag::coarray_type:
        case DwarfDieTag::dynamic_type:
            return true;
        default:
            return false;
    }
}

bool DwarfDie::is_signed_type() const {
    const auto* enc = get_attribute_value<uint64_t>(DwarfAttributeTag::encoding);
    if (enc == nullptr) {
        return false;
    }
    return *enc == DW_ATE_signed || *enc == DW_ATE_signed_char || *enc == DW_ATE_signed_fixed;
}

bool DwarfDie::is_char_type() const {
    const auto* enc = get_attribute_value<uint64_t>(DwarfAttributeTag::encoding);
    if (enc == nullptr) {
        return false;
    }
    return *enc == DW_ATE_signed_char || *enc == DW_ATE_unsigned_char;
}

bool DwarfDie::is_string_type() const {
    const auto t = get_tag();
    if (t == DwarfDieTag::array_type) {
        auto elem = get_array_element_type();
        return elem && elem->is_char_type();
    }
    if (t == DwarfDieTag::pointer_type) {
        auto pointee = get_dereference_type();
        return pointee && pointee->is_char_type();
    }
    return false;
}

std::optional<uint64_t> DwarfDie::get_size() const {
    if (const auto* u = get_attribute_value<uint64_t>(DwarfAttributeTag::byte_size)) {
        return *u;
    }

    const DwarfDieTag tag = get_tag();

    // Check for pointer or reference
    if (tag == DwarfDieTag::pointer_type || tag == DwarfDieTag::reference_type ||
        tag == DwarfDieTag::rvalue_reference_type) {
        Dwarf_Debug dbg = die.get_state();
        DwarfErrorHandle error(dbg);
        Dwarf_Half addr_size = 0;
        if (dwarf_get_die_address_size(die, &addr_size, &error) == DW_DLV_OK) {
            return addr_size;
        }
        return std::nullopt;
    }

    // Check for array
    if (tag == DwarfDieTag::array_type) {
        uint64_t array_size = 1;
        for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
            if (const auto* u = child->get_attribute_value<uint64_t>(DwarfAttributeTag::upper_bound)) {
                array_size *= (*u + 1);
            }
        }
        if (auto elem = get_die_from_attribute(DwarfAttributeTag::type)) {
            if (auto elem_size = elem->get_size()) {
                return array_size * *elem_size;
            }
        }
    }

    // Check if we can resolve a type and get its size.
    if (auto type_die = get_die_from_attribute(DwarfAttributeTag::type)) {
        return type_die->get_size();
    }

    // Symbol-table fallback for DIEs whose size DWARF didn't record but
    // .symtab did (typically symbol-anchored globals).
    if (const ElfSymbol* sym = find_symbol()) {
        return sym->size;
    }
    return std::nullopt;
}

static std::optional<uint64_t> get_address_recursed(const DwarfDie& die, bool allow_recursion) {
    std::optional<uint64_t> addr;

    if (const auto* a = die.get_attribute(DwarfAttributeTag::low_pc)) {
        addr = attr_as_uint(a);
    } else {
        // Try a simple DW_OP_addr location: the byte stream is just
        // `[0x03, addr_bytes...]`. Anything more elaborate (multi-op
        // expressions, location lists) goes through Phase 5's evaluator.
        if (const DwarfAttribute* loc_attr = die.get_attribute(DwarfAttributeTag::location)) {
            const auto* bytes = std::get_if<std::vector<uint8_t>>(&loc_attr->get_value());
            if (bytes != nullptr && !bytes->empty() && (*bytes)[0] == DW_OP_addr) {
                Dwarf_Debug dbg = die.get_state();
                DwarfErrorHandle error(dbg);
                Dwarf_Half addr_size = 0;
                if (dwarf_get_die_address_size(die, &addr_size, &error) == DW_DLV_OK &&
                    bytes->size() >= static_cast<size_t>(1 + addr_size)) {
                    uint64_t a = 0;
                    std::memcpy(&a, bytes->data() + 1, addr_size);
                    addr = a;
                }
            }
        }

        // Failing that, follow specification / abstract_origin if allowed.
        if (!addr && allow_recursion) {
            const auto* artificial_flag = die.get_attribute_value<bool>(DwarfAttributeTag::artificial);
            const bool artificial = artificial_flag != nullptr && *artificial_flag;
            if (!artificial) {
                DwarfDiePtr other = die.get_die_from_attribute(DwarfAttributeTag::specification);
                if (!other) {
                    other = die.get_die_from_attribute(DwarfAttributeTag::abstract_origin);
                }
                // Python also runs find_DIE_that_specifies for the case
                // where neither attribute is present; that requires a
                // CU-wide scan and is deferred.
                if (other) {
                    addr = get_address_recursed(*other, /*allow_recursion=*/false);
                }
            }
        }
    }

    if (!addr) {
        // Types, namespaces, and enumerators never have an address attached.
        if (die.is_type() || die.get_tag() == DwarfDieTag::enumerator) {
            return std::nullopt;
        }
        if (const auto* cv = die.get_attribute(DwarfAttributeTag::const_value)) {
            return attr_as_uint(cv);
        }
        // .symtab address fallback runs in the public wrapper below — keeps
        // this free function from needing private access to DwarfDie.
    }
    return addr;
}

std::optional<uint64_t> DwarfDie::get_data_member_location() const {
    if (const auto* a = get_attribute(DwarfAttributeTag::data_member_location)) {
        return attr_as_uint(a);
    }
    // Union members have an implicit offset of 0 — DWARF omits the attribute.
    if (auto p = get_parent(); p && p->get_tag() == DwarfDieTag::union_type) {
        return uint64_t{0};
    }
    return std::nullopt;
}

std::optional<uint64_t> DwarfDie::get_address() const {
    if (auto addr = get_address_recursed(*this, true)) {
        return addr;
    }
    // .symtab fallback — heavily load-bearing for tt-metal RISC-V firmware
    // globals. Many DIEs (e.g. cb_interface, noc_index, __ldm_bss_start)
    // are declared in headers but defined in the linker script or
    // assembly; DWARF has the name + type but no DwarfAttributeTag::location, so the
    // linker-produced .symtab is the only place the address lives.
    if (const ElfSymbol* sym = find_symbol()) {
        // A STT_TLS symbol's value is its offset within the TLS block, not an
        // absolute address. The runtime address is the containing section's VMA
        // plus that offset.
        if (sym->type == ElfSymbolType::STT_TLS) {
            if (auto info_ptr = info.lock()) {
                return info_ptr->get_section_address(sym->section_index) + sym->value;
            }
        }
        return sym->value;
    }
    return std::nullopt;
}

std::optional<DwarfFileLine> DwarfDie::resolve_file_info(DwarfAttributeTag file_tag, DwarfAttributeTag line_tag,
                                                         DwarfAttributeTag column_tag) const {
    const auto* file_attr = get_attribute_value<uint64_t>(file_tag);
    if (file_attr == nullptr) {
        return std::nullopt;
    }
    const uint64_t file_number = *file_attr;

    auto info_ptr = info.lock();
    if (!info_ptr) {
        return std::nullopt;
    }
    DwarfCompileUnit* cu = info_ptr->get_die_cu(get_offset());
    if (cu == nullptr) {
        return std::nullopt;
    }

    // DWARF 2/3/4 use 1-based file indices (0 means "no file"); DWARF 5 is direct.
    const int64_t idx =
        (cu->get_version() >= 5) ? static_cast<int64_t>(file_number) : static_cast<int64_t>(file_number) - 1;
    const auto& srcfiles = cu->get_srcfiles();
    if (idx < 0 || idx >= static_cast<int64_t>(srcfiles.size())) {
        return std::nullopt;
    }
    std::string_view file_path = srcfiles[static_cast<size_t>(idx)];

    uint32_t line = 0;
    if (const auto* v = get_attribute_value<uint64_t>(line_tag)) {
        line = static_cast<uint32_t>(*v);
    }
    uint32_t column = 0;
    if (const auto* v = get_attribute_value<uint64_t>(column_tag)) {
        column = static_cast<uint32_t>(*v);
    }
    return DwarfFileLine{std::string(file_path), line, column};
}

std::optional<DwarfFileLine> DwarfDie::get_decl_file_info() const {
    return resolve_file_info(DwarfAttributeTag::decl_file, DwarfAttributeTag::decl_line,
                             DwarfAttributeTag::decl_column);
}

std::optional<DwarfFileLine> DwarfDie::get_call_file_info() const {
    return resolve_file_info(DwarfAttributeTag::call_file, DwarfAttributeTag::call_line,
                             DwarfAttributeTag::call_column);
}

std::optional<ElfVariable> DwarfDie::read_value(const FrameInspection& frame) const {
    // Reading value only makes sense for variables and parameters.
    const auto tag = get_tag();
    if (tag != DwarfDieTag::formal_parameter && tag != DwarfDieTag::variable &&
        tag != DwarfDieTag::template_value_parameter) {
        return std::nullopt;
    }

    auto resolved = get_resolved_type();
    if (!resolved || resolved.get() == this) {
        return std::nullopt;
    }

    // Compile-time constant (DW_AT_const_value).
    auto const_value = get_constant_value();
    if (!std::holds_alternative<std::monostate>(const_value)) {
        const uint64_t size = resolved->get_size().value_or(4);
        uint64_t uint_value = 0;
        if (const auto* b = std::get_if<bool>(&const_value)) {
            uint_value = *b ? 1 : 0;
        } else if (const auto* s = std::get_if<int64_t>(&const_value)) {
            uint_value = static_cast<uint64_t>(*s);
        } else if (const auto* u = std::get_if<uint64_t>(&const_value)) {
            uint_value = *u;
        } else if (const auto* f = std::get_if<float>(&const_value)) {
            uint_value = std::bit_cast<uint32_t>(*f);
        } else if (const auto* d = std::get_if<double>(&const_value)) {
            uint_value = std::bit_cast<uint64_t>(*d);
        } else {
            return std::nullopt;
        }
        std::vector<std::byte> bytes(size);
        std::memcpy(bytes.data(), &uint_value, std::min(size, static_cast<uint64_t>(sizeof(uint_value))));
        auto cache = std::make_shared<CachedReadMemoryAccess>(0, std::move(bytes), NoMemoryAccess::instance());
        return ElfVariable(resolved, 0, std::move(cache));
    }

    // Static-storage variable (globals, file/function statics):
    // address is fixed at link time. memory_access alone is enough.
    if (auto addr = get_address(); addr.has_value()) {
        return ElfVariable(resolved, *addr, frame.get_memory_access());
    }

    // Runtime location expression — needs the live callstack context
    // (registers, CFA, inner-frame chain) carried by `frame`.
    auto location = evaluate_die_location(*this, &frame);
    if (!location.has_value() || !location->value.has_value()) {
        return std::nullopt;
    }
    if (location->is_address) {
        return ElfVariable(resolved, *location->value, frame.get_memory_access());
    }
    // Literal value (DW_OP_stack_value / register-direct / composite via
    // DW_OP_piece): synthesise a backing buffer holding the materialised
    // bytes and hand back a ElfVariable that reads from it.
    const uint64_t size = resolved->get_size().value_or(4);
    std::vector<std::byte> bytes(size);
    if (!location->raw_bytes.empty()) {
        // Composite location already assembled the bytes in little-endian
        // order — copy as much as fits the variable's type.
        std::memcpy(bytes.data(), location->raw_bytes.data(),
                    std::min(size, static_cast<uint64_t>(location->raw_bytes.size())));
    } else {
        uint64_t raw = *location->value;
        std::memcpy(bytes.data(), &raw, std::min(size, static_cast<uint64_t>(sizeof(raw))));
    }
    auto cache = std::make_shared<CachedReadMemoryAccess>(0, std::move(bytes), NoMemoryAccess::instance());
    return ElfVariable(resolved, 0, std::move(cache));
}

}  // namespace ttexalens::native_elf
