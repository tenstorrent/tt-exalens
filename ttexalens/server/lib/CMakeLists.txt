# Converting configuration files to embed
set(CONFIG_FILEPATH "${CMAKE_CURRENT_SOURCE_DIR}/configuration")
set(DEVICE_FILEPATH "${CMAKE_CURRENT_SOURCE_DIR}/../device")

set(TTEXALENS_SERVER_LIB_CONFIGURATION_FILES
    "${CONFIG_FILEPATH}/blackhole.embed" "${DEVICE_FILEPATH}/blackhole_10x14.yaml"
    "${CONFIG_FILEPATH}/grayskull.embed" "${DEVICE_FILEPATH}/grayskull_10x12.yaml"
    "${CONFIG_FILEPATH}/wormhole_b0.embed" "${DEVICE_FILEPATH}/wormhole_b0_8x10.yaml"
)

set(TTEXALENS_SERVER_LIB_EMBED_FILES "")

list(LENGTH TTEXALENS_SERVER_LIB_CONFIGURATION_FILES TTEXALENS_SERVER_LIB_EMBED_FILES_COUNT)
math(EXPR last_index "${TTEXALENS_SERVER_LIB_EMBED_FILES_COUNT} - 2")

foreach(i RANGE 0 ${last_index} 2)
    list(GET TTEXALENS_SERVER_LIB_CONFIGURATION_FILES ${i} embed_file)
    math(EXPR yaml_index "${i} + 1")
    list(GET TTEXALENS_SERVER_LIB_CONFIGURATION_FILES ${yaml_index} yaml_file)

    list(APPEND TTEXALENS_SERVER_LIB_EMBED_FILES ${embed_file})

    add_custom_command(
        OUTPUT ${embed_file}
        COMMAND ${CMAKE_COMMAND} -E make_directory ${CONFIG_FILEPATH}
        COMMAND cat ${yaml_file} | xxd -i > ${embed_file}
        DEPENDS ${yaml_file}
        COMMENT "Generating ${embed_file} from ${yaml_file}"
    )
endforeach()

add_custom_target(generate_embed_files ALL
    DEPENDS ${TTEXALENS_SERVER_LIB_EMBED_FILES}
)

# Library project
file(GLOB TTEXALENS_SERVER_LIB_SRCS "src/*.cpp")
add_library(ttexalens_server_lib STATIC ${TTEXALENS_SERVER_LIB_SRCS})
add_dependencies(ttexalens_server_lib generate_embed_files ttexalens_jtag_lib)
target_link_libraries(ttexalens_server_lib
    PUBLIC umd::device fmt cppzmq-static dl
)
target_include_directories(ttexalens_server_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/inc
)
set_target_properties(ttexalens_server_lib PROPERTIES
    OUTPUT_NAME libttexalensserver
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
    POSITION_INDEPENDENT_CODE ON
)
