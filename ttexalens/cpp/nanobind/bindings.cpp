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
using ttexalens::native_elf::DwarfAttribute;
using ttexalens::native_elf::DwarfAttributeForm;
using ttexalens::native_elf::DwarfAttributeTag;
using ttexalens::native_elf::DwarfDie;
using ttexalens::native_elf::DwarfDieTag;
using ttexalens::native_elf::DwarfFileLine;
using ttexalens::native_elf::DwarfInfo;
using ttexalens::native_elf::ElfFile;
using ttexalens::native_elf::ElfSection;
using ttexalens::native_elf::ElfSymbol;
using ttexalens::native_elf::ElfSymbolBinding;
using ttexalens::native_elf::ElfSymbolType;
using ttexalens::native_elf::ElfVariable;
using ttexalens::native_elf::FrameDescription;
using ttexalens::native_elf::FrameInspection;
using ttexalens::native_elf::InvalidArrayAccessException;
using ttexalens::native_elf::MemoryAccess;
using ttexalens::native_elf::SymbolNotFoundException;
using ttexalens::native_elf::TypeMismatchException;

namespace {

// Forward iterator over a DIE's direct children, walking the
// first_child/next_sibling linked-list. Used by DwarfDie.iter_children's
// nb::make_iterator binding to produce a Python iterator for
// `for child in die.iter_children():`.
class DieChildIterator {
   public:
    DieChildIterator() = default;
    explicit DieChildIterator(ttexalens::native_elf::DwarfDiePtr c) : current(std::move(c)) {}

    const ttexalens::native_elf::DwarfDiePtr& operator*() const { return current; }
    DieChildIterator& operator++() {
        if (current) {
            current = current->get_next_sibling();
        }
        return *this;
    }
    bool operator==(const DieChildIterator& other) const { return current == other.current; }
    bool operator!=(const DieChildIterator& other) const { return !(*this == other); }

   private:
    ttexalens::native_elf::DwarfDiePtr current;
};

// Forward index-based iterator over an ElfFile's sections. Paired with
// nb::make_iterator so ElfFile.iter_sections() exposes its element
// type to Python as Iterator[ElfSection].
class ElfSectionIterator {
   public:
    ElfSectionIterator() = default;
    ElfSectionIterator(const ttexalens::native_elf::ElfFile* elf, size_t index) : elf(elf), index(index) {}

    const ttexalens::native_elf::ElfSection* operator*() const { return elf->get_section(index); }
    ElfSectionIterator& operator++() {
        ++index;
        return *this;
    }
    bool operator==(const ElfSectionIterator& other) const { return elf == other.elf && index == other.index; }
    bool operator!=(const ElfSectionIterator& other) const { return !(*this == other); }

