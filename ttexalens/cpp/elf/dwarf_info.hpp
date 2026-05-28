// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <string_view>

#include "dwarf_die.hpp"
#include "dwarf_frame.hpp"

namespace ttexalens::native_elf {

namespace details {
class NativeElfFileImpl;
class NativeDwarfInfoImpl;
}  // namespace details

class NativeDwarfInfo {
   public:
    NativeDwarfInfo(std::weak_ptr<details::NativeElfFileImpl> elf_impl);

    ~NativeDwarfInfo();
    NativeDwarfInfo(const NativeDwarfInfo&) = delete;
    NativeDwarfInfo& operator=(const NativeDwarfInfo&) = delete;
    NativeDwarfInfo(NativeDwarfInfo&& other) noexcept;
    NativeDwarfInfo& operator=(NativeDwarfInfo&& other) noexcept;

    // Maps a PC to its source location via the .debug_line program. Returns
    // std::nullopt if no line entry covers the address.
    std::optional<NativeDwarfFileLine> find_file_line_by_address(uint64_t address) const;

    // Resolves a "Foo::Bar::baz" path against every CU's DIE tree and returns
    // the first non-declaration match (or a declaration as fallback). Follows
    // DW_AT_abstract_origin / DW_AT_specification one hop when present.
    NativeDwarfDiePtr get_die_by_name(std::string_view name) const;

    // Walks every CU and recursively drills into children to find the DIE
    // whose address range contains `address`. When multiple CUs match (e.g.
    // overlapping subprograms from inlining), the DIE with the narrowest
    // range wins. Returns nullptr if no DIE covers the address.
    NativeDwarfDiePtr find_function_by_address(uint64_t address) const;

    // Locates the FDE covering `pc` in .debug_frame (falling back to
    // .eh_frame) and returns a NativeFrameDescription bound to `memory_access`.
    // NativeFrameDescription's methods (read_register / read_previous_cfa)
    // route GPR reads through `memory_access->read_register(...)` and stack
    // memory reads through `memory_access->read(...)` to fetch live machine
    // state. Returns nullopt if no FDE covers `pc`.
    std::optional<NativeFrameDescription> get_frame_description(uint64_t pc,
                                                                std::shared_ptr<MemoryAccess> memory_access) const;

   private:
    std::shared_ptr<details::NativeDwarfInfoImpl> impl;
};

}  // namespace ttexalens::native_elf
