// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <dwarf.h>  // DW_TAG_* / DW_AT_* constants
#include <libdwarf.h>
#include <nanobind/make_iterator.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/variant.h>
#include <nanobind/stl/vector.h>
#include <nanobind/trampoline.h>

#include <cstddef>
#include <span>

#include "dwarf_attribute.hpp"
#include "dwarf_die.hpp"
#include "dwarf_frame.hpp"
#include "dwarf_info.hpp"
#include "elf_file.hpp"
#include "memory_access.hpp"
#include "variable.hpp"

namespace nb = nanobind;

using ttexalens::native_elf::DataLossException;
using ttexalens::native_elf::InvalidArrayAccessException;
using ttexalens::native_elf::MemoryAccess;
using ttexalens::native_elf::NativeDwarfAttribute;
using ttexalens::native_elf::NativeDwarfAttributeForm;
using ttexalens::native_elf::NativeDwarfAttributeTag;
using ttexalens::native_elf::NativeDwarfDie;
using ttexalens::native_elf::NativeDwarfDieTag;
using ttexalens::native_elf::NativeDwarfFileLine;
using ttexalens::native_elf::NativeDwarfInfo;
using ttexalens::native_elf::NativeElfFile;
using ttexalens::native_elf::NativeElfSection;
using ttexalens::native_elf::NativeElfSymbol;
using ttexalens::native_elf::NativeElfSymbolBinding;
using ttexalens::native_elf::NativeElfSymbolType;
using ttexalens::native_elf::NativeElfVariable;
using ttexalens::native_elf::NativeFrameDescription;
using ttexalens::native_elf::NativeFrameInspection;
using ttexalens::native_elf::SymbolNotFoundException;
using ttexalens::native_elf::TypeMismatchException;

namespace {

// Forward iterator over a DIE's direct children, walking the
// first_child/next_sibling linked-list. Used by NativeDwarfDie.iter_children's
// nb::make_iterator binding to produce a Python iterator for
// `for child in die.iter_children():`.
class DieChildIterator {
   public:
    DieChildIterator() = default;
    explicit DieChildIterator(ttexalens::native_elf::NativeDwarfDiePtr c) : current(std::move(c)) {}

    const ttexalens::native_elf::NativeDwarfDiePtr& operator*() const { return current; }
    DieChildIterator& operator++() {
        if (current) {
            current = current->get_next_sibling();
        }
        return *this;
    }
    bool operator==(const DieChildIterator& other) const { return current == other.current; }
    bool operator!=(const DieChildIterator& other) const { return !(*this == other); }

   private:
    ttexalens::native_elf::NativeDwarfDiePtr current;
};

// Trampoline so Python can subclass MemoryAccess and provide implementations.
class MemoryAccessTrampoline : public MemoryAccess {
   public:
    NB_TRAMPOLINE(MemoryAccess, 4);

    void read(uint64_t address, std::span<std::byte> buffer) const override {
        nb::gil_scoped_acquire gil;
        nanobind::detail::ticket nb_ticket(nb_trampoline, "read", /*pure=*/true);
        // Hand Python a writable memoryview over our buffer — zero-copy on
        // the C++ to Python boundary. Python writes directly into it.
        PyObject* mv = PyMemoryView_FromMemory(reinterpret_cast<char*>(buffer.data()),
                                               static_cast<Py_ssize_t>(buffer.size()), PyBUF_WRITE);
        if (mv == nullptr) {
            throw nb::python_error();
        }
        nb::object py_buf = nb::steal<nb::object>(mv);
        nb_trampoline.base().attr(nb_ticket.key)(address, py_buf);
    }

    void write(uint64_t address, std::span<const std::byte> buffer) override {
        nb::gil_scoped_acquire gil;
        nanobind::detail::ticket nb_ticket(nb_trampoline, "write", /*pure=*/true);
        // Hand Python a read-only memoryview over our buffer — zero-copy on
        // the C++ to Python boundary.
        PyObject* mv = PyMemoryView_FromMemory(const_cast<char*>(reinterpret_cast<const char*>(buffer.data())),
                                               static_cast<Py_ssize_t>(buffer.size()), PyBUF_READ);
        if (mv == nullptr) {
            throw nb::python_error();
        }
        nb::object data = nb::steal<nb::object>(mv);
        nb_trampoline.base().attr(nb_ticket.key)(address, data);
    }

    uint64_t read_register(uint16_t register_index) const override { NB_OVERRIDE_PURE(read_register, register_index); }

    void write_register(uint16_t register_index, uint64_t value) override {
        NB_OVERRIDE_PURE(write_register, register_index, value);
    }
};

}  // namespace

// Helpers for NativeElfVariable dunders: reduce a C++ TypeMismatchException
// (raised when read_value is called on a non-base/pointer/enum type) to
// Python's NotImplemented so the arithmetic/comparison operators degrade
// gracefully, matching the Python ElfVariable contract.
namespace {

nb::object var_value_obj(const NativeElfVariable& self) { return nb::cast(self.read_value()); }

template <typename Op>
nb::object try_binop(const NativeElfVariable& self, nb::handle other, Op&& op) {
    try {
        return op(var_value_obj(self), other);
    } catch (const TypeMismatchException&) {
        return nb::borrow(Py_NotImplemented);
    } catch (const nb::python_error& e) {
        if (e.matches(PyExc_TypeError)) {
            return nb::borrow(Py_NotImplemented);
        }
        throw;
    }
}

}  // namespace

