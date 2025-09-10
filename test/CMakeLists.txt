# Include CPM
include(${PROJECT_SOURCE_DIR}/third_party/umd/cmake/CPM.cmake)

# Add packages
CPMAddPackage(
    NAME googletest
    GITHUB_REPOSITORY google/googletest
    GIT_TAG v1.14.0
    VERSION 1.14.0
    OPTIONS
        "INSTALL_GTEST OFF"
)

# Add subdirectories
add_subdirectory(${PROJECT_SOURCE_DIR}/test/ttexalens/pybind)
