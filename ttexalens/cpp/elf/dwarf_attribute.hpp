// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <libdwarf.h>

#include <cstdint>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace ttexalens::native_elf {

// One DWARF attribute on a DIE: tag (DW_AT_*) + decoded value.
//
// The variant covers everything callers reach for today. Pick the right
// alternative with std::get_if<T>() or std::visit. Forms we don't decode
// (rare ones) come back as std::monostate.
//
//   bool                    DW_FORM_flag, DW_FORM_flag_present
//   uint64_t                addresses (DW_FORM_addr), unsigned constants,
//                           section offsets, DIE references (always given
//                           as a global .debug_info offset so callers can
//                           feed them straight to get_or_create_die)
//   int64_t                 DW_FORM_sdata
//   std::string             every string form (string, strp, strx, ...)
//   std::vector<uint8_t>    DW_FORM_block*, DW_FORM_exprloc
class NativeDwarfAttribute {
   public:
    using Value = std::variant<std::monostate, bool, uint64_t, int64_t, std::string, std::vector<uint8_t>>;

    NativeDwarfAttribute(Dwarf_Half tag, Dwarf_Half form, Value value)
        : tag(tag), form(form), value(std::move(value)) {}

    Dwarf_Half get_tag() const { return tag; }
    Dwarf_Half get_form() const { return form; }
    const Value& get_value() const { return value; }

   private:
    Dwarf_Half tag;
    Dwarf_Half form;
    Value value;
};

}  // namespace ttexalens::native_elf
