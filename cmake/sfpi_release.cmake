set(SFPI_DOWNLOAD_URL "https://github.com/tenstorrent/sfpi/releases/download/7.6.0/sfpi_7.6.0_x86_64_linux.txz")
set(SFPI_MD5_HASH "2714ff49907552416b037590c28d2341")
set(SFPI_LOCAL_FILE "${TTEXALENS_HOME}/build_riscv/sfpi_7.6.0_x86_64_linux.txz")
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