NB_MODULE(_native_ttexalens, m) {
    m.doc() = "Native code backend for ttexalens. Private API.";

    // Translate the C++ ELF-variable exceptions into the existing Python
    // exception classes so test code that does `except SymbolNotFoundError:`
    // (etc.) keeps working unchanged when the throws originate in C++.
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

    m.def(
        "libdwarf_version", []() { return dwarf_package_version(); },
        "Return the linked libdwarf version string. Smoke test that the native module is reachable.");

    // DWARF DIE tag values. Use with:
    //   from ttexalens._native_ttexalens import NativeDwarfDieTag as tag
    //   if die.tag == tag.subprogram: ...
    // Python sees a regular enum.Enum; comparisons against NativeDwarfDie.tag
    // (also a NativeDwarfDieTag instance) work directly.
    nb::enum_<ttexalens::native_elf::NativeDwarfDieTag>(m, "NativeDwarfDieTag")
        .value("access_declaration", NativeDwarfDieTag::access_declaration)
        .value("ALTIUM_circ_type", NativeDwarfDieTag::ALTIUM_circ_type)
        .value("ALTIUM_mwa_circ_type", NativeDwarfDieTag::ALTIUM_mwa_circ_type)
        .value("ALTIUM_rev_carry_type", NativeDwarfDieTag::ALTIUM_rev_carry_type)
        .value("ALTIUM_rom", NativeDwarfDieTag::ALTIUM_rom)
        .value("array_type", NativeDwarfDieTag::array_type)
        .value("atomic_type", NativeDwarfDieTag::atomic_type)
        .value("base_type", NativeDwarfDieTag::base_type)
        .value("BORLAND_Delphi_dynamic_array", NativeDwarfDieTag::BORLAND_Delphi_dynamic_array)
        .value("BORLAND_Delphi_set", NativeDwarfDieTag::BORLAND_Delphi_set)
        .value("BORLAND_Delphi_string", NativeDwarfDieTag::BORLAND_Delphi_string)
        .value("BORLAND_Delphi_variant", NativeDwarfDieTag::BORLAND_Delphi_variant)
        .value("BORLAND_property", NativeDwarfDieTag::BORLAND_property)
        .value("call_site", NativeDwarfDieTag::call_site)
        .value("call_site_parameter", NativeDwarfDieTag::call_site_parameter)
        .value("catch_block", NativeDwarfDieTag::catch_block)
        .value("class_template", NativeDwarfDieTag::class_template)
        .value("class_type", NativeDwarfDieTag::class_type)
        .value("coarray_type", NativeDwarfDieTag::coarray_type)
        .value("common_block", NativeDwarfDieTag::common_block)
        .value("common_inclusion", NativeDwarfDieTag::common_inclusion)
        .value("compile_unit", NativeDwarfDieTag::compile_unit)
        .value("condition", NativeDwarfDieTag::condition)
        .value("const_type", NativeDwarfDieTag::const_type)
        .value("constant", NativeDwarfDieTag::constant)
        .value("dwarf_procedure", NativeDwarfDieTag::dwarf_procedure)
        .value("dynamic_type", NativeDwarfDieTag::dynamic_type)
        .value("entry_point", NativeDwarfDieTag::entry_point)
        .value("enumeration_type", NativeDwarfDieTag::enumeration_type)
        .value("enumerator", NativeDwarfDieTag::enumerator)
        .value("file_type", NativeDwarfDieTag::file_type)
        .value("formal_parameter", NativeDwarfDieTag::formal_parameter)
        .value("format_label", NativeDwarfDieTag::format_label)
        .value("friend", NativeDwarfDieTag::friend_)
        .value("function_template", NativeDwarfDieTag::function_template)
        .value("generic_subrange", NativeDwarfDieTag::generic_subrange)
        .value("ghs_namespace", NativeDwarfDieTag::ghs_namespace)
        .value("ghs_template_templ_param", NativeDwarfDieTag::ghs_template_templ_param)
        .value("ghs_using_declaration", NativeDwarfDieTag::ghs_using_declaration)
        .value("ghs_using_namespace", NativeDwarfDieTag::ghs_using_namespace)
        .value("GNU_BINCL", NativeDwarfDieTag::GNU_BINCL)
        .value("GNU_call_site", NativeDwarfDieTag::GNU_call_site)
        .value("GNU_call_site_parameter", NativeDwarfDieTag::GNU_call_site_parameter)
        .value("GNU_EINCL", NativeDwarfDieTag::GNU_EINCL)
        .value("GNU_formal_parameter_pack", NativeDwarfDieTag::GNU_formal_parameter_pack)
        .value("GNU_template_parameter_pack", NativeDwarfDieTag::GNU_template_parameter_pack)
        .value("GNU_template_template_parameter", NativeDwarfDieTag::GNU_template_template_parameter)
        .value("HP_array_descriptor", NativeDwarfDieTag::HP_array_descriptor)
        .value("immutable_type", NativeDwarfDieTag::immutable_type)
        .value("imported_declaration", NativeDwarfDieTag::imported_declaration)
        .value("imported_module", NativeDwarfDieTag::imported_module)
        .value("imported_unit", NativeDwarfDieTag::imported_unit)
        .value("inheritance", NativeDwarfDieTag::inheritance)
        .value("inlined_subroutine", NativeDwarfDieTag::inlined_subroutine)
        .value("interface_type", NativeDwarfDieTag::interface_type)
        .value("label", NativeDwarfDieTag::label)
        .value("lexical_block", NativeDwarfDieTag::lexical_block)
        .value("LLVM_annotation", NativeDwarfDieTag::LLVM_annotation)
        .value("member", NativeDwarfDieTag::member)
        .value("MIPS_loop", NativeDwarfDieTag::MIPS_loop)
        .value("module", NativeDwarfDieTag::module)
        .value("mutable_type", NativeDwarfDieTag::mutable_type)
        .value("namelist", NativeDwarfDieTag::namelist)
        .value("namelist_item", NativeDwarfDieTag::namelist_item)
        .value("namespace", NativeDwarfDieTag::namespace_)
        .value("packed_type", NativeDwarfDieTag::packed_type)
        .value("partial_unit", NativeDwarfDieTag::partial_unit)
        .value("PGI_interface_block", NativeDwarfDieTag::PGI_interface_block)
        .value("PGI_kanji_type", NativeDwarfDieTag::PGI_kanji_type)
        .value("pointer_type", NativeDwarfDieTag::pointer_type)
        .value("ptr_to_member_type", NativeDwarfDieTag::ptr_to_member_type)
        .value("reference_type", NativeDwarfDieTag::reference_type)
        .value("restrict_type", NativeDwarfDieTag::restrict_type)
        .value("rvalue_reference_type", NativeDwarfDieTag::rvalue_reference_type)
        .value("set_type", NativeDwarfDieTag::set_type)
        .value("shared_type", NativeDwarfDieTag::shared_type)
        .value("skeleton_unit", NativeDwarfDieTag::skeleton_unit)
        .value("string_type", NativeDwarfDieTag::string_type)
        .value("structure_type", NativeDwarfDieTag::structure_type)
        .value("subprogram", NativeDwarfDieTag::subprogram)
        .value("subrange_type", NativeDwarfDieTag::subrange_type)
        .value("subroutine_type", NativeDwarfDieTag::subroutine_type)
        .value("SUN_class_template", NativeDwarfDieTag::SUN_class_template)
        .value("SUN_codeflags", NativeDwarfDieTag::SUN_codeflags)
        .value("SUN_dtor", NativeDwarfDieTag::SUN_dtor)
        .value("SUN_dtor_info", NativeDwarfDieTag::SUN_dtor_info)
        .value("SUN_f90_interface", NativeDwarfDieTag::SUN_f90_interface)
        .value("SUN_fortran_vax_structure", NativeDwarfDieTag::SUN_fortran_vax_structure)
        .value("SUN_function_template", NativeDwarfDieTag::SUN_function_template)
        .value("SUN_hi", NativeDwarfDieTag::SUN_hi)
        .value("SUN_indirect_inheritance", NativeDwarfDieTag::SUN_indirect_inheritance)
        .value("SUN_memop_info", NativeDwarfDieTag::SUN_memop_info)
        .value("SUN_omp_child_func", NativeDwarfDieTag::SUN_omp_child_func)
        .value("SUN_rtti_descriptor", NativeDwarfDieTag::SUN_rtti_descriptor)
        .value("SUN_struct_template", NativeDwarfDieTag::SUN_struct_template)
        .value("SUN_union_template", NativeDwarfDieTag::SUN_union_template)
        .value("template_alias", NativeDwarfDieTag::template_alias)
        .value("template_type_parameter", NativeDwarfDieTag::template_type_parameter)
        .value("template_value_parameter", NativeDwarfDieTag::template_value_parameter)
        .value("thrown_type", NativeDwarfDieTag::thrown_type)
        .value("TI_assign_register", NativeDwarfDieTag::TI_assign_register)
        .value("TI_far_type", NativeDwarfDieTag::TI_far_type)
        .value("TI_ioport_type", NativeDwarfDieTag::TI_ioport_type)
        .value("TI_near_type", NativeDwarfDieTag::TI_near_type)
        .value("TI_onchip_type", NativeDwarfDieTag::TI_onchip_type)
        .value("TI_restrict_type", NativeDwarfDieTag::TI_restrict_type)
        .value("try_block", NativeDwarfDieTag::try_block)
        .value("type_unit", NativeDwarfDieTag::type_unit)
        .value("typedef", NativeDwarfDieTag::typedef_)
        .value("union_type", NativeDwarfDieTag::union_type)
        .value("unspecified_parameters", NativeDwarfDieTag::unspecified_parameters)
        .value("unspecified_type", NativeDwarfDieTag::unspecified_type)
        .value("upc_relaxed_type", NativeDwarfDieTag::upc_relaxed_type)
        .value("upc_shared_type", NativeDwarfDieTag::upc_shared_type)
        .value("upc_strict_type", NativeDwarfDieTag::upc_strict_type)
        .value("variable", NativeDwarfDieTag::variable)
        .value("variant", NativeDwarfDieTag::variant)
        .value("variant_part", NativeDwarfDieTag::variant_part)
        .value("volatile_type", NativeDwarfDieTag::volatile_type)
        .value("with_stmt", NativeDwarfDieTag::with_stmt);

    // DW_AT_* attribute tags. Use with:
    //   from ttexalens._native_ttexalens import NativeDwarfAttributeTag as at
    //   die.get_attribute(at.declaration)
    nb::enum_<NativeDwarfAttributeTag>(m, "NativeDwarfAttributeTag")
        .value("abstract_origin", NativeDwarfAttributeTag::abstract_origin)
        .value("accessibility", NativeDwarfAttributeTag::accessibility)
        .value("addr_base", NativeDwarfAttributeTag::addr_base)
        .value("address_class", NativeDwarfAttributeTag::address_class)
        .value("alignment", NativeDwarfAttributeTag::alignment)
        .value("allocated", NativeDwarfAttributeTag::allocated)
        .value("ALTIUM_loclist", NativeDwarfAttributeTag::ALTIUM_loclist)
        .value("APPLE_block", NativeDwarfAttributeTag::APPLE_block)
        .value("APPLE_flags", NativeDwarfAttributeTag::APPLE_flags)
        .value("APPLE_isa", NativeDwarfAttributeTag::APPLE_isa)
        .value("APPLE_major_runtime_vers", NativeDwarfAttributeTag::APPLE_major_runtime_vers)
        .value("APPLE_objc_complete_type", NativeDwarfAttributeTag::APPLE_objc_complete_type)
        .value("APPLE_objc_direct", NativeDwarfAttributeTag::APPLE_objc_direct)
        .value("APPLE_omit_frame_ptr", NativeDwarfAttributeTag::APPLE_omit_frame_ptr)
        .value("APPLE_optimized", NativeDwarfAttributeTag::APPLE_optimized)
        .value("APPLE_origin", NativeDwarfAttributeTag::APPLE_origin)
        .value("APPLE_property", NativeDwarfAttributeTag::APPLE_property)
        .value("APPLE_property_attribute", NativeDwarfAttributeTag::APPLE_property_attribute)
        .value("APPLE_property_getter", NativeDwarfAttributeTag::APPLE_property_getter)
        .value("APPLE_property_name", NativeDwarfAttributeTag::APPLE_property_name)
        .value("APPLE_property_setter", NativeDwarfAttributeTag::APPLE_property_setter)
        .value("APPLE_runtime_class", NativeDwarfAttributeTag::APPLE_runtime_class)
        .value("APPLE_sdk", NativeDwarfAttributeTag::APPLE_sdk)
        .value("artificial", NativeDwarfAttributeTag::artificial)
        .value("associated", NativeDwarfAttributeTag::associated)
        .value("base_types", NativeDwarfAttributeTag::base_types)
        .value("binary_scale", NativeDwarfAttributeTag::binary_scale)
        .value("bit_offset", NativeDwarfAttributeTag::bit_offset)
        .value("bit_size", NativeDwarfAttributeTag::bit_size)
        .value("bit_stride", NativeDwarfAttributeTag::bit_stride)
        .value("body_begin", NativeDwarfAttributeTag::body_begin)
        .value("body_end", NativeDwarfAttributeTag::body_end)
        .value("BORLAND_closure", NativeDwarfAttributeTag::BORLAND_closure)
        .value("BORLAND_Delphi_ABI", NativeDwarfAttributeTag::BORLAND_Delphi_ABI)
        .value("BORLAND_Delphi_anonymous_method", NativeDwarfAttributeTag::BORLAND_Delphi_anonymous_method)
        .value("BORLAND_Delphi_class", NativeDwarfAttributeTag::BORLAND_Delphi_class)
        .value("BORLAND_Delphi_constructor", NativeDwarfAttributeTag::BORLAND_Delphi_constructor)
        .value("BORLAND_Delphi_destructor", NativeDwarfAttributeTag::BORLAND_Delphi_destructor)
        .value("BORLAND_Delphi_frameptr", NativeDwarfAttributeTag::BORLAND_Delphi_frameptr)
        .value("BORLAND_Delphi_interface", NativeDwarfAttributeTag::BORLAND_Delphi_interface)
        .value("BORLAND_Delphi_metaclass", NativeDwarfAttributeTag::BORLAND_Delphi_metaclass)
        .value("BORLAND_Delphi_record", NativeDwarfAttributeTag::BORLAND_Delphi_record)
        .value("BORLAND_Delphi_unit", NativeDwarfAttributeTag::BORLAND_Delphi_unit)
        .value("BORLAND_property_default", NativeDwarfAttributeTag::BORLAND_property_default)
        .value("BORLAND_property_implements", NativeDwarfAttributeTag::BORLAND_property_implements)
        .value("BORLAND_property_index", NativeDwarfAttributeTag::BORLAND_property_index)
        .value("BORLAND_property_read", NativeDwarfAttributeTag::BORLAND_property_read)
        .value("BORLAND_property_write", NativeDwarfAttributeTag::BORLAND_property_write)
        .value("byte_size", NativeDwarfAttributeTag::byte_size)
        .value("byte_stride", NativeDwarfAttributeTag::byte_stride)
        .value("call_all_calls", NativeDwarfAttributeTag::call_all_calls)
        .value("call_all_source_calls", NativeDwarfAttributeTag::call_all_source_calls)
        .value("call_all_tail_calls", NativeDwarfAttributeTag::call_all_tail_calls)
        .value("call_column", NativeDwarfAttributeTag::call_column)
        .value("call_data_location", NativeDwarfAttributeTag::call_data_location)
        .value("call_data_value", NativeDwarfAttributeTag::call_data_value)
        .value("call_file", NativeDwarfAttributeTag::call_file)
        .value("call_line", NativeDwarfAttributeTag::call_line)
        .value("call_origin", NativeDwarfAttributeTag::call_origin)
        .value("call_parameter", NativeDwarfAttributeTag::call_parameter)
        .value("call_pc", NativeDwarfAttributeTag::call_pc)
        .value("call_return_pc", NativeDwarfAttributeTag::call_return_pc)
        .value("call_tail_call", NativeDwarfAttributeTag::call_tail_call)
        .value("call_target", NativeDwarfAttributeTag::call_target)
        .value("call_target_clobbered", NativeDwarfAttributeTag::call_target_clobbered)
        .value("call_value", NativeDwarfAttributeTag::call_value)
        .value("calling_convention", NativeDwarfAttributeTag::calling_convention)
        .value("common_reference", NativeDwarfAttributeTag::common_reference)
        .value("comp_dir", NativeDwarfAttributeTag::comp_dir)
        .value("const_expr", NativeDwarfAttributeTag::const_expr)
        .value("const_value", NativeDwarfAttributeTag::const_value)
        .value("containing_type", NativeDwarfAttributeTag::containing_type)
        .value("count", NativeDwarfAttributeTag::count)
        .value("CPQ_discontig_ranges", NativeDwarfAttributeTag::CPQ_discontig_ranges)
        .value("CPQ_prologue_length", NativeDwarfAttributeTag::CPQ_prologue_length)
        .value("CPQ_semantic_events", NativeDwarfAttributeTag::CPQ_semantic_events)
        .value("CPQ_split_lifetimes_rtn", NativeDwarfAttributeTag::CPQ_split_lifetimes_rtn)
        .value("CPQ_split_lifetimes_var", NativeDwarfAttributeTag::CPQ_split_lifetimes_var)
        .value("data_bit_offset", NativeDwarfAttributeTag::data_bit_offset)
        .value("data_location", NativeDwarfAttributeTag::data_location)
        .value("data_member_location", NativeDwarfAttributeTag::data_member_location)
        .value("decimal_scale", NativeDwarfAttributeTag::decimal_scale)
        .value("decimal_sign", NativeDwarfAttributeTag::decimal_sign)
        .value("decl_column", NativeDwarfAttributeTag::decl_column)
        .value("decl_file", NativeDwarfAttributeTag::decl_file)
        .value("decl_line", NativeDwarfAttributeTag::decl_line)
        .value("declaration", NativeDwarfAttributeTag::declaration)
        .value("default_value", NativeDwarfAttributeTag::default_value)
        .value("defaulted", NativeDwarfAttributeTag::defaulted)
        .value("deleted", NativeDwarfAttributeTag::deleted)
        .value("description", NativeDwarfAttributeTag::description)
        .value("digit_count", NativeDwarfAttributeTag::digit_count)
        .value("discr", NativeDwarfAttributeTag::discr)
        .value("discr_list", NativeDwarfAttributeTag::discr_list)
        .value("discr_value", NativeDwarfAttributeTag::discr_value)
        .value("dwo_id", NativeDwarfAttributeTag::dwo_id)
        .value("dwo_name", NativeDwarfAttributeTag::dwo_name)
        .value("element_list", NativeDwarfAttributeTag::element_list)
        .value("elemental", NativeDwarfAttributeTag::elemental)
        .value("encoding", NativeDwarfAttributeTag::encoding)
        .value("endianity", NativeDwarfAttributeTag::endianity)
        .value("entry_pc", NativeDwarfAttributeTag::entry_pc)
        .value("enum_class", NativeDwarfAttributeTag::enum_class)
        .value("explicit", NativeDwarfAttributeTag::explicit_)
        .value("export_symbols", NativeDwarfAttributeTag::export_symbols)
        .value("extension", NativeDwarfAttributeTag::extension)
        .value("external", NativeDwarfAttributeTag::external)
        .value("frame_base", NativeDwarfAttributeTag::frame_base)
        .value("friend", NativeDwarfAttributeTag::friend_)
        .value("ghs_frames", NativeDwarfAttributeTag::ghs_frames)
        .value("ghs_frsm", NativeDwarfAttributeTag::ghs_frsm)
        .value("ghs_lbrace_line", NativeDwarfAttributeTag::ghs_lbrace_line)
        .value("ghs_mangled", NativeDwarfAttributeTag::ghs_mangled)
        .value("ghs_namespace_alias", NativeDwarfAttributeTag::ghs_namespace_alias)
        .value("ghs_rsm", NativeDwarfAttributeTag::ghs_rsm)
        .value("ghs_rso", NativeDwarfAttributeTag::ghs_rso)
        .value("ghs_subcpu", NativeDwarfAttributeTag::ghs_subcpu)
        .value("ghs_using_declaration", NativeDwarfAttributeTag::ghs_using_declaration)
        .value("ghs_using_namespace", NativeDwarfAttributeTag::ghs_using_namespace)
        .value("GNAT_descriptive_type", NativeDwarfAttributeTag::GNAT_descriptive_type)
        .value("GNU_addr_base", NativeDwarfAttributeTag::GNU_addr_base)
        .value("GNU_all_call_sites", NativeDwarfAttributeTag::GNU_all_call_sites)
        .value("GNU_all_source_call_sites", NativeDwarfAttributeTag::GNU_all_source_call_sites)
        .value("GNU_all_tail_call_sites", NativeDwarfAttributeTag::GNU_all_tail_call_sites)
        .value("GNU_bias", NativeDwarfAttributeTag::GNU_bias)
        .value("GNU_call_site_data_value", NativeDwarfAttributeTag::GNU_call_site_data_value)
        .value("GNU_call_site_target", NativeDwarfAttributeTag::GNU_call_site_target)
        .value("GNU_call_site_target_clobbered", NativeDwarfAttributeTag::GNU_call_site_target_clobbered)
        .value("GNU_call_site_value", NativeDwarfAttributeTag::GNU_call_site_value)
        .value("GNU_deleted", NativeDwarfAttributeTag::GNU_deleted)
        .value("GNU_denominator", NativeDwarfAttributeTag::GNU_denominator)
        .value("GNU_discriminator", NativeDwarfAttributeTag::GNU_discriminator)
        .value("GNU_dwo_id", NativeDwarfAttributeTag::GNU_dwo_id)
        .value("GNU_dwo_name", NativeDwarfAttributeTag::GNU_dwo_name)
        .value("GNU_entry_view", NativeDwarfAttributeTag::GNU_entry_view)
        .value("GNU_exclusive_locks_required", NativeDwarfAttributeTag::GNU_exclusive_locks_required)
        .value("GNU_guarded", NativeDwarfAttributeTag::GNU_guarded)
        .value("GNU_guarded_by", NativeDwarfAttributeTag::GNU_guarded_by)
        .value("GNU_locks_excluded", NativeDwarfAttributeTag::GNU_locks_excluded)
        .value("GNU_locviews", NativeDwarfAttributeTag::GNU_locviews)
        .value("GNU_macros", NativeDwarfAttributeTag::GNU_macros)
        .value("GNU_numerator", NativeDwarfAttributeTag::GNU_numerator)
        .value("GNU_odr_signature", NativeDwarfAttributeTag::GNU_odr_signature)
        .value("GNU_pt_guarded", NativeDwarfAttributeTag::GNU_pt_guarded)
        .value("GNU_pt_guarded_by", NativeDwarfAttributeTag::GNU_pt_guarded_by)
        .value("GNU_pubnames", NativeDwarfAttributeTag::GNU_pubnames)
        .value("GNU_pubtypes", NativeDwarfAttributeTag::GNU_pubtypes)
        .value("GNU_ranges_base", NativeDwarfAttributeTag::GNU_ranges_base)
        .value("GNU_shared_locks_required", NativeDwarfAttributeTag::GNU_shared_locks_required)
        .value("GNU_tail_call", NativeDwarfAttributeTag::GNU_tail_call)
        .value("GNU_template_name", NativeDwarfAttributeTag::GNU_template_name)
        .value("GNU_vector", NativeDwarfAttributeTag::GNU_vector)
        .value("go_closure_offset", NativeDwarfAttributeTag::go_closure_offset)
        .value("go_dict_index", NativeDwarfAttributeTag::go_dict_index)
        .value("go_elem", NativeDwarfAttributeTag::go_elem)
        .value("go_embedded_field", NativeDwarfAttributeTag::go_embedded_field)
        .value("go_key", NativeDwarfAttributeTag::go_key)
        .value("go_kind", NativeDwarfAttributeTag::go_kind)
        .value("go_package_name", NativeDwarfAttributeTag::go_package_name)
        .value("go_runtime_type", NativeDwarfAttributeTag::go_runtime_type)
        .value("high_pc", NativeDwarfAttributeTag::high_pc)
        .value("HP_actuals_stmt_list", NativeDwarfAttributeTag::HP_actuals_stmt_list)
        .value("HP_all_variables_modifiable", NativeDwarfAttributeTag::HP_all_variables_modifiable)
        .value("HP_block_index", NativeDwarfAttributeTag::HP_block_index)
        .value("HP_cold_region_high_pc", NativeDwarfAttributeTag::HP_cold_region_high_pc)
        .value("HP_cold_region_low_pc", NativeDwarfAttributeTag::HP_cold_region_low_pc)
        .value("HP_default_location", NativeDwarfAttributeTag::HP_default_location)
        .value("HP_definition_points", NativeDwarfAttributeTag::HP_definition_points)
        .value("HP_epilogue", NativeDwarfAttributeTag::HP_epilogue)
        .value("HP_is_result_param", NativeDwarfAttributeTag::HP_is_result_param)
        .value("HP_linkage_name", NativeDwarfAttributeTag::HP_linkage_name)
        .value("HP_opt_flags", NativeDwarfAttributeTag::HP_opt_flags)
        .value("HP_opt_level", NativeDwarfAttributeTag::HP_opt_level)
        .value("HP_pass_by_reference", NativeDwarfAttributeTag::HP_pass_by_reference)
        .value("HP_proc_per_section", NativeDwarfAttributeTag::HP_proc_per_section)
        .value("HP_prof_flags", NativeDwarfAttributeTag::HP_prof_flags)
        .value("HP_prof_version_id", NativeDwarfAttributeTag::HP_prof_version_id)
        .value("HP_prologue", NativeDwarfAttributeTag::HP_prologue)
        .value("HP_raw_data_ptr", NativeDwarfAttributeTag::HP_raw_data_ptr)
        .value("HP_unit_name", NativeDwarfAttributeTag::HP_unit_name)
        .value("HP_unit_size", NativeDwarfAttributeTag::HP_unit_size)
        .value("HP_unmodifiable", NativeDwarfAttributeTag::HP_unmodifiable)
        .value("HP_widened_byte_size", NativeDwarfAttributeTag::HP_widened_byte_size)
        .value("IBM_alt_srcview", NativeDwarfAttributeTag::IBM_alt_srcview)
        .value("IBM_home_location", NativeDwarfAttributeTag::IBM_home_location)
        .value("IBM_wsa_addr", NativeDwarfAttributeTag::IBM_wsa_addr)
        .value("identifier_case", NativeDwarfAttributeTag::identifier_case)
        .value("import_", NativeDwarfAttributeTag::import)
        .value("inline", NativeDwarfAttributeTag::inline_)
        .value("INTEL_other_endian", NativeDwarfAttributeTag::INTEL_other_endian)
        .value("is_optional", NativeDwarfAttributeTag::is_optional)
        .value("language", NativeDwarfAttributeTag::language)
        .value("language_name", NativeDwarfAttributeTag::language_name)
        .value("language_version", NativeDwarfAttributeTag::language_version)
        .value("linkage_name", NativeDwarfAttributeTag::linkage_name)
        .value("LLVM_active_lane", NativeDwarfAttributeTag::LLVM_active_lane)
        .value("LLVM_apinotes", NativeDwarfAttributeTag::LLVM_apinotes)
        .value("LLVM_augmentation", NativeDwarfAttributeTag::LLVM_augmentation)
        .value("LLVM_config_macros", NativeDwarfAttributeTag::LLVM_config_macros)
        .value("LLVM_include_path", NativeDwarfAttributeTag::LLVM_include_path)
        .value("LLVM_lane_pc", NativeDwarfAttributeTag::LLVM_lane_pc)
        .value("LLVM_lanes", NativeDwarfAttributeTag::LLVM_lanes)
        .value("LLVM_sysroot", NativeDwarfAttributeTag::LLVM_sysroot)
        .value("LLVM_tag_offset", NativeDwarfAttributeTag::LLVM_tag_offset)
        .value("LLVM_vector_size", NativeDwarfAttributeTag::LLVM_vector_size)
        .value("location", NativeDwarfAttributeTag::location)
        .value("loclists_base", NativeDwarfAttributeTag::loclists_base)
        .value("low_pc", NativeDwarfAttributeTag::low_pc)
        .value("lower_bound", NativeDwarfAttributeTag::lower_bound)
        .value("mac_info", NativeDwarfAttributeTag::mac_info)
        .value("macro_info", NativeDwarfAttributeTag::macro_info)
        .value("macros", NativeDwarfAttributeTag::macros)
        .value("main_subprogram", NativeDwarfAttributeTag::main_subprogram)
        .value("member", NativeDwarfAttributeTag::member)
        .value("MIPS_abstract_name", NativeDwarfAttributeTag::MIPS_abstract_name)
        .value("MIPS_allocatable_dopetype", NativeDwarfAttributeTag::MIPS_allocatable_dopetype)
        .value("MIPS_assumed_shape_dopetype", NativeDwarfAttributeTag::MIPS_assumed_shape_dopetype)
        .value("MIPS_assumed_size", NativeDwarfAttributeTag::MIPS_assumed_size)
        .value("MIPS_clone_origin", NativeDwarfAttributeTag::MIPS_clone_origin)
        .value("MIPS_epilog_begin", NativeDwarfAttributeTag::MIPS_epilog_begin)
        .value("MIPS_fde", NativeDwarfAttributeTag::MIPS_fde)
        .value("MIPS_has_inlines", NativeDwarfAttributeTag::MIPS_has_inlines)
        .value("MIPS_linkage_name", NativeDwarfAttributeTag::MIPS_linkage_name)
        .value("MIPS_loop_begin", NativeDwarfAttributeTag::MIPS_loop_begin)
        .value("MIPS_loop_unroll_factor", NativeDwarfAttributeTag::MIPS_loop_unroll_factor)
        .value("MIPS_ptr_dopetype", NativeDwarfAttributeTag::MIPS_ptr_dopetype)
        .value("MIPS_software_pipeline_depth", NativeDwarfAttributeTag::MIPS_software_pipeline_depth)
        .value("MIPS_stride", NativeDwarfAttributeTag::MIPS_stride)
        .value("MIPS_stride_byte", NativeDwarfAttributeTag::MIPS_stride_byte)
        .value("MIPS_stride_elem", NativeDwarfAttributeTag::MIPS_stride_elem)
        .value("MIPS_tail_loop_begin", NativeDwarfAttributeTag::MIPS_tail_loop_begin)
        .value("mutable", NativeDwarfAttributeTag::mutable_)
        .value("name_", NativeDwarfAttributeTag::name)
        .value("namelist_item", NativeDwarfAttributeTag::namelist_item)
        .value("noreturn", NativeDwarfAttributeTag::noreturn)
        .value("object_pointer", NativeDwarfAttributeTag::object_pointer)
        .value("ordering", NativeDwarfAttributeTag::ordering)
        .value("PGI_lbase", NativeDwarfAttributeTag::PGI_lbase)
        .value("PGI_lstride", NativeDwarfAttributeTag::PGI_lstride)
        .value("PGI_soffset", NativeDwarfAttributeTag::PGI_soffset)
        .value("picture_string", NativeDwarfAttributeTag::picture_string)
        .value("priority", NativeDwarfAttributeTag::priority)
        .value("producer", NativeDwarfAttributeTag::producer)
        .value("prototyped", NativeDwarfAttributeTag::prototyped)
        .value("pure", NativeDwarfAttributeTag::pure)
        .value("ranges", NativeDwarfAttributeTag::ranges)
        .value("rank", NativeDwarfAttributeTag::rank)
        .value("recursive", NativeDwarfAttributeTag::recursive)
        .value("reference", NativeDwarfAttributeTag::reference)
        .value("return_addr", NativeDwarfAttributeTag::return_addr)
        .value("rnglists_base", NativeDwarfAttributeTag::rnglists_base)
        .value("rvalue_reference", NativeDwarfAttributeTag::rvalue_reference)
        .value("segment", NativeDwarfAttributeTag::segment)
        .value("sf_names", NativeDwarfAttributeTag::sf_names)
        .value("sibling", NativeDwarfAttributeTag::sibling)
        .value("signature", NativeDwarfAttributeTag::signature)
        .value("small", NativeDwarfAttributeTag::small)
        .value("specification", NativeDwarfAttributeTag::specification)
        .value("src_coords", NativeDwarfAttributeTag::src_coords)
        .value("src_info", NativeDwarfAttributeTag::src_info)
        .value("start_scope", NativeDwarfAttributeTag::start_scope)
        .value("static_link", NativeDwarfAttributeTag::static_link)
        .value("stmt_list", NativeDwarfAttributeTag::stmt_list)
        .value("str_offsets_base", NativeDwarfAttributeTag::str_offsets_base)
        .value("stride", NativeDwarfAttributeTag::stride)
        .value("stride_size", NativeDwarfAttributeTag::stride_size)
        .value("string_length", NativeDwarfAttributeTag::string_length)
        .value("string_length_bit_size", NativeDwarfAttributeTag::string_length_bit_size)
        .value("string_length_byte_size", NativeDwarfAttributeTag::string_length_byte_size)
        .value("SUN_alignment", NativeDwarfAttributeTag::SUN_alignment)
        .value("SUN_amd64_parmdump", NativeDwarfAttributeTag::SUN_amd64_parmdump)
        .value("SUN_browser_file", NativeDwarfAttributeTag::SUN_browser_file)
        .value("SUN_c_vla", NativeDwarfAttributeTag::SUN_c_vla)
        .value("SUN_cf_kind", NativeDwarfAttributeTag::SUN_cf_kind)
        .value("SUN_command_line", NativeDwarfAttributeTag::SUN_command_line)
        .value("SUN_compile_options", NativeDwarfAttributeTag::SUN_compile_options)
        .value("SUN_count_guarantee", NativeDwarfAttributeTag::SUN_count_guarantee)
        .value("SUN_dtor_length", NativeDwarfAttributeTag::SUN_dtor_length)
        .value("SUN_dtor_start", NativeDwarfAttributeTag::SUN_dtor_start)
        .value("SUN_dtor_state_deltas", NativeDwarfAttributeTag::SUN_dtor_state_deltas)
        .value("SUN_dtor_state_final", NativeDwarfAttributeTag::SUN_dtor_state_final)
        .value("SUN_dtor_state_initial", NativeDwarfAttributeTag::SUN_dtor_state_initial)
        .value("SUN_f90_allocatable", NativeDwarfAttributeTag::SUN_f90_allocatable)
        .value("SUN_f90_assumed_shape_array", NativeDwarfAttributeTag::SUN_f90_assumed_shape_array)
        .value("SUN_f90_pointer", NativeDwarfAttributeTag::SUN_f90_pointer)
        .value("SUN_f90_use_only", NativeDwarfAttributeTag::SUN_f90_use_only)
        .value("SUN_fortran_based", NativeDwarfAttributeTag::SUN_fortran_based)
        .value("SUN_fortran_main_alias", NativeDwarfAttributeTag::SUN_fortran_main_alias)
        .value("SUN_func_offset", NativeDwarfAttributeTag::SUN_func_offset)
        .value("SUN_func_offsets", NativeDwarfAttributeTag::SUN_func_offsets)
        .value("SUN_hwcprof_signature", NativeDwarfAttributeTag::SUN_hwcprof_signature)
        .value("SUN_import_by_lname", NativeDwarfAttributeTag::SUN_import_by_lname)
        .value("SUN_import_by_name", NativeDwarfAttributeTag::SUN_import_by_name)
        .value("SUN_is_omp_child_func", NativeDwarfAttributeTag::SUN_is_omp_child_func)
        .value("SUN_language", NativeDwarfAttributeTag::SUN_language)
        .value("SUN_link_name", NativeDwarfAttributeTag::SUN_link_name)
        .value("SUN_memop_signature", NativeDwarfAttributeTag::SUN_memop_signature)
        .value("SUN_memop_type_ref", NativeDwarfAttributeTag::SUN_memop_type_ref)
        .value("SUN_namelist_spec", NativeDwarfAttributeTag::SUN_namelist_spec)
        .value("SUN_obj_dir", NativeDwarfAttributeTag::SUN_obj_dir)
        .value("SUN_obj_file", NativeDwarfAttributeTag::SUN_obj_file)
        .value("SUN_omp_child_func", NativeDwarfAttributeTag::SUN_omp_child_func)
        .value("SUN_omp_tpriv_addr", NativeDwarfAttributeTag::SUN_omp_tpriv_addr)
        .value("SUN_original_name", NativeDwarfAttributeTag::SUN_original_name)
        .value("SUN_part_link_name", NativeDwarfAttributeTag::SUN_part_link_name)
        .value("SUN_pass_by_ref", NativeDwarfAttributeTag::SUN_pass_by_ref)
        .value("SUN_pass_with_const", NativeDwarfAttributeTag::SUN_pass_with_const)
        .value("SUN_profile_id", NativeDwarfAttributeTag::SUN_profile_id)
        .value("SUN_return_value_ptr", NativeDwarfAttributeTag::SUN_return_value_ptr)
        .value("SUN_return_with_const", NativeDwarfAttributeTag::SUN_return_with_const)
        .value("SUN_template", NativeDwarfAttributeTag::SUN_template)
        .value("SUN_vbase", NativeDwarfAttributeTag::SUN_vbase)
        .value("SUN_vtable", NativeDwarfAttributeTag::SUN_vtable)
        .value("SUN_vtable_abi", NativeDwarfAttributeTag::SUN_vtable_abi)
        .value("SUN_vtable_index", NativeDwarfAttributeTag::SUN_vtable_index)
        .value("threads_scaled", NativeDwarfAttributeTag::threads_scaled)
        .value("TI_asm", NativeDwarfAttributeTag::TI_asm)
        .value("TI_interrupt", NativeDwarfAttributeTag::TI_interrupt)
        .value("TI_skeletal", NativeDwarfAttributeTag::TI_skeletal)
        .value("TI_symbol_name", NativeDwarfAttributeTag::TI_symbol_name)
        .value("TI_veneer", NativeDwarfAttributeTag::TI_veneer)
        .value("TI_version", NativeDwarfAttributeTag::TI_version)
        .value("trampoline", NativeDwarfAttributeTag::trampoline)
        .value("type", NativeDwarfAttributeTag::type)
        .value("upc_threads_scaled", NativeDwarfAttributeTag::upc_threads_scaled)
        .value("upper_bound", NativeDwarfAttributeTag::upper_bound)
        .value("use_GNAT_descriptive_type", NativeDwarfAttributeTag::use_GNAT_descriptive_type)
        .value("use_location", NativeDwarfAttributeTag::use_location)
        .value("use_UTF8", NativeDwarfAttributeTag::use_UTF8)
        .value("variable_parameter", NativeDwarfAttributeTag::variable_parameter)
        .value("virtuality", NativeDwarfAttributeTag::virtuality)
        .value("visibility", NativeDwarfAttributeTag::visibility)
        .value("VMS_rtnbeg_pd_address", NativeDwarfAttributeTag::VMS_rtnbeg_pd_address)
        .value("vtable_elem_location", NativeDwarfAttributeTag::vtable_elem_location);

    // DW_FORM_* — attribute form. Determines which std::variant alternative
    // NativeDwarfAttribute.value will hold (see dwarf_attribute.hpp).
    nb::enum_<NativeDwarfAttributeForm>(m, "NativeDwarfAttributeForm")
        .value("addr", NativeDwarfAttributeForm::addr)
        .value("addrx", NativeDwarfAttributeForm::addrx)
        .value("addrx1", NativeDwarfAttributeForm::addrx1)
        .value("addrx2", NativeDwarfAttributeForm::addrx2)
        .value("addrx3", NativeDwarfAttributeForm::addrx3)
        .value("addrx4", NativeDwarfAttributeForm::addrx4)
        .value("block", NativeDwarfAttributeForm::block)
        .value("block1", NativeDwarfAttributeForm::block1)
        .value("block2", NativeDwarfAttributeForm::block2)
        .value("block4", NativeDwarfAttributeForm::block4)
        .value("data1", NativeDwarfAttributeForm::data1)
        .value("data16", NativeDwarfAttributeForm::data16)
        .value("data2", NativeDwarfAttributeForm::data2)
        .value("data4", NativeDwarfAttributeForm::data4)
        .value("data8", NativeDwarfAttributeForm::data8)
        .value("exprloc", NativeDwarfAttributeForm::exprloc)
        .value("flag", NativeDwarfAttributeForm::flag)
        .value("flag_present", NativeDwarfAttributeForm::flag_present)
        .value("GNU_addr_index", NativeDwarfAttributeForm::GNU_addr_index)
        .value("GNU_ref_alt", NativeDwarfAttributeForm::GNU_ref_alt)
        .value("GNU_str_index", NativeDwarfAttributeForm::GNU_str_index)
        .value("GNU_strp_alt", NativeDwarfAttributeForm::GNU_strp_alt)
        .value("implicit_const", NativeDwarfAttributeForm::implicit_const)
        .value("indirect", NativeDwarfAttributeForm::indirect)
        .value("line_strp", NativeDwarfAttributeForm::line_strp)
        .value("LLVM_addrx_offset", NativeDwarfAttributeForm::LLVM_addrx_offset)
        .value("loclistx", NativeDwarfAttributeForm::loclistx)
        .value("ref1", NativeDwarfAttributeForm::ref1)
        .value("ref2", NativeDwarfAttributeForm::ref2)
        .value("ref4", NativeDwarfAttributeForm::ref4)
        .value("ref8", NativeDwarfAttributeForm::ref8)
        .value("ref_addr", NativeDwarfAttributeForm::ref_addr)
        .value("ref_sig8", NativeDwarfAttributeForm::ref_sig8)
        .value("ref_sup4", NativeDwarfAttributeForm::ref_sup4)
        .value("ref_sup8", NativeDwarfAttributeForm::ref_sup8)
        .value("ref_udata", NativeDwarfAttributeForm::ref_udata)
        .value("rnglistx", NativeDwarfAttributeForm::rnglistx)
        .value("sdata", NativeDwarfAttributeForm::sdata)
        .value("sec_offset", NativeDwarfAttributeForm::sec_offset)
        .value("string", NativeDwarfAttributeForm::string)
        .value("strp", NativeDwarfAttributeForm::strp)
        .value("strp_sup", NativeDwarfAttributeForm::strp_sup)
        .value("strx", NativeDwarfAttributeForm::strx)
        .value("strx1", NativeDwarfAttributeForm::strx1)
        .value("strx2", NativeDwarfAttributeForm::strx2)
        .value("strx3", NativeDwarfAttributeForm::strx3)
        .value("strx4", NativeDwarfAttributeForm::strx4)
        .value("udata", NativeDwarfAttributeForm::udata);

    nb::class_<NativeDwarfAttribute>(m, "NativeDwarfAttribute")
        .def_prop_ro("tag", &NativeDwarfAttribute::get_tag)
        .def_prop_ro("form", &NativeDwarfAttribute::get_form)
        // Variant alternatives map to bool / int / str / bytes / None. Default
        // nanobind would expose std::vector<uint8_t> as a Python list[int],
        // but DW_FORM_block* / exprloc payloads are conceptually opaque byte
        // strings — hand them out as nb::bytes so callers don't have to
        // wrap with bytes(...) before struct.unpack / hash / etc.
        .def_prop_ro(
            "value",
            [](const NativeDwarfAttribute& a) -> nb::object {
                return std::visit(
                    [](const auto& v) -> nb::object {
                        using T = std::decay_t<decltype(v)>;
                        if constexpr (std::is_same_v<T, std::monostate>) {
                            return nb::none();
                        } else if constexpr (std::is_same_v<T, std::vector<uint8_t>>) {
                            return nb::bytes(reinterpret_cast<const char*>(v.data()), v.size());
                        } else {
                            return nb::cast(v);  // bool, ints, str
                        }
                    },
                    a.get_value());
            },
            nb::sig("def value(self) -> bool | int | str | bytes | None"));

    nb::class_<MemoryAccess, MemoryAccessTrampoline>(m, "MemoryAccess")
        .def(nb::init<>())
        .def(
            "read",
            [](const MemoryAccess& self, uint64_t address, nb::handle buffer) {
                Py_buffer buf{};
                if (PyObject_GetBuffer(buffer.ptr(), &buf, PyBUF_WRITABLE) != 0) {
                    throw nb::python_error();
                }
                struct BufferGuard {
                    Py_buffer* b;
                    ~BufferGuard() { PyBuffer_Release(b); }
                } guard{&buf};
                self.read(address,
                          std::span<std::byte>(static_cast<std::byte*>(buf.buf), static_cast<size_t>(buf.len)));
            },
            nb::arg("address"), nb::arg("buffer"),
            nb::sig("def read(self, address: int, buffer: memoryview | bytearray) -> None"))
        .def(
            "write",
            [](MemoryAccess& self, uint64_t address, nb::handle data) {
                Py_buffer buf{};
                if (PyObject_GetBuffer(data.ptr(), &buf, PyBUF_SIMPLE) != 0) {
                    throw nb::python_error();
                }
                struct BufferGuard {
                    Py_buffer* b;
                    ~BufferGuard() { PyBuffer_Release(b); }
                } guard{&buf};
                self.write(address, std::span<const std::byte>(static_cast<const std::byte*>(buf.buf),
                                                               static_cast<size_t>(buf.len)));
            },
            nb::arg("address"), nb::arg("data"),
            nb::sig("def write(self, address: int, data: bytes | bytearray | memoryview) -> None"))
        .def("read_register", &MemoryAccess::read_register, nb::arg("register_index"))
        .def("write_register", &MemoryAccess::write_register, nb::arg("register_index"), nb::arg("value"));

    // MemoryAccess that raises on every operation. There's no per-instance
    // state, so a single process-wide shared_ptr (NoMemoryAccess.instance())
    // is what callers should use whenever a MemoryAccess is required but no
    // live target is available.
    nb::class_<ttexalens::native_elf::NoMemoryAccess, MemoryAccess>(m, "NoMemoryAccess")
        .def(nb::init<>())
        .def_static("instance", &ttexalens::native_elf::NoMemoryAccess::instance);

    // Concrete MemoryAccess that serves reads from a byte snapshot when the
    // address falls in the cached range, otherwise delegates to `base`. Used
    // by NativeElfVariable::read() but exposed here so Python can also
    // construct one directly.
    nb::class_<ttexalens::native_elf::CachedReadMemoryAccess, MemoryAccess>(m, "CachedReadMemoryAccess")
        .def(
            "__init__",
            [](ttexalens::native_elf::CachedReadMemoryAccess* self, uint64_t cached_address, nb::handle cached_data,
               std::shared_ptr<MemoryAccess> base) {
                Py_buffer buf{};
                if (PyObject_GetBuffer(cached_data.ptr(), &buf, PyBUF_SIMPLE) != 0) {
                    throw nb::python_error();
                }
                struct BufferGuard {
                    Py_buffer* b;
                    ~BufferGuard() { PyBuffer_Release(b); }
                } guard{&buf};
                std::vector<std::byte> data(static_cast<const std::byte*>(buf.buf),
                                            static_cast<const std::byte*>(buf.buf) + buf.len);
                new (self)
                    ttexalens::native_elf::CachedReadMemoryAccess(cached_address, std::move(data), std::move(base));
            },
            nb::arg("cached_address"), nb::arg("cached_data"), nb::arg("base"),
            nb::sig("def __init__(self, cached_address: int, cached_data: bytes | bytearray | memoryview, base: "
                    "MemoryAccess) -> None"));

    nb::class_<NativeElfSection>(m, "NativeElfSection")
        .def_prop_ro("name", &NativeElfSection::name)
        .def_prop_ro("address", &NativeElfSection::address)
        .def_prop_ro("size", &NativeElfSection::size)
        .def_prop_ro(
            "data",
            [](const NativeElfSection& s) {
                std::span<const std::byte> sp = s.data();
                PyObject* mv = PyMemoryView_FromMemory(const_cast<char*>(reinterpret_cast<const char*>(sp.data())),
                                                       static_cast<Py_ssize_t>(sp.size()), PyBUF_READ);
                if (mv == nullptr) {
                    throw nb::python_error();
                }
                return nb::steal<nb::object>(mv);
            },
            nb::rv_policy::reference_internal, nb::sig("def data(self) -> memoryview"));

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
            [](nb::handle data) {
                // Accept any buffer-protocol object — bytes, bytearray,
                // memoryview, NativeElfSection.data, etc. BytesImpl copies
                // into its own vector at construction, so the borrowed
                // buffer only needs to outlive this call.
                Py_buffer buf;
                if (PyObject_GetBuffer(data.ptr(), &buf, PyBUF_SIMPLE) != 0) {
                    throw nb::python_error();
                }
                struct BufferGuard {
                    Py_buffer* b;
                    ~BufferGuard() { PyBuffer_Release(b); }
                } guard{&buf};
                return NativeElfFile::from_bytes(
                    std::span<const std::byte>(static_cast<const std::byte*>(buf.buf), static_cast<size_t>(buf.len)));
            },
            nb::arg("data"), nb::sig("def from_bytes(data: bytes | bytearray | memoryview) -> NativeElfFile"))
        .def("get_sections_count", &NativeElfFile::get_sections_count)
        .def("get_section", &NativeElfFile::get_section, nb::arg("index"), nb::rv_policy::reference_internal,
             nb::sig("def get_section(self, index: int) -> NativeElfSection | None"))
        .def("get_section_by_name", &NativeElfFile::get_section_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal,
             nb::sig("def get_section_by_name(self, name: str) -> NativeElfSection | None"))
        .def("read_symbol_table_section", &NativeElfFile::read_symbol_table_section, nb::arg("section_name"),
             nb::call_guard<nb::gil_scoped_release>())
        .def("has_dwarf_info", &NativeElfFile::has_dwarf_info, nb::arg("strict") = false)
        .def_prop_ro("dwarf_info", &NativeElfFile::get_dwarf_info, nb::rv_policy::reference_internal,
                     nb::call_guard<nb::gil_scoped_release>());

    nb::class_<NativeDwarfFileLine>(m, "NativeDwarfFileLine")
        .def(nb::init<std::string, uint32_t, uint32_t>(), nb::arg("file"), nb::arg("line"), nb::arg("column") = 0)
        .def_prop_ro("file", [](const NativeDwarfFileLine& f) -> std::string_view { return f.file; })
        .def_ro("line", &NativeDwarfFileLine::line)
        .def_ro("column", &NativeDwarfFileLine::column);

    nb::class_<NativeDwarfDie>(m, "NativeDwarfDie")
        // name / linkage_name return None (not the empty string) when the DIE
        // has no DW_AT_name / DW_AT_linkage_name — matches the legacy
        // ElfDie.name semantics, so call sites that test `if var.name is not
        // None` don't pass through empty strings.
        .def_prop_ro("name",
                     [](const NativeDwarfDie& self) -> std::optional<std::string> {
                         auto name = self.get_name();
                         if (name.empty()) {
                             return std::nullopt;
                         }
                         return std::string(name);
                     })
        .def_prop_ro("linkage_name",
                     [](const NativeDwarfDie& self) -> std::optional<std::string> {
                         auto name = self.get_linkage_name();
                         if (name.empty()) {
                             return std::nullopt;
                         }
                         return std::string(name);
                     })
        .def_prop_ro("offset", &NativeDwarfDie::get_offset)
        .def_prop_ro("tag", &NativeDwarfDie::get_tag)
        .def_prop_ro("attributes", &NativeDwarfDie::get_attributes, nb::rv_policy::reference_internal)
        .def_prop_ro("is_signed_type", &NativeDwarfDie::is_signed_type)
        .def_prop_ro("is_declaration", &NativeDwarfDie::is_declaration)
        .def("get_attribute", &NativeDwarfDie::get_attribute, nb::arg("attribute_tag"),
             nb::rv_policy::reference_internal,
             nb::sig("def get_attribute(self, attribute_tag: NativeDwarfAttributeTag) -> NativeDwarfAttribute | None"))
        .def("has_attribute", &NativeDwarfDie::has_attribute, nb::arg("attribute_tag"))
        .def("get_path", &NativeDwarfDie::get_path)
        .def("get_search_path", &NativeDwarfDie::get_search_path)
        .def("get_size", &NativeDwarfDie::get_size)
        .def("get_address", &NativeDwarfDie::get_address)
        .def(
            "get_constant_value",
            [](const NativeDwarfDie& d) -> nb::object {
                return std::visit(
                    [](const auto& v) -> nb::object {
                        using T = std::decay_t<decltype(v)>;
                        if constexpr (std::is_same_v<T, std::monostate>) {
                            return nb::none();
                        } else {
                            return nb::cast(v);
                        }
                    },
                    d.get_constant_value());
            },
            nb::sig("def get_constant_value(self) -> bool | int | float | None"))
        .def("get_resolved_type", &NativeDwarfDie::get_resolved_type, nb::rv_policy::reference_internal,
             nb::sig("def get_resolved_type(self) -> NativeDwarfDie | None"))
        .def("get_dereference_type", &NativeDwarfDie::get_dereference_type, nb::rv_policy::reference_internal,
             nb::sig("def get_dereference_type(self) -> NativeDwarfDie | None"))
        .def("get_array_element_type", &NativeDwarfDie::get_array_element_type, nb::rv_policy::reference_internal,
             nb::sig("def get_array_element_type(self) -> NativeDwarfDie | None"))
        .def("find_child_by_name", &NativeDwarfDie::find_child_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal,
             nb::sig("def find_child_by_name(self, name: str) -> NativeDwarfDie | None"))
        .def("get_die_from_attribute", &NativeDwarfDie::get_die_from_attribute, nb::arg("attribute_tag"),
             nb::rv_policy::reference_internal,
             nb::sig(
                 "def get_die_from_attribute(self, attribute_tag: NativeDwarfAttributeTag) -> NativeDwarfDie | None"))
        .def("get_address_ranges", &NativeDwarfDie::get_address_ranges)
        .def("get_decl_file_info", &NativeDwarfDie::get_decl_file_info)
        .def("get_call_file_info", &NativeDwarfDie::get_call_file_info)
        .def("read_value", &NativeDwarfDie::read_value, nb::arg("frame").none())
        .def("get_first_child", &NativeDwarfDie::get_first_child, nb::rv_policy::reference_internal,
             nb::sig("def get_first_child(self) -> NativeDwarfDie | None"))
        .def("get_next_sibling", &NativeDwarfDie::get_next_sibling, nb::rv_policy::reference_internal,
             nb::sig("def get_next_sibling(self) -> NativeDwarfDie | None"))
        .def("get_parent", &NativeDwarfDie::get_parent, nb::rv_policy::reference_internal,
             nb::sig("def get_parent(self) -> NativeDwarfDie | None"))
        .def("get_template_value_parameters", &NativeDwarfDie::get_template_value_parameters)
        .def(
            "iter_children",
            [](NativeDwarfDie& self) {
                return nb::make_iterator<nb::rv_policy::reference_internal>(
                    nb::type<NativeDwarfDie>(), "DieChildIterator", DieChildIterator(self.get_first_child()),
                    DieChildIterator());
            },
            nb::rv_policy::reference_internal);

    nb::class_<NativeDwarfInfo>(m, "NativeDwarfInfo")
        .def("find_file_line_by_address", &NativeDwarfInfo::find_file_line_by_address, nb::arg("address"))
        .def("get_die_by_name", &NativeDwarfInfo::get_die_by_name, nb::arg("name"), nb::rv_policy::reference_internal,
             nb::sig("def get_die_by_name(self, name: str) -> NativeDwarfDie | None"))
        .def("find_function_by_address", &NativeDwarfInfo::find_function_by_address, nb::arg("address"),
             nb::rv_policy::reference_internal,
             nb::sig("def find_function_by_address(self, address: int) -> NativeDwarfDie | None"))
        // keep_alive<0, 1>: the returned NativeFrameDescription holds a raw
        // Dwarf_Fde owned by self (NativeDwarfInfo). Tie its Python-side
        // lifetime to self so callers can't accidentally outlive the parent.
        .def("get_frame_description", &NativeDwarfInfo::get_frame_description, nb::arg("pc"), nb::arg("memory_access"),
             nb::rv_policy::reference_internal)
        .def("find_symbol_by_name", &NativeDwarfInfo::find_symbol_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal,
             nb::sig("def find_symbol_by_name(self, name: str) -> NativeElfSymbol | None"))
        .def("get_enum_value", &NativeDwarfInfo::get_enum_value, nb::arg("name"))
        // Like NativeDwarfDie::get_constant_value, the variant alternatives
        // map to bool / int / float; monostate is unreachable here because
        // get_constant() throws TypeMismatchException for non-constant DIEs.
        .def(
            "get_constant",
            [](const NativeDwarfInfo& self, std::string_view name) -> nb::object {
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
        // keep_alive<0, 1>: the returned NativeElfVariable holds shared_ptr
        // to a NativeDwarfDie owned by self's NativeDwarfInfoImpl. Without
        // this annotation, Python could release self while the variable is
        // still in use — the C++ shared_ptr would keep the DIE alive but
        // the parent Dwarf_Debug would already be finished, leaking ref-
        // counts and ultimately corrupting the heap. The native side has a
        // defensive destructor that detaches handles when the parent impl
        // is expired, but this keeps the lifetime contract intact too.
        .def("get_global", &NativeDwarfInfo::get_global, nb::arg("name"), nb::arg("memory_access"),
             nb::rv_policy::reference_internal)
        .def("read_global", &NativeDwarfInfo::read_global, nb::arg("name"), nb::arg("memory_access"),
             nb::rv_policy::reference_internal);

    nb::class_<NativeFrameDescription>(m, "NativeFrameDescription")
        .def_prop_ro("pc", &NativeFrameDescription::get_pc)
        .def("read_register", &NativeFrameDescription::read_register, nb::arg("register_index"), nb::arg("cfa"))
        .def("try_read_register", &NativeFrameDescription::try_read_register, nb::arg("register_index"),
             nb::arg("cfa").none())
        .def("read_previous_cfa", &NativeFrameDescription::read_previous_cfa,
             nb::arg("current_cfa").none() = nb::none());

    // Per-frame context for NativeDwarfDie::read_value. Construct with the
    // active MemoryAccess plus an optional NativeFrameDescription: pass
    // None for the top frame (read_register hits live GPRs through
    // MemoryAccess) and a description for inner frames (read_register
    // delegates to try_read_register against the FDE save rules).
    nb::class_<NativeFrameInspection>(m, "NativeFrameInspection")
        .def(nb::init<std::shared_ptr<MemoryAccess>, std::optional<NativeFrameDescription>, std::optional<uint64_t>,
                      uint64_t>(),
             nb::arg("memory_access"), nb::arg("frame_description").none(), nb::arg("cfa").none(), nb::arg("pc"))
        .def("read_register", &NativeFrameInspection::read_register, nb::arg("register_index"))
        .def("read_memory", &NativeFrameInspection::read_memory, nb::arg("address"), nb::arg("register_size"))
        .def_prop_ro("cfa", &NativeFrameInspection::get_cfa)
        .def_prop_ro("pc", &NativeFrameInspection::get_pc);

    // Live view of a variable located by DWARF. Mirrors
    // ttexalens.elf.variable.ElfVariable: structural methods on the C++ side,
    // Python dunders wired here so call sites can keep doing `var.x.y[i] + 1`.
    nb::class_<NativeElfVariable>(m, "NativeElfVariable")
        .def(nb::init<ttexalens::native_elf::NativeDwarfDiePtr, uint64_t, std::shared_ptr<MemoryAccess>>(),
             nb::arg("type_die"), nb::arg("address"), nb::arg("memory_access"))
        // Core structural / value methods.
        .def("get_member", &NativeElfVariable::get_member, nb::arg("member_name"))
        .def("dereference", &NativeElfVariable::dereference)
        .def("get_address", &NativeElfVariable::get_address)
        .def("get_size", &NativeElfVariable::get_size)
        .def("read_bytes",
             [](const NativeElfVariable& self) {
                 auto v = self.read_bytes();
                 return nb::bytes(reinterpret_cast<const char*>(v.data()), v.size());
             })
        .def("read_value", &NativeElfVariable::read_value)
        .def("write_value", &NativeElfVariable::write_value, nb::arg("value"), nb::arg("check_data_loss") = true)
        // Snapshots the variable's bytes; subsequent member/index walks read
        // from the cache instead of re-hitting live memory.
        .def("read", &NativeElfVariable::read)
        // Array helpers — materialize all elements eagerly.
        .def("as_list",
             [](const NativeElfVariable& self) {
                 const uint64_t n = self.get_length();
                 nb::list out;
                 for (uint64_t i = 0; i < n; ++i) {
                     out.append(nb::cast(self.get_index(static_cast<int64_t>(i))));
                 }
                 return out;
             })
        .def("as_value_list",
             [](const NativeElfVariable& self) {
                 const uint64_t n = self.get_length();
                 nb::list out;
                 for (uint64_t i = 0; i < n; ++i) {
                     out.append(nb::cast(self.get_index(static_cast<int64_t>(i)).read_value()));
                 }
                 return out;
             })
        // __getitem__ handles both struct member access (string keys) and
        // array/pointer indexing (integer keys). Mirrors ElfVariable.__getitem__.
        .def("__getitem__",
             [](const NativeElfVariable& self, nb::handle key) -> NativeElfVariable {
                 if (nb::isinstance<nb::str>(key)) {
                     return self.get_member(nb::cast<std::string>(key));
                 }
                 if (nb::isinstance<nb::int_>(key)) {
                     return self.get_index(nb::cast<int64_t>(key));
                 }
                 // Fall back to int conversion (mirrors Python: int(key)).
                 try {
                     return self.get_index(nb::cast<int64_t>(key));
                 } catch (const nb::cast_error&) {
                     throw nb::type_error("NativeElfVariable indices must be integers or strings");
                 }
             })
        // __getattr__ is only invoked when normal attribute lookup fails, so
        // bound C++ methods take precedence over struct members of the same
        // name (matching the Python implementation).
        .def("__getattr__", [](const NativeElfVariable& self, std::string_view name) { return self.get_member(name); })
        .def("__len__", &NativeElfVariable::get_length)
        .def("__iter__",
             [](const NativeElfVariable& self) {
                 const uint64_t n = self.get_length();
                 nb::list elements;
                 for (uint64_t i = 0; i < n; ++i) {
                     elements.append(nb::cast(self.get_index(static_cast<int64_t>(i))));
                 }
                 return nb::iter(elements);
             })
        // Comparison: equal/less-than/etc. fall back to NotImplemented on a
        // type mismatch, matching the Python ElfVariable contract. Array
        // variables compare element-by-element with any other indexable
        // sequence.
        .def(
            "__eq__",
            [](const NativeElfVariable& self, nb::handle other) -> nb::object {
                if (self.get_type_die()->get_tag() == NativeDwarfDieTag::array_type) {
                    if (nb::isinstance<nb::str>(other)) {
                        return try_binop(self, other,
                                         [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a.equal(b)); });
                    }
                    if (!PyObject_HasAttrString(other.ptr(), "__len__") ||
                        !PyObject_HasAttrString(other.ptr(), "__getitem__")) {
                        return nb::cast(false);
                    }
                    try {
                        const uint64_t n = self.get_length();
                        if (n != nb::cast<uint64_t>(nb::module_::import_("builtins").attr("len")(other))) {
                            return nb::cast(false);
                        }
                        for (uint64_t i = 0; i < n; ++i) {
                            nb::object lhs = nb::cast(self.get_index(static_cast<int64_t>(i)));
                            nb::object rhs = other[i];
                            if (!lhs.equal(rhs)) {
                                return nb::cast(false);
                            }
                        }
                        return nb::cast(true);
                    } catch (...) {
                        return nb::cast(false);
                    }
                }
                return try_binop(self, other,
                                 [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a.equal(b)); });
            },
            nb::sig("def __eq__(self, other: object, /) -> bool"))
        .def(
            "__ne__",
            [](const NativeElfVariable& self, nb::handle other) {
                return try_binop(self, other,
                                 [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a.not_equal(b)); });
            },
            nb::sig("def __ne__(self, other: object, /) -> bool"))
        .def("__lt__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a < b); });
             })
        .def("__le__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a <= b); });
             })
        .def("__gt__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a > b); });
             })
        .def("__ge__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a >= b); });
             })
        // Arithmetic — read_value() + Python's native operator dispatch.
        .def("__add__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a + b; });
             })
        .def("__radd__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b + a; });
             })
        .def("__sub__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a - b; });
             })
        .def("__rsub__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b - a; });
             })
        .def("__mul__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a * b; });
             })
        .def("__rmul__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b * a; });
             })
        .def("__truediv__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a / b; });
             })
        .def("__rtruediv__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b / a; });
             })
        .def("__floordiv__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a.floor_div(b); });
             })
        .def("__rfloordiv__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b.floor_div(a); });
             })
        .def("__mod__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a % b; });
             })
        .def("__rmod__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b % a; });
             })
        // ** doesn't have an overloaded operator on nb::object, so go through
        // PyNumber_Power which mirrors Python's natural fallback to
        // NotImplemented when either operand doesn't support the operation.
        .def("__pow__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) -> nb::object {
                     PyObject* r = PyNumber_Power(a.ptr(), b.ptr(), Py_None);
                     if (r == nullptr) {
                         throw nb::python_error();
                     }
                     return nb::steal<nb::object>(r);
                 });
             })
        .def("__rpow__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) -> nb::object {
                     PyObject* r = PyNumber_Power(b.ptr(), a.ptr(), Py_None);
                     if (r == nullptr) {
                         throw nb::python_error();
                     }
                     return nb::steal<nb::object>(r);
                 });
             })
        // Bitwise.
        .def("__and__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a & b; });
             })
        .def("__rand__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b & a; });
             })
        .def("__or__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a | b; });
             })
        .def("__ror__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b | a; });
             })
        .def("__xor__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a ^ b; });
             })
        .def("__rxor__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b ^ a; });
             })
        .def("__lshift__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a << b; });
             })
        .def("__rlshift__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b << a; });
             })
        .def("__rshift__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a >> b; });
             })
        .def("__rrshift__",
             [](const NativeElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b >> a; });
             })
        // Unary. Return is int | float at runtime — annotate the stubs so
        // call sites like `abs(-var.x)` typecheck.
        .def(
            "__neg__", [](const NativeElfVariable& self) { return -var_value_obj(self); },
            nb::sig("def __neg__(self) -> int | float"))
        .def(
            "__pos__",
            [](const NativeElfVariable& self) {
                // Python's unary + on int/float is a no-op; on bool it promotes to int.
                // Call PyNumber_Positive to mirror that exactly.
                nb::object val = var_value_obj(self);
                PyObject* r = PyNumber_Positive(val.ptr());
                if (r == nullptr) {
                    throw nb::python_error();
                }
                return nb::steal<nb::object>(r);
            },
            nb::sig("def __pos__(self) -> int | float"))
        .def(
            "__abs__",
            [](const NativeElfVariable& self) {
                return nb::module_::import_("builtins").attr("abs")(var_value_obj(self));
            },
            nb::sig("def __abs__(self) -> int | float"))
        .def(
            "__invert__", [](const NativeElfVariable& self) { return ~var_value_obj(self); },
            nb::sig("def __invert__(self) -> int"))
        // Truthiness — arrays are truthy when non-empty; scalars use the
        // underlying value (via Python's PyObject_IsTrue so int/float/bool
        // all work). Falls back to TypeMismatchException for composite types
        // (struct/union) that can't be read as a single value.
        .def("__bool__",
             [](const NativeElfVariable& self) {
                 if (self.get_type_die()->get_tag() == NativeDwarfDieTag::array_type) {
                     return self.get_length() > 0;
                 }
                 nb::object val = var_value_obj(self);
                 int r = PyObject_IsTrue(val.ptr());
                 if (r < 0) {
                     throw nb::python_error();
                 }
                 return r != 0;
             })
        // Index conversion (so var can be used directly as a list index).
        .def("__index__",
             [](const NativeElfVariable& self) {
                 nb::object val = var_value_obj(self);
                 if (nb::isinstance<nb::int_>(val) || nb::isinstance<nb::bool_>(val)) {
                     return nb::cast<int64_t>(val);
                 }
                 if (nb::isinstance<nb::float_>(val)) {
                     double d = nb::cast<double>(val);
                     if (d == static_cast<int64_t>(d)) {
                         return static_cast<int64_t>(d);
                     }
                 }
                 throw nb::type_error("ElfVariable cannot be used as an index");
             })
        // Hashing — value-based when scalar, identity-based for composites.
        .def("__hash__",
             [](const NativeElfVariable& self) -> Py_hash_t {
                 try {
                     return PyObject_Hash(var_value_obj(self).ptr());
                 } catch (const TypeMismatchException&) {
                     auto tuple = nb::make_tuple(self.get_type_die()->get_offset(), self.get_address());
                     return PyObject_Hash(tuple.ptr());
                 }
             })
        // Formatting hooks. __str__ tries read_value() and renders enum
        // values as their qualified name; falls back to __repr__ on failure.
        .def("__str__",
             [](const NativeElfVariable& self) -> std::string {
                 try {
                     nb::object val = var_value_obj(self);
                     if (self.get_type_die()->get_tag() == NativeDwarfDieTag::enumeration_type) {
                         for (auto child = self.get_type_die()->get_first_child(); child;
                              child = child->get_next_sibling()) {
                             auto cv = child->get_constant_value();
                             if (auto* iv = std::get_if<int64_t>(&cv)) {
                                 if (nb::cast<int64_t>(val) == *iv) {
                                     return child->get_path();
                                 }
                             } else if (auto* uv = std::get_if<uint64_t>(&cv)) {
                                 if (nb::cast<uint64_t>(val) == *uv) {
                                     return child->get_path();
                                 }
                             }
                         }
                     }
                     return nb::cast<std::string>(nb::str(val));
                 } catch (const TypeMismatchException&) {
                     // repr fallback when read_value is unsupported. Memory
                     // errors (Timeout/RiscHalt/Restricted) propagate.
                     return nb::cast<std::string>(nb::module_::import_("builtins").attr("repr")(nb::cast(self)));
                 }
             })
        .def("__repr__",
             [](const NativeElfVariable& self) {
                 std::string type_name(self.get_type_die()->get_name());
                 if (type_name.empty()) {
                     type_name = "Unknown";
                 }
                 std::string value_info;
                 try {
                     value_info = ", value=" + nb::cast<std::string>(nb::repr(var_value_obj(self)));
                 } catch (const TypeMismatchException&) {
                 }
                 std::string length_info;
                 try {
                     length_info = ", length=" + std::to_string(self.get_length());
                 } catch (const TypeMismatchException&) {
                 } catch (const InvalidArrayAccessException&) {
                 }
                 char addr_buf[32];
                 std::snprintf(addr_buf, sizeof(addr_buf), "0x%lx", static_cast<unsigned long>(self.get_address()));
                 return "NativeElfVariable(type_name='" + type_name + "', address=" + std::string(addr_buf) +
                        value_info + length_info + ")";
             })
        .def("__format__", [](const NativeElfVariable& self, std::string_view spec) {
            try {
                return nb::module_::import_("builtins")
                    .attr("format")(var_value_obj(self), nb::cast(std::string(spec)));
            } catch (const TypeMismatchException&) {
                return nb::module_::import_("builtins").attr("str")(nb::cast(self));
            }
        });
}
