// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/nanobind.h>
#include <nanobind/stl/shared_ptr.h>

#include "bindings.hpp"
#include "dwarf_cu.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

void bind_dwarf_cu(nb::module_& m) {
    // Compile-unit header. Instances are owned by DwarfInfo and only handed out
    // by reference (DwarfInfo.iter_compile_units(), DwarfDie.cu), so there is no
    // Python constructor.
    nb::class_<DwarfCompileUnit>(m, "DwarfCompileUnit")
        .def_prop_ro("die", &DwarfCompileUnit::get_die, nb::rv_policy::reference_internal,
                     nb::sig("def die(self) -> DwarfDie | None"))
        .def_prop_ro("header_length", &DwarfCompileUnit::get_header_length)
        .def_prop_ro("version", &DwarfCompileUnit::get_version)
        .def_prop_ro("abbrev_offset", &DwarfCompileUnit::get_abbrev_offset)
        .def_prop_ro("address_size", &DwarfCompileUnit::get_address_size)
        .def_prop_ro("length_size", &DwarfCompileUnit::get_length_size)
        .def_prop_ro("extension_size", &DwarfCompileUnit::get_extension_size)
        // 8-byte type signature of a type / skeleton unit; all zeros otherwise.
        .def_prop_ro(
            "signature",
            [](const DwarfCompileUnit& self) {
                const Dwarf_Sig8 signature = self.get_signature();
                return nb::bytes(signature.signature, sizeof(signature.signature));
            },
            nb::sig("def signature(self) -> bytes"))
        .def_prop_ro("type_offset", &DwarfCompileUnit::get_type_offset)
        .def_prop_ro("next_cu_offset", &DwarfCompileUnit::get_next_cu_offset)
        .def_prop_ro("header_cu_type", &DwarfCompileUnit::get_header_cu_type);
}

}  // namespace ttexalens::native_elf::bindings
