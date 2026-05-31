// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_die.hpp"

#include <dwarf.h>  // DW_AT_* / DW_RLE_* / DW_FORM_* constants

#include <bit>
#include <cstring>
#include <utility>

#include "dwarf_cu.hpp"
#include "elf_file.hpp"
#include "private/dwarf_info_impl.hpp"

namespace ttexalens::native_elf {

namespace {

// Decode a single libdwarf attribute into our variant. We dispatch on
// DW_FORM_* (not DW_AT_*) because the form fully determines the storage —
// the same tag (e.g. NativeDwarfAttributeTag::location) can be encoded with several forms
// across DWARF versions.
NativeDwarfAttribute::Value decode_attribute_value(Dwarf_Debug dbg, Dwarf_Attribute attr,
                                                   NativeDwarfAttributeForm form) {
    DwarfErrorHandle error(dbg);
    switch (form) {
        case NativeDwarfAttributeForm::addr:
        case NativeDwarfAttributeForm::addrx:
        case NativeDwarfAttributeForm::addrx1:
        case NativeDwarfAttributeForm::addrx2:
        case NativeDwarfAttributeForm::addrx3:
        case NativeDwarfAttributeForm::addrx4:
        case NativeDwarfAttributeForm::GNU_addr_index: {
            Dwarf_Addr a = 0;
            if (dwarf_formaddr(attr, &a, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(a);
            }
            return std::monostate{};
        }
        case NativeDwarfAttributeForm::flag:
        case NativeDwarfAttributeForm::flag_present: {
            Dwarf_Bool b = 0;
            if (dwarf_formflag(attr, &b, &error) == DW_DLV_OK) {
                return b != 0;
            }
            return std::monostate{};
        }
        case NativeDwarfAttributeForm::string:
        case NativeDwarfAttributeForm::strp:
        case NativeDwarfAttributeForm::strp_sup:
        case NativeDwarfAttributeForm::GNU_strp_alt:
        case NativeDwarfAttributeForm::line_strp:
        case NativeDwarfAttributeForm::strx:
        case NativeDwarfAttributeForm::strx1:
        case NativeDwarfAttributeForm::strx2:
        case NativeDwarfAttributeForm::strx3:
        case NativeDwarfAttributeForm::strx4:
        case NativeDwarfAttributeForm::GNU_str_index: {
            char* s = nullptr;
            if (dwarf_formstring(attr, &s, &error) == DW_DLV_OK && s != nullptr) {
                return std::string(s);
            }
            return std::monostate{};
        }
        case NativeDwarfAttributeForm::sdata: {
            Dwarf_Signed v = 0;
            if (dwarf_formsdata(attr, &v, &error) == DW_DLV_OK) {
                return static_cast<int64_t>(v);
            }
            return std::monostate{};
        }
        case NativeDwarfAttributeForm::data1:
        case NativeDwarfAttributeForm::data2:
        case NativeDwarfAttributeForm::data4:
        case NativeDwarfAttributeForm::data8:
        case NativeDwarfAttributeForm::data16:
        case NativeDwarfAttributeForm::udata:
        case NativeDwarfAttributeForm::implicit_const:
        case NativeDwarfAttributeForm::sec_offset:
        case NativeDwarfAttributeForm::loclistx:
        case NativeDwarfAttributeForm::rnglistx: {
            Dwarf_Unsigned v = 0;
            if (dwarf_formudata(attr, &v, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(v);
            }
            return std::monostate{};
        }
        case NativeDwarfAttributeForm::ref1:
        case NativeDwarfAttributeForm::ref2:
        case NativeDwarfAttributeForm::ref4:
        case NativeDwarfAttributeForm::ref8:
        case NativeDwarfAttributeForm::ref_udata:
        case NativeDwarfAttributeForm::ref_addr:
        case NativeDwarfAttributeForm::ref_sig8:
        case NativeDwarfAttributeForm::ref_sup4:
        case NativeDwarfAttributeForm::ref_sup8:
        case NativeDwarfAttributeForm::GNU_ref_alt: {
            // Always hand back a global .debug_info offset so callers can
            // feed it to get_or_create_die without knowing the encoding.
            Dwarf_Off off = 0;
            if (dwarf_global_formref(attr, &off, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(off);
            }
            return std::monostate{};
        }
        case NativeDwarfAttributeForm::block:
        case NativeDwarfAttributeForm::block1:
        case NativeDwarfAttributeForm::block2:
        case NativeDwarfAttributeForm::block4:
        case NativeDwarfAttributeForm::exprloc: {
            DwarfBlockHandle block(dbg);
            if (dwarf_formblock(attr, &block, &error) == DW_DLV_OK && block) {
                Dwarf_Block* b = block.get();
                const auto* data = static_cast<const uint8_t*>(b->bl_data);
                return std::vector<uint8_t>(data, data + b->bl_len);
            }
            return std::monostate{};
        }
        default:
            return std::monostate{};
    }
}

// IEEE-754 reinterpret helpers. The raw constant value can arrive as either
// a packed integer (NativeDwarfAttributeForm::data4 / data8) or a block of little-endian bytes
// (NativeDwarfAttributeForm::block*). Both encode the same bit pattern; we just need to fish
// out the right width.
float bits_to_float(uint64_t bits) { return std::bit_cast<float>(static_cast<uint32_t>(bits)); }
double bits_to_double(uint64_t bits) { return std::bit_cast<double>(bits); }
float bytes_to_float(const std::vector<uint8_t>& bytes) {
    uint32_t bits = 0;
    if (bytes.size() >= sizeof(bits)) {
        std::memcpy(&bits, bytes.data(), sizeof(bits));
    }
    return std::bit_cast<float>(bits);
}
double bytes_to_double(const std::vector<uint8_t>& bytes) {
    uint64_t bits = 0;
    if (bytes.size() >= sizeof(bits)) {
        std::memcpy(&bits, bytes.data(), sizeof(bits));
    }
    return std::bit_cast<double>(bits);
}

NativeDwarfDie::ConstantValue passthrough_constant(const NativeDwarfAttribute::Value& raw) {
    if (const auto* b = std::get_if<bool>(&raw)) return *b;
    if (const auto* s = std::get_if<int64_t>(&raw)) return *s;
    if (const auto* u = std::get_if<uint64_t>(&raw)) return *u;
    return std::monostate{};
}

NativeDwarfDie::ConstantValue retype_constant(const NativeDwarfAttribute::Value& raw, std::string_view type_name) {
    if (type_name == "bool") {
        if (const auto* u = std::get_if<uint64_t>(&raw)) return *u != 0;
        if (const auto* s = std::get_if<int64_t>(&raw)) return *s != 0;
        if (const auto* b = std::get_if<bool>(&raw)) return *b;
        if (const auto* bytes = std::get_if<std::vector<uint8_t>>(&raw)) return !bytes->empty() && (*bytes)[0] != 0;
        return std::monostate{};
    }
    if (type_name == "float") {
        if (const auto* u = std::get_if<uint64_t>(&raw)) return bits_to_float(*u);
        if (const auto* bytes = std::get_if<std::vector<uint8_t>>(&raw)) return bytes_to_float(*bytes);
        return std::monostate{};
    }
    if (type_name == "double") {
        if (const auto* u = std::get_if<uint64_t>(&raw)) return bits_to_double(*u);
        if (const auto* bytes = std::get_if<std::vector<uint8_t>>(&raw)) return bytes_to_double(*bytes);
        return std::monostate{};
    }
    return passthrough_constant(raw);
}

bool is_type_tag(NativeDwarfDieTag tag) {
    switch (tag) {
        case NativeDwarfDieTag::typedef_:
        case NativeDwarfDieTag::namespace_:
        case NativeDwarfDieTag::array_type:
        case NativeDwarfDieTag::base_type:
        case NativeDwarfDieTag::class_type:
        case NativeDwarfDieTag::const_type:
        case NativeDwarfDieTag::enumeration_type:
        case NativeDwarfDieTag::pointer_type:
        case NativeDwarfDieTag::ptr_to_member_type:
        case NativeDwarfDieTag::reference_type:
        case NativeDwarfDieTag::rvalue_reference_type:
        case NativeDwarfDieTag::string_type:
        case NativeDwarfDieTag::structure_type:
        case NativeDwarfDieTag::subrange_type:
        case NativeDwarfDieTag::subroutine_type:
        case NativeDwarfDieTag::thrown_type:
        case NativeDwarfDieTag::union_type:
        case NativeDwarfDieTag::unspecified_type:
        case NativeDwarfDieTag::volatile_type:
        case NativeDwarfDieTag::packed_type:
        case NativeDwarfDieTag::restrict_type:
        case NativeDwarfDieTag::atomic_type:
        case NativeDwarfDieTag::immutable_type:
        case NativeDwarfDieTag::shared_type:
        case NativeDwarfDieTag::interface_type:
        case NativeDwarfDieTag::set_type:
        case NativeDwarfDieTag::coarray_type:
        case NativeDwarfDieTag::dynamic_type:
            return true;
        default:
            return false;
    }
}

bool is_type_wrapper(NativeDwarfDieTag tag) {
    return tag == NativeDwarfDieTag::typedef_ || tag == NativeDwarfDieTag::const_type ||
           tag == NativeDwarfDieTag::volatile_type;
}

// Pulls an integer attribute value out of the variant for the case where
// we accept both signed and unsigned representations.
std::optional<uint64_t> attr_as_uint(const NativeDwarfAttribute* attr) {
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

// Inline parse for the common single-op DW_OP_addr location: the byte
// stream is just `[0x03, addr_bytes...]`. Anything more elaborate (multi-op
// expressions, location lists) goes through Phase 5's evaluator.
std::optional<uint64_t> location_addr_only(const NativeDwarfDie& die) {
    const NativeDwarfAttribute* loc_attr = die.get_attribute(NativeDwarfAttributeTag::location);
    if (loc_attr == nullptr) {
        return std::nullopt;
    }
    const auto* bytes = std::get_if<std::vector<uint8_t>>(&loc_attr->get_value());
    if (bytes == nullptr || bytes->empty() || (*bytes)[0] != DW_OP_addr) {
        return std::nullopt;
    }
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    Dwarf_Half addr_size = 0;
    if (dwarf_get_die_address_size(die, &addr_size, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    if (bytes->size() < static_cast<size_t>(1 + addr_size)) {
        return std::nullopt;
    }
    uint64_t addr = 0;
    std::memcpy(&addr, bytes->data() + 1, addr_size);
    return addr;
}

// Returns true iff a tag should never have an address attached (types,
// namespaces, enumerators).
bool tag_is_address_less(NativeDwarfDieTag tag) { return is_type_tag(tag) || tag == NativeDwarfDieTag::enumerator; }

}  // namespace

NativeDwarfDie::NativeDwarfDie(DwarfDieHandle die, std::weak_ptr<details::NativeDwarfInfoImpl> info)
    : die(std::move(die)), info(std::move(info)) {}

std::string_view NativeDwarfDie::get_name() const {
    if (!name) {
        Dwarf_Debug dbg = die.get_state();
        DwarfErrorHandle error(dbg);
        NativeDwarfString s(dbg);
        dwarf_diename(die, &s, &error);
        name = std::move(s);
    }
    if (!name->empty()) {
        return *name;
    }
    // Follow DW_AT_abstract_origin / DW_AT_specification one hop. Inlined
    // and abstract-instance DIEs typically don't carry their own DW_AT_name
    // — the name lives on the declaration this DIE points at.
    if (auto origin = get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin)) {
        return origin->get_name();
    }
    if (auto spec = get_die_from_attribute(NativeDwarfAttributeTag::specification)) {
        return spec->get_name();
    }
    return *name;
}

std::string_view NativeDwarfDie::get_linkage_name() const {
    if (const auto* s = get_attribute_value<std::string>(NativeDwarfAttributeTag::linkage_name)) {
        return *s;
    }
    return {};
}

const NativeElfSymbol* NativeDwarfDie::find_symbol() const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return nullptr;
    }
    if (std::string_view linkage = get_linkage_name(); !linkage.empty()) {
        if (const NativeElfSymbol* sym = info_ptr->find_symbol_by_name(linkage)) {
            return sym;
        }
    }
    if (std::string_view die_name = get_name(); !die_name.empty()) {
        if (const NativeElfSymbol* sym = info_ptr->find_symbol_by_name(die_name)) {
            return sym;
        }
    }
    std::string path = get_search_path();
    if (!path.empty()) {
        if (const NativeElfSymbol* sym = info_ptr->find_symbol_by_demangled_name(path)) {
            return sym;
        }
    }
    return nullptr;
}

// Tries to create human-friendly names for this DIE.
std::string NativeDwarfDie::get_readable_name() const {
    if (auto name_attribute = get_attribute(NativeDwarfAttributeTag::name)) {
        if (const auto* s = std::get_if<std::string>(&name_attribute->get_value())) {
            return *s;
        }
    } else if (auto specification = get_die_from_attribute(NativeDwarfAttributeTag::specification)) {
        return specification->get_readable_name();
    }
    // The pointer / reference / const / volatile cases follow DW_AT_type
    // directly (no get_resolved_type() — that would strip the cv-qualifiers
    // we're trying to render). The recursion preserves the DWARF chain
    // order, which for GCC mirrors the Itanium ABI mangling, so the output
    // matches `__cxa_demangle` (e.g. `int const volatile*`).
    else if (get_tag() == NativeDwarfDieTag::pointer_type) {
        if (auto pointee = get_die_from_attribute(NativeDwarfAttributeTag::type)) {
            return pointee->get_readable_name() + "*";
        }
        return "<pointer to unknown type>";
    } else if (get_tag() == NativeDwarfDieTag::reference_type) {
        if (auto pointee = get_die_from_attribute(NativeDwarfAttributeTag::type)) {
            return pointee->get_readable_name() + "&";
        }
        return "<reference to unknown type>";
    } else if (get_tag() == NativeDwarfDieTag::rvalue_reference_type) {
        if (auto pointee = get_die_from_attribute(NativeDwarfAttributeTag::type); pointee) {
            return pointee->get_readable_name() + "&&";
        }
        return "<rvalue reference to unknown type>";
    } else if (get_tag() == NativeDwarfDieTag::const_type) {
        if (auto inner = get_die_from_attribute(NativeDwarfAttributeTag::type)) {
            return inner->get_readable_name() + " const";
        }
        return "<const unknown>";
    } else if (get_tag() == NativeDwarfDieTag::volatile_type) {
        if (auto inner = get_die_from_attribute(NativeDwarfAttributeTag::type)) {
            return inner->get_readable_name() + " volatile";
        }
        return "<volatile unknown>";
    } else if (get_tag() == NativeDwarfDieTag::mutable_type) {
        if (auto inner = get_die_from_attribute(NativeDwarfAttributeTag::type)) {
            return inner->get_readable_name() + " mutable";
        }
        return "<mutable unknown>";
    } else if (auto origin = get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin)) {
        if (get_tag() == NativeDwarfDieTag::inlined_subroutine) {
            return origin->get_path();
        }
        return origin->get_readable_name();
    } else {
        return "tag (" + std::to_string(static_cast<uint64_t>(get_tag())) + ") at offset " +
               std::to_string(get_offset());
    }
    return std::string(get_name());
}

std::string NativeDwarfDie::get_path() const {
    // Follow DW_AT_abstract_origin / DW_AT_specification when present.
    if (auto origin = get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin)) {
        return origin->get_path();
    }
    if (auto spec = get_die_from_attribute(NativeDwarfAttributeTag::specification)) {
        return spec->get_path();
    }

    auto name = get_readable_name();
    auto parent = get_parent();
    if (parent && parent->get_tag() != NativeDwarfDieTag::compile_unit) {
        return parent->get_path() + "::" + name;
    }
    return name;
}

// Like get_path(), but emits the parameter list `(t1, t2, ...)` after every
// subprogram segment so the result matches the form `__cxa_demangle`
// produces. Used to look up `.symtab` entries by their demangled name —
// notably function-local statics, whose linker symbol's demangled form
// spells out the enclosing function's signature.
std::string NativeDwarfDie::get_search_path() const {
    if (auto origin = get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin)) {
        return origin->get_search_path();
    }
    if (auto spec = get_die_from_attribute(NativeDwarfAttributeTag::specification)) {
        return spec->get_search_path();
    }

