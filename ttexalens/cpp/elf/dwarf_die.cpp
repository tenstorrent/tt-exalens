// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_die.hpp"

#include <dwarf.h>  // DW_AT_* / DW_RLE_* / DW_FORM_* constants

#include <bit>
#include <cstring>
#include <utility>

namespace ttexalens::native_elf {

NativeDwarfDie::NativeDwarfDie(DwarfDieHandle die, std::weak_ptr<NativeDwarfInfo::Impl> info)
    : die(std::move(die)), info(std::move(info)) {}

std::string_view NativeDwarfDie::get_name() const {
    if (!name) {
        Dwarf_Debug dbg = die.get_state();
        DwarfErrorHandle error(dbg);
        NativeDwarfString s(dbg);
        dwarf_diename(die, &s, &error);
        name = std::move(s);
    }
    return *name;
}

Dwarf_Off NativeDwarfDie::get_offset() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    Dwarf_Off offset = 0;
    dwarf_dieoffset(die, &offset, &error);
    return offset;
}

Dwarf_Half NativeDwarfDie::get_tag() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    Dwarf_Half value = 0;
    dwarf_tag(die, &value, &error);
    return value;
}

namespace {

// Decode a single libdwarf attribute into our variant. We dispatch on
// DW_FORM_* (not DW_AT_*) because the form fully determines the storage —
// the same tag (e.g. DW_AT_location) can be encoded with several forms
// across DWARF versions.
NativeDwarfAttribute::Value decode_attribute_value(Dwarf_Debug dbg, Dwarf_Attribute attr, Dwarf_Half form) {
    DwarfErrorHandle error(dbg);
    switch (form) {
        case DW_FORM_addr:
        case DW_FORM_addrx:
        case DW_FORM_addrx1:
        case DW_FORM_addrx2:
        case DW_FORM_addrx3:
        case DW_FORM_addrx4:
        case DW_FORM_GNU_addr_index: {
            Dwarf_Addr a = 0;
            if (dwarf_formaddr(attr, &a, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(a);
            }
            return std::monostate{};
        }
        case DW_FORM_flag:
        case DW_FORM_flag_present: {
            Dwarf_Bool b = 0;
            if (dwarf_formflag(attr, &b, &error) == DW_DLV_OK) {
                return b != 0;
            }
            return std::monostate{};
        }
        case DW_FORM_string:
        case DW_FORM_strp:
        case DW_FORM_strp_sup:
        case DW_FORM_GNU_strp_alt:
        case DW_FORM_line_strp:
        case DW_FORM_strx:
        case DW_FORM_strx1:
        case DW_FORM_strx2:
        case DW_FORM_strx3:
        case DW_FORM_strx4:
        case DW_FORM_GNU_str_index: {
            char* s = nullptr;
            if (dwarf_formstring(attr, &s, &error) == DW_DLV_OK && s != nullptr) {
                return std::string(s);
            }
            return std::monostate{};
        }
        case DW_FORM_sdata: {
            Dwarf_Signed v = 0;
            if (dwarf_formsdata(attr, &v, &error) == DW_DLV_OK) {
                return static_cast<int64_t>(v);
            }
            return std::monostate{};
        }
        case DW_FORM_data1:
        case DW_FORM_data2:
        case DW_FORM_data4:
        case DW_FORM_data8:
        case DW_FORM_data16:
        case DW_FORM_udata:
        case DW_FORM_implicit_const:
        case DW_FORM_sec_offset:
        case DW_FORM_loclistx:
        case DW_FORM_rnglistx: {
            Dwarf_Unsigned v = 0;
            if (dwarf_formudata(attr, &v, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(v);
            }
            return std::monostate{};
        }
        case DW_FORM_ref1:
        case DW_FORM_ref2:
        case DW_FORM_ref4:
        case DW_FORM_ref8:
        case DW_FORM_ref_udata:
        case DW_FORM_ref_addr:
        case DW_FORM_ref_sig8:
        case DW_FORM_ref_sup4:
        case DW_FORM_ref_sup8:
        case DW_FORM_GNU_ref_alt: {
            // Always hand back a global .debug_info offset so callers can
            // feed it to get_or_create_die without knowing the encoding.
            Dwarf_Off off = 0;
            if (dwarf_global_formref(attr, &off, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(off);
            }
            return std::monostate{};
        }
        case DW_FORM_block:
        case DW_FORM_block1:
        case DW_FORM_block2:
        case DW_FORM_block4:
        case DW_FORM_exprloc: {
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

}  // namespace

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
            vec.emplace_back(tag_value, form, decode_attribute_value(dbg, attr, form));
        }
    }
    return *attributes;
}

const NativeDwarfAttribute* NativeDwarfDie::get_attribute(Dwarf_Half attribute_tag) const {
    for (const auto& attr : get_attributes()) {
        if (attr.get_tag() == attribute_tag) {
            return &attr;
        }
    }
    return nullptr;
}

bool NativeDwarfDie::has_attribute(Dwarf_Half attribute_tag) const { return get_attribute(attribute_tag) != nullptr; }

namespace {

// IEEE-754 reinterpret helpers. The raw constant value can arrive as either
// a packed integer (DW_FORM_data4 / data8) or a block of little-endian bytes
// (DW_FORM_block*). Both encode the same bit pattern; we just need to fish
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

}  // namespace

NativeDwarfDie::ConstantValue NativeDwarfDie::get_constant_value() const {
    const NativeDwarfAttribute* attr = get_attribute(DW_AT_const_value);
    if (attr == nullptr) {
        attr = get_attribute(DW_AT_const_expr);
    }
    if (attr == nullptr) {
        if (auto origin = get_die_from_attribute(DW_AT_abstract_origin)) {
            return origin->get_constant_value();
        }
        return std::monostate{};
    }

    if (auto type_die = get_resolved_type(); type_die && type_die->get_tag() == DW_TAG_base_type) {
        return retype_constant(attr->get_value(), type_die->get_name());
    }
    return passthrough_constant(attr->get_value());
}

namespace {

bool is_type_tag(Dwarf_Half tag) {
    switch (tag) {
        case DW_TAG_typedef:
        case DW_TAG_namespace:
        case DW_TAG_array_type:
        case DW_TAG_base_type:
        case DW_TAG_class_type:
        case DW_TAG_const_type:
        case DW_TAG_enumeration_type:
        case DW_TAG_pointer_type:
        case DW_TAG_ptr_to_member_type:
        case DW_TAG_reference_type:
        case DW_TAG_rvalue_reference_type:
        case DW_TAG_string_type:
        case DW_TAG_structure_type:
        case DW_TAG_subrange_type:
        case DW_TAG_subroutine_type:
        case DW_TAG_thrown_type:
        case DW_TAG_union_type:
        case DW_TAG_unspecified_type:
        case DW_TAG_volatile_type:
        case DW_TAG_packed_type:
        case DW_TAG_restrict_type:
        case DW_TAG_atomic_type:
        case DW_TAG_immutable_type:
        case DW_TAG_shared_type:
        case DW_TAG_interface_type:
        case DW_TAG_set_type:
        case DW_TAG_coarray_type:
        case DW_TAG_dynamic_type:
            return true;
        default:
            return false;
    }
}

bool is_type_wrapper(Dwarf_Half tag) {
    return tag == DW_TAG_typedef || tag == DW_TAG_const_type || tag == DW_TAG_volatile_type;
}

}  // namespace

NativeDwarfDiePtr NativeDwarfDie::get_resolved_type() const {
    auto current = std::const_pointer_cast<NativeDwarfDie>(shared_from_this());
    while (current) {
        const Dwarf_Half tag = current->get_tag();

        if (is_type_wrapper(tag)) {
            auto next = current->get_die_from_attribute(DW_AT_type);
            if (!next) {
                break;
            }
            if (is_type_wrapper(next->get_tag())) {
                current = std::move(next);
                continue;
            }
            return next;
        }

        // Check DW_AT_type for non-type DIEs
        if (!is_type_tag(tag) && current->has_attribute(DW_AT_type)) {
            auto next = current->get_die_from_attribute(DW_AT_type);
            if (!next) {
                break;
            }
            if (is_type_wrapper(next->get_tag())) {
                current = std::move(next);
                continue;
            }
            return next;
        }

        // Check DW_AT_specification
        if (auto spec = current->get_die_from_attribute(DW_AT_specification)) {
            current = std::move(spec);
            continue;
        }

        // Check DW_AT_abstract_origin
        if (auto origin = current->get_die_from_attribute(DW_AT_abstract_origin)) {
            current = std::move(origin);
            continue;
        }

        // Check DW_AT_type for enumeration_type
        if (tag == DW_TAG_enumeration_type) {
            if (auto next = current->get_die_from_attribute(DW_AT_type)) {
                current = std::move(next);
                continue;
            }
        }

        break;
    }
    // Only meaningful stuck case is a wrapper that ran out of DW_AT_type;
    // hand it back. Anything else means we couldn't reach a type at all.
    return is_type_wrapper(current->get_tag()) ? current : nullptr;
}

bool NativeDwarfDie::is_declaration() const {
    const auto* attr = get_attribute(DW_AT_declaration);
    if (attr == nullptr) {
        return false;
    }
    const auto* flag = std::get_if<bool>(&attr->get_value());
    return flag != nullptr && *flag;
}

NativeDwarfDiePtr NativeDwarfDie::get_die_from_attribute(Dwarf_Half attribute_tag) const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return nullptr;
    }
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(die, attribute_tag, &attr, &error) != DW_DLV_OK) {
        return nullptr;
    }
    Dwarf_Off offset = 0;
    if (dwarf_global_formref(attr, &offset, &error) != DW_DLV_OK) {
        return nullptr;
    }
    return get_or_create_die(std::move(info_ptr), offset);
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
            result = register_die(std::move(info_ptr), std::move(handle));
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
            result = register_die(std::move(info_ptr), std::move(handle));
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
        result = find_parent(std::move(info_ptr), get_offset());
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

const std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>>& NativeDwarfDie::get_address_ranges() const {
    if (address_ranges) {
        return *address_ranges;
    }
    auto& ranges = address_ranges.emplace();
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);

    // 1. DW_AT_low_pc + DW_AT_high_pc → one absolute range.
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

    // 2. DW_AT_ranges (DWARF 5 .debug_rnglists). Use libdwarf's "cooked"
    //    addresses so base-address selection is applied for us.
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(die, DW_AT_ranges, &attr, &error) == DW_DLV_OK) {
        Dwarf_Half version = 0;
        Dwarf_Half offset_size = 0;
        if (dwarf_get_version_of_die(die, &version, &offset_size) == DW_DLV_OK && version >= 5) {
            Dwarf_Half form = 0;
            if (dwarf_whatform(attr, &form, &error) == DW_DLV_OK) {
                Dwarf_Unsigned attr_value = 0;
                bool have_value = false;
                if (form == DW_FORM_rnglistx) {
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

}  // namespace ttexalens::native_elf
