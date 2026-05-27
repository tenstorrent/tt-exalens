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

#include <cstddef>
#include <span>

#include "dwarf_attribute.hpp"
#include "dwarf_cfi.hpp"
#include "dwarf_die.hpp"
#include "dwarf_info.hpp"
#include "elf_file.hpp"

namespace nb = nanobind;

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
using ttexalens::native_elf::NativeFrameDescription;

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

}  // namespace

NB_MODULE(_native_ttexalens, m) {
    m.doc() = "Native code backend for ttexalens. Private API.";

    m.def(
        "libdwarf_version", []() { return dwarf_package_version(); },
        "Return the linked libdwarf version string. Smoke test that the native module is reachable.");

    // DWARF DIE tag values. Use with:
    //   from ttexalens._native_ttexalens import NativeDwarfDieTag as tag
    //   if die.tag == tag.subprogram: ...
    // Python sees a regular enum.Enum; comparisons against NativeDwarfDie.tag
    // (also a NativeDwarfDieTag instance) work directly.
    nb::enum_<ttexalens::native_elf::NativeDwarfDieTag>(m, "NativeDwarfDieTag")
        .value("array_type", NativeDwarfDieTag::array_type)
        .value("base_type", NativeDwarfDieTag::base_type)
        .value("call_site", NativeDwarfDieTag::call_site)
        .value("class_type", NativeDwarfDieTag::class_type)
        .value("compile_unit", NativeDwarfDieTag::compile_unit)
        .value("const_type", NativeDwarfDieTag::const_type)
        .value("enumeration_type", NativeDwarfDieTag::enumeration_type)
        .value("enumerator", NativeDwarfDieTag::enumerator)
        .value("formal_parameter", NativeDwarfDieTag::formal_parameter)
        .value("GNU_call_site", NativeDwarfDieTag::GNU_call_site)
        .value("GNU_formal_parameter_pack", NativeDwarfDieTag::GNU_formal_parameter_pack)
        .value("GNU_template_parameter_pack", NativeDwarfDieTag::GNU_template_parameter_pack)
        .value("imported_declaration", NativeDwarfDieTag::imported_declaration)
        .value("imported_module", NativeDwarfDieTag::imported_module)
        .value("inheritance", NativeDwarfDieTag::inheritance)
        .value("inlined_subroutine", NativeDwarfDieTag::inlined_subroutine)
        .value("label", NativeDwarfDieTag::label)
        .value("lexical_block", NativeDwarfDieTag::lexical_block)
        .value("member", NativeDwarfDieTag::member)
        .value("namespace", NativeDwarfDieTag::namespace_)
        .value("pointer_type", NativeDwarfDieTag::pointer_type)
        .value("reference_type", NativeDwarfDieTag::reference_type)
        .value("structure_type", NativeDwarfDieTag::structure_type)
        .value("subprogram", NativeDwarfDieTag::subprogram)
        .value("subrange_type", NativeDwarfDieTag::subrange_type)
        .value("subroutine_type", NativeDwarfDieTag::subroutine_type)
        .value("template_type_parameter", NativeDwarfDieTag::template_type_parameter)
        .value("template_value_parameter", NativeDwarfDieTag::template_value_parameter)
        .value("typedef", NativeDwarfDieTag::typedef_)
        .value("union_type", NativeDwarfDieTag::union_type)
        .value("unspecified_parameters", NativeDwarfDieTag::unspecified_parameters)
        .value("variable", NativeDwarfDieTag::variable)
        .value("volatile_type", NativeDwarfDieTag::volatile_type);

    // DW_AT_* attribute tags. Use with:
    //   from ttexalens._native_ttexalens import NativeDwarfAttributeTag as at
    //   die.get_attribute(at.declaration)
    nb::enum_<NativeDwarfAttributeTag>(m, "NativeDwarfAttributeTag")
        .value("abstract_origin", NativeDwarfAttributeTag::abstract_origin)
        .value("artificial", NativeDwarfAttributeTag::artificial)
        .value("byte_size", NativeDwarfAttributeTag::byte_size)
        .value("call_column", NativeDwarfAttributeTag::call_column)
        .value("call_file", NativeDwarfAttributeTag::call_file)
        .value("call_line", NativeDwarfAttributeTag::call_line)
        .value("const_expr", NativeDwarfAttributeTag::const_expr)
        .value("const_value", NativeDwarfAttributeTag::const_value)
        .value("data_member_location", NativeDwarfAttributeTag::data_member_location)
        .value("decl_column", NativeDwarfAttributeTag::decl_column)
        .value("decl_file", NativeDwarfAttributeTag::decl_file)
        .value("decl_line", NativeDwarfAttributeTag::decl_line)
        .value("declaration", NativeDwarfAttributeTag::declaration)
        .value("encoding", NativeDwarfAttributeTag::encoding)
        .value("frame_base", NativeDwarfAttributeTag::frame_base)
        .value("high_pc", NativeDwarfAttributeTag::high_pc)
        .value("linkage_name", NativeDwarfAttributeTag::linkage_name)
        .value("location", NativeDwarfAttributeTag::location)
        .value("low_pc", NativeDwarfAttributeTag::low_pc)
        .value("name", NativeDwarfAttributeTag::name)
        .value("ranges", NativeDwarfAttributeTag::ranges)
        .value("specification", NativeDwarfAttributeTag::specification)
        .value("type", NativeDwarfAttributeTag::type)
        .value("upper_bound", NativeDwarfAttributeTag::upper_bound);

    // DW_FORM_* — attribute form. Determines which std::variant alternative
    // NativeDwarfAttribute.value will hold (see dwarf_attribute.hpp).
    nb::enum_<NativeDwarfAttributeForm>(m, "NativeDwarfAttributeForm")
        .value("addr", NativeDwarfAttributeForm::addr)
        .value("addrx", NativeDwarfAttributeForm::addrx)
        .value("addrx1", NativeDwarfAttributeForm::addrx1)
        .value("addrx2", NativeDwarfAttributeForm::addrx2)
        .value("addrx3", NativeDwarfAttributeForm::addrx3)
        .value("addrx4", NativeDwarfAttributeForm::addrx4)
        .value("GNU_addr_index", NativeDwarfAttributeForm::GNU_addr_index)
        .value("block", NativeDwarfAttributeForm::block)
        .value("block1", NativeDwarfAttributeForm::block1)
        .value("block2", NativeDwarfAttributeForm::block2)
        .value("block4", NativeDwarfAttributeForm::block4)
        .value("data1", NativeDwarfAttributeForm::data1)
        .value("data2", NativeDwarfAttributeForm::data2)
        .value("data4", NativeDwarfAttributeForm::data4)
        .value("data8", NativeDwarfAttributeForm::data8)
        .value("data16", NativeDwarfAttributeForm::data16)
        .value("exprloc", NativeDwarfAttributeForm::exprloc)
        .value("flag", NativeDwarfAttributeForm::flag)
        .value("flag_present", NativeDwarfAttributeForm::flag_present)
        .value("implicit_const", NativeDwarfAttributeForm::implicit_const)
        .value("line_strp", NativeDwarfAttributeForm::line_strp)
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
        .value("GNU_ref_alt", NativeDwarfAttributeForm::GNU_ref_alt)
        .value("rnglistx", NativeDwarfAttributeForm::rnglistx)
        .value("sdata", NativeDwarfAttributeForm::sdata)
        .value("sec_offset", NativeDwarfAttributeForm::sec_offset)
        .value("string", NativeDwarfAttributeForm::string)
        .value("strp", NativeDwarfAttributeForm::strp)
        .value("strp_sup", NativeDwarfAttributeForm::strp_sup)
        .value("GNU_strp_alt", NativeDwarfAttributeForm::GNU_strp_alt)
        .value("strx", NativeDwarfAttributeForm::strx)
        .value("strx1", NativeDwarfAttributeForm::strx1)
        .value("strx2", NativeDwarfAttributeForm::strx2)
        .value("strx3", NativeDwarfAttributeForm::strx3)
        .value("strx4", NativeDwarfAttributeForm::strx4)
        .value("GNU_str_index", NativeDwarfAttributeForm::GNU_str_index)
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
        .def("get_section", &NativeElfFile::get_section, nb::arg("index"), nb::rv_policy::reference_internal)
        .def("get_section_by_name", &NativeElfFile::get_section_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal)
        .def("read_symbol_table_section", &NativeElfFile::read_symbol_table_section, nb::arg("section_name"),
             nb::call_guard<nb::gil_scoped_release>())
        .def("has_dwarf_info", &NativeElfFile::has_dwarf_info, nb::arg("strict") = false)
        .def_prop_ro("dwarf_info", &NativeElfFile::get_dwarf_info, nb::rv_policy::reference_internal,
                     nb::call_guard<nb::gil_scoped_release>());

    nb::class_<NativeDwarfFileLine>(m, "NativeDwarfFileLine")
        .def_prop_ro("file", [](const NativeDwarfFileLine& f) -> std::string_view { return f.file; })
        .def_ro("line", &NativeDwarfFileLine::line)
        .def_ro("column", &NativeDwarfFileLine::column);

    nb::class_<NativeDwarfDie>(m, "NativeDwarfDie")
        .def_prop_ro("name", &NativeDwarfDie::get_name)
        .def_prop_ro("linkage_name", &NativeDwarfDie::get_linkage_name)
        .def_prop_ro("offset", &NativeDwarfDie::get_offset)
        .def_prop_ro("tag", &NativeDwarfDie::get_tag)
        .def_prop_ro("attributes", &NativeDwarfDie::get_attributes, nb::rv_policy::reference_internal)
        .def_prop_ro("is_signed_type", &NativeDwarfDie::is_signed_type)
        .def_prop_ro("is_declaration", &NativeDwarfDie::is_declaration)
        .def("get_attribute", &NativeDwarfDie::get_attribute, nb::arg("attribute_tag"),
             nb::rv_policy::reference_internal)
        .def("has_attribute", &NativeDwarfDie::has_attribute, nb::arg("attribute_tag"))
        .def("get_path", &NativeDwarfDie::get_path)
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
        .def("get_resolved_type", &NativeDwarfDie::get_resolved_type, nb::rv_policy::reference_internal)
        .def("get_dereference_type", &NativeDwarfDie::get_dereference_type, nb::rv_policy::reference_internal)
        .def("get_array_element_type", &NativeDwarfDie::get_array_element_type, nb::rv_policy::reference_internal)
        .def("find_child_by_name", &NativeDwarfDie::find_child_by_name, nb::arg("name"),
             nb::rv_policy::reference_internal)
        .def("get_die_from_attribute", &NativeDwarfDie::get_die_from_attribute, nb::arg("attribute_tag"),
             nb::rv_policy::reference_internal)
        .def("get_address_ranges", &NativeDwarfDie::get_address_ranges)
        .def("get_first_child", &NativeDwarfDie::get_first_child, nb::rv_policy::reference_internal)
        .def("get_next_sibling", &NativeDwarfDie::get_next_sibling, nb::rv_policy::reference_internal)
        .def("get_parent", &NativeDwarfDie::get_parent, nb::rv_policy::reference_internal)
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