    auto name = get_readable_name();
    if (get_tag() == NativeDwarfDieTag::subprogram) {
        std::string params = "(";
        bool first = true;
        for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
            if (child->get_tag() != NativeDwarfDieTag::formal_parameter) {
                continue;
            }
            if (!first) {
                params += ", ";
            }
            first = false;
            if (auto type_die = child->get_die_from_attribute(NativeDwarfAttributeTag::type)) {
                params += type_die->get_readable_name();
            }
        }
        params += ")";
        name += params;
    }
    auto parent = get_parent();
    if (parent && parent->get_tag() != NativeDwarfDieTag::compile_unit) {
        return parent->get_search_path() + "::" + name;
    }
    return name;
}

Dwarf_Off NativeDwarfDie::get_offset() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    Dwarf_Off offset = 0;
    dwarf_dieoffset(die, &offset, &error);
    return offset;
}

NativeDwarfDieTag NativeDwarfDie::get_tag() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    Dwarf_Half value = 0;
    dwarf_tag(die, &value, &error);
    return static_cast<NativeDwarfDieTag>(value);
}

const std::vector<NativeDwarfAttribute>& NativeDwarfDie::get_attributes() const {
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
        Dwarf_Attribute attr = attrs[i];
        Dwarf_Half tag_value = 0;
        Dwarf_Half form = 0;
        if (dwarf_whatattr(attr, &tag_value, &error) == DW_DLV_OK && dwarf_whatform(attr, &form, &error) == DW_DLV_OK) {
            auto form_enum = static_cast<NativeDwarfAttributeForm>(form);
            vec.emplace_back(static_cast<NativeDwarfAttributeTag>(tag_value), form_enum,
                             decode_attribute_value(dbg, attr, form_enum));
        }
    }
    return *attributes;
}

