cmake_minimum_required(VERSION 3.22)
cmake_policy(VERSION 3.22)

project(RISCVProject LANGUAGES CXX ASM)

option(DUMP_ELFS "Dump data using objdump and readelf" OFF)

# Set toolchain and tools
set(TOOL_PATH "${SFPI_RELEASE_PATH}/compiler/bin")
set(GXX "${TOOL_PATH}/riscv-tt-elf-g++")
set(OBJDUMP "${TOOL_PATH}/riscv-tt-elf-objdump")
set(OBJCOPY "${TOOL_PATH}/riscv-tt-elf-objcopy")
set(READELF "${TOOL_PATH}/riscv-tt-elf-readelf")

# rv64 (lp64) is used for Rocket cores on Quasar, rv32 (ilp32) for the other cores
set(RISCV_ISAS "rv32" "rv64")

# Compiler options for optimized builds
set(OPTIMIZED_OPTIONS_ALL_rv32 -O3 -mabi=ilp32 -std=c++17 -g -ffast-math -flto)
set(OPTIMIZED_OPTIONS_ALL_rv64 -O3 -mcpu=tt-qsr64 -mabi=lp64 -std=c++17 -g -ffast-math -flto)
set(OPTIMIZED_OPTIONS_COMPILE -fno-use-cxa-atexit -Wall -fno-exceptions -fno-rtti -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable -DTENSIX_FIRMWARE)
set(OPTIMIZED_OPTIONS_LINK -fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Lttexalens/riscv-src)

# Compiler options
set(OPTIONS_ALL_rv32 -O0 -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -flto -ffast-math)
set(OPTIONS_ALL_rv64 -O0 -mcpu=tt-qsr64 -mabi=lp64 -std=c++17 -g -flto -ffast-math)
set(OPTIONS_COMPILE -fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable)
set(OPTIONS_LINK -fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Lttexalens/riscv-src)

# Note that -fprofile-info-section must be specified so as to not rely on unavailable runtime support (libc, complete crt, etc),
# but instead have GCC provide us with a pointer to the raw coverage data and let us extract it ourselves.
set(GCOV_FLAGS -fprofile-arcs -ftest-coverage -fprofile-info-section -DCOVERAGE)

# Define project paths: source files, ELFs, and object files
set(RISCV_SOURCE "${CMAKE_CURRENT_LIST_DIR}")
set(RISCV_OUTPUT "${CMAKE_SOURCE_DIR}/build/riscv-src")
set(RISCV_OBJECT_rv32 "${CMAKE_SOURCE_DIR}/build/riscv-src/obj/rv32")
set(RISCV_OBJECT_rv64 "${CMAKE_SOURCE_DIR}/build/riscv-src/obj/rv64")

# Define architectures, the cores of each architecture per ISA, and applications
set(RISCV_ARCHITECTURES "wormhole" "blackhole" "quasar")
set(RISCV_CORES_wormhole_rv32 "brisc" "trisc0" "trisc1" "trisc2" "ncrisc" "erisc")
set(RISCV_CORES_blackhole_rv32 "brisc" "trisc0" "trisc1" "trisc2" "ncrisc" "erisc0" "erisc1" "drisc")
set(RISCV_CORES_quasar_rv32 "trisc0" "trisc1" "trisc2" "trisc3")
set(RISCV_CORES_quasar_rv64 "rocket0" "rocket1" "rocket2" "rocket3" "rocket4" "rocket5" "rocket6" "rocket7")
set(RISCV_APPS "sample" "run_elf_test" "callstack" "cov_test" "globals_test" "edge_mem_test")

# Create the object file output directories
file(MAKE_DIRECTORY ${RISCV_OBJECT_rv32} ${RISCV_OBJECT_rv64})

