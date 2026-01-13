cmake_minimum_required(VERSION 3.22)
cmake_policy(VERSION 3.22)

project(RISCVProject LANGUAGES CXX ASM)

# Set toolchain and tools
set(TOOL_PATH "${SFPI_RELEASE_PATH}/compiler/bin")
set(GXX "${TOOL_PATH}/riscv-tt-elf-g++")
set(OBJDUMP "${TOOL_PATH}/riscv-tt-elf-objdump")
set(OBJCOPY "${TOOL_PATH}/riscv-tt-elf-objcopy")
set(READELF "${TOOL_PATH}/riscv-tt-elf-readelf")

# Compiler options for optimized builds
set(OPTIMIZED_OPTIONS_ALL -O3 -mabi=ilp32 -std=c++17 -g -ffast-math -flto)
set(OPTIMIZED_OPTIONS_COMPILE -fno-use-cxa-atexit -Wall -fno-exceptions -fno-rtti -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable -DTENSIX_FIRMWARE)
set(OPTIMIZED_OPTIONS_LINK -fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Lttexalens/riscv-src)

# Compiler options
set(OPTIONS_ALL -O0 -mtune=rvtt-b1 -mabi=ilp32 -std=c++17 -g -flto -ffast-math)
set(OPTIONS_COMPILE -fno-use-cxa-atexit -fno-exceptions -Wall -Werror -Wno-unknown-pragmas -Wno-error=multistatement-macros -Wno-error=parentheses -Wno-error=unused-but-set-variable -Wno-unused-variable)
set(OPTIONS_LINK -fno-exceptions -Wl,-z,max-page-size=16 -Wl,-z,common-page-size=16 -nostartfiles -Lttexalens/riscv-src)

# Note that -fprofile-info-section must be specified so as to not rely on unavailable runtime support (libc, complete crt, etc),
# but instead have GCC provide us with a pointer to the raw coverage data and let us extract it ourselves.
set(GCOV_FLAGS -fprofile-arcs -ftest-coverage -fprofile-info-section -DCOVERAGE)

# Define project paths: source files, ELFs, and object files
set(RISCV_SOURCE "${CMAKE_CURRENT_LIST_DIR}")
set(RISCV_OUTPUT "${CMAKE_SOURCE_DIR}/build/riscv-src")
set(RISCV_OBJECT "${CMAKE_SOURCE_DIR}/build/riscv-src/obj")

# Define architectures, applications, and cores
set(RISCV_ARCHITECTURES "wormhole" "blackhole")
set(RISCV_CORES "brisc" "trisc0" "trisc1" "trisc2" "ncrisc" "erisc" "erisc0" "erisc1")
set(RISCV_APPS "sample" "run_elf_test" "callstack" "cov_test" "globals_test" "edge_mem_test" "frame_unwinding_test" "frame_unwinding_test_aliasing" "frame_unwinding_test_deep")

# Create the object file output directory
file(MAKE_DIRECTORY ${RISCV_OBJECT})

# Helper function to add object files for each source
function(add_riscv_object OBJECT_NAME SOURCE_FILE BUILD_TYPE)
    if(BUILD_TYPE STREQUAL "release")
        set(COMPILE_OPTIONS ${OPTIMIZED_OPTIONS_ALL} ${OPTIMIZED_OPTIONS_COMPILE})
    else()
        set(COMPILE_OPTIONS ${OPTIONS_ALL} ${OPTIONS_COMPILE})
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

# Compile the coverage-related libraries (always optimized and without instrumentation)
set(GCOV_OBJ "${RISCV_OBJECT}/gcov.o")
set(COVERAGE_OBJ "${RISCV_OBJECT}/coverage.o")
add_riscv_object("${GCOV_OBJ}" "${RISCV_SOURCE}/coverage/gcov.c" "release")

