file(GLOB_RECURSE DEBUDA_PYBIND_SRCS "src/*.cpp")
add_library(debuda_pybind SHARED ${DEBUDA_PYBIND_SRCS})
set_target_properties(debuda_pybind PROPERTIES
    OUTPUT_NAME "tt_dbd_pybind"
    PREFIX ""
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)
target_link_libraries(debuda_pybind
    debuda_server_lib
    umd_device
    yaml-cpp
    pthread
)
target_include_directories(debuda_pybind
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/inc
    PRIVATE
        ${pybind11_INCLUDE_DIR}
        ${Python3_INCLUDE_DIRS}
)
set_target_properties(debuda_pybind PROPERTIES
    BUILD_WITH_INSTALL_RPATH true
    INSTALL_RPATH "$ORIGIN:$ORIGIN/../lib"
)
