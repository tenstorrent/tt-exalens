set(SFPI_RELEASE_PATH "${TTEXALENS_HOME}/build/sfpi")

if(NOT EXISTS "${SFPI_RELEASE_PATH}")
    message(STATUS "Downloading sfpi release")

    include(FetchContent)
    FetchContent_Declare(
        sfpi
        URL https://github.com/tenstorrent/sfpi/releases/download/v6.11.1/sfpi-x86_64_Linux.txz
        URL_HASH MD5=14ade50b3fdf3fff5078195332edc15a
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
        SOURCE_DIR ${SFPI_RELEASE_PATH}
    )
    FetchContent_MakeAvailable(sfpi)
else()
    message(STATUS "Using sfpi release from ${SFPI_RELEASE_PATH}")
endif()
