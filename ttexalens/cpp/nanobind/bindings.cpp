// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <libdwarf.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/vector.h>

#include <cstddef>
#include <span>

#include "dwarf_cfi.hpp"
#include "dwarf_die.hpp"
#include "dwarf_info.hpp"
#include "elf_file.hpp"

namespace nb = nanobind;

using ttexalens::native_elf::NativeDwarfDie;
using ttexalens::native_elf::NativeDwarfFileLine;
using ttexalens::native_elf::NativeDwarfInfo;
using ttexalens::native_elf::NativeElfFile;
using ttexalens::native_elf::NativeElfSection;
using ttexalens::native_elf::NativeElfSymbol;
using ttexalens::native_elf::NativeElfSymbolBinding;
using ttexalens::native_elf::NativeElfSymbolType;
using ttexalens::native_elf::NativeFrameDescription;

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

    nb::enum_<NativeElfSymbolType>(m, "NativeElfSymbolType")
        .value("STT_NOTYPE", NativeElfSymbolType::STT_NOTYPE)
        .value("STT_OBJECT", NativeElfSymbolType::STT_OBJECT)
        .value("STT_FUNC", NativeElfSymbolType::STT_FUNC)
        .value("STT_SECTION", NativeElfSymbolType::STT_SECTION)
        .value("STT_FILE", NativeElfSymbolType::STT_FILE)
        .value("STT_COMMON", NativeElfSymbolType::STT_COMMON)
        .value("STT_TLS", NativeElfSymbolType::STT_TLS)
        .value("STT_LOOS", NativeElfSymbolType::STT_LOOS)
        .value("STT_AMDGPU_HSA_KERNEL", NativeElfSymbolType::STT_AMDGPU_HSA_KERNEL)
        .value("STT_HIOS", NativeElfSymbolType::STT_HIOS)
        .value("STT_LOPROC", NativeElfSymbolType::STT_LOPROC)
        .value("STT_HIPROC", NativeElfSymbolType::STT_HIPROC);

    nb::enum_<NativeElfSymbolBinding>(m, "NativeElfSymbolBinding")
        .value("STB_LOCAL", NativeElfSymbolBinding::STB_LOCAL)
        .value("STB_GLOBAL", NativeElfSymbolBinding::STB_GLOBAL)
        .value("STB_WEAK", NativeElfSymbolBinding::STB_WEAK)
        .value("STB_LOOS", NativeElfSymbolBinding::STB_LOOS)
        .value("STB_HIOS", NativeElfSymbolBinding::STB_HIOS)
        .value("STB_MULTIDEF", NativeElfSymbolBinding::STB_MULTIDEF)
        .value("STB_LOPROC", NativeElfSymbolBinding::STB_LOPROC)
        .value("STB_HIPROC", NativeElfSymbolBinding::STB_HIPROC);

    nb::class_<NativeElfSymbol>(m, "NativeElfSymbol")
        .def_ro("name", &NativeElfSymbol::name)
        .def_ro("value", &NativeElfSymbol::value)
        .def_ro("size", &NativeElfSymbol::size)
        .def_ro("type", &NativeElfSymbol::type)
        .def_ro("bind", &NativeElfSymbol::bind);

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
        .def("read_symbol_table_section", &NativeElfFile::read_symbol_table_section, nb::arg("section_name"),
             nb::call_guard<nb::gil_scoped_release>())
        .def("has_dwarf_info", &NativeElfFile::has_dwarf_info, nb::arg("strict") = false)
        .def("get_dwarf_info", &NativeElfFile::get_dwarf_info, nb::rv_policy::reference_internal);

    nb::class_<NativeDwarfFileLine>(m, "NativeDwarfFileLine")
        .def_prop_ro("file", [](const NativeDwarfFileLine& f) -> std::string_view { return f.file; })
        .def_ro("line", &NativeDwarfFileLine::line)
        .def_ro("column", &NativeDwarfFileLine::column);

    nb::class_<NativeDwarfDie>(m, "NativeDwarfDie")
        .def_prop_ro("name", &NativeDwarfDie::get_name)
        .def_prop_ro("offset", &NativeDwarfDie::get_offset)
        .def("find_child_by_name", &NativeDwarfDie::find_child_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal)
        .def("get_die_from_attribute", &NativeDwarfDie::get_die_from_attribute, nb::arg("attribute_tag"),
             nb::rv_policy::reference_internal)
        .def("has_attribute", &NativeDwarfDie::has_attribute, nb::arg("attribute_tag"))
        .def("is_declaration", &NativeDwarfDie::is_declaration)
        .def("get_address_ranges", &NativeDwarfDie::get_address_ranges)
        .def("get_first_child", &NativeDwarfDie::get_first_child, nb::rv_policy::reference_internal)
        .def("get_next_sibling", &NativeDwarfDie::get_next_sibling, nb::rv_policy::reference_internal)
        .def("get_parent", &NativeDwarfDie::get_parent, nb::rv_policy::reference_internal);

    nb::class_<NativeDwarfInfo>(m, "NativeDwarfInfo")
        .def("find_file_line_by_address", &NativeDwarfInfo::find_file_line_by_address, nb::arg("address"))
        .def("get_die_by_name", &NativeDwarfInfo::get_die_by_name, nb::arg("name"), nb::rv_policy::reference_internal)
        .def("find_function_by_address", &NativeDwarfInfo::find_function_by_address, nb::arg("address"),
             nb::rv_policy::reference_internal)
        .def("get_frame_description", &NativeDwarfInfo::get_frame_description, nb::arg("pc"), nb::arg("read_gpr"),
             nb::arg("read_memory"));

    nb::class_<NativeFrameDescription>(m, "NativeFrameDescription")
        .def_prop_ro("pc", &NativeFrameDescription::get_pc)
        .def("read_register", &NativeFrameDescription::read_register, nb::arg("register_index"), nb::arg("cfa"))
        .def("try_read_register", &NativeFrameDescription::try_read_register, nb::arg("register_index"),
             nb::arg("cfa").none())
        .def("read_previous_cfa", &NativeFrameDescription::read_previous_cfa, nb::arg("current_cfa").none());
}
