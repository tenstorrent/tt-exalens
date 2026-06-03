// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_attribute.hpp"

#include "dwarf_handle.hpp"

namespace ttexalens::native_elf {

namespace {

// Decode a single libdwarf attribute into our variant. We dispatch on
// DW_FORM_* (not DW_AT_*) because the form fully determines the storage —
// the same tag (e.g. DwarfAttributeTag::location) can be encoded with several forms
// across DWARF versions.
DwarfAttribute::Value decode_attribute_value(Dwarf_Debug dbg, Dwarf_Attribute attr, DwarfAttributeForm form) {
    DwarfErrorHandle error(dbg);
    switch (form) {
        case DwarfAttributeForm::addr:
        case DwarfAttributeForm::addrx:
        case DwarfAttributeForm::addrx1:
        case DwarfAttributeForm::addrx2:
        case DwarfAttributeForm::addrx3:
        case DwarfAttributeForm::addrx4:
        case DwarfAttributeForm::GNU_addr_index: {
            Dwarf_Addr a = 0;
            if (dwarf_formaddr(attr, &a, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(a);
            }
            return std::monostate{};
        }
        case DwarfAttributeForm::flag:
        case DwarfAttributeForm::flag_present: {
            Dwarf_Bool b = 0;
            if (dwarf_formflag(attr, &b, &error) == DW_DLV_OK) {
                return b != 0;
            }
            return std::monostate{};
        }
        case DwarfAttributeForm::string:
        case DwarfAttributeForm::strp:
        case DwarfAttributeForm::strp_sup:
        case DwarfAttributeForm::GNU_strp_alt:
        case DwarfAttributeForm::line_strp:
        case DwarfAttributeForm::strx:
        case DwarfAttributeForm::strx1:
        case DwarfAttributeForm::strx2:
        case DwarfAttributeForm::strx3:
        case DwarfAttributeForm::strx4:
        case DwarfAttributeForm::GNU_str_index: {
            char* s = nullptr;
            if (dwarf_formstring(attr, &s, &error) == DW_DLV_OK && s != nullptr) {
                return std::string(s);
            }
            return std::monostate{};
        }
        case DwarfAttributeForm::sdata: {
            Dwarf_Signed v = 0;
            if (dwarf_formsdata(attr, &v, &error) == DW_DLV_OK) {
                return static_cast<int64_t>(v);
            }
            return std::monostate{};
        }
        case DwarfAttributeForm::data1:
        case DwarfAttributeForm::data2:
        case DwarfAttributeForm::data4:
        case DwarfAttributeForm::data8:
        case DwarfAttributeForm::data16:
        case DwarfAttributeForm::udata:
        case DwarfAttributeForm::implicit_const:
        case DwarfAttributeForm::sec_offset:
        case DwarfAttributeForm::loclistx:
        case DwarfAttributeForm::rnglistx: {
            Dwarf_Unsigned v = 0;
            if (dwarf_formudata(attr, &v, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(v);
            }
            return std::monostate{};
        }
        case DwarfAttributeForm::ref1:
        case DwarfAttributeForm::ref2:
        case DwarfAttributeForm::ref4:
        case DwarfAttributeForm::ref8:
        case DwarfAttributeForm::ref_udata:
        case DwarfAttributeForm::ref_addr:
        case DwarfAttributeForm::ref_sig8:
        case DwarfAttributeForm::ref_sup4:
        case DwarfAttributeForm::ref_sup8:
        case DwarfAttributeForm::GNU_ref_alt: {
            // Always hand back a global .debug_info offset so callers can
            // feed it to get_or_create_die without knowing the encoding.
            Dwarf_Off off = 0;
            if (dwarf_global_formref(attr, &off, &error) == DW_DLV_OK) {
                return static_cast<uint64_t>(off);
            }
            return std::monostate{};
        }
        case DwarfAttributeForm::block:
        case DwarfAttributeForm::block1:
        case DwarfAttributeForm::block2:
        case DwarfAttributeForm::block4:
        case DwarfAttributeForm::exprloc: {
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

std::optional<DwarfAttribute> DwarfAttribute::from_libdwarf(Dwarf_Debug dbg, Dwarf_Attribute attr) {
    DwarfErrorHandle error(dbg);
    Dwarf_Half tag_value = 0;
    Dwarf_Half form = 0;
    if (dwarf_whatattr(attr, &tag_value, &error) != DW_DLV_OK || dwarf_whatform(attr, &form, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    const auto form_enum = static_cast<DwarfAttributeForm>(form);
    return DwarfAttribute(static_cast<DwarfAttributeTag>(tag_value), form_enum,
                          decode_attribute_value(dbg, attr, form_enum));
}

}  // namespace ttexalens::native_elf
