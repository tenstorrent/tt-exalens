# Check if there is ttlens_private project already in cpmcache.
# If it is not, we should check if user has access to private repository.

set(TTLENS_PRIVATE_GIT_REPOSITORY "git@yyz-gitlab.local.tenstorrent.com:tenstorrent/tt-lens-private.git")
set(TTLENS_PRIVATE_GIT_TAG "vjovanovic/moving_to_cmake")#"main") # TODO: Fix this before check-in!!!
set(DOWNLOAD_TTLENS_PRIVATE ON)

if (NOT EXISTS "$ENV{CPM_SOURCE_CACHE}/ttlens_private")

    # Trying to download private repository which will provide additional functionality that is not required
    # We do this by creating fake source directory and running CMake in it

    message(STATUS "Checking access for tt-lens-private repository...")

    file(COPY "${CMAKE_CURRENT_LIST_DIR}/ttlens_private_check.cmake"
        DESTINATION "${CMAKE_BINARY_DIR}/tt_lens_private_check")

    file(WRITE "${CMAKE_BINARY_DIR}/tt_lens_private_check/CMakeLists.txt" "include(${CMAKE_CURRENT_LIST_DIR}/ttlens_private_check.cmake)")

    execute_process(
        COMMAND ${CMAKE_COMMAND} -B build -Wno-dev -DTTLENS_PRIVATE_GIT_REPOSITORY=${TTLENS_PRIVATE_GIT_REPOSITORY} -DTTLENS_PRIVATE_GIT_TAG=${TTLENS_PRIVATE_GIT_TAG}
        WORKING_DIRECTORY "${CMAKE_BINARY_DIR}/tt_lens_private_check"
        RESULT_VARIABLE TTLENS_PRIVATE_CHECK_RESULT
        OUTPUT_VARIABLE TTLENS_PRIVATE_CHECK_OUTPUT
        ERROR_QUIET
    )

    if(TTLENS_PRIVATE_CHECK_RESULT EQUAL "0")
        execute_process(
            COMMAND ${CMAKE_COMMAND} --build build
            WORKING_DIRECTORY "${CMAKE_BINARY_DIR}/tt_lens_private_check"
            RESULT_VARIABLE TTLENS_PRIVATE_CHECK_RESULT
            OUTPUT_VARIABLE TTLENS_PRIVATE_CHECK_OUTPUT
            ERROR_QUIET
        )
    endif()

    # Check if we succeeded in cloning the private repository
    if(NOT TTLENS_PRIVATE_CHECK_RESULT EQUAL "0")
        message(WARNING "tt-lens-private project check failed with error code ${TTLENS_PRIVATE_CHECK_RESULT}. Continuing without it.")
        set(DOWNLOAD_TTLENS_PRIVATE OFF)
    endif()
endif()

if (DOWNLOAD_TTLENS_PRIVATE)
    CPMAddPackage(
        NAME ttlens_private
        GIT_REPOSITORY ${TTLENS_PRIVATE_GIT_REPOSITORY}
        GIT_TAG ${TTLENS_PRIVATE_GIT_TAG}
    )
else()
    # Since we don't have ttlens_private project, we need to create empty jtag interface library
    add_library(ttlens_jtag_lib INTERFACE)
endif()
