file(GLOB_RECURSE TTEXALENS_PYBIND_UNIT_TESTS_SRCS "*.cpp")

nanobind_add_module(ttexalens_pybind_unit_tests ${TTEXALENS_PYBIND_UNIT_TESTS_SRCS})

target_link_libraries(ttexalens_pybind_unit_tests
    PRIVATE
    umd::device
    yaml-cpp
    pthread
)

target_include_directories(ttexalens_pybind_unit_tests
    PUBLIC
        $<TARGET_PROPERTY:ttexalens_pybind,INTERFACE_INCLUDE_DIRECTORIES>
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
