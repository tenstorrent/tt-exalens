// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "elf_file.hpp"

#include <elfio/elfio.hpp>
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

NativeElfFile::NativeElfFile(std::shared_ptr<details::NativeElfFileImpl> impl) : impl(std::move(impl)) {}

NativeElfFile::NativeElfFile(const std::string& path) : NativeElfFile(std::make_shared<details::PathImpl>(path)) {}
NativeElfFile::NativeElfFile(const std::filesystem::path& path)
    : NativeElfFile(std::make_shared<details::PathImpl>(path)) {}

NativeElfFile NativeElfFile::from_bytes(std::span<const std::byte> data) {
    return NativeElfFile(std::make_shared<details::BytesImpl>(data));
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

}  // namespace ttexalens::native_elf
