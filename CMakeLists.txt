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
option(BUILD_PYTHON_WHEEL "Only download SFPI, skip RISCV kernel builds" OFF)
option(STRIP_SYMBOLS "Strip symbols from GDB binary" OFF)

# build_riscv: shared output dir for RISCV kernel builds AND sfpi download.
# Decoupled from host build mode so switching Debug<->Release doesn't trigger
# kernel rebuilds or toolchain redownload. Created unconditionally because
# sfpi_release.cmake writes the toolchain archive here even in wheel builds.
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

# Check for SFPI release (writes to build_riscv/, see sfpi_release.cmake)
include(${PROJECT_SOURCE_DIR}/cmake/sfpi_release.cmake)

# Build RISCV kernels unless building Python wheel
if(NOT BUILD_PYTHON_WHEEL)
    add_subdirectory(${PROJECT_SOURCE_DIR}/riscv-src)
endif()

# Dependencies for the _native_ttexalens Python extension module, and the module itself.
include(${PROJECT_SOURCE_DIR}/cmake/native_elf.cmake)
add_subdirectory(${PROJECT_SOURCE_DIR}/ttexalens/cpp/elf)
add_subdirectory(${PROJECT_SOURCE_DIR}/ttexalens/cpp/nanobind)

# Staging copy of the GDB binary for wheel packaging. Lives under the current
# CMAKE_BINARY_DIR so dev and wheel builds keep their staging trees separate.
set(SFPI_GDB_SOURCE "${SFPI_RELEASE_PATH}/compiler/bin/riscv-tt-elf-gdb")
set(SFPI_GDB_DEST "${CMAKE_BINARY_DIR}/stripped/riscv-tt-elf-gdb")

add_custom_target(install-gdb-for-wheel ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_BINARY_DIR}/stripped"
    COMMAND ${CMAKE_COMMAND} -E copy "${SFPI_GDB_SOURCE}" "${SFPI_GDB_DEST}"
    COMMENT "Copying GDB binary for Python wheel packaging"
)

# Add optional strip command if STRIP_SYMBOLS is enabled
if(STRIP_SYMBOLS)
    add_custom_command(TARGET install-gdb-for-wheel POST_BUILD
        COMMAND strip "${SFPI_GDB_DEST}"
        COMMENT "Stripping symbols from GDB binary"
    )
endif()

# Install the GDB binary for the wheel when BUILD_PYTHON_WHEEL is enabled
if(BUILD_PYTHON_WHEEL)
    install(FILES "${SFPI_GDB_DEST}"
            DESTINATION "sfpi/compiler/bin"
            COMPONENT python_wheel)
endif()
