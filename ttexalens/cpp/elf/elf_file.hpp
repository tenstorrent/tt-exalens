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

// Forward declarations — the full ELFIO headers are only included in elf_file.cpp,
// keeping consumers of this header out of ELFIO's transitive include cost.
namespace ELFIO {
class elfio;
class section;
}  // namespace ELFIO

namespace ttexalens::native_elf {

class NativeElfSection {
   public:
    NativeElfSection(std::shared_ptr<ELFIO::elfio> elf, unsigned int section_index);

    std::string name() const;
    uint64_t address() const;
    uint64_t size() const;
    std::span<const std::byte> data() const;

   private:
    std::shared_ptr<ELFIO::elfio>
        elf;  // We need to hold onto the ELFIO instance to ensure the section reference remains valid.
    const ELFIO::section& section;
};

class NativeElfFile {
   public:
    explicit NativeElfFile(const std::string& path);
    explicit NativeElfFile(const std::filesystem::path& path);
    static NativeElfFile from_bytes(std::span<const std::byte> data);

    const std::vector<NativeElfSection>& sections() const;
    std::optional<NativeElfSection> get_section_by_name(std::string_view name) const;

   private:
    NativeElfFile();
    void populate_sections();

    std::shared_ptr<ELFIO::elfio> elf;
    std::vector<NativeElfSection> section_list;
};

}  // namespace ttexalens::native_elf
