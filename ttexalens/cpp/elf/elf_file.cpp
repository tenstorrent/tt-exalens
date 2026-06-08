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

ElfSection::ElfSection(const ELFIO::section& section) : section(section) {}

std::string ElfSection::name() const { return section.get_name(); }

uint16_t ElfSection::index() const { return static_cast<uint16_t>(section.get_index()); }

uint64_t ElfSection::address() const { return static_cast<uint64_t>(section.get_address()); }

uint64_t ElfSection::size() const { return static_cast<uint64_t>(section.get_size()); }

std::span<const std::byte> ElfSection::data() const {
    const char* p = section.get_data();
    size_t sz = static_cast<size_t>(section.get_size());
    if (p == nullptr || sz == 0) {
        return {};
    }
    return {reinterpret_cast<const std::byte*>(p), sz};
}

// Out-of-line so the shared_ptr<Impl> deleter sees the complete type.
ElfFile::~ElfFile() = default;
ElfFile::ElfFile(ElfFile&&) noexcept = default;
ElfFile& ElfFile::operator=(ElfFile&&) noexcept = default;
ElfFile::ElfFile(const ElfFile&) = default;
ElfFile& ElfFile::operator=(const ElfFile&) = default;

ElfFile::ElfFile(std::shared_ptr<details::ElfFileImpl> impl, std::string elf_file_path, int64_t loaded_offset)
    : impl(std::move(impl)), elf_file_path(std::move(elf_file_path)), loaded_offset(loaded_offset) {}

ElfFile::ElfFile(const std::string& path, std::optional<uint64_t> load_address)
    : ElfFile(std::filesystem::path(path), load_address) {}
ElfFile::ElfFile(const std::filesystem::path& path, std::optional<uint64_t> load_address)
    : ElfFile(std::make_shared<details::PathImpl>(path), path.string(), 0) {
    if (load_address.has_value()) {
        loaded_offset = static_cast<int64_t>(get_code_load_address()) - static_cast<int64_t>(*load_address);
    }
}

ElfFile ElfFile::from_bytes(std::span<const std::byte> data, std::string elf_file_path,
                            std::optional<uint64_t> load_address) {
    ElfFile elf(std::make_shared<details::BytesImpl>(data), std::move(elf_file_path), 0);
    if (load_address.has_value()) {
        elf.loaded_offset = static_cast<int64_t>(elf.get_code_load_address()) - static_cast<int64_t>(*load_address);
    }
    return elf;
}

size_t ElfFile::get_sections_count() const { return impl->sections.size(); }

const ElfSection* ElfFile::get_section(size_t index) const {
    if (index >= impl->sections.size()) {
        return nullptr;
    }
    return &impl->sections[index];
}

const ElfSection* ElfFile::get_section_by_name(std::string_view name) const {
    for (const auto& s : impl->sections) {
        if (s.name() == name) {
            return &s;
        }
    }
    return nullptr;
}

std::vector<ElfSymbol> ElfFile::read_symbol_table_section(std::string_view section_name) const {
    return impl->read_symbol_table_section(section_name);
}

bool ElfFile::has_dwarf_info(bool strict) const {
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

const DwarfInfo* ElfFile::get_dwarf_info() const { return impl->get_dwarf_info(); }

uint64_t ElfFile::get_code_load_address() const { return impl->get_entry(); }

ElfFile ElfFile::with_load_address(uint64_t load_address) const {
    ElfFile clone(*this);
    clone.loaded_offset = static_cast<int64_t>(get_code_load_address()) - static_cast<int64_t>(load_address);
    return clone;
}

std::optional<FrameDescription> ElfFile::get_frame_description(uint64_t pc,
                                                               std::shared_ptr<MemoryAccess> memory_access) const {
    const DwarfInfo* dwarf = get_dwarf_info();
    if (dwarf == nullptr) {
        return std::nullopt;
    }
    return dwarf->get_frame_description(pc + loaded_offset, std::move(memory_access));
}

const ElfSymbol* ElfFile::find_symbol_by_name(std::string_view name) const {
    const DwarfInfo* dwarf = get_dwarf_info();
    return dwarf == nullptr ? nullptr : dwarf->find_symbol_by_name(name);
}

DwarfDiePtr ElfFile::find_die_by_name(std::string_view name) const {
    const DwarfInfo* dwarf = get_dwarf_info();
    return dwarf == nullptr ? nullptr : dwarf->get_die_by_name(name);
}

std::optional<uint64_t> ElfFile::get_enum_value(std::string_view name) const {
    const DwarfInfo* dwarf = get_dwarf_info();
    return dwarf == nullptr ? std::nullopt : dwarf->get_enum_value(name);
}

DwarfDie::ConstantValue ElfFile::get_constant(std::string_view name) const {
    const DwarfInfo* dwarf = get_dwarf_info();
    return dwarf == nullptr ? DwarfDie::ConstantValue{} : dwarf->get_constant(name);
}

ElfVariable ElfFile::get_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const {
    const DwarfInfo* dwarf = get_dwarf_info();
    if (dwarf == nullptr) {
        throw std::runtime_error("ELF has no DWARF info; cannot resolve global '" + std::string(name) + "'");
    }
    return dwarf->get_global(name, std::move(memory_access));
}

ElfVariable ElfFile::read_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const {
    const DwarfInfo* dwarf = get_dwarf_info();
    if (dwarf == nullptr) {
        throw std::runtime_error("ELF has no DWARF info; cannot resolve global '" + std::string(name) + "'");
    }
    return dwarf->read_global(name, std::move(memory_access));
}

}  // namespace ttexalens::native_elf
