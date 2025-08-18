file(GLOB_RECURSE TTEXALENS_PYBIND_SRCS "src/*.cpp")
nanobind_add_module(ttexalens_pybind ${TTEXALENS_PYBIND_SRCS})
set_target_properties(ttexalens_pybind PROPERTIES
    OUTPUT_NAME "ttexalens_pybind"
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)
target_link_libraries(ttexalens_pybind
    PRIVATE
    ttexalens_server_lib
    umd::device
    yaml-cpp
    pthread
)
target_include_directories(ttexalens_pybind
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/inc
)
set_target_properties(ttexalens_pybind PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)

add_pybind_stubgen(ttexalens_pybind)
