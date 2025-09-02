set(SFPI_DOWNLOAD_URL "https://github.com/tenstorrent/sfpi/releases/download/v6.11.1/sfpi-x86_64_Linux.txz")
set(SFPI_MD5_HASH "14ade50b3fdf3fff5078195332edc15a")
set(SFPI_LOCAL_FILE "${TTEXALENS_HOME}/build_riscv/sfpi-x86_64_Linux-v6.11.1.txz")
set(SFPI_RELEASE_PATH "${TTEXALENS_HOME}/build_riscv/sfpi")

if(NOT EXISTS "${SFPI_LOCAL_FILE}")
    message(STATUS "Downloading sfpi release")
    file(DOWNLOAD
        ${SFPI_DOWNLOAD_URL}
        ${SFPI_LOCAL_FILE}
        EXPECTED_MD5 ${SFPI_MD5_HASH}
        SHOW_PROGRESS)
else()
    message(STATUS "Using sfpi release from ${SFPI_LOCAL_FILE}")
endif()

include(FetchContent)

if(${CMAKE_VERSION} VERSION_GREATER "3.24.1")
    FetchContent_Declare(
        sfpi
        URL ${SFPI_LOCAL_FILE}
        URL_HASH MD5=${SFPI_MD5_HASH}
        SOURCE_DIR ${SFPI_RELEASE_PATH}
        DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    )
else()
    FetchContent_Declare(
        sfpi
        URL ${SFPI_LOCAL_FILE}
        URL_HASH MD5=${SFPI_MD5_HASH}
        SOURCE_DIR ${SFPI_RELEASE_PATH}
    )
endif()
FetchContent_MakeAvailable(sfpi)
