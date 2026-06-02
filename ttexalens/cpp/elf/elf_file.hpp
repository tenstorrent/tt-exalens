// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include "dwarf_info.hpp"
#include "memory_access.hpp"

// Forward declarations.
namespace ELFIO {
class section;
}  // namespace ELFIO

namespace ttexalens::native_elf {

namespace details {
class ElfFileImpl;
}  // namespace details

class ElfSection {
   public:
    explicit ElfSection(const ELFIO::section& section);

    std::string name() const;
    uint64_t address() const;
    uint64_t size() const;
    std::span<const std::byte> data() const;

   private:
    const ELFIO::section& section;
};

// Standard ELF symbol type (st_info high nibble — ST_TYPE). Values mirror the
// STT_* constants defined in ELFIO's elf_types.hpp.
enum class ElfSymbolType : uint8_t {
    STT_NOTYPE = 0,
    STT_OBJECT = 1,
    STT_FUNC = 2,
    STT_SECTION = 3,
    STT_FILE = 4,
    STT_COMMON = 5,
    STT_TLS = 6,
    STT_LOOS = 10,
    STT_AMDGPU_HSA_KERNEL = 10,  // alias of STT_LOOS
    STT_HIOS = 12,
    STT_LOPROC = 13,
    STT_HIPROC = 15,
};

// Standard ELF symbol binding (st_info low nibble — ST_BIND). Values mirror
// the STB_* constants defined in ELFIO's elf_types.hpp.
enum class ElfSymbolBinding : uint8_t {
    STB_LOCAL = 0,
    STB_GLOBAL = 1,
    STB_WEAK = 2,
    STB_LOOS = 10,
    STB_HIOS = 12,
    STB_MULTIDEF = 13,
    STB_LOPROC = 13,  // alias of STB_MULTIDEF
    STB_HIPROC = 15,
};

struct ElfSymbol {
    std::string name;
    std::string demangled_name;
    uint64_t value;
    uint64_t size;
    ElfSymbolType type;
    ElfSymbolBinding bind;
};

class ElfFile {
   public:
    explicit ElfFile(const std::string& path);
    explicit ElfFile(const std::filesystem::path& path);

    // Constructs from an in-memory ELF buffer.
    // `elf_file_path` is recorded for diagnostics / re-loading
    // `load_address` (when given) sets the loaded_offset = code_load_address - load_address so subsequent PC
    // lookups can map live addresses to ELF addresses.
    static ElfFile from_bytes(std::span<const std::byte> data, std::string elf_file_path = "",
                              std::optional<uint64_t> load_address = std::nullopt);

    // Defined out-of-line in elf_file.cpp because Impl needs to be complete
    // at the point of destruction.
    ~ElfFile();
    ElfFile(ElfFile&&) noexcept;
    ElfFile& operator=(ElfFile&&) noexcept;
    ElfFile(const ElfFile&);
    ElfFile& operator=(const ElfFile&);

    // Sections are enumerated by index (0 .. get_sections_count()-1). The
    // pointer-returning accessors hand out a non-owning pointer into the
    // internal cache; return nullptr when the index is out of range / the
    // name isn't found.
    size_t get_sections_count() const;
    const ElfSection* get_section(size_t index) const;
    const ElfSection* get_section_by_name(std::string_view name) const;

    // Parses a symbol-table section (e.g. ".symtab" or ".dynsym") on demand
    // and returns all entries. Returns an empty vector when the section
    // doesn't exist. Not cached — each call re-parses.
    std::vector<ElfSymbol> read_symbol_table_section(std::string_view section_name) const;

    bool has_dwarf_info(bool strict = false) const;
    // Returns a pointer to the libdwarf-backed handle, or nullptr when the
    // file has no usable DWARF info (stripped binaries, from_bytes loads,
    // libdwarf init failures). Pointer is owned by ElfFile.
    const DwarfInfo* get_dwarf_info() const;

    const std::string& get_elf_file_path() const { return elf_file_path; }
    int64_t get_loaded_offset() const { return loaded_offset; }

    // Static base address of the code section (.text, falling back to
    // .firmware_text). Throws std::runtime_error if neither exists.
    uint64_t get_code_load_address() const;

    // Returns a copy of this ElfFile (sharing Impl) re-anchored so
    // that the supplied live load_address maps back to get_code_load_address
    // — i.e. with loaded_offset = get_code_load_address() - load_address.
    ElfFile with_load_address(uint64_t load_address) const;

    // Translates a live PC by loaded_offset and asks the DWARF FDE table
    // for the matching frame description. Returns nullopt when no DWARF
    // info is present or no FDE covers the PC.
    std::optional<FrameDescription> get_frame_description(uint64_t pc,
                                                          std::shared_ptr<MemoryAccess> memory_access) const;

    // Convenience pass-throughs to the underlying DwarfInfo so call
    // sites don't need to reach for `.dwarf_info` for every lookup.
    const ElfSymbol* find_symbol_by_name(std::string_view name) const;
    DwarfDiePtr find_die_by_name(std::string_view name) const;
    std::optional<uint64_t> get_enum_value(std::string_view name) const;
    DwarfDie::ConstantValue get_constant(std::string_view name) const;
    ElfVariable get_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const;
    ElfVariable read_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const;

   private:
    explicit ElfFile(std::shared_ptr<details::ElfFileImpl> impl, std::string elf_file_path = "",
                     int64_t loaded_offset = 0);

    friend class DwarfDie;

    std::shared_ptr<details::ElfFileImpl> impl;
    std::string elf_file_path;
    int64_t loaded_offset = 0;
};

}  // namespace ttexalens::native_elf
