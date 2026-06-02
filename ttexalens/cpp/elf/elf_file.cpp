// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "elf_file.hpp"

#include <elfio/elfio.hpp>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>

#include "dwarf_info.hpp"
#include "private/elf_file_impl.hpp"

using namespace std::string_view_literals;

namespace ttexalens::native_elf {

NativeElfSection::NativeElfSection(const ELFIO::section& section) : section(section) {}

std::string NativeElfSection::name() const { return section.get_name(); }

uint64_t NativeElfSection::address() const { return static_cast<uint64_t>(section.get_address()); }

uint64_t NativeElfSection::size() const { return static_cast<uint64_t>(section.get_size()); }

std::span<const std::byte> NativeElfSection::data() const {
    const char* p = section.get_data();
    size_t sz = static_cast<size_t>(section.get_size());
    if (p == nullptr || sz == 0) {
        return {};
    }
    return {reinterpret_cast<const std::byte*>(p), sz};
}

// Out-of-line so the shared_ptr<Impl> deleter sees the complete type.
NativeElfFile::~NativeElfFile() = default;
NativeElfFile::NativeElfFile(NativeElfFile&&) noexcept = default;
NativeElfFile& NativeElfFile::operator=(NativeElfFile&&) noexcept = default;
NativeElfFile::NativeElfFile(const NativeElfFile&) = default;
NativeElfFile& NativeElfFile::operator=(const NativeElfFile&) = default;

NativeElfFile::NativeElfFile(std::shared_ptr<details::NativeElfFileImpl> impl, std::string elf_file_path,
                             int64_t loaded_offset)
    : impl(std::move(impl)), elf_file_path(std::move(elf_file_path)), loaded_offset(loaded_offset) {}

NativeElfFile::NativeElfFile(const std::string& path)
    : NativeElfFile(std::make_shared<details::PathImpl>(path), path) {}
NativeElfFile::NativeElfFile(const std::filesystem::path& path)
    : NativeElfFile(std::make_shared<details::PathImpl>(path), path.string()) {}

NativeElfFile NativeElfFile::from_bytes(std::span<const std::byte> data, std::string elf_file_path,
                                        std::optional<uint64_t> load_address) {
    NativeElfFile elf(std::make_shared<details::BytesImpl>(data), std::move(elf_file_path), 0);
    if (load_address.has_value()) {
        elf.loaded_offset = static_cast<int64_t>(elf.get_code_load_address()) - static_cast<int64_t>(*load_address);
    }
    return elf;
}

size_t NativeElfFile::get_sections_count() const { return impl->sections.size(); }

const NativeElfSection* NativeElfFile::get_section(size_t index) const {
    if (index >= impl->sections.size()) {
        return nullptr;
    }
    return &impl->sections[index];
}

const NativeElfSection* NativeElfFile::get_section_by_name(std::string_view name) const {
    for (const auto& s : impl->sections) {
        if (s.name() == name) {
            return &s;
        }
    }
    return nullptr;
}

std::vector<NativeElfSymbol> NativeElfFile::read_symbol_table_section(std::string_view section_name) const {
    return impl->read_symbol_table_section(section_name);
}

bool NativeElfFile::has_dwarf_info(bool strict) const {
    for (const auto& s : impl->sections) {
        const std::string n = s.name();
        if (n == ".debug_info"sv || n == ".zdebug_info"sv) {
            return true;
        }
        if (!strict && n == ".eh_frame"sv) {
            return true;
        }
    }
    return false;
}

const NativeDwarfInfo* NativeElfFile::get_dwarf_info() const { return impl->get_dwarf_info(); }

uint64_t NativeElfFile::get_code_load_address() const {
    const NativeElfSection* text = get_section_by_name(".text");
    if (text == nullptr) {
        text = get_section_by_name(".firmware_text");
    }
    if (text == nullptr) {
        throw std::runtime_error("Could not locate text section in " +
                                 (elf_file_path.empty() ? std::string("ELF") : elf_file_path));
    }
    return text->address();
}

NativeElfFile NativeElfFile::with_load_address(uint64_t load_address) const {
    NativeElfFile clone(*this);
    clone.loaded_offset = static_cast<int64_t>(get_code_load_address()) - static_cast<int64_t>(load_address);
    return clone;
}

std::optional<NativeFrameDescription> NativeElfFile::get_frame_description(
    uint64_t pc, std::shared_ptr<MemoryAccess> memory_access) const {
    const NativeDwarfInfo* dwarf = get_dwarf_info();
    if (dwarf == nullptr) {
        return std::nullopt;
    }
    return dwarf->get_frame_description(pc + loaded_offset, std::move(memory_access));
}

const NativeElfSymbol* NativeElfFile::find_symbol_by_name(std::string_view name) const {
    const NativeDwarfInfo* dwarf = get_dwarf_info();
    return dwarf == nullptr ? nullptr : dwarf->find_symbol_by_name(name);
}

NativeDwarfDiePtr NativeElfFile::find_die_by_name(std::string_view name) const {
    const NativeDwarfInfo* dwarf = get_dwarf_info();
    return dwarf == nullptr ? nullptr : dwarf->get_die_by_name(name);
}

std::optional<uint64_t> NativeElfFile::get_enum_value(std::string_view name) const {
    const NativeDwarfInfo* dwarf = get_dwarf_info();
    return dwarf == nullptr ? std::nullopt : dwarf->get_enum_value(name);
}

NativeDwarfDie::ConstantValue NativeElfFile::get_constant(std::string_view name) const {
    const NativeDwarfInfo* dwarf = get_dwarf_info();
    return dwarf == nullptr ? NativeDwarfDie::ConstantValue{} : dwarf->get_constant(name);
}

NativeElfVariable NativeElfFile::get_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const {
    const NativeDwarfInfo* dwarf = get_dwarf_info();
    if (dwarf == nullptr) {
        throw std::runtime_error("ELF has no DWARF info; cannot resolve global '" + std::string(name) + "'");
    }
    return dwarf->get_global(name, std::move(memory_access));
}

NativeElfVariable NativeElfFile::read_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const {
    const NativeDwarfInfo* dwarf = get_dwarf_info();
    if (dwarf == nullptr) {
        throw std::runtime_error("ELF has no DWARF info; cannot resolve global '" + std::string(name) + "'");
    }
    return dwarf->read_global(name, std::move(memory_access));
}

}  // namespace ttexalens::native_elf
