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

std::optional<NativeDwarfDie> NativeDwarfDie::find_child_by_name(std::string_view target) const {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfDieHandle ch(dbg);
    if (dwarf_child(die, &ch, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    // Each iteration wraps `ch` into a NativeDwarfDie so we can call
    // get_name() for the comparison. If no match, we get the next sibling
    // into a fresh DwarfDieHandle and reuse it on the next loop turn.
    while (true) {
        NativeDwarfDie child(std::move(ch));
        if (child.get_name() == target) {
            return child;
        }
        DwarfDieHandle next(dbg);
        if (dwarf_siblingof_b(dbg, child, /*is_info=*/true, &next, &error) != DW_DLV_OK) {
            return std::nullopt;
        }
        ch = std::move(next);
    }
}

}  // namespace ttexalens::native_elf
