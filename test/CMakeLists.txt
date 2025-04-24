# Include CPM
include(${PROJECT_SOURCE_DIR}/third_party/umd/cmake/CPM.cmake)

# Add packages
CPMAddPackage(
    NAME googletest
    GITHUB_REPOSITORY google/googletest
    GIT_TAG v1.13.0
    VERSION 1.13.0
    OPTIONS
        "INSTALL_GTEST OFF"
)

# Add subdirectories
add_subdirectory(${PROJECT_SOURCE_DIR}/test/ttexalens/pybind)
add_subdirectory(${PROJECT_SOURCE_DIR}/test/ttexalens/server)
