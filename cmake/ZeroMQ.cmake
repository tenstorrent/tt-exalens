
# Try to find if ZeroMQ is installed
set(PKG_CONFIG_USE_CMAKE_PREFIX_PATH ON)
find_package(PkgConfig)
pkg_check_modules(PC_LIBZMQ QUIET libzmq)
set(ZeroMQ_VERSION ${PC_LIBZMQ_VERSION})
find_path(ZeroMQ_INCLUDE_DIR zmq.h PATHS ${ZeroMQ_DIR}/include ${PC_LIBZMQ_INCLUDE_DIRS})
find_library(ZeroMQ_LIBRARY NAMES zmq PATHS ${ZeroMQ_DIR}/lib ${PC_LIBZMQ_LIBDIR} ${PC_LIBZMQ_LIBRARY_DIRS})
if(ZeroMQ_LIBRARY)
    set(ZeroMQ_FOUND ON)
endif()

# ZeroMQ dependency
if(NOT ZeroMQ_FOUND)
    CPMAddPackage(
    NAME libzmq
    GITHUB_REPOSITORY zeromq/libzmq
    GIT_TAG v4.3.5
    OPTIONS
        "WITH_PERF_TOOL OFF"
        "ZMQ_BUILD_TESTS OFF"
        "BUILD_SHARED OFF"
        "BUILD_STATIC ON"
    )

    CPMAddPackage(
    NAME cppzmq
    GITHUB_REPOSITORY zeromq/cppzmq
    GIT_TAG v4.10.0
    OPTIONS
        "CPPZMQ_BUILD_TESTS OFF"
    )
else()
    add_library(cppzmq-static INTERFACE)
    target_link_libraries(cppzmq-static INTERFACE zmq)
endif()
