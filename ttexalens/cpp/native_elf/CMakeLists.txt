# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

# Nanobind wrapper around the pure-C++ ttexalens_elf library.

nanobind_add_module(
    _native_elf
    STABLE_ABI
    NB_STATIC
    bindings.cpp
)

target_link_libraries(_native_elf PRIVATE ttexalens_elf libdwarf::dwarf-static)

# scikit-build-core prepends `wheel.install-dir` (= "ttexalens") to DESTINATION,
# so DESTINATION "." installs the .so at ttexalens/_native_elf*.so inside the wheel.
install(TARGETS _native_elf LIBRARY DESTINATION "." COMPONENT python_wheel)