# Compile coverage.c with -fno-strict-aliasing, the tricks done in the code necessitate it.
add_custom_command(
    OUTPUT ${COVERAGE_OBJ}
    COMMAND ${GXX}
            ${OPTIMIZED_OPTIONS_ALL}
            ${OPTIMIZED_OPTIONS_COMPILE}
            -fno-strict-aliasing
            -c -o ${COVERAGE_OBJ}
            ${RISCV_SOURCE}/coverage/coverage.c
    DEPENDS ${RISCV_SOURCE}/coverage/coverage.c
)

# Add the CRT object (assembly file)
# The "coverage" build just adds a call to gcov_dump into the CRT.
add_riscv_object("${RISCV_OBJECT}/tmu-crt0.debug.o" "${RISCV_SOURCE}/tmu-crt0.S" "debug")
add_riscv_object("${RISCV_OBJECT}/tmu-crt0.release.o" "${RISCV_SOURCE}/tmu-crt0.S" "release")
add_riscv_object("${RISCV_OBJECT}/tmu-crt0.coverage.o" "${RISCV_SOURCE}/tmu-crt0.S" "coverage")

# Add C++ compile target
foreach(app ${RISCV_APPS})
    add_riscv_object("${RISCV_OBJECT}/${app}.debug.o" "${RISCV_SOURCE}/${app}.cc" "debug")
    add_riscv_object("${RISCV_OBJECT}/${app}.release.o" "${RISCV_SOURCE}/${app}.cc" "release")
    add_riscv_object("${RISCV_OBJECT}/${app}.coverage.o" "${RISCV_SOURCE}/${app}.cc" "coverage")
endforeach()

# Define function to create targets for a specific architecture, application, and core
function(create_riscv_target ARCH APP CORE BUILD_TYPE)
    if(BUILD_TYPE STREQUAL "release")
        set(LINK_OPTIONS ${OPTIMIZED_OPTIONS_ALL} ${OPTIMIZED_OPTIONS_LINK})
    else()
        set(LINK_OPTIONS ${OPTIONS_ALL} ${OPTIONS_LINK})
    endif()

    set(OUTPUT_ELF "${RISCV_OUTPUT}/${ARCH}/${APP}.${BUILD_TYPE}.${CORE}.elf")
    set(OUTPUT_OBJDUMP "${RISCV_OUTPUT}/${ARCH}/${APP}.${BUILD_TYPE}.${CORE}.objdump")
    set(OUTPUT_DWARF "${RISCV_OUTPUT}/${ARCH}/${APP}.${BUILD_TYPE}.${CORE}.dwarf")

    set(LINK_OBJECTS
        ${RISCV_OBJECT}/tmu-crt0.${BUILD_TYPE}.o
        ${RISCV_OBJECT}/${APP}.${BUILD_TYPE}.o
    )

    # Handle memory.${ARCH}.debug.ld and memory.${ARCH}.release.ld
    set(LDSCRIPT_EXTENSION ${BUILD_TYPE})

    if(BUILD_TYPE STREQUAL "coverage")
        list(APPEND LINK_OBJECTS ${GCOV_OBJ} ${COVERAGE_OBJ})
        # Debug ld script should be used in coverage builds
        set(LDSCRIPT_EXTENSION "debug")
    endif()

    add_custom_command(
        OUTPUT ${OUTPUT_ELF}
        COMMAND ${GXX} ${LINK_OPTIONS}
            ${LINK_OBJECTS}
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
endfunction()

# Create targets for all architectures, applications, and cores
foreach(CORE ${RISCV_CORES})
    foreach(APP ${RISCV_APPS})
        foreach(ARCH ${RISCV_ARCHITECTURES})
            if (ARCH STREQUAL "blackhole" AND CORE MATCHES "^erisc$")
                # Skip invalid combinations of blackhole architecture with erisc cores
                continue()
            endif()
            if (ARCH STREQUAL "wormhole" AND (CORE MATCHES "^erisc0$" OR CORE MATCHES "^erisc1$"))
                # Skip invalid combinations of wormhole architecture with erisc0 and erisc1 cores
                continue()
            endif()
            foreach(BUILD_TYPE debug release coverage)
                create_riscv_target(${ARCH} ${APP} ${CORE} ${BUILD_TYPE})
            endforeach()
        endforeach()
    endforeach()
endforeach()
