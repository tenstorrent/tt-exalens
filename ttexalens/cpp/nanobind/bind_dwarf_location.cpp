// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>

#include "bindings.hpp"
#include "dwarf_die.hpp"
#include "dwarf_frame.hpp"
#include "dwarf_location.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

void bind_dwarf_location(nb::module_& m) {
    // Result of evaluating a DW_AT_location expression: either the address of
    // the variable's bytes (is_address) or the value itself (`value`, or
    // `raw_bytes` for payloads wider than 64 bits).
    nb::class_<LocationResult>(m, "LocationResult")
        .def_ro("is_address", &LocationResult::is_address)
        .def_ro("value", &LocationResult::value)
        .def_prop_ro(
            "raw_bytes",
            [](const LocationResult& self) {
                return nb::bytes(reinterpret_cast<const char*>(self.raw_bytes.data()), self.raw_bytes.size());
            },
            nb::sig("def raw_bytes(self) -> bytes"));

    // Evaluates `die`'s DW_AT_location against `frame` (None for no frame
    // context). Returns None when the location can't be resolved.
    m.def("evaluate_die_location", &evaluate_die_location, nb::arg("die"), nb::arg("frame").none());
}

}  // namespace ttexalens::native_elf::bindings
