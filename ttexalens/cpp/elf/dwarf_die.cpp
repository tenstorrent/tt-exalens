// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_die.hpp"

#include <dwarf.h>  // DW_AT_* constants

#include <utility>

namespace ttexalens::native_elf {

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

std::optional<NativeDwarfDie> NativeDwarfDie::get_die_from_attribute(Dwarf_Half attribute_tag) const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(die, attribute_tag, &attr, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    Dwarf_Off offset = 0;
    if (dwarf_global_formref(attr, &offset, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    DwarfDieHandle target(dbg);
    if (dwarf_offdie_b(dbg, offset, /*is_info=*/true, &target, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    return NativeDwarfDie(std::move(target));
}

std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>> NativeDwarfDie::get_address_ranges() const {
    std::vector<std::pair<Dwarf_Addr, Dwarf_Addr>> ranges;
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);

    // 1. DW_AT_low_pc + DW_AT_high_pc → one absolute range.
    Dwarf_Addr low_pc = 0;
    if (dwarf_lowpc(die, &low_pc, &error) == DW_DLV_OK) {
        Dwarf_Half hp_form = 0;
        enum Dwarf_Form_Class hp_class = DW_FORM_CLASS_UNKNOWN;
        Dwarf_Addr high_pc = 0;
        if (dwarf_highpc_b(die, &high_pc, &hp_form, &hp_class, &error) == DW_DLV_OK) {
            // DW_AT_high_pc is either an absolute address (class addrptr) or
            // an offset from low_pc (class constant) per DWARF 4+.
            Dwarf_Addr end = (hp_class == DW_FORM_CLASS_ADDRESS) ? high_pc : (low_pc + high_pc);
            ranges.emplace_back(low_pc, end);
            return ranges;
        }
        // Has low_pc but no high_pc — odd, but fall through to DW_AT_ranges.
    }

    // 2. DW_AT_ranges (DWARF 5 .debug_rnglists). Use libdwarf's "cooked"
    //    addresses so base-address selection is applied for us.
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(die, DW_AT_ranges, &attr, &error) == DW_DLV_OK) {
        Dwarf_Half version = 0;
        Dwarf_Half offset_size = 0;
        // dwarf_get_version_of_die: which DWARF version owns this DIE?
        if (dwarf_get_version_of_die(die, &version, &offset_size) == DW_DLV_OK && version >= 5) {
            Dwarf_Half form = 0;
            if (dwarf_whatform(attr, &form, &error) == DW_DLV_OK) {
                // DW_FORM_rnglistx is an index into the CU's rnglists base;
                // everything else here is a sec_offset.
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
                            // Base-address selection entries are folded into
                            // the cooked values by libdwarf; nothing to emit.
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
        // TODO: DWARF <=4 .debug_ranges via dwarf_get_ranges_b. Requires
        // walking up to the CU root for the base address; we don't have a
        // parent pointer yet, so leave it for when we hit an ELF that needs it.
        return ranges;
    }

    // 3. No address attributes on this DIE — union of children's ranges.
    for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
        auto child_ranges = child->get_address_ranges();
        ranges.insert(ranges.end(), child_ranges.begin(), child_ranges.end());
    }
    return ranges;
}

Dwarf_Off NativeDwarfDie::get_offset() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    Dwarf_Off offset = 0;
    dwarf_dieoffset(die, &offset, &error);
    return offset;
}

std::optional<NativeDwarfDie> NativeDwarfDie::get_first_child() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfDieHandle child(dbg);
    if (dwarf_child(die, &child, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    return NativeDwarfDie(std::move(child));
}

std::optional<NativeDwarfDie> NativeDwarfDie::get_next_sibling() const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfDieHandle next(dbg);
    if (dwarf_siblingof_b(dbg, die, /*is_info=*/true, &next, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    return NativeDwarfDie(std::move(next));
}

std::optional<NativeDwarfDie> NativeDwarfDie::find_child_by_name(std::string_view target) const {
    for (auto child = get_first_child(); child; child = child->get_next_sibling()) {
        if (child->get_name() == target) {
            return child;
        }
    }
    return std::nullopt;
}

}  // namespace ttexalens::native_elf
