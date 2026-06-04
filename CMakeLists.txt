cmake_minimum_required(VERSION 3.22)
cmake_policy(VERSION 3.22)

# Emit compile_commands.json so clangd can find each TU's flags. We symlink it
# into the repo root below for the Makefile-driven dev flow.
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Read version from VERSION file
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" TT_EXALENS_VERSION)
string(STRIP "${TT_EXALENS_VERSION}" TT_EXALENS_VERSION)

project(ttexalens VERSION ${TT_EXALENS_VERSION} LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Set default values for variables/options
set(TTEXALENS_HOME "${PROJECT_SOURCE_DIR}")
option(BUILD_PYTHON_WHEEL "Skip SFPI download and RISCV kernel builds (pure-Python wheel)" OFF)

# build_riscv: shared output dir for RISCV kernel builds AND sfpi download.
# Decoupled from host build mode so switching Debug<->Release doesn't trigger
# kernel rebuilds or toolchain redownload.
file(MAKE_DIRECTORY "${CMAKE_SOURCE_DIR}/build_riscv")

# Symlinks for the Makefile-driven dev flow:
#   build/                      -> active build dir (build_debug or build_release)
#   build/riscv-src/            -> build_riscv/ (shared across Debug/Release)
#   compile_commands.json       -> build_*/compile_commands.json (so clangd finds it)
# Skipped under BUILD_PYTHON_WHEEL because scikit-build-core uses its own
# build dir and shouldn't clobber the dev symlinks.
if(NOT BUILD_PYTHON_WHEEL)
    file(REMOVE "${CMAKE_BINARY_DIR}/riscv-src")
    file(CREATE_LINK "${CMAKE_SOURCE_DIR}/build_riscv" "${CMAKE_BINARY_DIR}/riscv-src" SYMBOLIC)

    # `build` -> current binary dir. Only refresh if the existing entry is
    # absent or already a symlink (so we never blow away a real `build/`
    # directory left by other tooling).
    set(_build_link "${CMAKE_SOURCE_DIR}/build")
    if(NOT EXISTS "${_build_link}" OR IS_SYMLINK "${_build_link}")
        file(REMOVE "${_build_link}")
        file(CREATE_LINK "${CMAKE_BINARY_DIR}" "${_build_link}" SYMBOLIC)
    endif()

    # compile_commands.json -> active build's copy, so clangd at the repo root works.
    set(_ccjson_link "${CMAKE_SOURCE_DIR}/compile_commands.json")
    if(NOT EXISTS "${_ccjson_link}" OR IS_SYMLINK "${_ccjson_link}")
        file(REMOVE "${_ccjson_link}")
        file(CREATE_LINK "${CMAKE_BINARY_DIR}/compile_commands.json" "${_ccjson_link}" SYMBOLIC)
    endif()
endif()

# The Python wheel is pure Python: it no longer bundles the SFPI GDB client
# (the binary is not portable across platforms; it is located at runtime via
# the system install, SFPI_ROOT, or PATH instead - see get_gdb_client_path()).
# So wheel builds skip both the SFPI download and the RISCV kernel build, which
# also lets the wheel be built on hosts that SFPI does not ship binaries for.
if(NOT BUILD_PYTHON_WHEEL)
    # SFPI provides the RISCV toolchain used to build the test kernels.
    include(${PROJECT_SOURCE_DIR}/cmake/sfpi_release.cmake)
    add_subdirectory(${PROJECT_SOURCE_DIR}/riscv-src)
endif()

# Dependencies for the _native_ttexalens Python extension module, and the module itself.
include(${PROJECT_SOURCE_DIR}/cmake/native_elf.cmake)
add_subdirectory(${PROJECT_SOURCE_DIR}/ttexalens/cpp/elf)
add_subdirectory(${PROJECT_SOURCE_DIR}/ttexalens/cpp/nanobind)
