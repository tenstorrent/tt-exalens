// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string_view.h>

#include <variant>

#include "bindings.hpp"
#include "dwarf_die.hpp"
#include "dwarf_info.hpp"
#include "elf_file.hpp"  // ElfSymbol (forward-declared via dwarf_die.hpp)

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

void bind_dwarf_info(nb::module_& m) {
    nb::class_<DwarfInfo>(m, "DwarfInfo")
        .def("find_file_line_by_address", &DwarfInfo::find_file_line_by_address, nb::arg("address"))
        .def(
            "get_die_by_name", [](const DwarfInfo& self, std::string_view name) { return self.get_die_by_name(name); },
            nb::arg("name"), nb::rv_policy::reference_internal,
            nb::sig("def get_die_by_name(self, name: str) -> DwarfDie | None"))
        .def("find_function_by_address", &DwarfInfo::find_function_by_address, nb::arg("address"),
             nb::rv_policy::reference_internal,
             nb::sig("def find_function_by_address(self, address: int) -> DwarfDie | None"))
        // nb::rv_policy::reference_internal: the returned FrameDescription holds a raw
        // Dwarf_Fde owned by self (DwarfInfo). Tie its Python-side
        // lifetime to self so callers can't accidentally outlive the parent.
        .def("get_frame_description", &DwarfInfo::get_frame_description, nb::arg("pc"), nb::arg("memory_access"),
             nb::rv_policy::reference_internal)
        .def("find_symbol_by_name", &DwarfInfo::find_symbol_by_name, nb::arg("name"), nb::rv_policy::reference_internal,
             nb::sig("def find_symbol_by_name(self, name: str) -> ElfSymbol | None"))
        .def("get_enum_value", &DwarfInfo::get_enum_value, nb::arg("name"))
        // Like DwarfDie::get_constant_value, the variant alternatives
        // map to bool / int / float; monostate is unreachable here because
        // get_constant() throws TypeMismatchException for non-constant DIEs.
        .def(
            "get_constant",
            [](const DwarfInfo& self, std::string_view name) -> nb::object {
                return std::visit(
                    [](const auto& v) -> nb::object {
                        using T = std::decay_t<decltype(v)>;
                        if constexpr (std::is_same_v<T, std::monostate>) {
                            return nb::none();
                        } else {
                            return nb::cast(v);
                        }
                    },
                    self.get_constant(name));
            },
            nb::arg("name"), nb::sig("def get_constant(self, name: str) -> bool | int | float"))
        // nb::rv_policy::reference_internal: the returned ElfVariable holds shared_ptr
        // to a DwarfDie owned by self's DwarfInfoImpl. Without
        // this annotation, Python could release self while the variable is
        // still in use — the C++ shared_ptr would keep the DIE alive but
        // the parent Dwarf_Debug would already be finished, leaking ref-
        // counts and ultimately corrupting the heap. The native side has a
        // defensive destructor that detaches handles when the parent impl
        // is expired, but this keeps the lifetime contract intact too.
        .def("get_global", &DwarfInfo::get_global, nb::arg("name"), nb::arg("memory_access"),
             nb::rv_policy::reference_internal)
        .def("read_global", &DwarfInfo::read_global, nb::arg("name"), nb::arg("memory_access"),
             nb::rv_policy::reference_internal);
}

}  // namespace ttexalens::native_elf::bindings
