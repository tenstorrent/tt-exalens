# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

# Nanobind wrapper exposing ttexalens' native code to Python.

nanobind_add_module(
    _native_ttexalens
    STABLE_ABI
    NB_STATIC
    bindings.cpp
)

target_link_libraries(_native_ttexalens PRIVATE ttexalens_elf libdwarf::dwarf-static)

# scikit-build-core prepends `wheel.install-dir` (= "ttexalens") to DESTINATION,
# so DESTINATION "." installs the .so at ttexalens/_native_ttexalens*.so inside the wheel.
install(TARGETS _native_ttexalens LIBRARY DESTINATION "." COMPONENT python_wheel)

# Source-tree dev flow (`make` + `python tt-exalens.py`): drop the freshly
# built .so next to the Python package so `import ttexalens._native_ttexalens`
# works without `pip install .`. Skipped when scikit-build-core is driving the
# build (BUILD_PYTHON_WHEEL is set in pyproject.toml's cmake.args) so wheel
# builds don't leak artifacts into the source tree.
if(NOT BUILD_PYTHON_WHEEL)
    add_custom_command(TARGET _native_ttexalens POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            $<TARGET_FILE:_native_ttexalens>
            ${PROJECT_SOURCE_DIR}/ttexalens/$<TARGET_FILE_NAME:_native_ttexalens>
        COMMENT "Copying _native_ttexalens module into source tree for in-place imports"
    )
endif()
