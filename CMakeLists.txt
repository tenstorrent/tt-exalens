cmake_minimum_required(VERSION 3.22)
cmake_policy(VERSION 3.22)

# Read version from VERSION file
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" TT_EXALENS_VERSION)
string(STRIP "${TT_EXALENS_VERSION}" TT_EXALENS_VERSION)

project(ttexalens VERSION ${TT_EXALENS_VERSION})

# Set default values for variables/options
set(TTEXALENS_HOME "${PROJECT_SOURCE_DIR}")
option(BUILD_PYTHON_WHEEL "Skip SFPI download and RISCV kernel builds (pure-Python wheel)" OFF)

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
