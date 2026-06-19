// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "dwarf_die.hpp"
#include "memory_access.hpp"
#include "variable.hpp"

namespace ttexalens::native_elf {

class ElfFile;

// One variable captured for a callstack frame — an argument, a local, or a
// template value parameter. `die` is the DWARF DIE describing it; `value`, when
// present, is the variable read from the inspected frame (nullopt when the
// frame had no MemoryAccess or the location couldn't be evaluated).
struct CallstackEntryVariable {
    DwarfDiePtr die;
    std::optional<ElfVariable> value;
};

// One entry on a callstack. `function_name` is the DIE's qualified path (nullopt
// when no function DIE covers the PC). `file_info` is the source location. Inlined
// frames produce extra entries with `pc` == nullopt (matching GDB's virtual-frame display).
struct CallstackEntry {
    std::optional<uint64_t> pc;
    std::optional<std::string> function_name;
    std::optional<DwarfFileLine> file_info;
    std::optional<uint64_t> cfa;
    std::vector<CallstackEntryVariable> arguments;
    std::vector<CallstackEntryVariable> locals;
    std::vector<CallstackEntryVariable> template_parameters;
};

// Builds the callstack entries for the single frame at `pc`: the function
// covering it plus any inlined functions it expands into (virtual frames).
// Locates the covering ELF / FDE across `elfs` itself, so this is a static
// lookup needing no live state — the entries carry names and source locations
// but (lacking a MemoryAccess) no variable values or CFA. When
// `extract_variables` is set the argument / local / template-parameter DIEs are
// still listed (with null values); when false those lists are left empty.
// Returns an empty vector when no ELF covers `pc`.
std::vector<CallstackEntry> get_frame_callstack(const std::vector<ElfFile>& elfs, uint64_t pc, bool extract_variables);

// Walks the call frames starting at live program counter `pc` and returns the
// callstack, inner frame first. `elfs` are the ELF images (already re-anchored
// to their live load addresses) consulted for frame/DWARF info; `memory_access`
// reads live registers and target memory. Stops after `limit` entries, when the
// CFA chain ends, or — when `stop_function_name` is set — once the specified
// function is reported. `limit` == 0 means no limit. When `extract_variables` is
// false, per-frame argument / local / template-parameter lists are skipped for a
// faster name-only backtrace.
//
// When `expand_tail_call_inline_frames` is set, a reconstructed tail-call frame
// is expanded into its full inlined-function chain (one entry per enclosing
// inlined subroutine, name + source line only) instead of the single innermost
// entry GDB emits. The extra entries carry no PC or variables — a tail-called
// frame has no live state — but reproduce the source-level call chain exactly.
// Off by default to stay byte-for-byte comparable with GDB's output.
//
// Returns an empty vector when no ELF covers `pc`.
std::vector<CallstackEntry> get_callstack(const std::vector<ElfFile>& elfs, uint64_t pc,
                                          std::shared_ptr<MemoryAccess> memory_access, size_t limit,
                                          std::string_view stop_function_name, bool extract_variables,
                                          bool expand_tail_call_inline_frames = false);

// Bridges the gap a tail call leaves in the physical stack. After the frame for
// `callee_subprogram` has been appended, its return address points back at the
// function that the *original* caller invoked - skipping every function that was
// reached by a tail jump. When the call site that returns to `return_address`
// names a different function than `callee_subprogram`, the functions in between
// were tail-called; this synthesizes a frame for each, innermost first, so the
// reconstructed stack matches a non-optimized (or GDB) walk.
//
// Precondition: `return_address` (a live address) lies within `elf`, and
// `callee_subprogram` belongs to `elf`'s DWARF. The caller guarantees this by
// only invoking us once the next-frame lookup has resolved the caller to the
// same ELF, so the load-offset translation and the DIE-offset comparisons below
// are all within one image.
void append_tail_call_frames(const ElfFile& elf, const DwarfDiePtr& callee_subprogram, uint64_t return_address,
                             std::vector<CallstackEntry>& callstack, bool expand_inline_frames = false);

}  // namespace ttexalens::native_elf
