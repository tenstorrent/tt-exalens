# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

include_guard(GLOBAL)

# CPM is already available under the exalens build and CPM-based parents; pull it
# in otherwise so this file also works when included on its own.
if(NOT COMMAND CPMAddPackage)
    include(${CMAKE_CURRENT_LIST_DIR}/CPM.cmake)
endif()

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
    VERSION 2.9.2
    OPTIONS "CMAKE_MESSAGE_LOG_LEVEL NOTICE"
)
