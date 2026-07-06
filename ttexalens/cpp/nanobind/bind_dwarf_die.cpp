// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <nanobind/make_iterator.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/variant.h>
#include <nanobind/stl/vector.h>

#include <utility>

#include "bindings.hpp"
#include "dwarf_die.hpp"
#include "dwarf_frame.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

namespace {

// Forward iterator over a DIE's direct children, walking the
// first_child/next_sibling linked-list. Used by DwarfDie.iter_children's
// nb::make_iterator binding to produce a Python iterator for
// `for child in die.iter_children():`.
class DieChildIterator {
   public:
    DieChildIterator() = default;
    explicit DieChildIterator(DwarfDiePtr c) : current(std::move(c)) {}

    const DwarfDiePtr& operator*() const { return current; }
    DieChildIterator& operator++() {
        if (current) {
            current = current->get_next_sibling();
        }
        return *this;
    }
    bool operator==(const DieChildIterator& other) const { return current == other.current; }
    bool operator!=(const DieChildIterator& other) const { return !(*this == other); }

   private:
    DwarfDiePtr current;
};

}  // namespace

void bind_dwarf_die(nb::module_& m) {
    // DWARF DIE tag values. Use with:
    //   from ttexalens._native_ttexalens import DwarfDieTag as tag
    //   if die.tag == tag.subprogram: ...
    // Python sees a regular enum.Enum; comparisons against DwarfDie.tag
    // (also a DwarfDieTag instance) work directly.
    nb::enum_<DwarfDieTag>(m, "DwarfDieTag")
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
        .def("find_child_by_name",
             [](const DwarfDie& self, std::string_view name) { return self.find_child_by_name(name); }, nb::arg("name"),
             nb::rv_policy::reference_internal, nb::sig("def find_child_by_name(self, name: str) -> DwarfDie | None"))
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
}

}  // namespace ttexalens::native_elf::bindings
