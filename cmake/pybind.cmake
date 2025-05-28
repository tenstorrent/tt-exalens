# Check if pybind11_stubgen is available in the Python environment
set(PYBIND11_STUBGEN_AVAILABLE OFF)
execute_process(
    COMMAND ${Python3_EXECUTABLE} -m pybind11_stubgen --help
    RESULT_VARIABLE _pybind11_stubgen_found
    OUTPUT_QUIET
    ERROR_QUIET
)
if(_pybind11_stubgen_found EQUAL 0)
    set(PYBIND11_STUBGEN_AVAILABLE ON)
else()
    message(WARNING "pybind11_stubgen is not available in the Python environment. Skipping stub generation.")
endif()

option(GENERATE_PYBIND_STUBS "Generate pybind11 stub files (.pyi)" ${PYBIND11_STUBGEN_AVAILABLE})


function(add_pybind_stubgen TARGET)
    set(options)
    set(oneValueArgs OUTPUT_DIR)
    set(multiValueArgs)
    cmake_parse_arguments(PYBIND_STUBGEN "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN})

    if(NOT PYBIND_STUBGEN_OUTPUT_DIR)
        set(PYBIND_STUBGEN_OUTPUT_DIR "${CMAKE_BINARY_DIR}/stubs")
    endif()

    get_target_property(MODULE_NAME ${TARGET} OUTPUT_NAME)
    if(NOT MODULE_NAME)
        set(MODULE_NAME ${TARGET})
    endif()

    get_target_property(WORKING_DIRECTORY ${TARGET} LIBRARY_OUTPUT_DIRECTORY)
    if(NOT WORKING_DIRECTORY)
        set(WORKING_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
    endif()

    if(GENERATE_PYBIND_STUBS)
        add_custom_command(TARGET ${TARGET} POST_BUILD
            COMMAND ${Python3_EXECUTABLE} -m pybind11_stubgen ${MODULE_NAME} --output-dir ${PYBIND_STUBGEN_OUTPUT_DIR}
            WORKING_DIRECTORY ${WORKING_DIRECTORY}
            COMMENT "Generating .pyi file for ${MODULE_NAME} using pybind11-stubgen"
        )
    endif()
endfunction()