const NativeDwarfAttribute* NativeDwarfDie::get_attribute(NativeDwarfAttributeTag attribute_tag) const {
    for (const auto& attr : get_attributes()) {
        if (attr.get_tag() == attribute_tag) {
            return &attr;
        }
    }
    return nullptr;
}

bool NativeDwarfDie::has_attribute(NativeDwarfAttributeTag attribute_tag) const {
    return get_attribute(attribute_tag) != nullptr;
}

NativeDwarfDie::ConstantValue NativeDwarfDie::get_constant_value() const {
    const NativeDwarfAttribute* attr = get_attribute(NativeDwarfAttributeTag::const_value);
    if (attr == nullptr) {
        attr = get_attribute(NativeDwarfAttributeTag::const_expr);
    }
    if (attr == nullptr) {
        if (auto origin = get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin)) {
            return origin->get_constant_value();
        }
        return std::monostate{};
    }

    if (auto type_die = get_resolved_type(); type_die && type_die->get_tag() == NativeDwarfDieTag::base_type) {
        return retype_constant(attr->get_value(), type_die->get_name());
    }
    return passthrough_constant(attr->get_value());
}

NativeDwarfDiePtr NativeDwarfDie::get_resolved_type() const {
    auto current = std::const_pointer_cast<NativeDwarfDie>(shared_from_this());
    while (current) {
        const NativeDwarfDieTag tag = current->get_tag();

        if (is_type_wrapper(tag)) {
            auto next = current->get_die_from_attribute(NativeDwarfAttributeTag::type);
            if (!next) {
                break;
            }
            if (is_type_wrapper(next->get_tag())) {
                current = std::move(next);
                continue;
            }
            return next;
        }

        // Check NativeDwarfAttributeTag::type for non-type DIEs
        if (!is_type_tag(tag) && current->has_attribute(NativeDwarfAttributeTag::type)) {
            auto next = current->get_die_from_attribute(NativeDwarfAttributeTag::type);
            if (!next) {
                break;
            }
            if (is_type_wrapper(next->get_tag())) {
                current = std::move(next);
                continue;
            }
            return next;
        }

        // Check NativeDwarfAttributeTag::specification
        if (auto spec = current->get_die_from_attribute(NativeDwarfAttributeTag::specification)) {
            current = std::move(spec);
            continue;
        }

        // Check NativeDwarfAttributeTag::abstract_origin
        if (auto origin = current->get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin)) {
            current = std::move(origin);
            continue;
        }

        // Check NativeDwarfAttributeTag::type for enumeration_type
        if (tag == NativeDwarfDieTag::enumeration_type) {
            if (auto next = current->get_die_from_attribute(NativeDwarfAttributeTag::type)) {
                current = std::move(next);
                continue;
            }
        }

        break;
    }
    // Only meaningful stuck case is a wrapper that ran out of NativeDwarfAttributeTag::type;
    // hand it back. Anything else means we couldn't reach a type at all.
    return is_type_wrapper(current->get_tag()) ? current : nullptr;
}

