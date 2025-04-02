set(SFPI_RELEASE_PATH "${TTEXALENS_HOME}/build/sfpi")

if(NOT EXISTS "${SFPI_RELEASE_PATH}")
    message(STATUS "Downloading sfpi release")

    include(FetchContent)
    FetchContent_Declare(
        sfpi
        URL
            https://github.com/tenstorrent/sfpi/releases/download/v6.6.0/sfpi-release.tgz
        URL_HASH MD5=8eed4d1128809e2fb2df00e04b5a51ea
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
        SOURCE_DIR
        ${SFPI_RELEASE_PATH}
    )
    FetchContent_MakeAvailable(sfpi)
else()
    message(STATUS "Using sfpi release from ${SFPI_RELEASE_PATH}")
endif()
