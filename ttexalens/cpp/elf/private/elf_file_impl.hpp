// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <elfio/elfio.hpp>
#include <filesystem>
#include <fstream>
#include <optional>

#include "../dwarf_info.hpp"
#include "../elf_file.hpp"

namespace ttexalens::native_elf::details {

class NativeElfFileImpl : public std::enable_shared_from_this<NativeElfFileImpl> {
   public:
    NativeElfFileImpl() = default;
    virtual ~NativeElfFileImpl() = default;
    NativeElfFileImpl(const NativeElfFileImpl&) = delete;
    NativeElfFileImpl& operator=(const NativeElfFileImpl&) = delete;

    std::vector<NativeElfSection> sections;

    std::vector<NativeElfSymbol> read_symbol_table_section(std::string_view section_name);
    NativeDwarfInfo* get_dwarf_info();

   protected:
    void populate_sections();
    void try_open_dwarf();

    ELFIO::elfio elf;
    // Set by the derived constructor — file size on disk (PathImpl) or buffer
    // size (BytesImpl). Used by ElfObjAccess for libdwarf's filesize callback.
    uint64_t file_size = 0;
    std::optional<NativeDwarfInfo> dwarf_info;
    bool loaded_dwarf_info = false;

    friend class ElfObjAccess;
};

// ELF loaded from a filesystem path. Owns the ifstream so ELFIO can read
// lazily through it (file_stream declared before elf -> destroyed after).
class PathImpl : public NativeElfFileImpl {
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
class BytesImpl : public NativeElfFileImpl {
   public:
    explicit BytesImpl(std::span<const std::byte> data);

   private:
    std::vector<std::byte> buffer;
    SpanStreamBuf buf;
    std::istream stream;
};

}  // namespace ttexalens::native_elf::details
