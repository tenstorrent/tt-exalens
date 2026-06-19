// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/vector.h>

#include <optional>
#include <string>

#include "bindings.hpp"
#include "callstack.hpp"
#include "dwarf_die.hpp"
#include "elf_file.hpp"
#include "memory_access.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

void bind_callstack(nb::module_& m) {
    // name / type / declared_at are derived from `die` to mirror the Python
    // CallstackEntryVariable dataclass's cached properties, so existing call
    // sites that read .name / .value / .type / .declared_at keep working.
    nb::class_<CallstackEntryVariable>(m, "CallstackEntryVariable")
        .def_ro("die", &CallstackEntryVariable::die, nb::rv_policy::reference_internal)
        .def_ro("value", &CallstackEntryVariable::value, nb::rv_policy::reference_internal)
        .def_prop_ro(
            "name",
            [](const CallstackEntryVariable& self) -> std::optional<std::string> {
                if (!self.die) {
                    return std::nullopt;
                }
                std::string_view name = self.die->get_name();
                if (name.empty()) {
                    return std::nullopt;
                }
                return std::string(name);
            },
            nb::sig("def name(self) -> str | None"))
        .def_prop_ro(
            "type",
            [](const CallstackEntryVariable& self) { return self.die ? self.die->get_resolved_type() : nullptr; },
            nb::rv_policy::reference_internal, nb::sig("def type(self) -> DwarfDie | None"))
        .def_prop_ro("declared_at", [](const CallstackEntryVariable& self) -> std::optional<DwarfFileLine> {
            return self.die ? self.die->get_decl_file_info() : std::nullopt;
        });

    // pc / function_name / file_info are writable so the GDB-output parser
    // (gdb_client) can default-construct an entry and fill it in field by
    // field, matching the old mutable dataclass.
    nb::class_<CallstackEntry>(m, "CallstackEntry")
        .def(nb::init<>())
        .def_rw("pc", &CallstackEntry::pc)
        .def_rw("function_name", &CallstackEntry::function_name)
        .def_rw("file_info", &CallstackEntry::file_info)
        .def_ro("cfa", &CallstackEntry::cfa)
        .def_ro("arguments", &CallstackEntry::arguments, nb::rv_policy::reference_internal)
        .def_ro("locals", &CallstackEntry::locals, nb::rv_policy::reference_internal)
        .def_ro("template_parameters", &CallstackEntry::template_parameters, nb::rv_policy::reference_internal);

    // Walks the call frames from a live PC and returns the callstack. The
    // GIL is held throughout: the MemoryAccess trampoline reacquires it per
    // callback, so holding it here is correct (nested acquire is a no-op).
    m.def("get_callstack", &get_callstack, nb::arg("elfs"), nb::arg("pc"), nb::arg("memory_access"),
          nb::arg("limit") = 100, nb::arg("stop_function_name") = "main", nb::arg("extract_variables") = true,
          nb::arg("expand_tail_call_inline_frames") = false);

    // Builds the entries for the single frame at `pc` (plus its inlined virtual
    // frames), locating the covering ELF / FDE across `elfs` itself. Static
    // lookup: names and source locations only, no variable values. When
    // extract_variables is false the per-frame variable DIE lists are skipped.
    m.def("get_frame_callstack", &get_frame_callstack, nb::arg("elfs"), nb::arg("pc"),
          nb::arg("extract_variables") = true);
}

}  // namespace ttexalens::native_elf::bindings
