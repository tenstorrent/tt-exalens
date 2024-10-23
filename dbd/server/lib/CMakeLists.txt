# Converting configuration files to embed
set(CONFIG_FILEPATH "${CMAKE_CURRENT_SOURCE_DIR}/configuration")
set(DEVICE_FILEPATH "${CMAKE_CURRENT_SOURCE_DIR}/../device")

set(DEBUDA_SERVER_LIB_CONFIGURATION_FILES
	"${CONFIG_FILEPATH}/blackhole.embed" "${DEVICE_FILEPATH}/blackhole_10x14.yaml"
	"${CONFIG_FILEPATH}/grayskull.embed" "${DEVICE_FILEPATH}/grayskull_10x12.yaml"
	"${CONFIG_FILEPATH}/wormhole.embed" "${DEVICE_FILEPATH}/wormhole_8x10.yaml"
	"${CONFIG_FILEPATH}/wormhole_b0.embed" "${DEVICE_FILEPATH}/wormhole_b0_8x10.yaml"
)

set(DEBUDA_SERVER_LIB_EMBED_FILES "")

list(LENGTH DEBUDA_SERVER_LIB_CONFIGURATION_FILES DEBUDA_SERVER_LIB_EMBED_FILES_COUNT)
math(EXPR last_index "${DEBUDA_SERVER_LIB_EMBED_FILES_COUNT} - 2")

foreach(i RANGE 0 ${last_index} 2)
    list(GET DEBUDA_SERVER_LIB_CONFIGURATION_FILES ${i} embed_file)
    math(EXPR yaml_index "${i} + 1")
    list(GET DEBUDA_SERVER_LIB_CONFIGURATION_FILES ${yaml_index} yaml_file)

    list(APPEND DEBUDA_SERVER_LIB_EMBED_FILES ${embed_file})

    add_custom_command(
        OUTPUT ${embed_file}
        COMMAND ${CMAKE_COMMAND} -E make_directory ${CONFIG_FILEPATH}
        COMMAND cat ${yaml_file} | xxd -i > ${embed_file}
        DEPENDS ${yaml_file}
        COMMENT "Generating ${embed_file} from ${yaml_file}"
    )
endforeach()

add_custom_target(generate_embed_files ALL
    DEPENDS ${DEBUDA_SERVER_LIB_EMBED_FILES}
)

# Copy create-ethernet-map to output directory
set(CREATE_ETHERNET_MAP_WORMHOLE_DBD "${CMAKE_BUILD_BIN_DIR}/debuda-create-ethernet-map-wormhole")
set(CREATE_ETHERNET_MAP_WORMHOLE_DBD_SOURCE "${UMD_HOME}/device/bin/silicon/x86/create-ethernet-map")
set(CREATE_ETHERNET_MAP_BLACKHOLE_DBD "${CMAKE_BUILD_BIN_DIR}/debuda-create-ethernet-map-blackhole")
set(CREATE_ETHERNET_MAP_BLACKHOLE_DBD_SOURCE "${DEBUDA_HOME}/dbd/server/bin/create-ethernet-map-blackhole")

add_custom_command(
    OUTPUT ${CREATE_ETHERNET_MAP_WORMHOLE_DBD}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BUILD_BIN_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy ${CREATE_ETHERNET_MAP_WORMHOLE_DBD_SOURCE} ${CREATE_ETHERNET_MAP_WORMHOLE_DBD}
    COMMAND chmod +x ${CREATE_ETHERNET_MAP_WORMHOLE_DBD}
    DEPENDS ${CREATE_ETHERNET_MAP_WORMHOLE_DBD_SOURCE}  # Ensure the command runs when source files change
    COMMENT "Copying create-ethernet-map and setting executable permission"
)

add_custom_command(
    OUTPUT ${CREATE_ETHERNET_MAP_BLACKHOLE_DBD}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BUILD_BIN_DIR}
    COMMAND ${CMAKE_COMMAND} -E copy ${CREATE_ETHERNET_MAP_BLACKHOLE_DBD_SOURCE} ${CREATE_ETHERNET_MAP_BLACKHOLE_DBD}
    COMMAND chmod +x ${CREATE_ETHERNET_MAP_BLACKHOLE_DBD}
    DEPENDS ${CREATE_ETHERNET_MAP_BLACKHOLE_DBD_SOURCE}  # Ensure the command runs when source files change
    COMMENT "Copying create-ethernet-map for blackhole and setting executable permission"
)

add_custom_target(copy_create_ethernet_map ALL DEPENDS ${CREATE_ETHERNET_MAP_WORMHOLE_DBD} ${CREATE_ETHERNET_MAP_BLACKHOLE_DBD})

# Library project
file(GLOB DEBUDA_SERVER_LIB_SRCS "src/*.cpp")
add_library(debuda_server_lib STATIC ${DEBUDA_SERVER_LIB_SRCS})
add_dependencies(debuda_server_lib generate_embed_files copy_create_ethernet_map)
target_link_libraries(debuda_server_lib 
    PUBLIC umd_device fmt cppzmq-static
)
target_include_directories(debuda_server_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/inc
)
set_target_properties(debuda_server_lib PROPERTIES 
    OUTPUT_NAME libdbdserver
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    POSITION_INDEPENDENT_CODE ON
)

# TODO: This should be removed from this repository and should be fixed correctly in umd repository
# Copy UMD dependencies to build/lib directory
set(nng_lib_path "${CMAKE_BINARY_DIR}/_deps/nanomsg-build/libnng.so.1")
set(uv_lib_path "${CMAKE_BINARY_DIR}/_deps/libuv-build/libuv.so.1")

add_custom_command(TARGET debuda_server_lib
    POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy ${nng_lib_path} ${CMAKE_BINARY_DIR}/lib
    COMMAND ${CMAKE_COMMAND} -E copy ${uv_lib_path} ${CMAKE_BINARY_DIR}/lib
    COMMENT "Copying umd dependencies to ${CMAKE_BINARY_DIR}/lib"
)
