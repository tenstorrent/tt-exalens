// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "dwarf_die.hpp"
#include "dwarf_handle.hpp"

namespace ttexalens::native_elf {

class NativeDwarfInfo;

class NativeDwarfCompileUnit {
   public:
    NativeDwarfDiePtr get_die() const { return die; }
    Dwarf_Unsigned get_header_length() const { return header_length; }
    Dwarf_Half get_version() const { return version; }
    Dwarf_Unsigned get_abbrev_offset() const { return abbrev_offset; }
    Dwarf_Half get_address_size() const { return address_size; }
    Dwarf_Half get_length_size() const { return length_size; }
    Dwarf_Half get_extension_size() const { return extension_size; }
    Dwarf_Sig8 get_signature() const { return signature; }
    Dwarf_Unsigned get_type_offset() const { return type_offset; }
    Dwarf_Unsigned get_next_cu_offset() const { return next_cu_offset; }
    Dwarf_Half get_header_cu_type() const { return header_cu_type; }

   private:
    friend class NativeDwarfInfo;

    NativeDwarfCompileUnit() = default;

    // Lazy line context. First call invokes dwarf_srclines_b; later calls
    // return the cached context. Test the returned wrapper with operator bool
    // — empty means dwarf_srclines_b failed (loaded_line_context is set
    // regardless so we don't retry on every call).
    DwarfLineContextHandle& get_line_context() {
        if (!loaded_line_context) {
            loaded_line_context = true;
            DwarfErrorHandle error(die->get_state());
            Dwarf_Unsigned line_version = 0;
            Dwarf_Small table_count = 0;
            dwarf_srclines_b(*die, &line_version, &table_count, &line_context, &error);
        }
        return line_context;
    }

    NativeDwarfDiePtr die;
    Dwarf_Unsigned header_length = 0;
    Dwarf_Half version = 0;
    Dwarf_Unsigned abbrev_offset = 0;
    Dwarf_Half address_size = 0;
    Dwarf_Half length_size = 0;
    Dwarf_Half extension_size = 0;
    Dwarf_Sig8 signature{};
    Dwarf_Unsigned type_offset = 0;
    Dwarf_Unsigned next_cu_offset = 0;
    Dwarf_Half header_cu_type = 0;

    DwarfLineContextHandle line_context;
    bool loaded_line_context = false;
};

}  // namespace ttexalens::native_elf
