cmake_minimum_required(VERSION 3.16)
cmake_policy(VERSION 3.16)

# Sanity check, forgetting to clone submodules is a common omission and results in a poor error message
if (NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/third_party/umd/CMakeLists.txt")
    message(FATAL_ERROR "Missing submodules.  Run: git submodule update --init --recursive")
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(TT_UMD_BUILD_SIMULATION "Force UMD to include its simulation harnessing" ON)

include(third_party/umd/cmake/compilers.cmake)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

if (DEFINED ENV{CMAKE_C_COMPILER} AND DEFINED ENV{CMAKE_CXX_COMPILER})
    message(STATUS "Setting C and C++ compiler from environment variables")
    set(CMAKE_C_COMPILER $ENV{CMAKE_C_COMPILER})
    set(CMAKE_CXX_COMPILER $ENV{CMAKE_CXX_COMPILER})
endif()

if (CMAKE_CXX_COMPILER AND CMAKE_C_COMPILER)
    message(STATUS "Using specifed C++ compiler: ${CMAKE_CXX_COMPILER}")
    message(STATUS "Using specifed C compiler: ${CMAKE_C_COMPILER}")
else()
    message(STATUS "No C or C++ compiler specified, defaulting to Clang-17")
    FIND_AND_SET_CLANG17()
endif()

project(ttexalens)

CHECK_COMPILERS()

# Creating interface libraries needed for UMD
add_library(linker_flags INTERFACE)

add_library(compiler_warnings INTERFACE)
target_compile_options(compiler_warnings INTERFACE -Werror -Wdelete-non-virtual-dtor -Wreturn-type -Wswitch -Wuninitialized -Wno-unused-parameter)

add_library(compiler_flags INTERFACE)
target_link_libraries(compiler_flags INTERFACE linker_flags)
target_compile_options(compiler_flags INTERFACE -mavx2 -fPIC -DFMT_HEADER_ONLY -fvisibility-inlines-hidden -fno-lto)

# Find Python3
set(Python3_FIND_STRATEGY LOCATION)
find_package (Python3 COMPONENTS Interpreter Development)
message(STATUS "Python3 include dirs: ${Python3_INCLUDE_DIRS}")

# Set default values for variables/options
set(CMAKE_BUILD_BIN_DIR "${CMAKE_BINARY_DIR}/bin")
set(TTEXALENS_HOME "${PROJECT_SOURCE_DIR}")
set(UMD_HOME "${PROJECT_SOURCE_DIR}/third_party/umd")

# Third party dependencies
add_subdirectory(${PROJECT_SOURCE_DIR}/third_party/umd)

# Handle symlinks: build should point to build_debug or build_release,
# and build_*/riscv-src should point to build_elfs
set(BUILD_SYMLINK "${CMAKE_SOURCE_DIR}/build")
set(ELF_SYMLINK "${CMAKE_BINARY_DIR}/riscv-src")
file(MAKE_DIRECTORY "build_elfs")

# Refresh the symlinks
file(REMOVE "${BUILD_SYMLINK}")
file(CREATE_LINK "${CMAKE_BINARY_DIR}" "${BUILD_SYMLINK}" SYMBOLIC)
file(REMOVE "${ELF_SYMLINK}")
file(CREATE_LINK "../build_elfs" "${ELF_SYMLINK}" SYMBOLIC)

# Check for SFPI release
include(${PROJECT_SOURCE_DIR}/cmake/sfpi_release.cmake)

# Check for ZeroMQ
include(${PROJECT_SOURCE_DIR}/cmake/ZeroMQ.cmake)

# Including private repository
include(${PROJECT_SOURCE_DIR}/cmake/ttexalens_private.cmake)

# Include pybind custom functions
include(${PROJECT_SOURCE_DIR}/cmake/pybind.cmake)

# Add subdirectories
add_subdirectory(${PROJECT_SOURCE_DIR}/ttexalens)
add_subdirectory(${PROJECT_SOURCE_DIR}/utils)
add_subdirectory(${PROJECT_SOURCE_DIR}/test)

# As build_<type>/riscv-src is a symlink, CMake can't put its configuration files there
# directly, so we specify here that it should place them in build_elfs instead.
add_subdirectory(${PROJECT_SOURCE_DIR}/riscv-src ${CMAKE_BINARY_DIR}/../build_elfs)
