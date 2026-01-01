cmake_minimum_required(VERSION 3.22)
cmake_policy(VERSION 3.22)

# Read version from VERSION file
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/VERSION" TT_EXALENS_VERSION)
string(STRIP "${TT_EXALENS_VERSION}" TT_EXALENS_VERSION)

project(ttexalens VERSION ${TT_EXALENS_VERSION})

# Set default values for variables/options
set(TTEXALENS_HOME "${PROJECT_SOURCE_DIR}")

# Check for SFPI release
include(${PROJECT_SOURCE_DIR}/cmake/sfpi_release.cmake)

# As build_<type>/riscv-src is a symlink, CMake can't put its configuration files there
# directly, so we specify here that it should place them in build_riscv instead.
add_subdirectory(${PROJECT_SOURCE_DIR}/riscv-src ${PROJECT_SOURCE_DIR}/build_riscv)
