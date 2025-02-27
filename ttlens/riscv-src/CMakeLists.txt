cmake_minimum_required(VERSION 3.16)
cmake_policy(VERSION 3.16)

project(RISCVProject LANGUAGES CXX ASM)

# Check if TTEXALENS_HOME is set, if not set it to ../../ from the directory that contains this file
if(NOT TTEXALENS_HOME)
    set(TTEXALENS_HOME "${CMAKE_CURRENT_LIST_DIR}/../..")
endif()

message(STATUS "Downloading sfpi release")

include(FetchContent)
FetchContent_Declare(
    sfpi
    URL
        https://github.com/tenstorrent/sfpi/releases/download/v5.0.0/sfpi-release.tgz
    URL_HASH MD5=10cacabe92846076cb4d7596e46d06be
    SOURCE_DIR
    ${TTEXALENS_HOME}/sfpi
)
FetchContent_MakeAvailable(sfpi)

# Set toolchain and tools
set(TOOL_PATH "${TTEXALENS_HOME}/sfpi/compiler/bin")
set(GXX "${TOOL_PATH}/riscv32-unknown-elf-g++")
set(OBJDUMP "${TOOL_PATH}/riscv32-unknown-elf-objdump")
set(OBJCOPY "${TOOL_PATH}/riscv32-unknown-elf-objcopy")
set(READELF "${TOOL_PATH}/riscv32-unknown-elf-readelf")

# Compiler options for optimized builds
set(OPTIMIZED_OPTIONS_ALL -O3 -mabi=ilp32 -std=c++17 -g -ffast-math -flto)
set(OPTIMIZED_OPTIONS_COMPILE -fno-use-cxa-atexit -Wall -fno-exceptions -fno-rtti -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable -DTENSIX_FIRMWARE)
set(OPTIMIZED_OPTIONS_LINK -fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Lttlens/riscv-src)

# Compiler options
set(OPTIONS_ALL -O0 -march=rv32imw -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -flto -ffast-math)
set(OPTIONS_COMPILE -fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable)
set(OPTIONS_LINK -fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Lttlens/riscv-src)

# Define project paths
set(RISCV_SOURCE "${CMAKE_CURRENT_LIST_DIR}")
set(RISCV_OUTPUT "${CMAKE_BINARY_DIR}/riscv-src")
set(RISCV_OBJECT "${CMAKE_BINARY_DIR}/obj/riscv-src")

# Define architectures, applications, and cores
set(RISCV_ARCHITECTURES "grayskull" "wormhole" "blackhole")
set(RISCV_CORES "brisc" "trisc0" "trisc1" "trisc2" "ncrisc")
set(RISCV_APPS "sample" "run_elf_test" "callstack")
set(RISCV_OPTIMIZED_APPS "callstack")

# Create output directories
file(MAKE_DIRECTORY ${RISCV_OBJECT})
file(MAKE_DIRECTORY ${RISCV_OUTPUT})
# Helper function to add object files for each source
function(add_riscv_object OBJECT_NAME SOURCE_FILE OPTIMIZED)
    if(OPTIMIZED)
        set(COMPILE_OPTIONS ${OPTIMIZED_OPTIONS_ALL} ${OPTIMIZED_OPTIONS_COMPILE})
    else()
        set(COMPILE_OPTIONS ${OPTIONS_ALL} ${OPTIONS_COMPILE})
    endif()
    add_custom_command(
        OUTPUT ${OBJECT_NAME}
        COMMAND ${GXX} ${COMPILE_OPTIONS} -c -o ${OBJECT_NAME} ${SOURCE_FILE}
        DEPENDS ${SOURCE_FILE}
        COMMENT "Compiling ${SOURCE_FILE} to ${OBJECT_NAME}"
    )
endfunction()

# Add the CRT object (assembly file)
add_riscv_object("${RISCV_OBJECT}/tmu-crt0.o" "${RISCV_SOURCE}/tmu-crt0.S" OFF)
add_riscv_object("${RISCV_OBJECT}/tmu-crt0.optimized.o" "${RISCV_SOURCE}/tmu-crt0.S" ON)

# Add C++ compile target
foreach(app ${RISCV_APPS})
    add_riscv_object("${RISCV_OBJECT}/${app}.o" "${RISCV_SOURCE}/${app}.cc" OFF)
