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
add_dependencies(ttlens_server_lib generate_embed_files ttlens_jtag_lib)
target_link_libraries(ttlens_server_lib
    PUBLIC umd::device fmt cppzmq-static dl
)
target_include_directories(ttlens_server_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/inc
)
set_target_properties(ttlens_server_lib PROPERTIES
    OUTPUT_NAME libttlensserver
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    POSITION_INDEPENDENT_CODE ON
)
