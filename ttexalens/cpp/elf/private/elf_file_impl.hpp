// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <elfio/elfio.hpp>
#include <filesystem>
#include <fstream>
#include <optional>
#include <unordered_map>

#include "../dwarf_info.hpp"
#include "../elf_file.hpp"

namespace ttexalens::native_elf::details {

class ElfFileImpl : public std::enable_shared_from_this<ElfFileImpl> {
   public:
    ElfFileImpl() = default;
    virtual ~ElfFileImpl() = default;
    ElfFileImpl(const ElfFileImpl&) = delete;
    ElfFileImpl& operator=(const ElfFileImpl&) = delete;

    std::vector<ElfSection> sections;

    std::vector<ElfSymbol> read_symbol_table_section(std::string_view section_name);
    DwarfInfo* get_dwarf_info();

    // Looks up a section by its ELF section header index (st_shndx), not by its
    // position in `sections`. Returns nullptr when no section carries that
    // index.
    const ElfSection* get_section_by_index(uint16_t index) const;

    // ELF header e_entry — the program's start-of-execution address.
    uint64_t get_entry() const { return static_cast<uint64_t>(elf.get_entry()); }

   protected:
    void populate_sections();
    void try_open_dwarf();

    ELFIO::elfio elf;
    // Set by the derived constructor — file size on disk (PathImpl) or buffer
    // size (BytesImpl). Used by ElfObjAccess for libdwarf's filesize callback.
    uint64_t file_size = 0;
    std::optional<DwarfInfo> dwarf_info;
    bool loaded_dwarf_info = false;

    std::unordered_map<uint16_t, const ElfSection*> section_by_index;

    friend class ElfObjAccess;
    friend class ttexalens::native_elf::ElfFile;
};

// ELF loaded from a filesystem path. Owns the ifstream so ELFIO can read
// lazily through it (file_stream declared before elf -> destroyed after).
class PathImpl : public ElfFileImpl {
   public:
    explicit PathImpl(const std::filesystem::path& path);

   private:
    std::ifstream file_stream;
};

// Read-only std::streambuf that views a contiguous span of bytes without copying.
class SpanStreamBuf : public std::streambuf {
   public:
    explicit SpanStreamBuf(std::span<const std::byte> data);

   protected:
    pos_type seekoff(off_type off, std::ios_base::seekdir dir, std::ios_base::openmode which) override;
    pos_type seekpos(pos_type pos, std::ios_base::openmode which) override;
};

// ELF loaded from an in-memory byte span. Holds a copy of the bytes plus the
// streambuf/istream that ELFIO reads through, so lazy section reads stay
// valid for the lifetime of this object.
//
// Member declaration order is significant: buffer → buf → stream, so on
// destruction stream goes first (just an istream object), then buf (a
// streambuf viewing buffer), then buffer (frees the bytes). ELFIO's internal
// `pstream` becomes dangling at that point but is never dereferenced again.
class BytesImpl : public ElfFileImpl {
   public:
    explicit BytesImpl(std::span<const std::byte> data);

   private:
    std::vector<std::byte> buffer;
    SpanStreamBuf buf;
    std::istream stream;
};

}  // namespace ttexalens::native_elf::details
