add_executable(ttlens-server-standalone)

file(GLOB_RECURSE TTLENS_SERVER_SRCS "*.cpp")
target_sources(ttlens-server-standalone PRIVATE ${TTLENS_SERVER_SRCS})

target_link_libraries(ttlens-server-standalone
    PRIVATE ttlens_server_lib ttlens_utils yaml-cpp stdc++fs pthread
)

set_target_properties(ttlens-server-standalone PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)

set_target_properties(ttlens-server-standalone PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
