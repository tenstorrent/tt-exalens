cmake_minimum_required(VERSION 3.22)
cmake_policy(VERSION 3.22)

# Read version from VERSION file
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" TT_EXALENS_VERSION)
string(STRIP "${TT_EXALENS_VERSION}" TT_EXALENS_VERSION)

project(ttexalens VERSION ${TT_EXALENS_VERSION})

# Set default values for variables/options
set(TTEXALENS_HOME "${PROJECT_SOURCE_DIR}")
option(BUILD_PYTHON_WHEEL "Only download SFPI, skip RISCV kernel builds" OFF)
option(STRIP_SYMBOLS "Strip symbols from GDB binary" OFF)

# Check for SFPI release
include(${PROJECT_SOURCE_DIR}/cmake/sfpi_release.cmake)

# Build RISCV kernels unless building Python wheel
if(NOT BUILD_PYTHON_WHEEL)
    add_subdirectory(${PROJECT_SOURCE_DIR}/riscv-src)
endif()

# Install target for Python wheel: copy GDB binary to source tree
set(SFPI_GDB_SOURCE "${SFPI_RELEASE_PATH}/compiler/bin/riscv-tt-elf-gdb")
set(SFPI_GDB_DEST "${CMAKE_SOURCE_DIR}/build/stripped/riscv-tt-elf-gdb")

add_custom_target(install-gdb-for-wheel ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_SOURCE_DIR}/build/stripped"
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
