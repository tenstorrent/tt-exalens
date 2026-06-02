// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <vector>

namespace ttexalens::native_elf {

class NativeDwarfDie;
using NativeDwarfDiePtr = std::shared_ptr<NativeDwarfDie>;
class NativeFrameInspection;

// Result of evaluating a DWARF location expression. Either:
//   * is_address == true  — `value` is the memory address holding the
//                           variable's bytes. The caller reads from there
//                           through the active MemoryAccess.
//   * is_address == false — `value` (or `raw_bytes`) IS the variable's
//                           literal value (DW_OP_stack_value / DW_OP_regN /
//                           const_type). `raw_bytes` is used for widths the
//                           uint64 path can't represent losslessly (e.g.
//                           DWARF5 const_type with a typed byte payload).
struct LocationResult {
    bool is_address = false;
    std::optional<uint64_t> value;
    std::vector<std::byte> raw_bytes;
};

// Evaluates the variable / parameter / template_value_param DIE's
// DW_AT_location attribute against `frame`. Returns nullopt when the
// location can't be resolved (unsupported form, missing frame info,
// memory read failure, etc.). Constant-only variables (no location) are
// handled by NativeDwarfDie::read_value before this is called.
std::optional<LocationResult> evaluate_die_location(const NativeDwarfDie& die, const NativeFrameInspection* frame);

}  // namespace ttexalens::native_elf
