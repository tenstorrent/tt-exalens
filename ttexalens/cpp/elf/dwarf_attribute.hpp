// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <dwarf.h>
#include <libdwarf.h>

#include <cstdint>
#include <string>
#include <utility>
#include <variant>
#include <vector>

namespace ttexalens::native_elf {

// Attribute tags - DW_AT_*
enum class NativeDwarfAttributeTag : Dwarf_Half {
    abstract_origin = DW_AT_abstract_origin,
    artificial = DW_AT_artificial,
    byte_size = DW_AT_byte_size,
    call_column = DW_AT_call_column,
    call_file = DW_AT_call_file,
    call_line = DW_AT_call_line,
    const_expr = DW_AT_const_expr,
    const_value = DW_AT_const_value,
    data_member_location = DW_AT_data_member_location,
    decl_column = DW_AT_decl_column,
    decl_file = DW_AT_decl_file,
    decl_line = DW_AT_decl_line,
    declaration = DW_AT_declaration,
    encoding = DW_AT_encoding,
    frame_base = DW_AT_frame_base,
    high_pc = DW_AT_high_pc,
    linkage_name = DW_AT_linkage_name,
    location = DW_AT_location,
    low_pc = DW_AT_low_pc,
    name = DW_AT_name,
    ranges = DW_AT_ranges,
    specification = DW_AT_specification,
    type = DW_AT_type,
    upper_bound = DW_AT_upper_bound,
};

// Attribute forms - DW_FORM_*
enum class NativeDwarfAttributeForm : Dwarf_Half {
    addr = DW_FORM_addr,
    addrx = DW_FORM_addrx,
    addrx1 = DW_FORM_addrx1,
    addrx2 = DW_FORM_addrx2,
    addrx3 = DW_FORM_addrx3,
    addrx4 = DW_FORM_addrx4,
    GNU_addr_index = DW_FORM_GNU_addr_index,
    block = DW_FORM_block,
    block1 = DW_FORM_block1,
    block2 = DW_FORM_block2,
    block4 = DW_FORM_block4,
    data1 = DW_FORM_data1,
    data2 = DW_FORM_data2,
    data4 = DW_FORM_data4,
    data8 = DW_FORM_data8,
    data16 = DW_FORM_data16,
    exprloc = DW_FORM_exprloc,
    flag = DW_FORM_flag,
    flag_present = DW_FORM_flag_present,
    implicit_const = DW_FORM_implicit_const,
    line_strp = DW_FORM_line_strp,
    loclistx = DW_FORM_loclistx,
    ref1 = DW_FORM_ref1,
    ref2 = DW_FORM_ref2,
    ref4 = DW_FORM_ref4,
    ref8 = DW_FORM_ref8,
    ref_addr = DW_FORM_ref_addr,
    ref_sig8 = DW_FORM_ref_sig8,
    ref_sup4 = DW_FORM_ref_sup4,
    ref_sup8 = DW_FORM_ref_sup8,
    ref_udata = DW_FORM_ref_udata,
    GNU_ref_alt = DW_FORM_GNU_ref_alt,
    rnglistx = DW_FORM_rnglistx,
    sdata = DW_FORM_sdata,
    sec_offset = DW_FORM_sec_offset,
    string = DW_FORM_string,
    strp = DW_FORM_strp,
    strp_sup = DW_FORM_strp_sup,
    GNU_strp_alt = DW_FORM_GNU_strp_alt,
    strx = DW_FORM_strx,
    strx1 = DW_FORM_strx1,
    strx2 = DW_FORM_strx2,
    strx3 = DW_FORM_strx3,
    strx4 = DW_FORM_strx4,
    GNU_str_index = DW_FORM_GNU_str_index,
    udata = DW_FORM_udata,
};

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

    NativeDwarfAttribute(NativeDwarfAttributeTag tag, NativeDwarfAttributeForm form, Value value)
        : tag(tag), form(form), value(std::move(value)) {}

    NativeDwarfAttributeTag get_tag() const { return tag; }
    NativeDwarfAttributeForm get_form() const { return form; }
    const Value& get_value() const { return value; }

   private:
    NativeDwarfAttributeTag tag;
    NativeDwarfAttributeForm form;
    Value value;
};

}  // namespace ttexalens::native_elf
