# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

# Pure C++ ELF reader library — no Python / nanobind dependency. Wrapped for
# Python in the sibling `native_elf` subproject.

add_library(ttexalens_elf STATIC
    private/elf_file_impl.cpp
    private/dwarf_info_impl.cpp
    elf_file.cpp
    dwarf_info.cpp
    dwarf_attribute.cpp
    dwarf_die.cpp
    dwarf_cu.cpp
    dwarf_frame.cpp
    dwarf_location.cpp
    variable.cpp
)
target_compile_features(ttexalens_elf PUBLIC cxx_std_20)
target_include_directories(ttexalens_elf PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(ttexalens_elf
    PUBLIC elfio libdwarf::dwarf-static
)
set_target_properties(ttexalens_elf PROPERTIES POSITION_INDEPENDENT_CODE ON)
