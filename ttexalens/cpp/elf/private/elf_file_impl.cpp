// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "elf_file_impl.hpp"

#include <cxxabi.h>

#include <cstdlib>

namespace ttexalens::native_elf::details {

std::vector<ElfSymbol> ElfFileImpl::read_symbol_table_section(std::string_view section_name) {
    std::vector<ElfSymbol> result;
    ELFIO::section* sym_sec = elf.sections[section_name];
    if (sym_sec == nullptr) {
        return result;
    }
    ELFIO::symbol_section_accessor accessor(elf, sym_sec);
    const auto n = accessor.get_symbols_num();
    result.reserve(n);
    for (ELFIO::Elf_Xword i = 0; i < n; ++i) {
        std::string name;
        ELFIO::Elf64_Addr value = 0;
        ELFIO::Elf_Xword size = 0;
        unsigned char bind = 0;
        unsigned char type = 0;
        ELFIO::Elf_Half section_index = 0;
        unsigned char other = 0;
        if (!accessor.get_symbol(i, name, value, size, bind, type, section_index, other)) {
            continue;
        }

        // Demangle the symbol name if possible.
        std::string demangled;
        if (!name.empty()) {
            int status = 0;
            char* d = abi::__cxa_demangle(name.c_str(), nullptr, nullptr, &status);
            if (status == 0 && d != nullptr) {
                demangled = d;
            }
            std::free(d);
        }
        result.push_back(ElfSymbol{
            std::move(name),
            std::move(demangled),
            static_cast<uint64_t>(value),
            static_cast<uint64_t>(size),
            static_cast<ElfSymbolType>(type),
            static_cast<ElfSymbolBinding>(bind),
            static_cast<uint16_t>(section_index),
        });
    }
    return result;
}

DwarfInfo* ElfFileImpl::get_dwarf_info() {
    if (!loaded_dwarf_info) {
        try_open_dwarf();
        loaded_dwarf_info = true;
    }

    return dwarf_info ? &*dwarf_info : nullptr;
}

void ElfFileImpl::populate_sections() {
    const size_t n = elf.sections.size();
    sections.reserve(n);
    for (size_t i = 0; i < n; ++i) {
        sections.emplace_back(*elf.sections[static_cast<unsigned int>(i)]);
    }

    section_by_index.reserve(n);
    for (const ElfSection& s : sections) {
        section_by_index.emplace(s.index(), &s);
    }
}

const ElfSection* ElfFileImpl::get_section_by_index(uint16_t index) const {
    auto it = section_by_index.find(index);
    return it == section_by_index.end() ? nullptr : it->second;
}

// Identical for path- and bytes-backed sources: both just need elf and
// file_size (which the derived ctor sets). Any failure (no DWARF info,
// libdwarf init error) leaves dwarf_info null.
void ElfFileImpl::try_open_dwarf() {
    try {
        dwarf_info.emplace(weak_from_this());
    } catch (...) {
    }
}

PathImpl::PathImpl(const std::filesystem::path& path) {
    file_stream.open(path, std::ios::in | std::ios::binary);
    if (!file_stream.is_open()) {
        throw std::runtime_error("Failed to open ELF file: " + path.string());
    }
    // Stash the file size for libdwarf's filesize callback before ELFIO
    // starts seeking inside the stream.
    file_stream.seekg(0, std::ios::end);
    file_size = static_cast<uint64_t>(file_stream.tellg());
    file_stream.seekg(0, std::ios::beg);
    if (!elf.load(file_stream, /*is_lazy=*/true)) {
        throw std::runtime_error("Failed to load ELF file: " + path.string());
    }
    populate_sections();
}

SpanStreamBuf::SpanStreamBuf(std::span<const std::byte> data) {
    char* begin = const_cast<char*>(reinterpret_cast<const char*>(data.data()));
    setg(begin, begin, begin + data.size());
}

SpanStreamBuf::pos_type SpanStreamBuf::seekoff(off_type off, std::ios_base::seekdir dir,
                                               std::ios_base::openmode which) {
    if ((which & std::ios_base::in) == 0) {
        return pos_type(off_type(-1));
    }
    char* base = eback();
    char* target = nullptr;
    switch (dir) {
        case std::ios_base::beg:
            target = base + off;
            break;
        case std::ios_base::cur:
            target = gptr() + off;
            break;
        case std::ios_base::end:
            target = egptr() + off;
            break;
        default:
            return pos_type(off_type(-1));
    }
    if (target < base || target > egptr()) {
        return pos_type(off_type(-1));
    }
    setg(base, target, egptr());
    return pos_type(target - base);
}

SpanStreamBuf::pos_type SpanStreamBuf::seekpos(pos_type pos, std::ios_base::openmode which) {
    return seekoff(off_type(pos), std::ios_base::beg, which);
}

BytesImpl::BytesImpl(std::span<const std::byte> data) : buffer(data.begin(), data.end()), buf(buffer), stream(&buf) {
    file_size = static_cast<uint64_t>(buffer.size());
    if (!elf.load(stream, /*is_lazy=*/true)) {
        throw std::runtime_error("Failed to load ELF from bytes");
    }
    populate_sections();
}

}  // namespace ttexalens::native_elf::details