endforeach()
foreach(app ${RISCV_OPTIMIZED_APPS})
    add_riscv_object("${RISCV_OBJECT}/${app}.optimized.o" "${RISCV_SOURCE}/${app}.cc" ON)
endforeach()

# Define function to create targets for a specific architecture, application, and core
function(create_riscv_target ARCH APP CORE OPTIMIZED)
    if(OPTIMIZED)
        set(COMPILE_OPTIONS ${OPTIMIZED_OPTIONS_ALL} ${OPTIMIZED_OPTIONS_LINK})
        set(OPTIMIZED_EXTENSION ".optimized")
    else()
        set(COMPILE_OPTIONS ${OPTIONS_ALL} ${OPTIONS_LINK})
        set(OPTIMIZED_EXTENSION "")
    endif()
    set(OUTPUT_ELF "${RISCV_OUTPUT}/${ARCH}/${APP}${OPTIMIZED_EXTENSION}.${CORE}.elf")
    set(OUTPUT_DUMP "${RISCV_OUTPUT}/${ARCH}/${APP}${OPTIMIZED_EXTENSION}.${CORE}.dump")
    set(OUTPUT_DIS "${RISCV_OUTPUT}/${ARCH}/${APP}${OPTIMIZED_EXTENSION}.${CORE}.dis")

    add_custom_command(
        OUTPUT ${OUTPUT_ELF}
        COMMAND ${GXX} ${COMPILE_OPTIONS}
            ${RISCV_OBJECT}/tmu-crt0${OPTIMIZED_EXTENSION}.o ${RISCV_OBJECT}/${APP}${OPTIMIZED_EXTENSION}.o
            -T${RISCV_SOURCE}/memory.${ARCH}.ld
            -T${RISCV_SOURCE}/${CORE}.ld
            -T${RISCV_SOURCE}/sections.ld
            -o ${OUTPUT_ELF}
        DEPENDS ${RISCV_OBJECT}/tmu-crt0${OPTIMIZED_EXTENSION}.o ${RISCV_OBJECT}/${APP}${OPTIMIZED_EXTENSION}.o ${RISCV_SOURCE}/memory.${ARCH}.ld ${RISCV_SOURCE}/${CORE}.ld ${RISCV_SOURCE}/sections.ld
        COMMENT "Linking ${OUTPUT_ELF}"
    )

    add_custom_target("${ARCH}_${APP}_${CORE}_${OPTIMIZED}_target" ALL
        DEPENDS ${OUTPUT_ELF})

    add_custom_command(
        OUTPUT ${OUTPUT_DUMP} ${OUTPUT_DIS}
        COMMAND ${OBJDUMP} -d -s -S ${OUTPUT_ELF} > ${OUTPUT_DUMP}
        COMMAND ${OBJDUMP} -t ${OUTPUT_ELF} | sort >> ${OUTPUT_DUMP}
        COMMAND ${READELF} --debug-dump ${OUTPUT_ELF} > ${OUTPUT_DIS}
        DEPENDS ${OUTPUT_ELF}
        COMMENT "Generating dump and disassembly for ${OUTPUT_ELF}"
    )

    add_custom_target("${ARCH}_${APP}_${CORE}_${OPTIMIZED}_dump_dis" ALL
        DEPENDS ${OUTPUT_DUMP} ${OUTPUT_DIS})

    add_dependencies("${ARCH}_${APP}_${CORE}_${OPTIMIZED}_target" "${ARCH}_${APP}_${CORE}_${OPTIMIZED}_dump_dis")
endfunction()

# Create targets for all architectures, applications, and cores
foreach(CORE ${RISCV_CORES})
    foreach(APP ${RISCV_APPS})
        foreach(ARCH ${RISCV_ARCHITECTURES})
            create_riscv_target(${ARCH} ${APP} ${CORE} OFF)
        endforeach()
    endforeach()
endforeach()

foreach(CORE ${RISCV_CORES})
    foreach(APP ${RISCV_OPTIMIZED_APPS})
        foreach(ARCH ${RISCV_ARCHITECTURES})
            create_riscv_target(${ARCH} ${APP} ${CORE} ON)
        endforeach()
    endforeach()
endforeach()
