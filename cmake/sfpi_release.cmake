set(SFPI_VERSION "7.7.0")

if(CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "aarch64")
    set(SFPI_ARCH "aarch64_debian")
    set(SFPI_MD5_HASH "b682f17260eb260611a2882ea17878f8")
elseif(CMAKE_HOST_SYSTEM_PROCESSOR STREQUAL "x86_64")
    set(SFPI_ARCH "x86_64_debian")
    set(SFPI_MD5_HASH "56ce59c0945264abc4e89159d0f6d4e8")
else()
    message(FATAL_ERROR "Unsupported host architecture for sfpi: ${CMAKE_HOST_SYSTEM_PROCESSOR}")
endif()

set(SFPI_DOWNLOAD_URL "https://github.com/tenstorrent/sfpi/releases/download/${SFPI_VERSION}/sfpi_${SFPI_VERSION}_${SFPI_ARCH}.txz")
set(SFPI_LOCAL_FILE "${TTEXALENS_HOME}/build/sfpi_${SFPI_VERSION}_${SFPI_ARCH}.txz")
set(SFPI_RELEASE_PATH "${TTEXALENS_HOME}/build/sfpi")

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
