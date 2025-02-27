file(GLOB_RECURSE TTEXALENS_PYBIND_SRCS "src/*.cpp")
add_library(ttlens_pybind SHARED ${TTEXALENS_PYBIND_SRCS})
set_target_properties(ttlens_pybind PROPERTIES
    OUTPUT_NAME "ttlens_pybind"
    PREFIX ""
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)
target_link_libraries(ttlens_pybind
    ttlens_server_lib
    umd::device
    yaml-cpp
    pthread
)
target_include_directories(ttlens_pybind
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/inc
    PRIVATE
        ${pybind11_INCLUDE_DIR}
        ${Python3_INCLUDE_DIRS}
)
set_target_properties(ttlens_pybind PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)
