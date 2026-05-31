// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <libdwarf.h>

#include <cstdint>
#include <memory>
#include <optional>

#include "memory_access.hpp"

namespace ttexalens::native_elf {

namespace details {
class NativeDwarfInfoImpl;
}  // namespace details

class MemoryAccess;

// Resolved Call Frame Information for a single PC inside an FDE. Combines the
// FDE we found with a MemoryAccess the caller wires up so we can read live
// machine state (GPRs + target memory) without implementing them in this
// library.
// Even though we use uint64_t for register values and addresses, this class is
// architecture-agnostic — the caller can choose to only read 32 bits in a
// 32-bit architecture.
class NativeFrameDescription {
   public:
    NativeFrameDescription(std::weak_ptr<details::NativeDwarfInfoImpl> info, Dwarf_Fde fde, uint64_t pc,
                           std::shared_ptr<MemoryAccess> memory_access);

    uint64_t get_pc() const { return pc; }

    std::optional<uint64_t> read_register(uint16_t register_index, uint64_t cfa) const;
    std::optional<uint64_t> try_read_register(uint16_t register_index, std::optional<uint64_t> cfa) const;
    std::optional<uint64_t> read_previous_cfa(std::optional<uint64_t> current_cfa) const;

   private:
    // Guard for fde validity
    std::weak_ptr<details::NativeDwarfInfoImpl> info;
    Dwarf_Fde fde;
    uint64_t pc;
    std::shared_ptr<MemoryAccess> memory_access;
};

// Per-frame context the DWARF location-expression evaluator reads through.
// Mirrors the legacy Python FrameInspection: bundles a MemoryAccess, an
// optional NativeFrameDescription (present only for non-top frames), this
// frame's CFA, and the PC at which the expression applies.
//
//   * top frame  — frame_description is nullopt; read_register goes
//                  straight to MemoryAccess::read_register (the live RISC).
//   * non-top    — frame_description carries the FDE; read_register
//                  delegates to FrameDescription::try_read_register(reg, cfa),
//                  which can return std::nullopt when no save rule exists.
//
// Memory loads always route through MemoryAccess regardless of frame depth.
class NativeFrameInspection {
   public:
    NativeFrameInspection(std::shared_ptr<MemoryAccess> memory_access,
                          std::optional<NativeFrameDescription> frame_description, std::optional<uint64_t> cfa,
                          uint64_t pc);

    std::optional<uint64_t> read_register(int register_index) const;
    std::optional<uint64_t> read_memory(uint64_t address, uint8_t register_size) const;
    std::optional<uint64_t> get_cfa() const { return cfa; }
    uint64_t get_pc() const { return pc; }
    const std::shared_ptr<MemoryAccess>& get_memory_access() const { return memory_access; }

   private:
    std::shared_ptr<MemoryAccess> memory_access;
    std::optional<NativeFrameDescription> frame_description;
    std::optional<uint64_t> cfa;
    uint64_t pc;
};

}  // namespace ttexalens::native_elf