NativeDwarfDiePtr NativeDwarfDie::get_dereference_type() const {
    const NativeDwarfDieTag tag = get_tag();
    if (tag != NativeDwarfDieTag::pointer_type && tag != NativeDwarfDieTag::reference_type) {
        return nullptr;
    }
    auto pointee = get_die_from_attribute(NativeDwarfAttributeTag::type);
    if (!pointee) {
        return nullptr;
    }
    auto resolved = pointee->get_resolved_type();
    return resolved ? resolved : pointee;
}

NativeDwarfDiePtr NativeDwarfDie::get_array_element_type() const {
    if (get_tag() != NativeDwarfDieTag::array_type) {
        return nullptr;
    }
    auto element = get_die_from_attribute(NativeDwarfAttributeTag::type);
    if (!element) {
        return nullptr;
    }
    auto resolved = element->get_resolved_type();
    return resolved ? resolved : element;
}

bool NativeDwarfDie::is_declaration() const {
    const auto* flag = get_attribute_value<bool>(NativeDwarfAttributeTag::declaration);
    return flag != nullptr && *flag;
}

NativeDwarfDiePtr NativeDwarfDie::get_die_from_attribute(NativeDwarfAttributeTag attribute_tag) const {
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

NativeDwarfDiePtr NativeDwarfDie::get_first_child() const {
    if (first_child) {
        return *first_child;
    }
    NativeDwarfDiePtr result;
    if (auto info_ptr = info.lock()) {
        Dwarf_Debug dbg = die.get_state();
        DwarfErrorHandle error(dbg);
        DwarfDieHandle handle(dbg);
        if (dwarf_child(die, &handle, &error) == DW_DLV_OK) {
            result = info_ptr->register_die(std::move(handle));
            if (result) {
                result->parent = std::const_pointer_cast<NativeDwarfDie>(shared_from_this());
            }
        }
    }
    first_child = result;
    return result;
}

NativeDwarfDiePtr NativeDwarfDie::get_next_sibling() const {
    if (next_sibling) {
        return *next_sibling;
    }
    NativeDwarfDiePtr result;
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

NativeDwarfDiePtr NativeDwarfDie::get_parent() const {
    if (parent) {
        return parent->lock();
    }
    NativeDwarfDiePtr result;
    if (auto info_ptr = info.lock()) {
        result = info_ptr->find_parent(get_offset());
    }
    // The descent in find_parent typically sets `parent` on us via the
    // get_first_child / get_next_sibling side effect — but if it didn't (e.g.
    // target wasn't found), cache the result explicitly so future calls don't
    // re-walk.
    if (!parent) {
        parent = result ? std::weak_ptr<NativeDwarfDie>(result) : std::weak_ptr<NativeDwarfDie>();
    }
    return parent->lock();
}

std::vector<NativeDwarfDiePtr> NativeDwarfDie::get_template_value_parameters() const {
    // Instance / inlined DIEs don't carry their template params directly —
    // follow specification or abstract_origin one hop and recurse.
    if (auto spec = get_die_from_attribute(NativeDwarfAttributeTag::specification)) {
        return spec->get_template_value_parameters();
    }
    if (auto origin = get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin)) {
        return origin->get_template_value_parameters();
    }

    std::vector<NativeDwarfDiePtr> result;
    for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
        if (child->get_tag() == NativeDwarfDieTag::template_value_parameter) {
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

const std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>>& NativeDwarfDie::get_address_ranges() const {
    if (address_ranges) {
        return *address_ranges;
    }
    auto& ranges = address_ranges.emplace();
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);

    // 1. NativeDwarfAttributeTag::low_pc + NativeDwarfAttributeTag::high_pc → one absolute range.
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

    // 2. NativeDwarfAttributeTag::ranges (DWARF 5 .debug_rnglists). Use libdwarf's "cooked"
    //    addresses so base-address selection is applied for us.
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(die, static_cast<Dwarf_Half>(NativeDwarfAttributeTag::ranges), &attr, &error) == DW_DLV_OK) {
        Dwarf_Half version = 0;
        Dwarf_Half offset_size = 0;
        if (dwarf_get_version_of_die(die, &version, &offset_size) == DW_DLV_OK && version >= 5) {
            Dwarf_Half form = 0;
            if (dwarf_whatform(attr, &form, &error) == DW_DLV_OK) {
                Dwarf_Unsigned attr_value = 0;
                bool have_value = false;
                if (static_cast<NativeDwarfAttributeForm>(form) == NativeDwarfAttributeForm::rnglistx) {
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
        }
        // TODO: DWARF <=4 .debug_ranges via dwarf_get_ranges_b.
        return ranges;
    }

    // 3. No address attributes on this DIE — union of children's ranges.
    for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
        const auto& child_ranges = child->get_address_ranges();
        ranges.insert(ranges.end(), child_ranges.begin(), child_ranges.end());
    }
    return ranges;
}

NativeDwarfDiePtr NativeDwarfDie::find_child_by_name(std::string_view target) const {
    for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
        if (child->get_name() == target) {
            return child;
        }
    }
    return nullptr;
}

bool NativeDwarfDie::is_signed_type() const {
    const auto* enc = get_attribute_value<uint64_t>(NativeDwarfAttributeTag::encoding);
    if (enc == nullptr) {
        return false;
    }
    return *enc == DW_ATE_signed || *enc == DW_ATE_signed_char || *enc == DW_ATE_signed_fixed;
}

std::optional<uint64_t> NativeDwarfDie::get_size() const {
    if (const auto* u = get_attribute_value<uint64_t>(NativeDwarfAttributeTag::byte_size)) {
        return *u;
    }

    const NativeDwarfDieTag tag = get_tag();

    // Check for pointer or reference
    if (tag == NativeDwarfDieTag::pointer_type || tag == NativeDwarfDieTag::reference_type ||
        tag == NativeDwarfDieTag::rvalue_reference_type) {
        Dwarf_Debug dbg = die.get_state();
        DwarfErrorHandle error(dbg);
        Dwarf_Half addr_size = 0;
        if (dwarf_get_die_address_size(die, &addr_size, &error) == DW_DLV_OK) {
            return addr_size;
        }
        return std::nullopt;
    }

    // Check for array
    if (tag == NativeDwarfDieTag::array_type) {
        uint64_t array_size = 1;
        for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
            if (const auto* u = child->get_attribute_value<uint64_t>(NativeDwarfAttributeTag::upper_bound)) {
                array_size *= (*u + 1);
            }
        }
        if (auto elem = get_die_from_attribute(NativeDwarfAttributeTag::type)) {
            if (auto elem_size = elem->get_size()) {
                return array_size * *elem_size;
            }
        }
    }

    // Check if we can resolve a type and get its size.
    if (auto type_die = get_die_from_attribute(NativeDwarfAttributeTag::type)) {
        return type_die->get_size();
    }

    // Symbol-table fallback for DIEs whose size DWARF didn't record but
    // .symtab did (typically symbol-anchored globals).
    if (const NativeElfSymbol* sym = find_symbol()) {
        return sym->size;
    }
    return std::nullopt;
}

