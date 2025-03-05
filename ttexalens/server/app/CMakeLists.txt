add_executable(ttexalens-server-standalone)

file(GLOB_RECURSE TTEXALENS_SERVER_SRCS "*.cpp")
target_sources(ttexalens-server-standalone PRIVATE ${TTEXALENS_SERVER_SRCS})

target_link_libraries(ttexalens-server-standalone
    PRIVATE ttexalens_server_lib ttexalens_utils yaml-cpp stdc++fs pthread
)

set_target_properties(ttexalens-server-standalone PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)

set_target_properties(ttexalens-server-standalone PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
)
