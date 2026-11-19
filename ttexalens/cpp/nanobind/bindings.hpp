// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <nanobind/nanobind.h>

namespace ttexalens::native_elf::bindings {

// Each function below registers a slice of the native API on the given
// nanobind module. They are invoked from the single NB_MODULE block in
// bindings.cpp; splitting them keeps that file from ballooning past the
// readable limit and pairs each binding with the cpp/elf header it wraps.
void bind_callstack(nanobind::module_& m);
void bind_dwarf_attribute(nanobind::module_& m);
void bind_dwarf_cu(nanobind::module_& m);
void bind_dwarf_die(nanobind::module_& m);
void bind_dwarf_frame(nanobind::module_& m);
void bind_dwarf_info(nanobind::module_& m);
void bind_dwarf_location(nanobind::module_& m);
void bind_elf_file(nanobind::module_& m);
void bind_memory_access(nanobind::module_& m);
void bind_variable(nanobind::module_& m);

// Makes every enumerator name that shares its value with an earlier name an
// alias of that earlier member, as a Python Enum does. nanobind binds each
// .value() as its own member, so without this a duplicate name never equals
// the member a C++ value converts to.
void alias_duplicate_enum_members(nanobind::handle enum_type);

}  // namespace ttexalens::native_elf::bindings
