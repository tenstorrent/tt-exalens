# Find python package
find_package(Python REQUIRED COMPONENTS Development)

# Add nanobind CPM
CPMAddPackage(NAME nanobind GITHUB_REPOSITORY wjakob/nanobind VERSION 2.7.0 OPTIONS "CMAKE_MESSAGE_LOG_LEVEL NOTICE")

# Fix variable that nanobind uses to find Python
if(NOT Python_EXECUTABLE AND Python3_EXECUTABLE)
    set(Python_EXECUTABLE ${Python3_EXECUTABLE})
endif()

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
        set(WORKING_DIRECTORY $<TARGET_FILE_DIR:ttexalens_pybind>)
    endif()

    nanobind_add_stub(
        "${TARGET}_stub"
        MODULE ${TARGET}
        OUTPUT "${CMAKE_BINARY_DIR}/stubs/${TARGET}.pyi"
        PYTHON_PATH ${WORKING_DIRECTORY}
        DEPENDS ${TARGET})
endfunction()
