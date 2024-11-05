add_executable(debuda-server-standalone)

file(GLOB_RECURSE DEBUDA_SERVER_SRCS "*.cpp")
target_sources(debuda-server-standalone PRIVATE ${DEBUDA_SERVER_SRCS})

target_link_libraries(debuda-server-standalone
    PRIVATE debuda_server_lib debuda_utils yaml-cpp stdc++fs pthread
)

set_target_properties(debuda-server-standalone PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)

set_target_properties(debuda-server-standalone PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
