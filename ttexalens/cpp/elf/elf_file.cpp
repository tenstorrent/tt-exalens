// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "elf_file.hpp"

#include <elfio/elfio.hpp>
#include <fstream>
#include <ios>
#include <istream>
#include <optional>
#include <stdexcept>
#include <streambuf>
#include <string_view>
#include <utility>
#include <vector>

#include "dwarf_info.hpp"

using namespace std::string_view_literals;

namespace ttexalens::native_elf {

namespace {

// Read-only std::streambuf that views a contiguous span of bytes without copying.
class SpanStreamBuf : public std::streambuf {
   public:
    explicit SpanStreamBuf(std::span<const std::byte> data) {
        char* begin = const_cast<char*>(reinterpret_cast<const char*>(data.data()));
        setg(begin, begin, begin + data.size());
    }

   protected:
    pos_type seekoff(off_type off, std::ios_base::seekdir dir, std::ios_base::openmode which) override {
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

    pos_type seekpos(pos_type pos, std::ios_base::openmode which) override {
        return seekoff(off_type(pos), std::ios_base::beg, which);
    }
};

}  // namespace

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

class NativeElfFile::Impl {
   public:
    Impl() = default;
    virtual ~Impl() = default;
    Impl(const Impl&) = delete;
    Impl& operator=(const Impl&) = delete;

    std::vector<NativeElfSection> sections;

    std::vector<NativeElfSymbol> read_symbol_table_section(std::string_view section_name) {
        std::vector<NativeElfSymbol> result;
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
            result.push_back(NativeElfSymbol{
                std::move(name),
                static_cast<uint64_t>(value),
                static_cast<uint64_t>(size),
                static_cast<NativeElfSymbolType>(type),
                static_cast<NativeElfSymbolBinding>(bind),
            });
        }
        return result;
    }

    NativeDwarfInfo* get_dwarf_info() {
        if (!loaded_dwarf_info) {
            try_open_dwarf();
            loaded_dwarf_info = true;
        }

        return dwarf_info ? &*dwarf_info : nullptr;
    }

   protected:
    void populate_sections() {
        const size_t n = elf.sections.size();
        sections.reserve(n);
        for (size_t i = 0; i < n; ++i) {
            sections.emplace_back(*elf.sections[static_cast<unsigned int>(i)]);
        }
    }

    // Identical for path- and bytes-backed sources: both just need elf and
    // file_size (which the derived ctor sets). Any failure (no DWARF info,
    // libdwarf init error) leaves dwarf_info null.
    void try_open_dwarf() {
        try {
            dwarf_info.emplace(elf, file_size);
        } catch (...) {
        }
    }

    ELFIO::elfio elf;
    // Set by the derived constructor — file size on disk (PathImpl) or buffer
    // size (BytesImpl). Used by ElfObjAccess for libdwarf's filesize callback.
    uint64_t file_size = 0;
    std::optional<NativeDwarfInfo> dwarf_info;
    bool loaded_dwarf_info = false;
};

namespace {

// ELF loaded from a filesystem path. Owns the ifstream so ELFIO can read
// lazily through it (file_stream declared before elf -> destroyed after).
class PathImpl : public NativeElfFile::Impl {
   public:
    explicit PathImpl(const std::string& path) {
        file_stream.open(path, std::ios::in | std::ios::binary);
        if (!file_stream.is_open()) {
            throw std::runtime_error("Failed to open ELF file: " + path);
        }
        // Stash the file size for libdwarf's filesize callback before ELFIO
        // starts seeking inside the stream.
        file_stream.seekg(0, std::ios::end);
        file_size = static_cast<uint64_t>(file_stream.tellg());
        file_stream.seekg(0, std::ios::beg);
        if (!elf.load(file_stream, /*is_lazy=*/true)) {
            throw std::runtime_error("Failed to load ELF file: " + path);
        }
        populate_sections();
    }

   private:
    std::ifstream file_stream;
};

// ELF loaded from an in-memory byte span. Holds a copy of the bytes plus the
// streambuf/istream that ELFIO reads through, so lazy section reads stay
// valid for the lifetime of this object.
//
// Member declaration order is significant: buffer → buf → stream, so on
// destruction stream goes first (just an istream object), then buf (a
// streambuf viewing buffer), then buffer (frees the bytes). ELFIO's internal
// `pstream` becomes dangling at that point but is never dereferenced again.
class BytesImpl : public NativeElfFile::Impl {
   public:
    explicit BytesImpl(std::span<const std::byte> data) : buffer(data.begin(), data.end()), buf(buffer), stream(&buf) {
        file_size = static_cast<uint64_t>(buffer.size());
        if (!elf.load(stream, /*is_lazy=*/true)) {
            throw std::runtime_error("Failed to load ELF from bytes");
        }
        populate_sections();
    }

   private:
    std::vector<std::byte> buffer;
    SpanStreamBuf buf;
    std::istream stream;
};

}  // namespace

// Out-of-line so the unique_ptr<Impl> deleter sees the complete type.
NativeElfFile::~NativeElfFile() = default;
NativeElfFile::NativeElfFile(NativeElfFile&&) noexcept = default;
NativeElfFile& NativeElfFile::operator=(NativeElfFile&&) noexcept = default;

NativeElfFile::NativeElfFile(std::unique_ptr<Impl> impl) : impl(std::move(impl)) {}

NativeElfFile::NativeElfFile(const std::string& path) : NativeElfFile(std::make_unique<PathImpl>(path)) {}
NativeElfFile::NativeElfFile(const std::filesystem::path& path)
    : NativeElfFile(std::make_unique<PathImpl>(path.string())) {}

NativeElfFile NativeElfFile::from_bytes(std::span<const std::byte> data) {
    return NativeElfFile(std::make_unique<BytesImpl>(data));
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
