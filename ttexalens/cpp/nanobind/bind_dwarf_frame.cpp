// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/vector.h>

#include "bindings.hpp"
#include "dwarf_frame.hpp"
#include "memory_access.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

void bind_dwarf_frame(nb::module_& m) {
    // How one frame's CFI says to recover a register (see RegisterRuleKind in
    // dwarf_frame.hpp); saved_address is only meaningful for Saved.
    nb::enum_<RegisterRuleKind>(m, "RegisterRuleKind")
        .value("Saved", RegisterRuleKind::Saved)
        .value("SameValue", RegisterRuleKind::SameValue)
        .value("Undefined", RegisterRuleKind::Undefined)
        .value("Unknown", RegisterRuleKind::Unknown);

    nb::class_<RegisterRule>(m, "RegisterRule")
        .def_ro("kind", &RegisterRule::kind)
        .def_ro("saved_address", &RegisterRule::saved_address);

    nb::class_<FrameDescription>(m, "FrameDescription")
        .def_prop_ro("pc", &FrameDescription::get_pc)
        .def_prop_ro("pointer_size", &FrameDescription::get_pointer_size)
        .def("get_return_address_register", &FrameDescription::get_return_address_register)
        .def("classify_register_rule", &FrameDescription::classify_register_rule, nb::arg("register_index"),
             nb::arg("cfa"))
        .def("read_register", &FrameDescription::read_register, nb::arg("register_index"), nb::arg("cfa"))
        .def("try_read_register", &FrameDescription::try_read_register, nb::arg("register_index"),
             nb::arg("cfa").none())
        .def("compute_cfa", &FrameDescription::compute_cfa, nb::arg("inner_cfa").none() = nb::none());

    // Snapshot of one frame on the callstack at a particular PC. Used as
    // the building block for FrameInspection — both for the
    // inspected frame and for each frame in the inner chain.
    nb::class_<FrameSnapshot>(m, "FrameSnapshot")
        .def(nb::init<FrameDescription, uint64_t, uint64_t, uint64_t>(), nb::arg("fde"), nb::arg("cfa"),
             nb::arg("compute_pc"), nb::arg("reported_pc") = 0)
        .def_rw("fde", &FrameSnapshot::fde)
        .def_rw("cfa", &FrameSnapshot::cfa)
        .def_rw("compute_pc", &FrameSnapshot::compute_pc)
        .def_rw("reported_pc", &FrameSnapshot::reported_pc);

    // Per-frame context for DwarfDie::read_value. Construct with the
    // active MemoryAccess, the inspected frame's snapshot, and the chain
    // of frames between the inspected one and live state (live first,
    // immediate-child-of-inspected last). For the top frame, pass an empty
    // inner_frames; read_register reads live GPRs in that case.
    nb::class_<FrameInspection>(m, "FrameInspection")
        .def(nb::init<std::shared_ptr<MemoryAccess>, std::optional<FrameSnapshot>, std::vector<FrameSnapshot>>(),
             nb::arg("memory_access"), nb::arg("inspected").none() = nb::none(),
             nb::arg("inner_frames") = std::vector<FrameSnapshot>{})
        .def("read_register", &FrameInspection::read_register, nb::arg("register_index"))
        .def("read_memory", &FrameInspection::read_memory, nb::arg("address"), nb::arg("register_size"))
        .def_prop_ro("cfa", &FrameInspection::get_cfa)
        .def_prop_ro("pc", &FrameInspection::get_pc)
        .def_prop_ro("memory_access", &FrameInspection::get_memory_access);
}

}  // namespace ttexalens::native_elf::bindings
