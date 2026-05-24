// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <memory>

namespace ELFIO {
class elfio;
}  // namespace ELFIO

namespace ttexalens::native_elf {

// RAII wrapper around a libdwarf Dwarf_Debug handle. Construction opens the
// handle via dwarf_object_init_b backed by an ElfObjAccess adapter (no file
// re-open). Destruction closes via dwarf_object_finish.
//
// The held ElfObjAccess references the supplied ELFIO::elfio, so that elfio
// must outlive this NativeDwarfInfo.
class NativeDwarfInfo {
   public:
    NativeDwarfInfo(ELFIO::elfio& elf, uint64_t file_size);

    // Defined out-of-line in dwarf_info.cpp because Impl needs to be complete
    // at the point of destruction.
    ~NativeDwarfInfo();
    NativeDwarfInfo(NativeDwarfInfo&&) noexcept;
    NativeDwarfInfo& operator=(NativeDwarfInfo&&) noexcept;
    NativeDwarfInfo(const NativeDwarfInfo&) = delete;
    NativeDwarfInfo& operator=(const NativeDwarfInfo&) = delete;

   private:
    class Impl;
    std::unique_ptr<Impl> impl;
};

}  // namespace ttexalens::native_elf