# Helper function to add object files for each source
function(add_riscv_object OBJECT_NAME SOURCE_FILE BUILD_TYPE ISA)
    if(BUILD_TYPE STREQUAL "release")
        set(COMPILE_OPTIONS ${OPTIMIZED_OPTIONS_ALL_${ISA}} ${OPTIMIZED_OPTIONS_COMPILE})
    else()
        set(COMPILE_OPTIONS ${OPTIONS_ALL_${ISA}} ${OPTIONS_COMPILE})
        if(BUILD_TYPE STREQUAL "coverage")
            list(APPEND COMPILE_OPTIONS ${GCOV_FLAGS})
        endif()
    endif()

    add_custom_command(
        OUTPUT ${OBJECT_NAME}
        COMMAND ${GXX} ${COMPILE_OPTIONS} -c -o ${OBJECT_NAME} ${SOURCE_FILE}
        DEPENDS ${SOURCE_FILE}
        COMMENT "Compiling ${SOURCE_FILE} to ${OBJECT_NAME}"
    )
endfunction()

foreach(ISA ${RISCV_ISAS})
    set(OBJECT_DIR ${RISCV_OBJECT_${ISA}})

    # Compile the coverage support file (always optimized and without instrumentation).
    # Compile coverage.c with -fno-strict-aliasing, the tricks done in the code necessitate it.
    add_custom_command(
        OUTPUT ${OBJECT_DIR}/coverage.o
        COMMAND ${GXX}
                ${OPTIMIZED_OPTIONS_ALL_${ISA}}
                ${OPTIMIZED_OPTIONS_COMPILE}
                -fno-strict-aliasing
                -fno-builtin
                -c -o ${OBJECT_DIR}/coverage.o
                ${RISCV_SOURCE}/coverage.c
        DEPENDS ${RISCV_SOURCE}/coverage.c
    )

    # Add the CRT object (assembly file)
    # The "coverage" build just adds a call to gcov_dump into the CRT.
    add_riscv_object("${OBJECT_DIR}/tmu-crt0.debug.o" "${RISCV_SOURCE}/tmu-crt0.S" "debug" ${ISA})
    add_riscv_object("${OBJECT_DIR}/tmu-crt0.release.o" "${RISCV_SOURCE}/tmu-crt0.S" "release" ${ISA})
    add_riscv_object("${OBJECT_DIR}/tmu-crt0.coverage.o" "${RISCV_SOURCE}/tmu-crt0.S" "coverage" ${ISA})

    # Add C++ compile target
    foreach(app ${RISCV_APPS})
        add_riscv_object("${OBJECT_DIR}/${app}.debug.o" "${RISCV_SOURCE}/${app}.cc" "debug" ${ISA})
        add_riscv_object("${OBJECT_DIR}/${app}.release.o" "${RISCV_SOURCE}/${app}.cc" "release" ${ISA})
        add_riscv_object("${OBJECT_DIR}/${app}.coverage.o" "${RISCV_SOURCE}/${app}.cc" "coverage" ${ISA})
    endforeach()
endforeach()

