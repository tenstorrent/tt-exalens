# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0
#
# Third-party dependencies for the native ELF reader library (ttexalens_elf):
#   - libdwarf (via CPM; static, PIC)
#   - ELFIO    (header-only)

include_guard(GLOBAL)

# CPM is already available under the exalens build and CPM-based parents; pull it
# in otherwise so this file also works when included on its own.
if(NOT COMMAND CPMAddPackage)
    include(${CMAKE_CURRENT_LIST_DIR}/CPM.cmake)
endif()

# libdwarf — static archive, PIC so it can also link into a shared module.
# dwarfdump/example/tests off to keep build time minimal. Decompression off to
# avoid pulling in zlib/zstd (revisit if any ELFs we care about use SHF_COMPRESSED).
if(NOT TARGET libdwarf::dwarf-static)
    CPMAddPackage(
        NAME libdwarf
        GITHUB_REPOSITORY davea42/libdwarf-code
        GIT_TAG v2.3.1
        EXCLUDE_FROM_ALL YES
        OPTIONS
            "BUILD_NON_SHARED TRUE"
            "BUILD_SHARED FALSE"
            "BUILD_DWARFDUMP FALSE"
            "BUILD_DWARFGEN FALSE"
            "BUILD_DWARFEXAMPLE FALSE"
            "DO_TESTING FALSE"
            "PIC_ALWAYS TRUE"
            "ENABLE_DECOMPRESSION FALSE"
            "CMAKE_MESSAGE_LOG_LEVEL NOTICE"
    )
endif()

# ELFIO — header-only C++ ELF reader (section list + symbol table; libdwarf v2.x
# doesn't expose those publicly). DOWNLOAD_ONLY: we only want the headers.
if(NOT TARGET elfio)
    CPMAddPackage(
        NAME ELFIO
        GITHUB_REPOSITORY serge1/ELFIO
        GIT_TAG Release_3.12
        EXCLUDE_FROM_ALL YES
        DOWNLOAD_ONLY YES
    )
    add_library(elfio INTERFACE)
    target_include_directories(elfio SYSTEM INTERFACE "${ELFIO_SOURCE_DIR}")
endif()
