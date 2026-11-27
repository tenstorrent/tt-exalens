// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/make_iterator.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/function.h>
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
        // Compile units in .debug_info order, by reference: they're owned by
        // self and live as long as it does.
        .def(
            "iter_compile_units",
            [](const DwarfInfo& self) {
                auto units = self.get_compile_units();
                return nb::make_iterator<nb::rv_policy::reference_internal>(
                    nb::type<DwarfInfo>(), "DwarfCompileUnitIterator", units.begin(), units.end());
            },
            nb::keep_alive<0, 1>())
        .def("find_file_line_by_address", &DwarfInfo::find_file_line_by_address, nb::arg("address"))
        .def(
            "get_die_by_name",
            [](const DwarfInfo& self, std::string_view name,
               std::optional<std::function<bool(const DwarfDiePtr&)>> filter) {
                std::function<bool(const DwarfDiePtr&)> wrapped_filter;
                if (filter) {
                    wrapped_filter = [f = *filter](const DwarfDiePtr& d) { return f(DwarfDie::keep_elf_alive(d)); };
                }
                return DwarfDie::keep_elf_alive(self.get_die_by_name(name, wrapped_filter));
            },
            nb::arg("name"), nb::arg("filter") = nb::none(),
            nb::sig("def get_die_by_name(self, name: str, filter: collections.abc.Callable[[DwarfDie], bool] | None = "
                    "None) -> DwarfDie | None"))
        .def(
            "find_function_by_address",
            [](const DwarfInfo& self, uint64_t address) {
                return DwarfDie::keep_elf_alive(self.find_function_by_address(address));
            },
            nb::arg("address"), nb::sig("def find_function_by_address(self, address: int) -> DwarfDie | None"))
        // The returned object holds the parsed ELF itself (see DwarfDie::keep_elf_alive),
        // so it stays valid after self is released.
        .def("get_frame_description", &DwarfInfo::get_frame_description, nb::arg("pc"), nb::arg("memory_access"))
        .def("find_symbol_by_name", &DwarfInfo::find_symbol_by_name, nb::arg("name"), nb::rv_policy::reference_internal,
             nb::sig("def find_symbol_by_name(self, name: str) -> ElfSymbol | None"))
        .def("find_symbol_by_demangled_name", &DwarfInfo::find_symbol_by_demangled_name, nb::arg("demangled_name"),
             nb::rv_policy::reference_internal,
             nb::sig("def find_symbol_by_demangled_name(self, demangled_name: str) -> ElfSymbol | None"))
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
        // The returned object holds the parsed ELF itself (see DwarfDie::keep_elf_alive),
        // so it stays valid after self is released.
        .def("get_global", &DwarfInfo::get_global, nb::arg("name"), nb::arg("memory_access"))
        .def("read_global", &DwarfInfo::read_global, nb::arg("name"), nb::arg("memory_access"));
}

}  // namespace ttexalens::native_elf::bindings