# Define function to create targets for a specific architecture, application, and core
function(create_riscv_target ARCH APP CORE BUILD_TYPE ISA)
    if(BUILD_TYPE STREQUAL "release")
        set(LINK_OPTIONS ${OPTIMIZED_OPTIONS_ALL_${ISA}} ${OPTIMIZED_OPTIONS_LINK})
    else()
        set(LINK_OPTIONS ${OPTIONS_ALL_${ISA}} ${OPTIONS_LINK})
    endif()

    # -mtt-fix-whbhebreak emits the Wormhole/Blackhole ebreak hardware-bug workaround
    # (8 NOPs after every ebreak; the fetch pipeline has already prefetched the
    # instructions following an ebreak, so on WH/BH those must be NOPs).
    if(ARCH STREQUAL "wormhole" OR ARCH STREQUAL "blackhole")
        list(APPEND LINK_OPTIONS -mtt-fix-whbhebreak)
    endif()

    set(OUTPUT_ELF "${RISCV_OUTPUT}/${ARCH}/${APP}.${BUILD_TYPE}.${CORE}.elf")
    set(OUTPUT_OBJDUMP "${RISCV_OUTPUT}/${ARCH}/${APP}.${BUILD_TYPE}.${CORE}.objdump")
    set(OUTPUT_DWARF "${RISCV_OUTPUT}/${ARCH}/${APP}.${BUILD_TYPE}.${CORE}.dwarf")

    set(LINK_OBJECTS
        ${RISCV_OBJECT_${ISA}}/tmu-crt0.${BUILD_TYPE}.o
        ${RISCV_OBJECT_${ISA}}/${APP}.${BUILD_TYPE}.o
    )

    # Handle memory.${ARCH}.debug.ld and memory.${ARCH}.release.ld
    set(LDSCRIPT_EXTENSION ${BUILD_TYPE})
    set(LINK_LIBS)

    if(BUILD_TYPE STREQUAL "coverage")
        list(APPEND LINK_OBJECTS ${RISCV_OBJECT_${ISA}}/coverage.o)
        list(APPEND LINK_LIBS -lgcov)
        # Debug ld script should be used in coverage builds
        set(LDSCRIPT_EXTENSION "debug")
    endif()

    add_custom_command(
        OUTPUT ${OUTPUT_ELF}
        COMMAND ${GXX} ${LINK_OPTIONS}
            ${LINK_OBJECTS}
            ${LINK_LIBS}
            -T${RISCV_SOURCE}/memory.${ARCH}.${LDSCRIPT_EXTENSION}.ld
            -T${RISCV_SOURCE}/${CORE}.ld
            -T${RISCV_SOURCE}/sections.ld
            -o ${OUTPUT_ELF}
        DEPENDS ${LINK_OBJECTS}
                ${RISCV_SOURCE}/memory.${ARCH}.${LDSCRIPT_EXTENSION}.ld
                ${RISCV_SOURCE}/${CORE}.ld
                ${RISCV_SOURCE}/sections.ld
        COMMENT "Linking ${OUTPUT_ELF}"
    )

    add_custom_target("${ARCH}_${APP}_${CORE}_${BUILD_TYPE}_target" ALL
        DEPENDS ${OUTPUT_ELF})

    if(DUMP_ELFS)
        add_custom_command(
            OUTPUT ${OUTPUT_OBJDUMP} ${OUTPUT_DWARF}
            COMMAND ${OBJDUMP} -d -s -S ${OUTPUT_ELF} > ${OUTPUT_OBJDUMP}
            COMMAND ${OBJDUMP} -t ${OUTPUT_ELF} | sort >> ${OUTPUT_OBJDUMP}
            COMMAND ${READELF} --debug-dump ${OUTPUT_ELF} > ${OUTPUT_DWARF}
            DEPENDS ${OUTPUT_ELF}
            COMMENT "Generating dump and disassembly for ${OUTPUT_ELF}"
        )

        add_custom_target("${ARCH}_${APP}_${CORE}_${BUILD_TYPE}_dump_dis" ALL
            DEPENDS ${OUTPUT_OBJDUMP} ${OUTPUT_DWARF})

        add_dependencies("${ARCH}_${APP}_${CORE}_${BUILD_TYPE}_target" "${ARCH}_${APP}_${CORE}_${BUILD_TYPE}_dump_dis")
    endif()
endfunction()

# Create targets for all architectures, their cores, and applications
foreach(ARCH ${RISCV_ARCHITECTURES})
    foreach(ISA ${RISCV_ISAS})
        foreach(CORE IN LISTS RISCV_CORES_${ARCH}_${ISA})
            foreach(APP ${RISCV_APPS})
                foreach(BUILD_TYPE debug release coverage)
                    create_riscv_target(${ARCH} ${APP} ${CORE} ${BUILD_TYPE} ${ISA})
                endforeach()
            endforeach()
        endforeach()
    endforeach()
endforeach()
