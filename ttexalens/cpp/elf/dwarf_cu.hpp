// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <string>
#include <vector>

#include "dwarf_die.hpp"
#include "dwarf_handle.hpp"

namespace ttexalens::native_elf {

namespace details {
class NativeElfFileImpl;
}  // namespace details

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
    friend class NativeDwarfDie;
    friend class details::NativeDwarfInfoImpl;

    NativeDwarfCompileUnit() = default;

    // Lazy load line context if necessary.
    DwarfLineContextHandle& get_line_context();

    // Lazy load CU source-file table if necessary.
    const std::vector<std::string>& get_srcfiles();

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

    std::vector<std::string> srcfiles;
    bool loaded_srcfiles = false;
};

}  // namespace ttexalens::native_elf
