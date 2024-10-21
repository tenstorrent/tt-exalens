file(GLOB_RECURSE DEBUDA_SERVER_UNIT_TESTS_SRCS "*.cpp")
add_executable(debuda_server_unit_tests ${DEBUDA_SERVER_UNIT_TESTS_SRCS})
target_link_libraries(debuda_server_unit_tests
    debuda_server_lib
    debuda_utils
    gtest
    gmock
    gtest_main
    zmq
    pthread
)

set_target_properties(debuda_server_unit_tests PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
