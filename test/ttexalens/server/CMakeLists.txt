file(GLOB_RECURSE TTEXALENS_SERVER_UNIT_TESTS_SRCS "*.cpp")
add_executable(ttexalens_server_unit_tests ${TTEXALENS_SERVER_UNIT_TESTS_SRCS})
target_link_libraries(ttexalens_server_unit_tests
    ttexalens_server_lib
    ttexalens_utils
    gtest
    gmock
    gtest_main
    pthread
)

set_target_properties(ttexalens_server_unit_tests PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)

set_target_properties(ttexalens_server_unit_tests PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
