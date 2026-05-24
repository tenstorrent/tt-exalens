// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <span>
#include <string>
#include <string_view>

// Forward declarations.
namespace ELFIO {
class section;
}  // namespace ELFIO

namespace ttexalens::native_elf {

class NativeDwarfInfo;

class NativeElfSection {
   public:
    explicit NativeElfSection(const ELFIO::section& section);

    std::string name() const;
    uint64_t address() const;
    uint64_t size() const;
    std::span<const std::byte> data() const;

   private:
    const ELFIO::section& section;
};

class NativeElfFile {
   public:
    class Impl;

    explicit NativeElfFile(const std::string& path);
    explicit NativeElfFile(const std::filesystem::path& path);

    static NativeElfFile from_bytes(std::span<const std::byte> data);

    // Defined out-of-line in elf_file.cpp because Impl needs to be complete
    // at the point of destruction.
    ~NativeElfFile();
    NativeElfFile(NativeElfFile&&) noexcept;
    NativeElfFile& operator=(NativeElfFile&&) noexcept;
    NativeElfFile(const NativeElfFile&) = delete;
    NativeElfFile& operator=(const NativeElfFile&) = delete;

    // Sections are enumerated by index (0 .. get_sections_count()-1). The
    // pointer-returning accessors hand out a non-owning pointer into the
    // internal cache; return nullptr when the index is out of range / the
    // name isn't found.
    size_t get_sections_count() const;
    const NativeElfSection* get_section(size_t index) const;
    const NativeElfSection* get_section_by_name(std::string_view name) const;

    bool has_dwarf_info(bool strict = false) const;
    // Returns a pointer to the libdwarf-backed handle, or nullptr when the
    // file has no usable DWARF info (stripped binaries, from_bytes loads,
    // libdwarf init failures). Pointer is owned by NativeElfFile.
    const NativeDwarfInfo* get_dwarf_info() const;

   private:
    explicit NativeElfFile(std::unique_ptr<Impl> impl);

    std::unique_ptr<Impl> impl;
};

}  // namespace ttexalens::native_elf
