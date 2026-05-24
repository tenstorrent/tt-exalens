// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <libdwarf.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/vector.h>

#include <cstddef>
#include <span>

#include "elf_file.hpp"

namespace nb = nanobind;

using ttexalens::native_elf::NativeElfFile;
using ttexalens::native_elf::NativeElfSection;

NB_MODULE(_native_elf, m) {
    m.doc() = "Native ELF/DWARF parsing backend for ttexalens.elf. Private API.";

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
        .def("sections", &NativeElfFile::sections)
        .def("get_section_by_name", &NativeElfFile::get_section_by_name, nb::arg("name"));
}
