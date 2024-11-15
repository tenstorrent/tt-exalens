file(GLOB_RECURSE TTLENS_PYBIND_UNIT_TESTS_SRCS "*.cpp")

add_library(ttlens_pybind_unit_tests SHARED ${TTLENS_PYBIND_UNIT_TESTS_SRCS})

set_target_properties(ttlens_pybind_unit_tests PROPERTIES
    OUTPUT_NAME "ttlens_pybind_unit_tests"
    PREFIX ""
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)

target_link_libraries(ttlens_pybind_unit_tests
    ttlens_pybind
    pthread
)

target_include_directories(ttlens_pybind_unit_tests PRIVATE
    ${pybind11_INCLUDE_DIR}
    ${Python3_INCLUDE_DIRS}
)
set_target_properties(ttlens_pybind_unit_tests PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)
