// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <libdwarf.h>

#include <cstdint>
#include <memory>
#include <optional>
#include <vector>

#include "memory_access.hpp"

namespace ttexalens::native_elf {

namespace details {
class DwarfInfoImpl;
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
class FrameDescription {
   public:
    FrameDescription(std::weak_ptr<details::DwarfInfoImpl> info, Dwarf_Fde fde, uint64_t pc,
                     std::shared_ptr<MemoryAccess> memory_access);

    uint64_t get_pc() const { return pc; }
    uint16_t get_pointer_size() const;

    // DWARF register number of the return-address register, read from the CIE
    // this FDE belongs to. Returns nullopt if the CIE can't be read.
    std::optional<uint16_t> get_return_address_register() const;

    std::optional<uint64_t> read_register(uint16_t register_index, uint64_t cfa) const;
    std::optional<uint64_t> try_read_register(uint16_t register_index, std::optional<uint64_t> cfa) const;

    // Computes this FDE's CFA at its PC. For the top frame (`inner_cfa`
    // nullopt) reads the CFA-source register live; for any outer frame
    // passes the inner frame's CFA so the CFI rule chain can be followed
    // through any save/restore of the CFA-source register. Returns this
    // FDE's frame CFA, not the inner frame's.
    std::optional<uint64_t> compute_cfa(std::optional<uint64_t> inner_cfa = std::nullopt) const;

    // Resolves the CFI rule for `register_index` at this frame's PC into one
    // of the four `RegisterRule` shapes. `cfa` must be the inspected frame's
    // CFA; for `Saved` rules the returned address is `cfa + offset`.
    RegisterRule classify_register_rule(uint16_t register_index, uint64_t cfa) const;

   private:
    // Guard for fde validity
    std::weak_ptr<details::DwarfInfoImpl> info;
    Dwarf_Fde fde;
    uint64_t pc;
    std::shared_ptr<MemoryAccess> memory_access;
};

// Snapshot of one frame on the callstack at the PC where execution was
// when we walked through it. `fde` is the FDE whose address range covers
// the frame; `cfa` is the Canonical Frame Address computed via
// `fde.compute_cfa(...)`. Used both for the inspected frame and for each
// frame in the inner chain that FrameInspection carries.
//
// Two PCs are tracked because they serve different purposes:
//   * compute_pc — the DWARF-space (load-offset-adjusted) PC used for every
//     DWARF lookup: FDE row selection, function/line lookup, location
//     evaluation. This is what FrameInspection exposes via get_pc().
//   * reported_pc — the PC surfaced to callers / displayed (live PC for the
//     live frame, return address for outer frames, matching GDB). Carried
//     here so callstack walking needs only this one frame type; FrameInspection
//     itself ignores it.
struct FrameSnapshot {
    FrameDescription fde;
    uint64_t cfa = 0;
    uint64_t compute_pc = 0;
    uint64_t reported_pc = 0;
};

// Per-frame context the DWARF location-expression evaluator reads through.
// Bundles a MemoryAccess, the inspected frame's snapshot, and the chain of
// frames between it and the live state — needed to recover the value of a
// callee-saved register that this frame preserves but inner frames have
// spilled to the stack.
//
// inner_frames is in natural callstack order: live first, immediate-child-
// of-inspected last. read_register walks the list in reverse — starting at
// the immediate child and moving toward live — until a frame's CFI says it
// saved the requested register; if none did, the live register is returned.
// For the top frame `inner_frames` is empty: the walk is a no-op and we
// read the live register directly. The inspected frame's own CFI is
// intentionally NOT consulted — it describes the caller's view, not this
// frame's — so the inspected snapshot's `fde` is carried only to keep the
// (cfa, pc) plumbing uniform with inner_frames.
//
// Memory loads always route through MemoryAccess regardless of frame depth.
class FrameInspection {
   public:
    // The inspected snapshot defaults to nullopt for the "no frame
    // context" case (e.g. reading globals outside a callstack walk).
    // Runtime-location DIEs need a real snapshot and will fail to
    // evaluate otherwise.
    FrameInspection(std::shared_ptr<MemoryAccess> memory_access, std::optional<FrameSnapshot> inspected = std::nullopt,
                    std::vector<FrameSnapshot> inner_frames = {});

    std::optional<uint64_t> read_register(int register_index) const;
    std::optional<uint64_t> read_memory(uint64_t address, uint8_t register_size) const;
    std::optional<uint64_t> get_cfa() const {
        return inspected.has_value() ? std::optional{inspected->cfa} : std::nullopt;
    }
    uint64_t get_pc() const { return inspected.has_value() ? inspected->compute_pc : 0; }
    const std::shared_ptr<MemoryAccess>& get_memory_access() const { return memory_access; }

   private:
    std::shared_ptr<MemoryAccess> memory_access;
    std::optional<FrameSnapshot> inspected;
    std::vector<FrameSnapshot> inner_frames;
};

}  // namespace ttexalens::native_elf