// TODO: Verify if get_address() and get_address_recursed() work as expected with tests
static std::optional<uint64_t> get_address_recursed(const NativeDwarfDie& die, bool allow_recursion) {
    std::optional<uint64_t> addr;

    if (const auto* a = die.get_attribute(NativeDwarfAttributeTag::data_member_location)) {
        addr = attr_as_uint(a);
    } else if (const auto* a = die.get_attribute(NativeDwarfAttributeTag::low_pc)) {
        addr = attr_as_uint(a);
    } else {
        // Try a simple DW_OP_addr location.
        addr = location_addr_only(die);

        // Failing that, follow specification / abstract_origin if allowed.
        if (!addr && allow_recursion) {
            const auto* artificial_flag = die.get_attribute_value<bool>(NativeDwarfAttributeTag::artificial);
            const bool artificial = artificial_flag != nullptr && *artificial_flag;
            if (!artificial) {
                NativeDwarfDiePtr other = die.get_die_from_attribute(NativeDwarfAttributeTag::specification);
                if (!other) {
                    other = die.get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin);
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
        const NativeDwarfDieTag tag = die.get_tag();
        if (tag_is_address_less(tag)) {
            return std::nullopt;
        }
        if (auto parent = die.get_parent()) {
            if (parent->get_tag() == NativeDwarfDieTag::union_type) {
                return uint64_t{0};
            }
        }
        if (const auto* cv = die.get_attribute(NativeDwarfAttributeTag::const_value)) {
            return attr_as_uint(cv);
        }
        // .symtab address fallback runs in the public wrapper below — keeps
        // this free function from needing private access to NativeDwarfDie.
    }
    return addr;
}

std::optional<uint64_t> NativeDwarfDie::get_address() const {
    if (auto addr = get_address_recursed(*this, true)) {
        return addr;
    }
    // .symtab fallback — heavily load-bearing for tt-metal RISC-V firmware
    // globals. Many DIEs (e.g. cb_interface, noc_index, __ldm_bss_start)
    // are declared in headers but defined in the linker script or
    // assembly; DWARF has the name + type but no NativeDwarfAttributeTag::location, so the
    // linker-produced .symtab is the only place the address lives.
    if (const NativeElfSymbol* sym = find_symbol()) {
        return sym->value;
    }
    return std::nullopt;
}

std::optional<NativeDwarfFileLine> NativeDwarfDie::resolve_file_info(NativeDwarfAttributeTag file_tag,
                                                                     NativeDwarfAttributeTag line_tag,
                                                                     NativeDwarfAttributeTag column_tag) const {
    const auto* file_attr = get_attribute_value<uint64_t>(file_tag);
    if (file_attr == nullptr) {
        return std::nullopt;
    }
    const uint64_t file_number = *file_attr;

    auto info_ptr = info.lock();
    if (!info_ptr) {
        return std::nullopt;
    }
    NativeDwarfCompileUnit* cu = info_ptr->get_die_cu(get_offset());
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
    return NativeDwarfFileLine{std::string(file_path), line, column};
}

std::optional<NativeDwarfFileLine> NativeDwarfDie::get_decl_file_info() const {
    return resolve_file_info(NativeDwarfAttributeTag::decl_file, NativeDwarfAttributeTag::decl_line,
                             NativeDwarfAttributeTag::decl_column);
}

std::optional<NativeDwarfFileLine> NativeDwarfDie::get_call_file_info() const {
    return resolve_file_info(NativeDwarfAttributeTag::call_file, NativeDwarfAttributeTag::call_line,
                             NativeDwarfAttributeTag::call_column);
}

std::optional<NativeElfVariable> NativeDwarfDie::read_value(const NativeFrameInspection* /*frame*/) const {
    auto resolved = get_resolved_type();
    if (!resolved || resolved.get() == this) {
        return std::nullopt;
    }

    // Check if it is compile-time constant.
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
        return NativeElfVariable(resolved, 0, std::move(cache));
    }

    // TODO: Implement runtime value reading.
    return std::nullopt;
}

}  // namespace ttexalens::native_elf
