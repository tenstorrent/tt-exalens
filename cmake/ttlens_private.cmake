# Check if there is ttlens_private project already in cpmcache.
# If it is not, we should check if user has access to private repository.

set(TTLENS_PRIVATE_GIT_REPOSITORY "git@yyz-gitlab.local.tenstorrent.com:tenstorrent/tt-lens-private.git")
set(TTLENS_PRIVATE_GIT_TAG "b8dea1699eb9a5159cab1e57e0adffa49b82a9e9")
option(DOWNLOAD_TTLENS_PRIVATE "Download tt-lens private repository" OFF)

if (DOWNLOAD_TTLENS_PRIVATE)
    if (NOT EXISTS "$ENV{CPM_SOURCE_CACHE}/ttlens_private")

        # Trying to download private repository which will provide additional functionality that is not required
        # We do this by creating fake source directory and running CMake in it

        message(STATUS "Checking access for tt-lens-private repository...")

        file(COPY "${CMAKE_CURRENT_LIST_DIR}/ttlens_private_check.cmake"
            DESTINATION "${CMAKE_BINARY_DIR}/tt_lens_private_check")

        file(WRITE "${CMAKE_BINARY_DIR}/tt_lens_private_check/CMakeLists.txt" "cmake_minimum_required(VERSION 3.16)\ncmake_policy(VERSION 3.16)\ninclude(\${CMAKE_CURRENT_LIST_DIR}/ttlens_private_check.cmake)")

        message(STATUS "Checking for git-lfs...")
        find_program(GIT_LFS_EXECUTABLE NAMES git-lfs)
        message(STATUS "git-lfs executable: ${GIT_LFS_EXECUTABLE}")

        if(GIT_LFS_EXECUTABLE MATCHES "NOTFOUND")
            # git-lfs is not installed
            message(FATAL_ERROR "git-lfs is not installed. Please install git-lfs.")
            set(DOWNLOAD_TTLENS_PRIVATE OFF)
        else()
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
                )
            endif()

            # Check if we succeeded in cloning the private repository
            if(NOT TTLENS_PRIVATE_CHECK_RESULT EQUAL "0")
                message(WARNING "tt-lens-private project check failed with error code ${TTLENS_PRIVATE_CHECK_RESULT}. Continuing without it.")
                set(DOWNLOAD_TTLENS_PRIVATE OFF)
            endif()
        endif()

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
