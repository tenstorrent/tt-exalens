file(GLOB_RECURSE TTEXALENS_PYBIND_UNIT_TESTS_SRCS "*.cpp")

set(TTEXALENS_PYBIND_PATH "${CMAKE_SOURCE_DIR}/ttexalens/pybind")

# Add source files from ttexalens_pybind project using project source directory
file(GLOB TTEXALENS_PYBIND_SRCS "${TTEXALENS_PYBIND_PATH}/src/*.cpp")

# Combine with unit test sources
set(ALL_SRCS ${TTEXALENS_PYBIND_UNIT_TESTS_SRCS} ${TTEXALENS_PYBIND_SRCS})

nanobind_add_module(ttexalens_pybind_unit_tests ${ALL_SRCS})

target_include_directories(ttexalens_pybind_unit_tests
    PRIVATE
        ${TTEXALENS_PYBIND_PATH}/inc
)
target_link_libraries(ttexalens_pybind_unit_tests
    PRIVATE
    ttexalens_server_lib
    umd::device
    yaml-cpp
    pthread
)

set_target_properties(ttexalens_pybind_unit_tests PROPERTIES
    OUTPUT_NAME "ttexalens_pybind_unit_tests"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)

set_target_properties(ttexalens_pybind_unit_tests PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)
add_pybind_stubgen(ttexalens_pybind_unit_tests)
