// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_die.hpp"

#include <dwarf.h>  // DW_AT_* / DW_RLE_* / DW_FORM_* constants

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

bool NativeDwarfDie::has_attribute(Dwarf_Half attribute_tag) const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfAttributeHandle attr(dbg);
    return dwarf_attr(die, attribute_tag, &attr, &error) == DW_DLV_OK;
}

bool NativeDwarfDie::is_declaration() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(die, DW_AT_declaration, &attr, &error) != DW_DLV_OK) {
        return false;
    }
    Dwarf_Bool flag = 0;
    if (dwarf_formflag(attr, &flag, &error) != DW_DLV_OK) {
        return false;
    }
    return flag != 0;
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
