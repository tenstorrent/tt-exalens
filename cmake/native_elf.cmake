# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0
#
# Dependencies for the _native_elf Python extension module:
#   - Python development headers
#   - nanobind (via CPM)
#   - libdwarf (via CPM, static, PIC)

include(${PROJECT_SOURCE_DIR}/cmake/CPM.cmake)

# Python development headers (needed by nanobind)
set(Python3_FIND_STRATEGY LOCATION)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
message(STATUS "Python3 include dirs: ${Python3_INCLUDE_DIRS}")

# nanobind expects "Python_*" variables — mirror them from Python3_*.
if(Python3_FOUND AND NOT Python_FOUND)
    set(Python_FOUND ${Python3_FOUND})
    set(Python_EXECUTABLE ${Python3_EXECUTABLE})
    set(Python_INCLUDE_DIRS ${Python3_INCLUDE_DIRS})
    set(Python_LIBRARIES ${Python3_LIBRARIES})
    set(Python_Development_FOUND ${Python3_Development_FOUND})
endif()

CPMAddPackage(
    NAME nanobind
    GITHUB_REPOSITORY wjakob/nanobind
    VERSION 2.7.0
    OPTIONS "CMAKE_MESSAGE_LOG_LEVEL NOTICE"
)

# libdwarf — static archive, PIC so it can link into a shared module.
# We disable dwarfdump/dwarfexample/tests to keep build time minimal.
# Decompression is disabled for the first build to avoid pulling in zlib/zstd
# as transitive deps; revisit if any ELFs we care about use SHF_COMPRESSED.
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

# ELFIO — header-only C++ ELF reader. Used for section list + symbol table
# (libdwarf v2.x doesn't expose those publicly).
CPMAddPackage(
    NAME ELFIO
    GITHUB_REPOSITORY serge1/ELFIO
    GIT_TAG Release_3.12
    EXCLUDE_FROM_ALL YES
    DOWNLOAD_ONLY YES
)
# ELFIO's own CMakeLists creates a tests/examples — we only need the headers.
add_library(elfio INTERFACE)
target_include_directories(elfio INTERFACE "${ELFIO_SOURCE_DIR}")
