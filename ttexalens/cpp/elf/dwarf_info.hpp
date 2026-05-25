// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>

namespace ELFIO {
class elfio;
}  // namespace ELFIO

namespace ttexalens::native_elf {

// Source location for a particular program counter — returned by
// NativeDwarfInfo::find_file_line_by_address.
struct NativeDwarfFileLine {
    std::string file;
    uint32_t line;
    uint32_t column;
};

class NativeDwarfInfo {
   public:
    NativeDwarfInfo(ELFIO::elfio& elf, uint64_t file_size);

    ~NativeDwarfInfo();
    NativeDwarfInfo(const NativeDwarfInfo&) = delete;
    NativeDwarfInfo& operator=(const NativeDwarfInfo&) = delete;
    NativeDwarfInfo(NativeDwarfInfo&& other) noexcept;
    NativeDwarfInfo& operator=(NativeDwarfInfo&& other) noexcept;

    // Maps a PC to its source location via the .debug_line program. Returns
    // std::nullopt if no line entry covers the address.
    std::optional<NativeDwarfFileLine> find_file_line_by_address(uint64_t address) const;

   private:
    class Impl;
    std::unique_ptr<Impl> impl;
};

}  // namespace ttexalens::native_elf
