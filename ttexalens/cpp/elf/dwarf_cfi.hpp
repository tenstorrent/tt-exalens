// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <libdwarf.h>

#include <cstdint>
#include <functional>
#include <memory>
#include <optional>

#include "dwarf_info.hpp"

namespace ttexalens::native_elf {

// Resolved Call Frame Information for a single PC inside an FDE. Combines the
// FDE we found with two callbacks the caller wires up so we can read live machine
// state (GPRs + target memory) without implementing them in this library.
// Even though we use uint64_t for register values and addresses, this class is
// architecture-agnostic — the caller can choose to only read 32 bits in a 32-bit architecture.
class NativeFrameDescription {
   public:
    // Returns the GPR with the given DWARF register number. Implementations
    // are expected to never throw on a valid register index — the callstack
    // walker relies on getting *some* value back.
    using ReadGprFn = std::function<uint64_t(int)>;

    // Returns the register value at `address`, or nullopt if the access was refused.
    // 32bit architecture will read 4 bytes while 64bit will read 8 bytes.
    using ReadMemoryFn = std::function<std::optional<uint64_t>(uint64_t)>;

    NativeFrameDescription(std::weak_ptr<NativeDwarfInfo::Impl> info, Dwarf_Debug dbg, Dwarf_Fde fde, uint64_t pc,
                           ReadGprFn read_gpr, ReadMemoryFn read_memory);

    uint64_t get_pc() const { return pc; }

    std::optional<uint64_t> read_register(int register_index, uint64_t cfa) const;
    std::optional<uint64_t> try_read_register(int register_index, std::optional<uint64_t> cfa) const;
    std::optional<uint64_t> read_previous_cfa(std::optional<uint64_t> current_cfa) const;

   private:
    // info gates dbg's validity — if Impl is gone, dbg is too. We store
    // dbg directly because dwarf_cfi.cpp only sees Impl as a forward decl
    // and can't dereference info_ptr to fish it back out.
    std::weak_ptr<NativeDwarfInfo::Impl> info;
    Dwarf_Debug dbg;
    Dwarf_Fde fde;
    uint64_t pc;
    ReadGprFn read_gpr;
    ReadMemoryFn read_memory;
};

}  // namespace ttexalens::native_elf
