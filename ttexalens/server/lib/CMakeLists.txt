# Library project
file(GLOB TTEXALENS_SERVER_LIB_SRCS "src/*.cpp")
add_library(ttexalens_server_lib STATIC ${TTEXALENS_SERVER_LIB_SRCS})
add_dependencies(ttexalens_server_lib ttexalens_jtag_lib)
target_link_libraries(ttexalens_server_lib
    PUBLIC umd::device fmt cppzmq-static dl
)
target_include_directories(ttexalens_server_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/inc
)
set_target_properties(ttexalens_server_lib PROPERTIES
    OUTPUT_NAME libttexalensserver
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    POSITION_INDEPENDENT_CODE ON
)
