file(GLOB_RECURSE TTEXALENS_PYBIND_SRCS "src/*.cpp")
add_library(ttexalens_pybind SHARED ${TTEXALENS_PYBIND_SRCS})
set_target_properties(ttexalens_pybind PROPERTIES
    OUTPUT_NAME "ttexalens_pybind"
    PREFIX ""
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)
target_link_libraries(ttexalens_pybind
    ttexalens_server_lib
    umd::device
    yaml-cpp
    pthread
)
target_include_directories(ttexalens_pybind
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/inc
    PRIVATE
        ${pybind11_INCLUDE_DIR}
        ${Python3_INCLUDE_DIRS}
)
set_target_properties(ttexalens_pybind PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)

add_pybind_stubgen(ttexalens_pybind)