   private:
    const ttexalens::native_elf::ElfFile* elf = nullptr;
    size_t index = 0;
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

// Helpers for ElfVariable dunders: reduce a C++ TypeMismatchException
// (raised when read_value is called on a non-base/pointer/enum type) to
// Python's NotImplemented so the arithmetic/comparison operators degrade
// gracefully, matching the Python ElfVariable contract.
namespace {

nb::object var_value_obj(const ElfVariable& self) { return nb::cast(self.read_value()); }

template <typename Op>
nb::object try_binop(const ElfVariable& self, nb::handle other, Op&& op) {
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
    //   from ttexalens._native_ttexalens import DwarfDieTag as tag
    //   if die.tag == tag.subprogram: ...
    // Python sees a regular enum.Enum; comparisons against DwarfDie.tag
    // (also a DwarfDieTag instance) work directly.
    nb::enum_<ttexalens::native_elf::DwarfDieTag>(m, "DwarfDieTag")
        .value("access_declaration", DwarfDieTag::access_declaration)
        .value("ALTIUM_circ_type", DwarfDieTag::ALTIUM_circ_type)
        .value("ALTIUM_mwa_circ_type", DwarfDieTag::ALTIUM_mwa_circ_type)
        .value("ALTIUM_rev_carry_type", DwarfDieTag::ALTIUM_rev_carry_type)
        .value("ALTIUM_rom", DwarfDieTag::ALTIUM_rom)
        .value("array_type", DwarfDieTag::array_type)
        .value("atomic_type", DwarfDieTag::atomic_type)
        .value("base_type", DwarfDieTag::base_type)
        .value("BORLAND_Delphi_dynamic_array", DwarfDieTag::BORLAND_Delphi_dynamic_array)
        .value("BORLAND_Delphi_set", DwarfDieTag::BORLAND_Delphi_set)
        .value("BORLAND_Delphi_string", DwarfDieTag::BORLAND_Delphi_string)
        .value("BORLAND_Delphi_variant", DwarfDieTag::BORLAND_Delphi_variant)
        .value("BORLAND_property", DwarfDieTag::BORLAND_property)
        .value("call_site", DwarfDieTag::call_site)
        .value("call_site_parameter", DwarfDieTag::call_site_parameter)
        .value("catch_block", DwarfDieTag::catch_block)
        .value("class_template", DwarfDieTag::class_template)
        .value("class_type", DwarfDieTag::class_type)
        .value("coarray_type", DwarfDieTag::coarray_type)
        .value("common_block", DwarfDieTag::common_block)
        .value("common_inclusion", DwarfDieTag::common_inclusion)
        .value("compile_unit", DwarfDieTag::compile_unit)
        .value("condition", DwarfDieTag::condition)
        .value("const_type", DwarfDieTag::const_type)
        .value("constant", DwarfDieTag::constant)
        .value("dwarf_procedure", DwarfDieTag::dwarf_procedure)
        .value("dynamic_type", DwarfDieTag::dynamic_type)
        .value("entry_point", DwarfDieTag::entry_point)
        .value("enumeration_type", DwarfDieTag::enumeration_type)
        .value("enumerator", DwarfDieTag::enumerator)
        .value("file_type", DwarfDieTag::file_type)
        .value("formal_parameter", DwarfDieTag::formal_parameter)
        .value("format_label", DwarfDieTag::format_label)
        .value("friend", DwarfDieTag::friend_)
        .value("function_template", DwarfDieTag::function_template)
        .value("generic_subrange", DwarfDieTag::generic_subrange)
        .value("ghs_namespace", DwarfDieTag::ghs_namespace)
        .value("ghs_template_templ_param", DwarfDieTag::ghs_template_templ_param)
        .value("ghs_using_declaration", DwarfDieTag::ghs_using_declaration)
        .value("ghs_using_namespace", DwarfDieTag::ghs_using_namespace)
        .value("GNU_BINCL", DwarfDieTag::GNU_BINCL)
        .value("GNU_call_site", DwarfDieTag::GNU_call_site)
        .value("GNU_call_site_parameter", DwarfDieTag::GNU_call_site_parameter)
        .value("GNU_EINCL", DwarfDieTag::GNU_EINCL)
        .value("GNU_formal_parameter_pack", DwarfDieTag::GNU_formal_parameter_pack)
        .value("GNU_template_parameter_pack", DwarfDieTag::GNU_template_parameter_pack)
        .value("GNU_template_template_parameter", DwarfDieTag::GNU_template_template_parameter)
        .value("HP_array_descriptor", DwarfDieTag::HP_array_descriptor)
        .value("immutable_type", DwarfDieTag::immutable_type)
        .value("imported_declaration", DwarfDieTag::imported_declaration)
        .value("imported_module", DwarfDieTag::imported_module)
        .value("imported_unit", DwarfDieTag::imported_unit)
        .value("inheritance", DwarfDieTag::inheritance)
        .value("inlined_subroutine", DwarfDieTag::inlined_subroutine)
        .value("interface_type", DwarfDieTag::interface_type)
        .value("label", DwarfDieTag::label)
        .value("lexical_block", DwarfDieTag::lexical_block)
        .value("LLVM_annotation", DwarfDieTag::LLVM_annotation)
        .value("member", DwarfDieTag::member)
        .value("MIPS_loop", DwarfDieTag::MIPS_loop)
        .value("module", DwarfDieTag::module)
        .value("mutable_type", DwarfDieTag::mutable_type)
        .value("namelist", DwarfDieTag::namelist)
        .value("namelist_item", DwarfDieTag::namelist_item)
        .value("namespace", DwarfDieTag::namespace_)
        .value("packed_type", DwarfDieTag::packed_type)
        .value("partial_unit", DwarfDieTag::partial_unit)
        .value("PGI_interface_block", DwarfDieTag::PGI_interface_block)
        .value("PGI_kanji_type", DwarfDieTag::PGI_kanji_type)
        .value("pointer_type", DwarfDieTag::pointer_type)
        .value("ptr_to_member_type", DwarfDieTag::ptr_to_member_type)
        .value("reference_type", DwarfDieTag::reference_type)
        .value("restrict_type", DwarfDieTag::restrict_type)
        .value("rvalue_reference_type", DwarfDieTag::rvalue_reference_type)
        .value("set_type", DwarfDieTag::set_type)
        .value("shared_type", DwarfDieTag::shared_type)
        .value("skeleton_unit", DwarfDieTag::skeleton_unit)
        .value("string_type", DwarfDieTag::string_type)
        .value("structure_type", DwarfDieTag::structure_type)
        .value("subprogram", DwarfDieTag::subprogram)
        .value("subrange_type", DwarfDieTag::subrange_type)
        .value("subroutine_type", DwarfDieTag::subroutine_type)
        .value("SUN_class_template", DwarfDieTag::SUN_class_template)
        .value("SUN_codeflags", DwarfDieTag::SUN_codeflags)
        .value("SUN_dtor", DwarfDieTag::SUN_dtor)
        .value("SUN_dtor_info", DwarfDieTag::SUN_dtor_info)
        .value("SUN_f90_interface", DwarfDieTag::SUN_f90_interface)
        .value("SUN_fortran_vax_structure", DwarfDieTag::SUN_fortran_vax_structure)
        .value("SUN_function_template", DwarfDieTag::SUN_function_template)
        .value("SUN_hi", DwarfDieTag::SUN_hi)
        .value("SUN_indirect_inheritance", DwarfDieTag::SUN_indirect_inheritance)
        .value("SUN_memop_info", DwarfDieTag::SUN_memop_info)
        .value("SUN_omp_child_func", DwarfDieTag::SUN_omp_child_func)
        .value("SUN_rtti_descriptor", DwarfDieTag::SUN_rtti_descriptor)
        .value("SUN_struct_template", DwarfDieTag::SUN_struct_template)
        .value("SUN_union_template", DwarfDieTag::SUN_union_template)
        .value("template_alias", DwarfDieTag::template_alias)
        .value("template_type_parameter", DwarfDieTag::template_type_parameter)
        .value("template_value_parameter", DwarfDieTag::template_value_parameter)
        .value("thrown_type", DwarfDieTag::thrown_type)
        .value("TI_assign_register", DwarfDieTag::TI_assign_register)
        .value("TI_far_type", DwarfDieTag::TI_far_type)
        .value("TI_ioport_type", DwarfDieTag::TI_ioport_type)
        .value("TI_near_type", DwarfDieTag::TI_near_type)
        .value("TI_onchip_type", DwarfDieTag::TI_onchip_type)
        .value("TI_restrict_type", DwarfDieTag::TI_restrict_type)
        .value("try_block", DwarfDieTag::try_block)
        .value("type_unit", DwarfDieTag::type_unit)
        .value("typedef", DwarfDieTag::typedef_)
        .value("union_type", DwarfDieTag::union_type)
        .value("unspecified_parameters", DwarfDieTag::unspecified_parameters)
        .value("unspecified_type", DwarfDieTag::unspecified_type)
        .value("upc_relaxed_type", DwarfDieTag::upc_relaxed_type)
        .value("upc_shared_type", DwarfDieTag::upc_shared_type)
        .value("upc_strict_type", DwarfDieTag::upc_strict_type)
        .value("variable", DwarfDieTag::variable)
        .value("variant", DwarfDieTag::variant)
        .value("variant_part", DwarfDieTag::variant_part)
        .value("volatile_type", DwarfDieTag::volatile_type)
        .value("with_stmt", DwarfDieTag::with_stmt);

    // DW_AT_* attribute tags. Use with:
    //   from ttexalens._native_ttexalens import DwarfAttributeTag as at
    //   die.get_attribute(at.declaration)
    nb::enum_<DwarfAttributeTag>(m, "DwarfAttributeTag")
        .value("abstract_origin", DwarfAttributeTag::abstract_origin)
        .value("accessibility", DwarfAttributeTag::accessibility)
        .value("addr_base", DwarfAttributeTag::addr_base)
        .value("address_class", DwarfAttributeTag::address_class)
        .value("alignment", DwarfAttributeTag::alignment)
        .value("allocated", DwarfAttributeTag::allocated)
        .value("ALTIUM_loclist", DwarfAttributeTag::ALTIUM_loclist)
        .value("APPLE_block", DwarfAttributeTag::APPLE_block)
        .value("APPLE_flags", DwarfAttributeTag::APPLE_flags)
        .value("APPLE_isa", DwarfAttributeTag::APPLE_isa)
        .value("APPLE_major_runtime_vers", DwarfAttributeTag::APPLE_major_runtime_vers)
        .value("APPLE_objc_complete_type", DwarfAttributeTag::APPLE_objc_complete_type)
        .value("APPLE_objc_direct", DwarfAttributeTag::APPLE_objc_direct)
        .value("APPLE_omit_frame_ptr", DwarfAttributeTag::APPLE_omit_frame_ptr)
        .value("APPLE_optimized", DwarfAttributeTag::APPLE_optimized)
        .value("APPLE_origin", DwarfAttributeTag::APPLE_origin)
        .value("APPLE_property", DwarfAttributeTag::APPLE_property)
        .value("APPLE_property_attribute", DwarfAttributeTag::APPLE_property_attribute)
        .value("APPLE_property_getter", DwarfAttributeTag::APPLE_property_getter)
        .value("APPLE_property_name", DwarfAttributeTag::APPLE_property_name)
        .value("APPLE_property_setter", DwarfAttributeTag::APPLE_property_setter)
        .value("APPLE_runtime_class", DwarfAttributeTag::APPLE_runtime_class)
        .value("APPLE_sdk", DwarfAttributeTag::APPLE_sdk)
        .value("artificial", DwarfAttributeTag::artificial)
        .value("associated", DwarfAttributeTag::associated)
        .value("base_types", DwarfAttributeTag::base_types)
        .value("binary_scale", DwarfAttributeTag::binary_scale)
        .value("bit_offset", DwarfAttributeTag::bit_offset)
        .value("bit_size", DwarfAttributeTag::bit_size)
        .value("bit_stride", DwarfAttributeTag::bit_stride)
        .value("body_begin", DwarfAttributeTag::body_begin)
        .value("body_end", DwarfAttributeTag::body_end)
        .value("BORLAND_closure", DwarfAttributeTag::BORLAND_closure)
        .value("BORLAND_Delphi_ABI", DwarfAttributeTag::BORLAND_Delphi_ABI)
        .value("BORLAND_Delphi_anonymous_method", DwarfAttributeTag::BORLAND_Delphi_anonymous_method)
        .value("BORLAND_Delphi_class", DwarfAttributeTag::BORLAND_Delphi_class)
        .value("BORLAND_Delphi_constructor", DwarfAttributeTag::BORLAND_Delphi_constructor)
        .value("BORLAND_Delphi_destructor", DwarfAttributeTag::BORLAND_Delphi_destructor)
        .value("BORLAND_Delphi_frameptr", DwarfAttributeTag::BORLAND_Delphi_frameptr)
        .value("BORLAND_Delphi_interface", DwarfAttributeTag::BORLAND_Delphi_interface)
        .value("BORLAND_Delphi_metaclass", DwarfAttributeTag::BORLAND_Delphi_metaclass)
        .value("BORLAND_Delphi_record", DwarfAttributeTag::BORLAND_Delphi_record)
        .value("BORLAND_Delphi_unit", DwarfAttributeTag::BORLAND_Delphi_unit)
        .value("BORLAND_property_default", DwarfAttributeTag::BORLAND_property_default)
        .value("BORLAND_property_implements", DwarfAttributeTag::BORLAND_property_implements)
        .value("BORLAND_property_index", DwarfAttributeTag::BORLAND_property_index)
        .value("BORLAND_property_read", DwarfAttributeTag::BORLAND_property_read)
        .value("BORLAND_property_write", DwarfAttributeTag::BORLAND_property_write)
        .value("byte_size", DwarfAttributeTag::byte_size)
        .value("byte_stride", DwarfAttributeTag::byte_stride)
        .value("call_all_calls", DwarfAttributeTag::call_all_calls)
        .value("call_all_source_calls", DwarfAttributeTag::call_all_source_calls)
        .value("call_all_tail_calls", DwarfAttributeTag::call_all_tail_calls)
        .value("call_column", DwarfAttributeTag::call_column)
        .value("call_data_location", DwarfAttributeTag::call_data_location)
        .value("call_data_value", DwarfAttributeTag::call_data_value)
        .value("call_file", DwarfAttributeTag::call_file)
        .value("call_line", DwarfAttributeTag::call_line)
        .value("call_origin", DwarfAttributeTag::call_origin)
        .value("call_parameter", DwarfAttributeTag::call_parameter)
        .value("call_pc", DwarfAttributeTag::call_pc)
        .value("call_return_pc", DwarfAttributeTag::call_return_pc)
        .value("call_tail_call", DwarfAttributeTag::call_tail_call)
        .value("call_target", DwarfAttributeTag::call_target)
        .value("call_target_clobbered", DwarfAttributeTag::call_target_clobbered)
        .value("call_value", DwarfAttributeTag::call_value)
        .value("calling_convention", DwarfAttributeTag::calling_convention)
        .value("common_reference", DwarfAttributeTag::common_reference)
        .value("comp_dir", DwarfAttributeTag::comp_dir)
        .value("const_expr", DwarfAttributeTag::const_expr)
        .value("const_value", DwarfAttributeTag::const_value)
        .value("containing_type", DwarfAttributeTag::containing_type)
        .value("count", DwarfAttributeTag::count)
        .value("CPQ_discontig_ranges", DwarfAttributeTag::CPQ_discontig_ranges)
        .value("CPQ_prologue_length", DwarfAttributeTag::CPQ_prologue_length)
        .value("CPQ_semantic_events", DwarfAttributeTag::CPQ_semantic_events)
        .value("CPQ_split_lifetimes_rtn", DwarfAttributeTag::CPQ_split_lifetimes_rtn)
        .value("CPQ_split_lifetimes_var", DwarfAttributeTag::CPQ_split_lifetimes_var)
        .value("data_bit_offset", DwarfAttributeTag::data_bit_offset)
        .value("data_location", DwarfAttributeTag::data_location)
        .value("data_member_location", DwarfAttributeTag::data_member_location)
        .value("decimal_scale", DwarfAttributeTag::decimal_scale)
        .value("decimal_sign", DwarfAttributeTag::decimal_sign)
        .value("decl_column", DwarfAttributeTag::decl_column)
        .value("decl_file", DwarfAttributeTag::decl_file)
        .value("decl_line", DwarfAttributeTag::decl_line)
        .value("declaration", DwarfAttributeTag::declaration)
        .value("default_value", DwarfAttributeTag::default_value)
        .value("defaulted", DwarfAttributeTag::defaulted)
        .value("deleted", DwarfAttributeTag::deleted)
        .value("description", DwarfAttributeTag::description)
        .value("digit_count", DwarfAttributeTag::digit_count)
        .value("discr", DwarfAttributeTag::discr)
        .value("discr_list", DwarfAttributeTag::discr_list)
        .value("discr_value", DwarfAttributeTag::discr_value)
        .value("dwo_id", DwarfAttributeTag::dwo_id)
        .value("dwo_name", DwarfAttributeTag::dwo_name)
        .value("element_list", DwarfAttributeTag::element_list)
        .value("elemental", DwarfAttributeTag::elemental)
        .value("encoding", DwarfAttributeTag::encoding)
        .value("endianity", DwarfAttributeTag::endianity)
        .value("entry_pc", DwarfAttributeTag::entry_pc)
        .value("enum_class", DwarfAttributeTag::enum_class)
        .value("explicit", DwarfAttributeTag::explicit_)
        .value("export_symbols", DwarfAttributeTag::export_symbols)
        .value("extension", DwarfAttributeTag::extension)
        .value("external", DwarfAttributeTag::external)
        .value("frame_base", DwarfAttributeTag::frame_base)
        .value("friend", DwarfAttributeTag::friend_)
        .value("ghs_frames", DwarfAttributeTag::ghs_frames)
        .value("ghs_frsm", DwarfAttributeTag::ghs_frsm)
        .value("ghs_lbrace_line", DwarfAttributeTag::ghs_lbrace_line)
        .value("ghs_mangled", DwarfAttributeTag::ghs_mangled)
        .value("ghs_namespace_alias", DwarfAttributeTag::ghs_namespace_alias)
        .value("ghs_rsm", DwarfAttributeTag::ghs_rsm)
        .value("ghs_rso", DwarfAttributeTag::ghs_rso)
        .value("ghs_subcpu", DwarfAttributeTag::ghs_subcpu)
        .value("ghs_using_declaration", DwarfAttributeTag::ghs_using_declaration)
        .value("ghs_using_namespace", DwarfAttributeTag::ghs_using_namespace)
        .value("GNAT_descriptive_type", DwarfAttributeTag::GNAT_descriptive_type)
        .value("GNU_addr_base", DwarfAttributeTag::GNU_addr_base)
        .value("GNU_all_call_sites", DwarfAttributeTag::GNU_all_call_sites)
        .value("GNU_all_source_call_sites", DwarfAttributeTag::GNU_all_source_call_sites)
        .value("GNU_all_tail_call_sites", DwarfAttributeTag::GNU_all_tail_call_sites)
        .value("GNU_bias", DwarfAttributeTag::GNU_bias)
        .value("GNU_call_site_data_value", DwarfAttributeTag::GNU_call_site_data_value)
        .value("GNU_call_site_target", DwarfAttributeTag::GNU_call_site_target)
        .value("GNU_call_site_target_clobbered", DwarfAttributeTag::GNU_call_site_target_clobbered)
        .value("GNU_call_site_value", DwarfAttributeTag::GNU_call_site_value)
        .value("GNU_deleted", DwarfAttributeTag::GNU_deleted)
        .value("GNU_denominator", DwarfAttributeTag::GNU_denominator)
        .value("GNU_discriminator", DwarfAttributeTag::GNU_discriminator)
        .value("GNU_dwo_id", DwarfAttributeTag::GNU_dwo_id)
        .value("GNU_dwo_name", DwarfAttributeTag::GNU_dwo_name)
        .value("GNU_entry_view", DwarfAttributeTag::GNU_entry_view)
        .value("GNU_exclusive_locks_required", DwarfAttributeTag::GNU_exclusive_locks_required)
        .value("GNU_guarded", DwarfAttributeTag::GNU_guarded)
        .value("GNU_guarded_by", DwarfAttributeTag::GNU_guarded_by)
        .value("GNU_locks_excluded", DwarfAttributeTag::GNU_locks_excluded)
        .value("GNU_locviews", DwarfAttributeTag::GNU_locviews)
        .value("GNU_macros", DwarfAttributeTag::GNU_macros)
        .value("GNU_numerator", DwarfAttributeTag::GNU_numerator)
        .value("GNU_odr_signature", DwarfAttributeTag::GNU_odr_signature)
        .value("GNU_pt_guarded", DwarfAttributeTag::GNU_pt_guarded)
        .value("GNU_pt_guarded_by", DwarfAttributeTag::GNU_pt_guarded_by)
        .value("GNU_pubnames", DwarfAttributeTag::GNU_pubnames)
        .value("GNU_pubtypes", DwarfAttributeTag::GNU_pubtypes)
        .value("GNU_ranges_base", DwarfAttributeTag::GNU_ranges_base)
        .value("GNU_shared_locks_required", DwarfAttributeTag::GNU_shared_locks_required)
        .value("GNU_tail_call", DwarfAttributeTag::GNU_tail_call)
        .value("GNU_template_name", DwarfAttributeTag::GNU_template_name)
        .value("GNU_vector", DwarfAttributeTag::GNU_vector)
        .value("go_closure_offset", DwarfAttributeTag::go_closure_offset)
        .value("go_dict_index", DwarfAttributeTag::go_dict_index)
        .value("go_elem", DwarfAttributeTag::go_elem)
        .value("go_embedded_field", DwarfAttributeTag::go_embedded_field)
        .value("go_key", DwarfAttributeTag::go_key)
        .value("go_kind", DwarfAttributeTag::go_kind)
        .value("go_package_name", DwarfAttributeTag::go_package_name)
        .value("go_runtime_type", DwarfAttributeTag::go_runtime_type)
        .value("high_pc", DwarfAttributeTag::high_pc)
        .value("HP_actuals_stmt_list", DwarfAttributeTag::HP_actuals_stmt_list)
        .value("HP_all_variables_modifiable", DwarfAttributeTag::HP_all_variables_modifiable)
        .value("HP_block_index", DwarfAttributeTag::HP_block_index)
        .value("HP_cold_region_high_pc", DwarfAttributeTag::HP_cold_region_high_pc)
        .value("HP_cold_region_low_pc", DwarfAttributeTag::HP_cold_region_low_pc)
        .value("HP_default_location", DwarfAttributeTag::HP_default_location)
        .value("HP_definition_points", DwarfAttributeTag::HP_definition_points)
        .value("HP_epilogue", DwarfAttributeTag::HP_epilogue)
        .value("HP_is_result_param", DwarfAttributeTag::HP_is_result_param)
        .value("HP_linkage_name", DwarfAttributeTag::HP_linkage_name)
        .value("HP_opt_flags", DwarfAttributeTag::HP_opt_flags)
        .value("HP_opt_level", DwarfAttributeTag::HP_opt_level)
        .value("HP_pass_by_reference", DwarfAttributeTag::HP_pass_by_reference)
        .value("HP_proc_per_section", DwarfAttributeTag::HP_proc_per_section)
        .value("HP_prof_flags", DwarfAttributeTag::HP_prof_flags)
        .value("HP_prof_version_id", DwarfAttributeTag::HP_prof_version_id)
        .value("HP_prologue", DwarfAttributeTag::HP_prologue)
        .value("HP_raw_data_ptr", DwarfAttributeTag::HP_raw_data_ptr)
        .value("HP_unit_name", DwarfAttributeTag::HP_unit_name)
        .value("HP_unit_size", DwarfAttributeTag::HP_unit_size)
        .value("HP_unmodifiable", DwarfAttributeTag::HP_unmodifiable)
        .value("HP_widened_byte_size", DwarfAttributeTag::HP_widened_byte_size)
        .value("IBM_alt_srcview", DwarfAttributeTag::IBM_alt_srcview)
        .value("IBM_home_location", DwarfAttributeTag::IBM_home_location)
        .value("IBM_wsa_addr", DwarfAttributeTag::IBM_wsa_addr)
        .value("identifier_case", DwarfAttributeTag::identifier_case)
        .value("import_", DwarfAttributeTag::import)
        .value("inline", DwarfAttributeTag::inline_)
        .value("INTEL_other_endian", DwarfAttributeTag::INTEL_other_endian)
        .value("is_optional", DwarfAttributeTag::is_optional)
        .value("language", DwarfAttributeTag::language)
        .value("language_name", DwarfAttributeTag::language_name)
        .value("language_version", DwarfAttributeTag::language_version)
        .value("linkage_name", DwarfAttributeTag::linkage_name)
        .value("LLVM_active_lane", DwarfAttributeTag::LLVM_active_lane)
        .value("LLVM_apinotes", DwarfAttributeTag::LLVM_apinotes)
        .value("LLVM_augmentation", DwarfAttributeTag::LLVM_augmentation)
        .value("LLVM_config_macros", DwarfAttributeTag::LLVM_config_macros)
        .value("LLVM_include_path", DwarfAttributeTag::LLVM_include_path)
        .value("LLVM_lane_pc", DwarfAttributeTag::LLVM_lane_pc)
        .value("LLVM_lanes", DwarfAttributeTag::LLVM_lanes)
        .value("LLVM_sysroot", DwarfAttributeTag::LLVM_sysroot)
        .value("LLVM_tag_offset", DwarfAttributeTag::LLVM_tag_offset)
        .value("LLVM_vector_size", DwarfAttributeTag::LLVM_vector_size)
        .value("location", DwarfAttributeTag::location)
        .value("loclists_base", DwarfAttributeTag::loclists_base)
        .value("low_pc", DwarfAttributeTag::low_pc)
        .value("lower_bound", DwarfAttributeTag::lower_bound)
        .value("mac_info", DwarfAttributeTag::mac_info)
        .value("macro_info", DwarfAttributeTag::macro_info)
        .value("macros", DwarfAttributeTag::macros)
        .value("main_subprogram", DwarfAttributeTag::main_subprogram)
        .value("member", DwarfAttributeTag::member)
        .value("MIPS_abstract_name", DwarfAttributeTag::MIPS_abstract_name)
        .value("MIPS_allocatable_dopetype", DwarfAttributeTag::MIPS_allocatable_dopetype)
        .value("MIPS_assumed_shape_dopetype", DwarfAttributeTag::MIPS_assumed_shape_dopetype)
        .value("MIPS_assumed_size", DwarfAttributeTag::MIPS_assumed_size)
        .value("MIPS_clone_origin", DwarfAttributeTag::MIPS_clone_origin)
        .value("MIPS_epilog_begin", DwarfAttributeTag::MIPS_epilog_begin)
        .value("MIPS_fde", DwarfAttributeTag::MIPS_fde)
        .value("MIPS_has_inlines", DwarfAttributeTag::MIPS_has_inlines)
        .value("MIPS_linkage_name", DwarfAttributeTag::MIPS_linkage_name)
        .value("MIPS_loop_begin", DwarfAttributeTag::MIPS_loop_begin)
        .value("MIPS_loop_unroll_factor", DwarfAttributeTag::MIPS_loop_unroll_factor)
        .value("MIPS_ptr_dopetype", DwarfAttributeTag::MIPS_ptr_dopetype)
        .value("MIPS_software_pipeline_depth", DwarfAttributeTag::MIPS_software_pipeline_depth)
        .value("MIPS_stride", DwarfAttributeTag::MIPS_stride)
        .value("MIPS_stride_byte", DwarfAttributeTag::MIPS_stride_byte)
        .value("MIPS_stride_elem", DwarfAttributeTag::MIPS_stride_elem)
        .value("MIPS_tail_loop_begin", DwarfAttributeTag::MIPS_tail_loop_begin)
        .value("mutable", DwarfAttributeTag::mutable_)
        .value("name_", DwarfAttributeTag::name)
        .value("namelist_item", DwarfAttributeTag::namelist_item)
        .value("noreturn", DwarfAttributeTag::noreturn)
        .value("object_pointer", DwarfAttributeTag::object_pointer)
        .value("ordering", DwarfAttributeTag::ordering)
        .value("PGI_lbase", DwarfAttributeTag::PGI_lbase)
        .value("PGI_lstride", DwarfAttributeTag::PGI_lstride)
        .value("PGI_soffset", DwarfAttributeTag::PGI_soffset)
        .value("picture_string", DwarfAttributeTag::picture_string)
        .value("priority", DwarfAttributeTag::priority)
        .value("producer", DwarfAttributeTag::producer)
        .value("prototyped", DwarfAttributeTag::prototyped)
        .value("pure", DwarfAttributeTag::pure)
        .value("ranges", DwarfAttributeTag::ranges)
        .value("rank", DwarfAttributeTag::rank)
        .value("recursive", DwarfAttributeTag::recursive)
        .value("reference", DwarfAttributeTag::reference)
        .value("return_addr", DwarfAttributeTag::return_addr)
        .value("rnglists_base", DwarfAttributeTag::rnglists_base)
        .value("rvalue_reference", DwarfAttributeTag::rvalue_reference)
        .value("segment", DwarfAttributeTag::segment)
        .value("sf_names", DwarfAttributeTag::sf_names)
        .value("sibling", DwarfAttributeTag::sibling)
        .value("signature", DwarfAttributeTag::signature)
        .value("small", DwarfAttributeTag::small)
        .value("specification", DwarfAttributeTag::specification)
        .value("src_coords", DwarfAttributeTag::src_coords)
        .value("src_info", DwarfAttributeTag::src_info)
        .value("start_scope", DwarfAttributeTag::start_scope)
        .value("static_link", DwarfAttributeTag::static_link)
        .value("stmt_list", DwarfAttributeTag::stmt_list)
        .value("str_offsets_base", DwarfAttributeTag::str_offsets_base)
        .value("stride", DwarfAttributeTag::stride)
        .value("stride_size", DwarfAttributeTag::stride_size)
        .value("string_length", DwarfAttributeTag::string_length)
        .value("string_length_bit_size", DwarfAttributeTag::string_length_bit_size)
        .value("string_length_byte_size", DwarfAttributeTag::string_length_byte_size)
        .value("SUN_alignment", DwarfAttributeTag::SUN_alignment)
        .value("SUN_amd64_parmdump", DwarfAttributeTag::SUN_amd64_parmdump)
        .value("SUN_browser_file", DwarfAttributeTag::SUN_browser_file)
        .value("SUN_c_vla", DwarfAttributeTag::SUN_c_vla)
        .value("SUN_cf_kind", DwarfAttributeTag::SUN_cf_kind)
        .value("SUN_command_line", DwarfAttributeTag::SUN_command_line)
        .value("SUN_compile_options", DwarfAttributeTag::SUN_compile_options)
        .value("SUN_count_guarantee", DwarfAttributeTag::SUN_count_guarantee)
        .value("SUN_dtor_length", DwarfAttributeTag::SUN_dtor_length)
        .value("SUN_dtor_start", DwarfAttributeTag::SUN_dtor_start)
        .value("SUN_dtor_state_deltas", DwarfAttributeTag::SUN_dtor_state_deltas)
        .value("SUN_dtor_state_final", DwarfAttributeTag::SUN_dtor_state_final)
        .value("SUN_dtor_state_initial", DwarfAttributeTag::SUN_dtor_state_initial)
        .value("SUN_f90_allocatable", DwarfAttributeTag::SUN_f90_allocatable)
        .value("SUN_f90_assumed_shape_array", DwarfAttributeTag::SUN_f90_assumed_shape_array)
        .value("SUN_f90_pointer", DwarfAttributeTag::SUN_f90_pointer)
        .value("SUN_f90_use_only", DwarfAttributeTag::SUN_f90_use_only)
        .value("SUN_fortran_based", DwarfAttributeTag::SUN_fortran_based)
        .value("SUN_fortran_main_alias", DwarfAttributeTag::SUN_fortran_main_alias)
        .value("SUN_func_offset", DwarfAttributeTag::SUN_func_offset)
        .value("SUN_func_offsets", DwarfAttributeTag::SUN_func_offsets)
        .value("SUN_hwcprof_signature", DwarfAttributeTag::SUN_hwcprof_signature)
        .value("SUN_import_by_lname", DwarfAttributeTag::SUN_import_by_lname)
        .value("SUN_import_by_name", DwarfAttributeTag::SUN_import_by_name)
        .value("SUN_is_omp_child_func", DwarfAttributeTag::SUN_is_omp_child_func)
        .value("SUN_language", DwarfAttributeTag::SUN_language)
        .value("SUN_link_name", DwarfAttributeTag::SUN_link_name)
        .value("SUN_memop_signature", DwarfAttributeTag::SUN_memop_signature)
        .value("SUN_memop_type_ref", DwarfAttributeTag::SUN_memop_type_ref)
        .value("SUN_namelist_spec", DwarfAttributeTag::SUN_namelist_spec)
        .value("SUN_obj_dir", DwarfAttributeTag::SUN_obj_dir)
        .value("SUN_obj_file", DwarfAttributeTag::SUN_obj_file)
        .value("SUN_omp_child_func", DwarfAttributeTag::SUN_omp_child_func)
        .value("SUN_omp_tpriv_addr", DwarfAttributeTag::SUN_omp_tpriv_addr)
        .value("SUN_original_name", DwarfAttributeTag::SUN_original_name)
        .value("SUN_part_link_name", DwarfAttributeTag::SUN_part_link_name)
        .value("SUN_pass_by_ref", DwarfAttributeTag::SUN_pass_by_ref)
        .value("SUN_pass_with_const", DwarfAttributeTag::SUN_pass_with_const)
        .value("SUN_profile_id", DwarfAttributeTag::SUN_profile_id)
        .value("SUN_return_value_ptr", DwarfAttributeTag::SUN_return_value_ptr)
        .value("SUN_return_with_const", DwarfAttributeTag::SUN_return_with_const)
        .value("SUN_template", DwarfAttributeTag::SUN_template)
        .value("SUN_vbase", DwarfAttributeTag::SUN_vbase)
        .value("SUN_vtable", DwarfAttributeTag::SUN_vtable)
        .value("SUN_vtable_abi", DwarfAttributeTag::SUN_vtable_abi)
        .value("SUN_vtable_index", DwarfAttributeTag::SUN_vtable_index)
        .value("threads_scaled", DwarfAttributeTag::threads_scaled)
        .value("TI_asm", DwarfAttributeTag::TI_asm)
        .value("TI_interrupt", DwarfAttributeTag::TI_interrupt)
        .value("TI_skeletal", DwarfAttributeTag::TI_skeletal)
        .value("TI_symbol_name", DwarfAttributeTag::TI_symbol_name)
        .value("TI_veneer", DwarfAttributeTag::TI_veneer)
        .value("TI_version", DwarfAttributeTag::TI_version)
        .value("trampoline", DwarfAttributeTag::trampoline)
        .value("type", DwarfAttributeTag::type)
        .value("upc_threads_scaled", DwarfAttributeTag::upc_threads_scaled)
        .value("upper_bound", DwarfAttributeTag::upper_bound)
        .value("use_GNAT_descriptive_type", DwarfAttributeTag::use_GNAT_descriptive_type)
        .value("use_location", DwarfAttributeTag::use_location)
        .value("use_UTF8", DwarfAttributeTag::use_UTF8)
        .value("variable_parameter", DwarfAttributeTag::variable_parameter)
        .value("virtuality", DwarfAttributeTag::virtuality)
        .value("visibility", DwarfAttributeTag::visibility)
        .value("VMS_rtnbeg_pd_address", DwarfAttributeTag::VMS_rtnbeg_pd_address)
        .value("vtable_elem_location", DwarfAttributeTag::vtable_elem_location);

    // DW_FORM_* — attribute form. Determines which std::variant alternative
    // DwarfAttribute.value will hold (see dwarf_attribute.hpp).
    nb::enum_<DwarfAttributeForm>(m, "DwarfAttributeForm")
        .value("addr", DwarfAttributeForm::addr)
        .value("addrx", DwarfAttributeForm::addrx)
        .value("addrx1", DwarfAttributeForm::addrx1)
        .value("addrx2", DwarfAttributeForm::addrx2)
        .value("addrx3", DwarfAttributeForm::addrx3)
        .value("addrx4", DwarfAttributeForm::addrx4)
        .value("block", DwarfAttributeForm::block)
        .value("block1", DwarfAttributeForm::block1)
        .value("block2", DwarfAttributeForm::block2)
        .value("block4", DwarfAttributeForm::block4)
        .value("data1", DwarfAttributeForm::data1)
        .value("data16", DwarfAttributeForm::data16)
        .value("data2", DwarfAttributeForm::data2)
        .value("data4", DwarfAttributeForm::data4)
        .value("data8", DwarfAttributeForm::data8)
        .value("exprloc", DwarfAttributeForm::exprloc)
        .value("flag", DwarfAttributeForm::flag)
        .value("flag_present", DwarfAttributeForm::flag_present)
        .value("GNU_addr_index", DwarfAttributeForm::GNU_addr_index)
        .value("GNU_ref_alt", DwarfAttributeForm::GNU_ref_alt)
        .value("GNU_str_index", DwarfAttributeForm::GNU_str_index)
        .value("GNU_strp_alt", DwarfAttributeForm::GNU_strp_alt)
        .value("implicit_const", DwarfAttributeForm::implicit_const)
        .value("indirect", DwarfAttributeForm::indirect)
        .value("line_strp", DwarfAttributeForm::line_strp)
        .value("LLVM_addrx_offset", DwarfAttributeForm::LLVM_addrx_offset)
        .value("loclistx", DwarfAttributeForm::loclistx)
        .value("ref1", DwarfAttributeForm::ref1)
        .value("ref2", DwarfAttributeForm::ref2)
        .value("ref4", DwarfAttributeForm::ref4)
        .value("ref8", DwarfAttributeForm::ref8)
        .value("ref_addr", DwarfAttributeForm::ref_addr)
        .value("ref_sig8", DwarfAttributeForm::ref_sig8)
        .value("ref_sup4", DwarfAttributeForm::ref_sup4)
        .value("ref_sup8", DwarfAttributeForm::ref_sup8)
        .value("ref_udata", DwarfAttributeForm::ref_udata)
        .value("rnglistx", DwarfAttributeForm::rnglistx)
        .value("sdata", DwarfAttributeForm::sdata)
        .value("sec_offset", DwarfAttributeForm::sec_offset)
        .value("string", DwarfAttributeForm::string)
        .value("strp", DwarfAttributeForm::strp)
        .value("strp_sup", DwarfAttributeForm::strp_sup)
        .value("strx", DwarfAttributeForm::strx)
        .value("strx1", DwarfAttributeForm::strx1)
        .value("strx2", DwarfAttributeForm::strx2)
        .value("strx3", DwarfAttributeForm::strx3)
        .value("strx4", DwarfAttributeForm::strx4)
        .value("udata", DwarfAttributeForm::udata);

    nb::class_<DwarfAttribute>(m, "DwarfAttribute")
        .def_prop_ro("tag", &DwarfAttribute::get_tag)
        .def_prop_ro("form", &DwarfAttribute::get_form)
        // Variant alternatives map to bool / int / str / bytes / None. Default
        // nanobind would expose std::vector<uint8_t> as a Python list[int],
        // but DW_FORM_block* / exprloc payloads are conceptually opaque byte
        // strings — hand them out as nb::bytes so callers don't have to
        // wrap with bytes(...) before struct.unpack / hash / etc.
        .def_prop_ro(
            "value",
            [](const DwarfAttribute& a) -> nb::object {
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
    // by ElfVariable::read() but exposed here so Python can also
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

    nb::class_<ElfSection>(m, "ElfSection")
        .def_prop_ro("name", &ElfSection::name)
        .def_prop_ro("address", &ElfSection::address)
        .def_prop_ro("size", &ElfSection::size)
        .def_prop_ro(
            "data",
            [](const ElfSection& s) {
                std::span<const std::byte> sp = s.data();
                PyObject* mv = PyMemoryView_FromMemory(const_cast<char*>(reinterpret_cast<const char*>(sp.data())),
                                                       static_cast<Py_ssize_t>(sp.size()), PyBUF_READ);
                if (mv == nullptr) {
                    throw nb::python_error();
                }
                return nb::steal<nb::object>(mv);
            },
            nb::rv_policy::reference_internal, nb::sig("def data(self) -> memoryview"));

    nb::enum_<ElfSymbolType>(m, "ElfSymbolType")
        .value("STT_NOTYPE", ElfSymbolType::STT_NOTYPE)
        .value("STT_OBJECT", ElfSymbolType::STT_OBJECT)
        .value("STT_FUNC", ElfSymbolType::STT_FUNC)
        .value("STT_SECTION", ElfSymbolType::STT_SECTION)
        .value("STT_FILE", ElfSymbolType::STT_FILE)
        .value("STT_COMMON", ElfSymbolType::STT_COMMON)
        .value("STT_TLS", ElfSymbolType::STT_TLS)
        .value("STT_LOOS", ElfSymbolType::STT_LOOS)
        .value("STT_AMDGPU_HSA_KERNEL", ElfSymbolType::STT_AMDGPU_HSA_KERNEL)
        .value("STT_HIOS", ElfSymbolType::STT_HIOS)
        .value("STT_LOPROC", ElfSymbolType::STT_LOPROC)
        .value("STT_HIPROC", ElfSymbolType::STT_HIPROC);

    nb::enum_<ElfSymbolBinding>(m, "ElfSymbolBinding")
        .value("STB_LOCAL", ElfSymbolBinding::STB_LOCAL)
        .value("STB_GLOBAL", ElfSymbolBinding::STB_GLOBAL)
        .value("STB_WEAK", ElfSymbolBinding::STB_WEAK)
        .value("STB_LOOS", ElfSymbolBinding::STB_LOOS)
        .value("STB_HIOS", ElfSymbolBinding::STB_HIOS)
        .value("STB_MULTIDEF", ElfSymbolBinding::STB_MULTIDEF)
        .value("STB_LOPROC", ElfSymbolBinding::STB_LOPROC)
        .value("STB_HIPROC", ElfSymbolBinding::STB_HIPROC);

    nb::class_<ElfSymbol>(m, "ElfSymbol")
        .def_ro("name", &ElfSymbol::name)
        .def_ro("value", &ElfSymbol::value)
        .def_ro("size", &ElfSymbol::size)
        .def_ro("type", &ElfSymbol::type)
        .def_ro("bind", &ElfSymbol::bind);

    nb::class_<ElfFile>(m, "ElfFile")
        .def(nb::init<const std::string&>(), nb::arg("path"))
        .def_static(
            "from_bytes",
            [](nb::handle data, std::string elf_file_path, std::optional<uint64_t> load_address) {
                // Accept any buffer-protocol object — bytes, bytearray,
                // memoryview, ElfSection.data, etc. BytesImpl copies
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
                return ElfFile::from_bytes(
                    std::span<const std::byte>(static_cast<const std::byte*>(buf.buf), static_cast<size_t>(buf.len)),
                    std::move(elf_file_path), load_address);
            },
            nb::arg("data"), nb::arg("elf_file_path") = std::string{}, nb::arg("load_address").none() = nb::none(),
            nb::sig("def from_bytes(data: bytes | bytearray | memoryview, elf_file_path: str = '', "
                    "load_address: int | None = None) -> ElfFile"))
        .def("get_sections_count", &ElfFile::get_sections_count)
        .def("get_section", &ElfFile::get_section, nb::arg("index"), nb::rv_policy::reference_internal,
             nb::sig("def get_section(self, index: int) -> ElfSection | None"))
        .def("get_section_by_name", &ElfFile::get_section_by_name, nb::arg("name"), nb::rv_policy::reference_internal,
             nb::sig("def get_section_by_name(self, name: str) -> ElfSection | None"))
        .def("read_symbol_table_section", &ElfFile::read_symbol_table_section, nb::arg("section_name"),
             nb::call_guard<nb::gil_scoped_release>())
        .def("has_dwarf_info", &ElfFile::has_dwarf_info, nb::arg("strict") = false)
        .def_prop_ro("dwarf_info", &ElfFile::get_dwarf_info, nb::rv_policy::reference_internal,
                     nb::call_guard<nb::gil_scoped_release>())
        .def_prop_ro("elf_file_path", &ElfFile::get_elf_file_path)
        .def_prop_ro("loaded_offset", &ElfFile::get_loaded_offset)
        .def_prop_ro("code_load_address", &ElfFile::get_code_load_address)
        .def("with_load_address", &ElfFile::with_load_address, nb::arg("load_address"))
        // Iterates over the file's sections in index order. For direct
        // lookups, prefer get_section_by_name(name).
        .def(
            "iter_sections",
            [](ElfFile& self) {
                return nb::make_iterator<nb::rv_policy::reference_internal>(
                    nb::type<ElfSection>(), "ElfSectionIterator", ElfSectionIterator(&self, 0),
                    ElfSectionIterator(&self, self.get_sections_count()));
            },
            nb::rv_policy::reference_internal)
        .def("get_frame_description", &ElfFile::get_frame_description, nb::arg("pc"), nb::arg("memory_access"),
             nb::call_guard<nb::gil_scoped_release>())
        .def("find_symbol_by_name", &ElfFile::find_symbol_by_name, nb::arg("name"), nb::rv_policy::reference_internal,
             nb::sig("def find_symbol_by_name(self, name: str) -> ElfSymbol | None"))
        .def("find_die_by_name", &ElfFile::find_die_by_name, nb::arg("name"))
        .def("get_enum_value", &ElfFile::get_enum_value, nb::arg("name"))
        .def("get_constant", &ElfFile::get_constant, nb::arg("name"))
        .def("get_global", &ElfFile::get_global, nb::arg("name"), nb::arg("memory_access"), nb::keep_alive<0, 1>())
        .def("read_global", &ElfFile::read_global, nb::arg("name"), nb::arg("memory_access"), nb::keep_alive<0, 1>());

    nb::class_<DwarfFileLine>(m, "DwarfFileLine")
        .def(nb::init<std::string, uint32_t, uint32_t>(), nb::arg("file"), nb::arg("line"), nb::arg("column") = 0)
        .def_prop_ro("file", [](const DwarfFileLine& f) -> std::string_view { return f.file; })
        .def_ro("line", &DwarfFileLine::line)
        .def_ro("column", &DwarfFileLine::column);

    nb::class_<DwarfDie>(m, "DwarfDie")
        // name / linkage_name return None (not the empty string) when the DIE
        // has no DW_AT_name / DW_AT_linkage_name — matches the legacy
        // ElfDie.name semantics, so call sites that test `if var.name is not
        // None` don't pass through empty strings.
        .def_prop_ro("name",
                     [](const DwarfDie& self) -> std::optional<std::string> {
                         auto name = self.get_name();
                         if (name.empty()) {
                             return std::nullopt;
                         }
                         return std::string(name);
                     })
        .def_prop_ro("linkage_name",
                     [](const DwarfDie& self) -> std::optional<std::string> {
                         auto name = self.get_linkage_name();
                         if (name.empty()) {
                             return std::nullopt;
                         }
                         return std::string(name);
                     })
        .def_prop_ro("offset", &DwarfDie::get_offset)
        .def_prop_ro("tag", &DwarfDie::get_tag)
        .def_prop_ro("attributes", &DwarfDie::get_attributes, nb::rv_policy::reference_internal)
        .def_prop_ro("is_signed_type", &DwarfDie::is_signed_type)
        .def_prop_ro("is_declaration", &DwarfDie::is_declaration)
        .def("get_attribute", &DwarfDie::get_attribute, nb::arg("attribute_tag"), nb::rv_policy::reference_internal,
             nb::sig("def get_attribute(self, attribute_tag: DwarfAttributeTag) -> DwarfAttribute | None"))
        .def("has_attribute", &DwarfDie::has_attribute, nb::arg("attribute_tag"))
        .def("get_path", &DwarfDie::get_path)
        .def("get_search_path", &DwarfDie::get_search_path)
        .def("get_size", &DwarfDie::get_size)
        .def("get_address", &DwarfDie::get_address)
        .def(
            "get_constant_value",
            [](const DwarfDie& d) -> nb::object {
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
        .def("get_resolved_type", &DwarfDie::get_resolved_type, nb::rv_policy::reference_internal,
             nb::sig("def get_resolved_type(self) -> DwarfDie | None"))
        .def("get_dereference_type", &DwarfDie::get_dereference_type, nb::rv_policy::reference_internal,
             nb::sig("def get_dereference_type(self) -> DwarfDie | None"))
        .def("get_array_element_type", &DwarfDie::get_array_element_type, nb::rv_policy::reference_internal,
             nb::sig("def get_array_element_type(self) -> DwarfDie | None"))
        .def("find_child_by_name", &DwarfDie::find_child_by_name, nb::arg("name"), nb::rv_policy::reference_internal,
             nb::sig("def find_child_by_name(self, name: str) -> DwarfDie | None"))
        .def("get_die_from_attribute", &DwarfDie::get_die_from_attribute, nb::arg("attribute_tag"),
             nb::rv_policy::reference_internal,
             nb::sig("def get_die_from_attribute(self, attribute_tag: DwarfAttributeTag) -> DwarfDie | None"))
        .def("get_address_ranges", &DwarfDie::get_address_ranges)
        .def("get_decl_file_info", &DwarfDie::get_decl_file_info)
        .def("get_call_file_info", &DwarfDie::get_call_file_info)
        .def("read_value", &DwarfDie::read_value, nb::arg("frame").none())
        .def("get_first_child", &DwarfDie::get_first_child, nb::rv_policy::reference_internal,
             nb::sig("def get_first_child(self) -> DwarfDie | None"))
        .def("get_next_sibling", &DwarfDie::get_next_sibling, nb::rv_policy::reference_internal,
             nb::sig("def get_next_sibling(self) -> DwarfDie | None"))
        .def("get_parent", &DwarfDie::get_parent, nb::rv_policy::reference_internal,
             nb::sig("def get_parent(self) -> DwarfDie | None"))
        .def("get_template_value_parameters", &DwarfDie::get_template_value_parameters)
        .def(
            "iter_children",
            [](DwarfDie& self) {
                return nb::make_iterator<nb::rv_policy::reference_internal>(nb::type<DwarfDie>(), "DieChildIterator",
                                                                            DieChildIterator(self.get_first_child()),
                                                                            DieChildIterator());
            },
            nb::rv_policy::reference_internal);

    nb::class_<DwarfInfo>(m, "DwarfInfo")
        .def("find_file_line_by_address", &DwarfInfo::find_file_line_by_address, nb::arg("address"))
        .def("get_die_by_name", &DwarfInfo::get_die_by_name, nb::arg("name"), nb::rv_policy::reference_internal,
             nb::sig("def get_die_by_name(self, name: str) -> DwarfDie | None"))
        .def("find_function_by_address", &DwarfInfo::find_function_by_address, nb::arg("address"),
             nb::rv_policy::reference_internal,
             nb::sig("def find_function_by_address(self, address: int) -> DwarfDie | None"))
        // keep_alive<0, 1>: the returned FrameDescription holds a raw
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
        // keep_alive<0, 1>: the returned ElfVariable holds shared_ptr
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

    nb::class_<FrameDescription>(m, "FrameDescription")
        .def_prop_ro("pc", &FrameDescription::get_pc)
        .def("read_register", &FrameDescription::read_register, nb::arg("register_index"), nb::arg("cfa"))
        .def("try_read_register", &FrameDescription::try_read_register, nb::arg("register_index"),
             nb::arg("cfa").none())
        .def("compute_cfa", &FrameDescription::compute_cfa, nb::arg("inner_cfa").none() = nb::none());

    // Snapshot of one frame on the callstack at a particular PC. Used as
    // the building block for FrameInspection — both for the
    // inspected frame and for each frame in the inner chain.
    nb::class_<ttexalens::native_elf::FrameSnapshot>(m, "FrameSnapshot")
        .def(nb::init<ttexalens::native_elf::FrameDescription, uint64_t, uint64_t>(), nb::arg("fde"), nb::arg("cfa"),
             nb::arg("pc"))
        .def_rw("fde", &ttexalens::native_elf::FrameSnapshot::fde)
        .def_rw("cfa", &ttexalens::native_elf::FrameSnapshot::cfa)
        .def_rw("pc", &ttexalens::native_elf::FrameSnapshot::pc);

    // Per-frame context for DwarfDie::read_value. Construct with the
    // active MemoryAccess, the inspected frame's snapshot, and the chain
    // of frames between the inspected one and live state (live first,
    // immediate-child-of-inspected last). For the top frame, pass an empty
    // inner_frames; read_register reads live GPRs in that case.
    nb::class_<FrameInspection>(m, "FrameInspection")
        .def(nb::init<std::shared_ptr<MemoryAccess>, std::optional<ttexalens::native_elf::FrameSnapshot>,
                      std::vector<ttexalens::native_elf::FrameSnapshot>>(),
             nb::arg("memory_access"), nb::arg("inspected").none() = nb::none(),
             nb::arg("inner_frames") = std::vector<ttexalens::native_elf::FrameSnapshot>{})
        .def("read_register", &FrameInspection::read_register, nb::arg("register_index"))
        .def("read_memory", &FrameInspection::read_memory, nb::arg("address"), nb::arg("register_size"))
        .def_prop_ro("cfa", &FrameInspection::get_cfa)
        .def_prop_ro("pc", &FrameInspection::get_pc);

    // Live view of a variable located by DWARF. Mirrors
    // ttexalens.elf.variable.ElfVariable: structural methods on the C++ side,
    // Python dunders wired here so call sites can keep doing `var.x.y[i] + 1`.
    nb::class_<ElfVariable>(m, "ElfVariable")
        .def(nb::init<ttexalens::native_elf::DwarfDiePtr, uint64_t, std::shared_ptr<MemoryAccess>>(),
             nb::arg("type_die"), nb::arg("address"), nb::arg("memory_access"))
        // Core structural / value methods.
        .def("get_member", &ElfVariable::get_member, nb::arg("member_name"))
        .def("dereference", &ElfVariable::dereference)
        .def("get_address", &ElfVariable::get_address)
        .def("get_size", &ElfVariable::get_size)
        .def("read_bytes",
             [](const ElfVariable& self) {
                 auto v = self.read_bytes();
                 return nb::bytes(reinterpret_cast<const char*>(v.data()), v.size());
             })
        .def("read_value", &ElfVariable::read_value)
        .def("write_value", &ElfVariable::write_value, nb::arg("value"), nb::arg("check_data_loss") = true)
        // Snapshots the variable's bytes; subsequent member/index walks read
        // from the cache instead of re-hitting live memory.
        .def("read", &ElfVariable::read)
        // Array helpers — materialize all elements eagerly.
        .def("as_list",
             [](const ElfVariable& self) {
                 const uint64_t n = self.get_length();
                 nb::list out;
                 for (uint64_t i = 0; i < n; ++i) {
                     out.append(nb::cast(self.get_index(static_cast<int64_t>(i))));
                 }
                 return out;
             })
        .def("as_value_list",
             [](const ElfVariable& self) {
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
             [](const ElfVariable& self, nb::handle key) -> ElfVariable {
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
                     throw nb::type_error("ElfVariable indices must be integers or strings");
                 }
             })
        // __getattr__ is only invoked when normal attribute lookup fails, so
        // bound C++ methods take precedence over struct members of the same
        // name (matching the Python implementation).
        .def("__getattr__", [](const ElfVariable& self, std::string_view name) { return self.get_member(name); })
        .def("__len__", &ElfVariable::get_length)
        .def("__iter__",
             [](const ElfVariable& self) {
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
            [](const ElfVariable& self, nb::handle other) -> nb::object {
                if (self.get_type_die()->get_tag() == DwarfDieTag::array_type) {
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
            [](const ElfVariable& self, nb::handle other) {
                return try_binop(self, other,
                                 [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a.not_equal(b)); });
            },
            nb::sig("def __ne__(self, other: object, /) -> bool"))
        .def("__lt__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a < b); });
             })
        .def("__le__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a <= b); });
             })
        .def("__gt__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a > b); });
             })
        .def("__ge__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other,
                                  [](nb::object a, nb::handle b) -> nb::object { return nb::cast(a >= b); });
             })
        // Arithmetic — read_value() + Python's native operator dispatch.
        .def("__add__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a + b; });
             })
        .def("__radd__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b + a; });
             })
        .def("__sub__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a - b; });
             })
        .def("__rsub__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b - a; });
             })
        .def("__mul__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a * b; });
             })
        .def("__rmul__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b * a; });
             })
        .def("__truediv__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a / b; });
             })
        .def("__rtruediv__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b / a; });
             })
        .def("__floordiv__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a.floor_div(b); });
             })
        .def("__rfloordiv__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b.floor_div(a); });
             })
        .def("__mod__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a % b; });
             })
        .def("__rmod__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b % a; });
             })
        // ** doesn't have an overloaded operator on nb::object, so go through
        // PyNumber_Power which mirrors Python's natural fallback to
        // NotImplemented when either operand doesn't support the operation.
        .def("__pow__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) -> nb::object {
                     PyObject* r = PyNumber_Power(a.ptr(), b.ptr(), Py_None);
                     if (r == nullptr) {
                         throw nb::python_error();
                     }
                     return nb::steal<nb::object>(r);
                 });
             })
        .def("__rpow__",
             [](const ElfVariable& self, nb::handle other) {
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
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a & b; });
             })
        .def("__rand__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b & a; });
             })
        .def("__or__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a | b; });
             })
        .def("__ror__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b | a; });
             })
        .def("__xor__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a ^ b; });
             })
        .def("__rxor__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b ^ a; });
             })
        .def("__lshift__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a << b; });
             })
        .def("__rlshift__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b << a; });
             })
        .def("__rshift__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return a >> b; });
             })
        .def("__rrshift__",
             [](const ElfVariable& self, nb::handle other) {
                 return try_binop(self, other, [](nb::object a, nb::handle b) { return b >> a; });
             })
        // Unary. Return is int | float at runtime — annotate the stubs so
        // call sites like `abs(-var.x)` typecheck.
        .def(
            "__neg__", [](const ElfVariable& self) { return -var_value_obj(self); },
            nb::sig("def __neg__(self) -> int | float"))
        .def(
            "__pos__",
            [](const ElfVariable& self) {
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
            [](const ElfVariable& self) { return nb::module_::import_("builtins").attr("abs")(var_value_obj(self)); },
            nb::sig("def __abs__(self) -> int | float"))
        .def(
            "__invert__", [](const ElfVariable& self) { return ~var_value_obj(self); },
            nb::sig("def __invert__(self) -> int"))
        // Truthiness — arrays are truthy when non-empty; scalars use the
        // underlying value (via Python's PyObject_IsTrue so int/float/bool
        // all work). Falls back to TypeMismatchException for composite types
        // (struct/union) that can't be read as a single value.
        .def("__bool__",
             [](const ElfVariable& self) {
                 if (self.get_type_die()->get_tag() == DwarfDieTag::array_type) {
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
             [](const ElfVariable& self) {
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
             [](const ElfVariable& self) -> Py_hash_t {
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
             [](const ElfVariable& self) -> std::string {
                 try {
                     nb::object val = var_value_obj(self);
                     if (self.get_type_die()->get_tag() == DwarfDieTag::enumeration_type) {
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
             [](const ElfVariable& self) {
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
                 return "ElfVariable(type_name='" + type_name + "', address=" + std::string(addr_buf) + value_info +
                        length_info + ")";
             })
        .def("__format__", [](const ElfVariable& self, std::string_view spec) {
            try {
                return nb::module_::import_("builtins")
                    .attr("format")(var_value_obj(self), nb::cast(std::string(spec)));
            } catch (const TypeMismatchException&) {
                return nb::module_::import_("builtins").attr("str")(nb::cast(self));
            }
        });
}
