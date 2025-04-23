# Include CPM
include(${PROJECT_SOURCE_DIR}/cmake/CPM.cmake)

# Add packages
CPMAddPackage(
    NAME googletest
    GITHUB_REPOSITORY google/googletest
    GIT_TAG v1.13.0
    VERSION 1.13.0
    OPTIONS
        "INSTALL_GTEST OFF"
)
