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

#include <cstddef>
#include <span>
#include <utility>

#include "bindings.hpp"
#include "elf_file.hpp"
#include "memory_access.hpp"

namespace nb = nanobind;

namespace ttexalens::native_elf::bindings {

namespace {

// Forward index-based iterator over an ElfFile's sections. Paired with
// nb::make_iterator so ElfFile.iter_sections() exposes its element
// type to Python as Iterator[ElfSection].
class ElfSectionIterator {
   public:
    ElfSectionIterator() = default;
    ElfSectionIterator(const ElfFile* elf, size_t index) : elf(elf), index(index) {}

    const ElfSection* operator*() const { return elf->get_section(index); }
    ElfSectionIterator& operator++() {
        ++index;
        return *this;
    }
    bool operator==(const ElfSectionIterator& other) const { return elf == other.elf && index == other.index; }
    bool operator!=(const ElfSectionIterator& other) const { return !(*this == other); }

   private:
    const ElfFile* elf = nullptr;
    size_t index = 0;
};

}  // namespace

void bind_elf_file(nb::module_& m) {
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
        .def_ro("bind", &ElfSymbol::bind)
        .def_ro("section_index", &ElfSymbol::section_index);

    nb::class_<ElfFile>(m, "ElfFile")
        .def(nb::init<const std::string&, std::optional<uint64_t>>(), nb::arg("path"),
             nb::arg("load_address").none() = nb::none())
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
             nb::call_guard<nb::gil_scoped_release>(), nb::rv_policy::reference_internal)
        .def("find_symbol_by_name", &ElfFile::find_symbol_by_name, nb::arg("name"), nb::rv_policy::reference_internal,
             nb::sig("def find_symbol_by_name(self, name: str) -> ElfSymbol | None"))
        .def("find_die_by_name", &ElfFile::find_die_by_name, nb::arg("name"), nb::rv_policy::reference_internal)
        .def("get_enum_value", &ElfFile::get_enum_value, nb::arg("name"))
        .def("get_constant", &ElfFile::get_constant, nb::arg("name"))
        .def("get_global", &ElfFile::get_global, nb::arg("name"), nb::arg("memory_access"),
             nb::rv_policy::reference_internal)
        .def("read_global", &ElfFile::read_global, nb::arg("name"), nb::arg("memory_access"),
             nb::rv_policy::reference_internal)
        .def("get_pointer_size", &ElfFile::get_pointer_size);
}

}  // namespace ttexalens::native_elf::bindings
