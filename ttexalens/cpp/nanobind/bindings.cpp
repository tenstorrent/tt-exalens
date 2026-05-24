// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <libdwarf.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>

#include <cstddef>
#include <span>

#include "dwarf_info.hpp"
#include "elf_file.hpp"

namespace nb = nanobind;

using ttexalens::native_elf::NativeDwarfInfo;
using ttexalens::native_elf::NativeElfFile;
using ttexalens::native_elf::NativeElfSection;

NB_MODULE(_native_ttexalens, m) {
    m.doc() = "Native code backend for ttexalens. Private API.";

    m.def(
        "libdwarf_version", []() { return dwarf_package_version(); },
        "Return the linked libdwarf version string. Smoke test that the native module is reachable.");

    nb::class_<NativeElfSection>(m, "NativeElfSection")
        .def_prop_ro("name", &NativeElfSection::name)
        .def_prop_ro("address", &NativeElfSection::address)
        .def_prop_ro("size", &NativeElfSection::size)
        .def_prop_ro("data", [](const NativeElfSection& s) {
            std::span<const std::byte> sp = s.data();
            return nb::bytes(reinterpret_cast<const char*>(sp.data()), sp.size());
        });

    nb::class_<NativeElfFile>(m, "NativeElfFile")
        .def(nb::init<const std::string&>(), nb::arg("path"))
        .def_static(
            "from_bytes",
            [](nb::bytes data) {
                return NativeElfFile::from_bytes(
                    std::span<const std::byte>(reinterpret_cast<const std::byte*>(data.c_str()), data.size()));
            },
            nb::arg("data"))
        .def("get_sections_count", &NativeElfFile::get_sections_count)
        .def("get_section", &NativeElfFile::get_section, nb::arg("index"), nb::rv_policy::reference_internal)
        .def("get_section_by_name", &NativeElfFile::get_section_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal)
        .def("has_dwarf_info", &NativeElfFile::has_dwarf_info, nb::arg("strict") = false)
        .def("get_dwarf_info", &NativeElfFile::get_dwarf_info, nb::rv_policy::reference_internal);

    // Opaque handle to a libdwarf Dwarf_Debug. No methods are exposed yet —
    // future DWARF queries (CU iteration, DIE lookup, line program, ...) will
    // be added here.
    nb::class_<NativeDwarfInfo>(m, "NativeDwarfInfo");
}
