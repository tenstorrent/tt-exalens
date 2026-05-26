// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <dwarf.h>  // DW_TAG_* / DW_AT_* constants
#include <libdwarf.h>
#include <nanobind/nanobind.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/string_view.h>
#include <nanobind/stl/variant.h>
#include <nanobind/stl/vector.h>

#include <cstddef>
#include <span>

#include "dwarf_attribute.hpp"
#include "dwarf_cfi.hpp"
#include "dwarf_die.hpp"
#include "dwarf_info.hpp"
#include "elf_file.hpp"

namespace nb = nanobind;

using ttexalens::native_elf::NativeDwarfAttribute;
using ttexalens::native_elf::NativeDwarfDie;
using ttexalens::native_elf::NativeDwarfFileLine;
using ttexalens::native_elf::NativeDwarfInfo;
using ttexalens::native_elf::NativeElfFile;
using ttexalens::native_elf::NativeElfSection;
using ttexalens::native_elf::NativeElfSymbol;
using ttexalens::native_elf::NativeElfSymbolBinding;
using ttexalens::native_elf::NativeElfSymbolType;
using ttexalens::native_elf::NativeFrameDescription;

NB_MODULE(_native_ttexalens, m) {
    m.doc() = "Native code backend for ttexalens. Private API.";

    m.def(
        "libdwarf_version", []() { return dwarf_package_version(); },
        "Return the linked libdwarf version string. Smoke test that the native module is reachable.");

    // DWARF DIE tag values exposed as a Python-side namespace. Use with
    //   from ttexalens._native_ttexalens import NativeDwarfDieTag as tag
    //   if die.tag == tag.subprogram: ...
    // Values are plain ints (Dwarf_Half) so comparison against the int
    // returned by NativeDwarfDie.tag is direct.
    nb::module_ tag_mod = m.def_submodule("NativeDwarfDieTag", "DW_TAG_* constants for NativeDwarfDie.tag");
#define EXPOSE_TAG(short_name, dw_name) tag_mod.attr(short_name) = static_cast<int>(dw_name)
    EXPOSE_TAG("array_type", DW_TAG_array_type);
    EXPOSE_TAG("base_type", DW_TAG_base_type);
    EXPOSE_TAG("call_site", DW_TAG_call_site);
    EXPOSE_TAG("class_type", DW_TAG_class_type);
    EXPOSE_TAG("compile_unit", DW_TAG_compile_unit);
    EXPOSE_TAG("const_type", DW_TAG_const_type);
    EXPOSE_TAG("enumeration_type", DW_TAG_enumeration_type);
    EXPOSE_TAG("enumerator", DW_TAG_enumerator);
    EXPOSE_TAG("formal_parameter", DW_TAG_formal_parameter);
    EXPOSE_TAG("GNU_call_site", DW_TAG_GNU_call_site);
    EXPOSE_TAG("GNU_formal_parameter_pack", DW_TAG_GNU_formal_parameter_pack);
    EXPOSE_TAG("GNU_template_parameter_pack", DW_TAG_GNU_template_parameter_pack);
    EXPOSE_TAG("imported_declaration", DW_TAG_imported_declaration);
    EXPOSE_TAG("imported_module", DW_TAG_imported_module);
    EXPOSE_TAG("inheritance", DW_TAG_inheritance);
    EXPOSE_TAG("inlined_subroutine", DW_TAG_inlined_subroutine);
    EXPOSE_TAG("label", DW_TAG_label);
    EXPOSE_TAG("lexical_block", DW_TAG_lexical_block);
    EXPOSE_TAG("member", DW_TAG_member);
    EXPOSE_TAG("namespace", DW_TAG_namespace);
    EXPOSE_TAG("pointer_type", DW_TAG_pointer_type);
    EXPOSE_TAG("reference_type", DW_TAG_reference_type);
    EXPOSE_TAG("structure_type", DW_TAG_structure_type);
    EXPOSE_TAG("subprogram", DW_TAG_subprogram);
    EXPOSE_TAG("subrange_type", DW_TAG_subrange_type);
    EXPOSE_TAG("subroutine_type", DW_TAG_subroutine_type);
    EXPOSE_TAG("template_type_parameter", DW_TAG_template_type_parameter);
    EXPOSE_TAG("template_value_parameter", DW_TAG_template_value_parameter);
    EXPOSE_TAG("typedef", DW_TAG_typedef);
    EXPOSE_TAG("union_type", DW_TAG_union_type);
    EXPOSE_TAG("unspecified_parameters", DW_TAG_unspecified_parameters);
    EXPOSE_TAG("variable", DW_TAG_variable);
    EXPOSE_TAG("volatile_type", DW_TAG_volatile_type);
#undef EXPOSE_TAG

    // DW_AT_* constants exposed the same way as DW_TAG_*. Use with
    //   from ttexalens._native_ttexalens import NativeDwarfAttributeTag as at
    //   if at.declaration in die.attributes: ...
    nb::module_ at_mod =
        m.def_submodule("NativeDwarfAttributeTag", "DW_AT_* constants for keys in NativeDwarfDie.attributes");
#define EXPOSE_AT(short_name, dw_name) at_mod.attr(short_name) = static_cast<int>(dw_name)
    EXPOSE_AT("abstract_origin", DW_AT_abstract_origin);
    EXPOSE_AT("artificial", DW_AT_artificial);
    EXPOSE_AT("byte_size", DW_AT_byte_size);
    EXPOSE_AT("call_column", DW_AT_call_column);
    EXPOSE_AT("call_file", DW_AT_call_file);
    EXPOSE_AT("call_line", DW_AT_call_line);
    EXPOSE_AT("const_expr", DW_AT_const_expr);
    EXPOSE_AT("const_value", DW_AT_const_value);
    EXPOSE_AT("data_member_location", DW_AT_data_member_location);
    EXPOSE_AT("decl_column", DW_AT_decl_column);
    EXPOSE_AT("decl_file", DW_AT_decl_file);
    EXPOSE_AT("decl_line", DW_AT_decl_line);
    EXPOSE_AT("declaration", DW_AT_declaration);
    EXPOSE_AT("encoding", DW_AT_encoding);
    EXPOSE_AT("frame_base", DW_AT_frame_base);
    EXPOSE_AT("high_pc", DW_AT_high_pc);
    EXPOSE_AT("linkage_name", DW_AT_linkage_name);
    EXPOSE_AT("location", DW_AT_location);
    EXPOSE_AT("low_pc", DW_AT_low_pc);
    EXPOSE_AT("name", DW_AT_name);
    EXPOSE_AT("ranges", DW_AT_ranges);
    EXPOSE_AT("specification", DW_AT_specification);
    EXPOSE_AT("type", DW_AT_type);
    EXPOSE_AT("upper_bound", DW_AT_upper_bound);
#undef EXPOSE_AT

    // DW_FORM_* constants. The form tells you which std::variant alternative
    // NativeDwarfAttribute.value will hold:
    //   addr / addrx*           -> uint64_t (address)
    //   flag / flag_present     -> bool
    //   string / strp / strx*   -> str
    //   sdata                   -> int (signed)
    //   data*/udata/sec_offset  -> int (unsigned)
    //   ref* / ref_addr / ...   -> int (global .debug_info offset)
    //   block* / exprloc        -> bytes
    nb::module_ form_mod =
        m.def_submodule("NativeDwarfAttributeForm", "DW_FORM_* constants for NativeDwarfAttribute.form");
#define EXPOSE_FORM(short_name, dw_name) form_mod.attr(short_name) = static_cast<int>(dw_name)
    EXPOSE_FORM("addr", DW_FORM_addr);
    EXPOSE_FORM("addrx", DW_FORM_addrx);
    EXPOSE_FORM("addrx1", DW_FORM_addrx1);
    EXPOSE_FORM("addrx2", DW_FORM_addrx2);
    EXPOSE_FORM("addrx3", DW_FORM_addrx3);
    EXPOSE_FORM("addrx4", DW_FORM_addrx4);
    EXPOSE_FORM("GNU_addr_index", DW_FORM_GNU_addr_index);
    EXPOSE_FORM("block", DW_FORM_block);
    EXPOSE_FORM("block1", DW_FORM_block1);
    EXPOSE_FORM("block2", DW_FORM_block2);
    EXPOSE_FORM("block4", DW_FORM_block4);
    EXPOSE_FORM("data1", DW_FORM_data1);
    EXPOSE_FORM("data2", DW_FORM_data2);
    EXPOSE_FORM("data4", DW_FORM_data4);
    EXPOSE_FORM("data8", DW_FORM_data8);
    EXPOSE_FORM("data16", DW_FORM_data16);
    EXPOSE_FORM("exprloc", DW_FORM_exprloc);
    EXPOSE_FORM("flag", DW_FORM_flag);
    EXPOSE_FORM("flag_present", DW_FORM_flag_present);
    EXPOSE_FORM("implicit_const", DW_FORM_implicit_const);
    EXPOSE_FORM("line_strp", DW_FORM_line_strp);
    EXPOSE_FORM("loclistx", DW_FORM_loclistx);
    EXPOSE_FORM("ref1", DW_FORM_ref1);
    EXPOSE_FORM("ref2", DW_FORM_ref2);
    EXPOSE_FORM("ref4", DW_FORM_ref4);
    EXPOSE_FORM("ref8", DW_FORM_ref8);
    EXPOSE_FORM("ref_addr", DW_FORM_ref_addr);
    EXPOSE_FORM("ref_sig8", DW_FORM_ref_sig8);
    EXPOSE_FORM("ref_sup4", DW_FORM_ref_sup4);
    EXPOSE_FORM("ref_sup8", DW_FORM_ref_sup8);
    EXPOSE_FORM("ref_udata", DW_FORM_ref_udata);
    EXPOSE_FORM("GNU_ref_alt", DW_FORM_GNU_ref_alt);
    EXPOSE_FORM("rnglistx", DW_FORM_rnglistx);
    EXPOSE_FORM("sdata", DW_FORM_sdata);
    EXPOSE_FORM("sec_offset", DW_FORM_sec_offset);
    EXPOSE_FORM("string", DW_FORM_string);
    EXPOSE_FORM("strp", DW_FORM_strp);
    EXPOSE_FORM("strp_sup", DW_FORM_strp_sup);
    EXPOSE_FORM("GNU_strp_alt", DW_FORM_GNU_strp_alt);
    EXPOSE_FORM("strx", DW_FORM_strx);
    EXPOSE_FORM("strx1", DW_FORM_strx1);
    EXPOSE_FORM("strx2", DW_FORM_strx2);
    EXPOSE_FORM("strx3", DW_FORM_strx3);
    EXPOSE_FORM("strx4", DW_FORM_strx4);
    EXPOSE_FORM("GNU_str_index", DW_FORM_GNU_str_index);
    EXPOSE_FORM("udata", DW_FORM_udata);
#undef EXPOSE_FORM

    nb::class_<NativeDwarfAttribute>(m, "NativeDwarfAttribute")
        .def_prop_ro("tag", &NativeDwarfAttribute::get_tag)
        .def_prop_ro("form", &NativeDwarfAttribute::get_form)
        // Variant alternatives map to bool / int / str / bytes / None. Default
        // nanobind would expose std::vector<uint8_t> as a Python list[int],
        // but DW_FORM_block* / exprloc payloads are conceptually opaque byte
        // strings — hand them out as nb::bytes so callers don't have to
        // wrap with bytes(...) before struct.unpack / hash / etc.
        .def_prop_ro("value", [](const NativeDwarfAttribute& a) -> nb::object {
            return std::visit(
                [](const auto& v) -> nb::object {
                    using T = std::decay_t<decltype(v)>;
                    if constexpr (std::is_same_v<T, std::monostate>) {
                        return nb::none();
                    } else if constexpr (std::is_same_v<T, std::vector<uint8_t>>) {
                        return nb::bytes(reinterpret_cast<const char*>(v.data()), v.size());
                    } else {
                        return nb::cast(v);  // bool, ints, double, str
                    }
                },
                a.get_value());
        });

    nb::class_<NativeElfSection>(m, "NativeElfSection")
        .def_prop_ro("name", &NativeElfSection::name)
        .def_prop_ro("address", &NativeElfSection::address)
        .def_prop_ro("size", &NativeElfSection::size)
        .def_prop_ro("data", [](const NativeElfSection& s) {
            std::span<const std::byte> sp = s.data();
            return nb::bytes(reinterpret_cast<const char*>(sp.data()), sp.size());
        });

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
            [](nb::bytes data) {
                return NativeElfFile::from_bytes(
                    std::span<const std::byte>(reinterpret_cast<const std::byte*>(data.c_str()), data.size()));
            },
            nb::arg("data"))
        .def("get_sections_count", &NativeElfFile::get_sections_count)
        .def("get_section", &NativeElfFile::get_section, nb::arg("index"), nb::rv_policy::reference_internal)
        .def("get_section_by_name", &NativeElfFile::get_section_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal)
        .def("read_symbol_table_section", &NativeElfFile::read_symbol_table_section, nb::arg("section_name"),
             nb::call_guard<nb::gil_scoped_release>())
        .def("has_dwarf_info", &NativeElfFile::has_dwarf_info, nb::arg("strict") = false)
        .def("get_dwarf_info", &NativeElfFile::get_dwarf_info, nb::rv_policy::reference_internal);

    nb::class_<NativeDwarfFileLine>(m, "NativeDwarfFileLine")
        .def_prop_ro("file", [](const NativeDwarfFileLine& f) -> std::string_view { return f.file; })
        .def_ro("line", &NativeDwarfFileLine::line)
        .def_ro("column", &NativeDwarfFileLine::column);

    nb::class_<NativeDwarfDie>(m, "NativeDwarfDie")
        .def_prop_ro("name", &NativeDwarfDie::get_name)
        .def_prop_ro("offset", &NativeDwarfDie::get_offset)
        .def_prop_ro("tag", &NativeDwarfDie::get_tag)
        .def_prop_ro("attributes", &NativeDwarfDie::get_attributes, nb::rv_policy::reference_internal)
        .def("get_attribute", &NativeDwarfDie::get_attribute, nb::arg("attribute_tag"),
             nb::rv_policy::reference_internal)
        .def("get_constant_value",
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
             })
        .def("get_resolved_type", &NativeDwarfDie::get_resolved_type, nb::rv_policy::reference_internal)
        .def("find_child_by_name", &NativeDwarfDie::find_child_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal)
        .def("get_die_from_attribute", &NativeDwarfDie::get_die_from_attribute, nb::arg("attribute_tag"),
             nb::rv_policy::reference_internal)
        .def("has_attribute", &NativeDwarfDie::has_attribute, nb::arg("attribute_tag"))
        .def("is_declaration", &NativeDwarfDie::is_declaration)
        .def("get_address_ranges", &NativeDwarfDie::get_address_ranges)
        .def("get_first_child", &NativeDwarfDie::get_first_child, nb::rv_policy::reference_internal)
        .def("get_next_sibling", &NativeDwarfDie::get_next_sibling, nb::rv_policy::reference_internal)
        .def("get_parent", &NativeDwarfDie::get_parent, nb::rv_policy::reference_internal);

    nb::class_<NativeDwarfInfo>(m, "NativeDwarfInfo")
        .def("find_file_line_by_address", &NativeDwarfInfo::find_file_line_by_address, nb::arg("address"))
        .def("get_die_by_name", &NativeDwarfInfo::get_die_by_name, nb::arg("name"), nb::rv_policy::reference_internal)
        .def("find_function_by_address", &NativeDwarfInfo::find_function_by_address, nb::arg("address"),
             nb::rv_policy::reference_internal)
        .def("get_frame_description", &NativeDwarfInfo::get_frame_description, nb::arg("pc"), nb::arg("read_gpr"),
             nb::arg("read_memory"));

    nb::class_<NativeFrameDescription>(m, "NativeFrameDescription")
        .def_prop_ro("pc", &NativeFrameDescription::get_pc)
        .def("read_register", &NativeFrameDescription::read_register, nb::arg("register_index"), nb::arg("cfa"))
        .def("try_read_register", &NativeFrameDescription::try_read_register, nb::arg("register_index"),
             nb::arg("cfa").none())
        .def("read_previous_cfa", &NativeFrameDescription::read_previous_cfa, nb::arg("current_cfa").none());
}
