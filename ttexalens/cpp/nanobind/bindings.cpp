// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "bindings.hpp"

#include <libdwarf.h>
#include <nanobind/nanobind.h>

#include <exception>

#include "variable.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

namespace {

// Translates the C++ ELF-variable exceptions into the existing Python
// exception classes so test code that does `except SymbolNotFoundError:`
// (etc.) keeps working unchanged when the throws originate in C++.
void register_exception_translators() {
    nb::register_exception_translator([](const std::exception_ptr& p, void* /*payload*/) {
        try {
            std::rethrow_exception(p);
        } catch (const SymbolNotFoundException& e) {
            auto exc = nb::module_::import_("ttexalens.exceptions").attr("SymbolNotFoundError")(e.member_path());
            PyErr_SetObject(PyExceptionInstance_Class(exc.ptr()), exc.ptr());
        } catch (const TypeMismatchException& e) {
            auto exc =
                nb::module_::import_("ttexalens.exceptions").attr("TypeMismatchError")(e.operation(), e.actual_type());
            PyErr_SetObject(PyExceptionInstance_Class(exc.ptr()), exc.ptr());
        } catch (const InvalidArrayAccessException& e) {
            auto length = e.length().has_value() ? nb::cast(*e.length()) : nb::cast(nb::none());
            auto exc = nb::module_::import_("ttexalens.exceptions").attr("InvalidArrayAccessError")(e.index(), length);
            PyErr_SetObject(PyExceptionInstance_Class(exc.ptr()), exc.ptr());
        } catch (const DataLossException& e) {
            auto exc =
                nb::module_::import_("ttexalens.exceptions").attr("DataLossError")(e.value_repr(), e.type_name());
            PyErr_SetObject(PyExceptionInstance_Class(exc.ptr()), exc.ptr());
        }
    });
}

}  // namespace

}  // namespace ttexalens::native_elf::bindings

NB_MODULE(_native_ttexalens, m) {
    using namespace ttexalens::native_elf::bindings;

    m.doc() = "Native code backend for ttexalens. Private API.";

    register_exception_translators();

    m.def(
        "libdwarf_version", []() { return dwarf_package_version(); },
        "Return the linked libdwarf version string. Smoke test that the native module is reachable.");

    // Order roughly follows the dependency graph — types referenced in
    // method signatures are bound first so the runtime type registry is
    // populated before any binding that mentions them.
    bind_dwarf_attribute(m);
    bind_dwarf_die(m);
    bind_memory_access(m);
    bind_elf_file(m);
    bind_dwarf_info(m);
    bind_dwarf_frame(m);
    bind_variable(m);
    bind_callstack(m);
}
