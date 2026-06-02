// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <libdwarf.h>

#include <cstdint>
#include <memory>
#include <optional>
#include <utility>
#include <vector>

#include "memory_access.hpp"

namespace ttexalens::native_elf {

namespace details {
class NativeDwarfInfoImpl;
}  // namespace details

class MemoryAccess;

// Classification of a CFI rule for a single (register, PC) pair. Used when
// walking the live frame outward to recover a callee-saved register's value
// at an outer frame's PC.
//   * Saved      — the value is in memory at `saved_address`.
//   * SameValue  — this frame preserves the register; look further in.
//   * Undefined  — this frame does not preserve the register; abandon.
//   * Unknown    — rule kind not yet handled (DWARF expression, register-
//                  to-register, etc.). Treated as a hard stop.
enum class RegisterRuleKind { Saved, SameValue, Undefined, Unknown };
struct RegisterRule {
    RegisterRuleKind kind;
    uint64_t saved_address = 0;
};

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
    uint16_t get_pointer_size() const;

    std::optional<uint64_t> read_register(uint16_t register_index, uint64_t cfa) const;
    std::optional<uint64_t> try_read_register(uint16_t register_index, std::optional<uint64_t> cfa) const;
    std::optional<uint64_t> read_previous_cfa(std::optional<uint64_t> current_cfa) const;

    // Resolves the CFI rule for `register_index` at this frame's PC into one
    // of the four `RegisterRule` shapes. `cfa` must be the inspected frame's
    // CFA; for `Saved` rules the returned address is `cfa + offset`.
    RegisterRule classify_register_rule(uint16_t register_index, uint64_t cfa) const;

   private:
    // Guard for fde validity
    std::weak_ptr<details::NativeDwarfInfoImpl> info;
    Dwarf_Fde fde;
    uint64_t pc;
    std::shared_ptr<MemoryAccess> memory_access;
};

// Per-frame context the DWARF location-expression evaluator reads through.
// Bundles a MemoryAccess, the inspected frame's FDE/CFA/PC, and the chain of
// frames between this one and the live state — needed to recover the value
// of a callee-saved register that this frame preserves but inner frames
// have spilled to the stack.
//
//   * top frame  — frame_description is nullopt; inner_frames is empty;
//                  read_register reads the live register.
//   * non-top    — frame_description carries this frame's FDE. inner_frames
//                  is ordered immediate-child-of-inspected first, live last.
//                  read_register classifies this frame's CFI rule and walks
//                  the chain on SameValue, returning the live register only
//                  if no frame between here and live saved it.
//
// Memory loads always route through MemoryAccess regardless of frame depth.
class NativeFrameInspection {
   public:
    using InnerFrame = std::pair<NativeFrameDescription, uint64_t>;

    NativeFrameInspection(std::shared_ptr<MemoryAccess> memory_access,
                          std::optional<NativeFrameDescription> frame_description = std::nullopt,
                          std::optional<uint64_t> cfa = std::nullopt, uint64_t pc = 0,
                          std::vector<InnerFrame> inner_frames = {});

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
    std::vector<InnerFrame> inner_frames;
};

}  // namespace ttexalens::native_elf
