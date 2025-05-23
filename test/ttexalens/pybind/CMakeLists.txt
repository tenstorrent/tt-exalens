file(GLOB_RECURSE TTEXALENS_PYBIND_UNIT_TESTS_SRCS "*.cpp")

add_library(ttexalens_pybind_unit_tests SHARED ${TTEXALENS_PYBIND_UNIT_TESTS_SRCS})

set_target_properties(ttexalens_pybind_unit_tests PROPERTIES
    OUTPUT_NAME "ttexalens_pybind_unit_tests"
    PREFIX ""
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)

target_link_libraries(ttexalens_pybind_unit_tests
    ttexalens_pybind
    pthread
)

target_include_directories(ttexalens_pybind_unit_tests PRIVATE
    ${pybind11_INCLUDE_DIR}
    ${Python3_INCLUDE_DIRS}
)
set_target_properties(ttexalens_pybind_unit_tests PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)
add_pybind_stubgen(ttexalens_pybind_unit_tests)
