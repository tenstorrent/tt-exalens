// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_cu.hpp"

namespace ttexalens::native_elf {

DwarfLineContextHandle& DwarfCompileUnit::get_line_context() {
    if (!loaded_line_context) {
        loaded_line_context = true;
        DwarfErrorHandle error(die->get_state());
        Dwarf_Unsigned line_version = 0;
        Dwarf_Small table_count = 0;
        dwarf_srclines_b(*die, &line_version, &table_count, &line_context, &error);
    }
    return line_context;
}

const std::vector<std::string>& DwarfCompileUnit::get_srcfiles() {
    if (!loaded_srcfiles) {
        loaded_srcfiles = true;
        Dwarf_Debug dbg = die->get_state();
        DwarfErrorHandle error(dbg);
        char** files = nullptr;
        Dwarf_Signed file_count = 0;
        if (dwarf_srcfiles(*die, &files, &file_count, &error) == DW_DLV_OK && files != nullptr) {
            srcfiles.reserve(static_cast<size_t>(file_count));
            for (Dwarf_Signed i = 0; i < file_count; ++i) {
                srcfiles.emplace_back(files[i] != nullptr ? files[i] : "");
                dwarf_dealloc(dbg, files[i], DW_DLA_STRING);
            }
            dwarf_dealloc(dbg, files, DW_DLA_LIST);
        }
    }
    return srcfiles;
}

}  // namespace ttexalens::native_elf
