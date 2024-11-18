# Converting configuration files to embed
set(CONFIG_FILEPATH "${CMAKE_CURRENT_SOURCE_DIR}/configuration")
set(DEVICE_FILEPATH "${CMAKE_CURRENT_SOURCE_DIR}/../device")

set(TTLENS_SERVER_LIB_CONFIGURATION_FILES
	"${CONFIG_FILEPATH}/blackhole.embed" "${DEVICE_FILEPATH}/blackhole_10x14.yaml"
	"${CONFIG_FILEPATH}/grayskull.embed" "${DEVICE_FILEPATH}/grayskull_10x12.yaml"
	"${CONFIG_FILEPATH}/wormhole_b0.embed" "${DEVICE_FILEPATH}/wormhole_b0_8x10.yaml"
)

set(TTLENS_SERVER_LIB_EMBED_FILES "")

list(LENGTH TTLENS_SERVER_LIB_CONFIGURATION_FILES TTLENS_SERVER_LIB_EMBED_FILES_COUNT)
math(EXPR last_index "${TTLENS_SERVER_LIB_EMBED_FILES_COUNT} - 2")

foreach(i RANGE 0 ${last_index} 2)
    list(GET TTLENS_SERVER_LIB_CONFIGURATION_FILES ${i} embed_file)
    math(EXPR yaml_index "${i} + 1")
    list(GET TTLENS_SERVER_LIB_CONFIGURATION_FILES ${yaml_index} yaml_file)

    list(APPEND TTLENS_SERVER_LIB_EMBED_FILES ${embed_file})

    add_custom_command(
        OUTPUT ${embed_file}
        COMMAND ${CMAKE_COMMAND} -E make_directory ${CONFIG_FILEPATH}
        COMMAND cat ${yaml_file} | xxd -i > ${embed_file}
        DEPENDS ${yaml_file}
        COMMENT "Generating ${embed_file} from ${yaml_file}"
    )
endforeach()

add_custom_target(generate_embed_files ALL
    DEPENDS ${TTLENS_SERVER_LIB_EMBED_FILES}
)

# Library project
file(GLOB TTLENS_SERVER_LIB_SRCS "src/*.cpp")
add_library(ttlens_server_lib STATIC ${TTLENS_SERVER_LIB_SRCS})
add_dependencies(ttlens_server_lib generate_embed_files)
target_link_libraries(ttlens_server_lib 
    PUBLIC umd_device fmt cppzmq-static
)
target_include_directories(ttlens_server_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/inc
)
set_target_properties(ttlens_server_lib PROPERTIES 
    OUTPUT_NAME libttlensserver
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    POSITION_INDEPENDENT_CODE ON
)

# TODO: This should be removed from this repository and should be fixed correctly in umd repository
# Copy UMD dependencies to build/lib directory
set(nng_lib_path "${CMAKE_BINARY_DIR}/_deps/nanomsg-build/libnng.so.1")
set(uv_lib_path "${CMAKE_BINARY_DIR}/_deps/libuv-build/libuv.so.1")

add_custom_command(TARGET ttlens_server_lib
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy ${nng_lib_path} ${CMAKE_BINARY_DIR}/lib
    COMMAND ${CMAKE_COMMAND} -E copy ${uv_lib_path} ${CMAKE_BINARY_DIR}/lib
    COMMENT "Copying umd dependencies to ${CMAKE_BINARY_DIR}/lib"
)

# JTAG
set(JTAG_ACCESS_LIB_PATH "${TTLENS_HOME}/third_party/jtag-access-library")
set(LIBJTAG "${CMAKE_BINARY_DIR}/lib/libjtag.so")
set(LIBJTAG_SOURCE "${JTAG_ACCESS_LIB_PATH}/out/libjtag.so")
set(LIBJTAG_DEP "${CMAKE_BINARY_DIR}/lib/libjlinkarm.so")
set(LIBJTAG_DEP_SOURCE "${JTAG_ACCESS_LIB_PATH}/lib/libjlinkarm.so")

if(EXISTS "${JTAG_ACCESS_LIB_PATH}")
    add_custom_target(dummy_target ALL DEPENDS copy_jtag)
    add_custom_command(
        OUTPUT copy_jtag
        COMMAND make -C "${JTAG_ACCESS_LIB_PATH}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different "${LIBJTAG_SOURCE}" "${LIBJTAG}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different "${LIBJTAG_DEP_SOURCE}" "${LIBJTAG_DEP}"
        COMMENT "Rebuilding & copying JTAG libraries to ${CMAKE_BINARY_DIR}/lib"
    )
endif()