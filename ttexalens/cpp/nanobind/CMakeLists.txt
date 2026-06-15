# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

include(${CMAKE_CURRENT_SOURCE_DIR}/../../../cmake/nanobind.cmake)

# Nanobind wrapper exposing ttexalens' native code to Python.

nanobind_add_module(
    _native_ttexalens
    STABLE_ABI
    NB_STATIC
    bindings.cpp
    bind_callstack.cpp
    bind_dwarf_attribute.cpp
    bind_dwarf_die.cpp
    bind_dwarf_frame.cpp
    bind_dwarf_info.cpp
    bind_elf_file.cpp
    bind_memory_access.cpp
    bind_variable.cpp
)

target_link_libraries(_native_ttexalens PRIVATE ttexalens::elf libdwarf::dwarf-static)

# scikit-build-core prepends `wheel.install-dir` (= "ttexalens") to DESTINATION,
# so DESTINATION "." installs the .so at ttexalens/_native_ttexalens*.so inside the wheel.
install(TARGETS _native_ttexalens LIBRARY DESTINATION "." COMPONENT python_wheel)

# Drop the freshly built .so next to the Python package so
# `import ttexalens._native_ttexalens` works without `pip install .` for the
# in-source dev flow, AND so the stub generator below can import the module
# from PROJECT_SOURCE_DIR. Under scikit-build-core, PROJECT_SOURCE_DIR is an
# isolated build copy so this doesn't pollute the user's source tree.
add_custom_command(TARGET _native_ttexalens POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
        $<TARGET_FILE:_native_ttexalens>
        ${PROJECT_SOURCE_DIR}/ttexalens/$<TARGET_FILE_NAME:_native_ttexalens>
    COMMENT "Copying _native_ttexalens module into source tree for in-place imports"
)

# Type stubs for the nanobind module — drives Pylance / mypy autocomplete and
# powers static type-checking for downstream wheel consumers. The stubs-only
# package layout (`_native_ttexalens/__init__.pyi` next to the `.so`) lets
# Pylance treat the directory as the package while Python's runtime keeps
# importing the `.so` — only `__init__.py` (not `.pyi`) would turn the
# directory into a real package at runtime, so there's no conflict.
nanobind_add_stub(
    _native_ttexalens_stub
    MODULE _native_ttexalens
    OUTPUT ${PROJECT_SOURCE_DIR}/ttexalens/_native_ttexalens/__init__.pyi
    PYTHON_PATH ${PROJECT_SOURCE_DIR}
    DEPENDS _native_ttexalens
)

# Ship the stub in the wheel at ttexalens/_native_ttexalens/__init__.pyi.
install(
    FILES ${PROJECT_SOURCE_DIR}/ttexalens/_native_ttexalens/__init__.pyi
    DESTINATION "_native_ttexalens"
    COMPONENT python_wheel
)
