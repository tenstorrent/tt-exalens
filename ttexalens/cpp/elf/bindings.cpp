// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <libdwarf.h>
#include <nanobind/nanobind.h>

namespace nb = nanobind;

NB_MODULE(_native_elf, m) {
    m.doc() = "Native ELF/DWARF parsing backend for ttexalens.elf. Private API.";

    m.def(
        "libdwarf_version", []() { return dwarf_package_version(); },
        "Return the linked libdwarf version string. Smoke test that the native module is reachable.");
}
