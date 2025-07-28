find_package(Python REQUIRED COMPONENTS Development)

####################################################################################################################
# nanobind
####################################################################################################################
CPMAddPackage(NAME nanobind GITHUB_REPOSITORY wjakob/nanobind VERSION 2.7.0 OPTIONS "CMAKE_MESSAGE_LOG_LEVEL NOTICE")


# Check if nanobind_stubgen is available in the Python environment
set(NANOBIND_STUBGEN_AVAILABLE OFF)
execute_process(
    COMMAND ${Python3_EXECUTABLE} -m nanobind_stubgen --help
    RESULT_VARIABLE _nanobind_stubgen_found
    OUTPUT_QUIET
    ERROR_QUIET
)
if(_nanobind_stubgen_found EQUAL 0)
    set(NANOBIND_STUBGEN_AVAILABLE ON)
else()
    message(WARNING "nanobind_stubgen is not available in the Python environment. Skipping stub generation.")
endif()

option(GENERATE_NANOBIND_STUBS "Generate nanobind stub files (.pyi)" ${NANOBIND_STUBGEN_AVAILABLE})


function(add_pybind_stubgen TARGET)
    set(options)
    set(oneValueArgs OUTPUT_DIR)
    set(multiValueArgs)
    cmake_parse_arguments(NANOBIND_STUBGEN "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    if(NOT NANOBIND_STUBGEN_OUTPUT_DIR)
        set(NANOBIND_STUBGEN_OUTPUT_DIR "${CMAKE_BINARY_DIR}/stubs")
    endif()

    get_target_property(MODULE_NAME ${TARGET} OUTPUT_NAME)
    if(NOT MODULE_NAME)
        set(MODULE_NAME ${TARGET})
    endif()

    get_target_property(WORKING_DIRECTORY ${TARGET} LIBRARY_OUTPUT_DIRECTORY)
    if(NOT WORKING_DIRECTORY)
        set(WORKING_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
    endif()

    if(GENERATE_NANOBIND_STUBS)
        if(NOT EXISTS ${NANOBIND_STUBGEN_OUTPUT_DIR})
            file(MAKE_DIRECTORY ${NANOBIND_STUBGEN_OUTPUT_DIR})
        endif()
        add_custom_command(TARGET ${TARGET} POST_BUILD
            COMMAND ${Python3_EXECUTABLE} -m nanobind_stubgen ${MODULE_NAME} --out ${NANOBIND_STUBGEN_OUTPUT_DIR}
            WORKING_DIRECTORY ${WORKING_DIRECTORY}
            COMMENT "Generating .pyi file for ${MODULE_NAME} using nanobind-stubgen"
        )
    endif()
endfunction()
