// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "callstack.hpp"

#include <cassert>
#include <utility>

#include "dwarf_frame.hpp"
#include "dwarf_info.hpp"
#include "elf_file.hpp"

namespace ttexalens::native_elf {

namespace {

struct ElfFrame {
    const ElfFile* elf;
    FrameSnapshot frame;
};

struct ElfFde {
    const ElfFile* elf;
    FrameDescription fde;
};

// Walks the ELF images in order and returns the first whose DWARF frame table
// has an FDE covering `pc`, together with that FrameDescription. Empty when no
// image covers `pc`.
std::optional<ElfFde> find_elf_and_frame_description(const std::vector<ElfFile>& elfs, uint64_t pc,
                                                     const std::shared_ptr<MemoryAccess>& memory_access) {
    for (const ElfFile& elf : elfs) {
        std::optional<FrameDescription> fde = elf.get_frame_description(pc, memory_access);
        if (fde.has_value()) {
            return ElfFde{&elf, std::move(*fde)};
        }
    }
    return std::nullopt;
}

// Resolves the frame snapshot at `pc`, preferring `elf` (the previous frame's
// ELF) and falling back to a scan over all `elfs`. Computes the CFA against
// `inner_cfa` (nullopt for the top frame). Returns an empty frame when no FDE
// covers the PC or the CFA can't be computed.
std::optional<ElfFrame> get_elf_and_frame_snapshot(const ElfFile* elf, const std::vector<ElfFile>& elfs, uint64_t pc,
                                                   uint64_t reported_pc,
                                                   const std::shared_ptr<MemoryAccess>& memory_access,
                                                   std::optional<uint64_t> inner_cfa = std::nullopt) {
    std::optional<FrameDescription> fde;
    if (elf != nullptr) {
        fde = elf->get_frame_description(pc, memory_access);
    }
    if (!fde.has_value()) {
        if (std::optional<ElfFde> found = find_elf_and_frame_description(elfs, pc, memory_access)) {
            elf = found->elf;
            fde = std::move(found->fde);
        }
    }
    if (!fde.has_value()) {
        // No frame information for this PC — the caller stops the walk here.
        // (Python emits a WARN at this point; the native library has no
        // logging facility, so the diagnostic is dropped.)
        return std::nullopt;
    }
    std::optional<uint64_t> cfa = fde->compute_cfa(inner_cfa);
    if (!cfa.has_value()) {
        return std::nullopt;
    }
    // compute_pc is the DWARF-space PC the FDE is anchored at (already
    // load-offset-adjusted by FrameDescription), so downstream lookups don't
    // re-add the offset; reported_pc is the value surfaced to callers.
    const uint64_t compute_pc = fde->get_pc();
    return ElfFrame{elf, FrameSnapshot{std::move(*fde), *cfa, compute_pc, reported_pc}};
}

// Appends the callstack entries for a single physical frame and returns the
// function DIE covering it (used by the walker to detect `main`). Inlined
// subroutines expand into several virtual entries; lexical blocks are walked
// through but not emitted.
DwarfDiePtr append_frame_callstack(const ElfFile& elf, const FrameSnapshot& frame,
                                   std::vector<CallstackEntry>& callstack,
                                   const std::shared_ptr<MemoryAccess>& memory_access,
                                   const std::vector<FrameSnapshot>& inner_frames, bool extract_variables) {
    const uint64_t dwarf_pc = frame.compute_pc;
    const DwarfInfo* dwarf = elf.get_dwarf_info();
    assert(dwarf != nullptr && "ELF has no DWARF info; cannot inspect callstack");

    std::optional<DwarfFileLine> file_info = dwarf->find_file_line_by_address(dwarf_pc);
    DwarfDiePtr function_die = dwarf->find_function_by_address(dwarf_pc);

    // Variable values need live state, so build the inspection context only when
    // a MemoryAccess is available and the caller asked for variables.
    std::optional<FrameInspection> frame_inspection;
    if (extract_variables && memory_access != nullptr) {
        // Empty inner_frames means this is the top frame; FrameInspection then
        // reads the live registers directly. No special case needed. The
        // inspected frame and the inner chain are plain FrameSnapshots, so they
        // pass straight through with no rebuild.
        frame_inspection.emplace(memory_access, frame, inner_frames);
    }

    // Collects a DIE's arguments / locals / template value parameters into the
    // passed-in lists. A no-op when extract_variables is false, leaving the
    // entry's variable lists empty (used for fast name-only backtraces).
    auto collect_variables = [&](const DwarfDiePtr& fn_die, std::vector<CallstackEntryVariable>& arguments,
                                 std::vector<CallstackEntryVariable>& locals,
                                 std::vector<CallstackEntryVariable>& template_parameters) {
        if (!extract_variables) {
            return;
        }
        for (DwarfDiePtr child = fn_die->get_first_child(); child; child = child->get_next_sibling()) {
            std::optional<ElfVariable> value;
            if (frame_inspection.has_value()) {
                value = child->read_value(*frame_inspection);
            }
            const DwarfDieTag tag = child->get_tag();
            if (tag == DwarfDieTag::formal_parameter) {
                arguments.push_back(CallstackEntryVariable{child, std::move(value)});
            } else if (tag == DwarfDieTag::variable) {
                locals.push_back(CallstackEntryVariable{child, std::move(value)});
            }
        }
        for (const DwarfDiePtr& template_value_param : fn_die->get_template_value_parameters()) {
            std::optional<ElfVariable> value;
            if (frame_inspection.has_value()) {
                value = template_value_param->read_value(*frame_inspection);
            }
            template_parameters.push_back(CallstackEntryVariable{template_value_param, std::move(value)});
        }
    };

    std::vector<CallstackEntryVariable> arguments, locals, template_parameters;

    if (function_die && (function_die->get_tag() == DwarfDieTag::inlined_subroutine ||
                         function_die->get_tag() == DwarfDieTag::lexical_block)) {
        // Returning inlined functions (virtual frames).

        // Skipping lexical blocks since we do not print them.
        while (function_die->get_tag() == DwarfDieTag::lexical_block) {
            DwarfDiePtr parent = function_die->get_parent();
            if (!parent) {
                break;
            }
            collect_variables(function_die, arguments, locals, template_parameters);
            function_die = parent;
        }

        collect_variables(function_die, arguments, locals, template_parameters);
        callstack.push_back(CallstackEntry{frame.reported_pc, function_die->get_path(), file_info, frame.cfa,
                                           std::move(arguments), std::move(locals), std::move(template_parameters)});
        file_info = function_die->get_call_file_info();

        while (function_die->get_tag() == DwarfDieTag::inlined_subroutine) {
            std::vector<CallstackEntryVariable> arguments, locals, template_parameters;
            DwarfDiePtr parent = function_die->get_parent();

            function_die = parent;
            // Skipping lexical blocks since we do not print them.
            while (function_die->get_tag() == DwarfDieTag::lexical_block) {
                DwarfDiePtr inner_parent = function_die->get_parent();
                if (!inner_parent) {
                    break;
                }
                collect_variables(function_die, arguments, locals, template_parameters);
                function_die = inner_parent;
            }

            collect_variables(function_die, arguments, locals, template_parameters);
            callstack.push_back(CallstackEntry{std::nullopt, function_die->get_path(), file_info, frame.cfa,
                                               std::move(arguments), std::move(locals),
                                               std::move(template_parameters)});
            file_info = function_die->get_call_file_info();
        }
    } else if (function_die && function_die->get_tag() == DwarfDieTag::subprogram) {
        collect_variables(function_die, arguments, locals, template_parameters);
        callstack.push_back(CallstackEntry{frame.reported_pc, function_die->get_path(), file_info, frame.cfa,
                                           std::move(arguments), std::move(locals), std::move(template_parameters)});
    } else {
        callstack.push_back(CallstackEntry{frame.reported_pc, std::nullopt, file_info, frame.cfa, std::move(arguments),
                                           std::move(locals), std::move(template_parameters)});
    }
    return function_die;
}

}  // namespace

std::vector<CallstackEntry> get_frame_callstack(const std::vector<ElfFile>& elfs, uint64_t pc, bool extract_variables) {
    // Static top-frame lookup: no live state, so resolve the FDE with
    // NoMemoryAccess and skip CFA computation (cfa = 0). No MemoryAccess is
    // passed to append_frame_callstack, so even with extract_variables the
    // variable DIEs are collected without live values.
    std::optional<ElfFde> found = find_elf_and_frame_description(elfs, pc, NoMemoryAccess::instance());
    if (!found) {
        return {};
    }
    // get_pc() is the DWARF-space PC the FDE is anchored at; read it before
    // moving `found->fde`.
    const uint64_t compute_pc = found->fde.get_pc();
    FrameSnapshot frame{std::move(found->fde), /*cfa=*/0, compute_pc, /*reported_pc=*/pc};
    std::vector<CallstackEntry> callstack;
    append_frame_callstack(*found->elf, frame, callstack, /*memory_access=*/nullptr, /*inner_frames=*/{},
                           extract_variables);
    return callstack;
}

std::vector<CallstackEntry> get_callstack(const std::vector<ElfFile>& elfs, uint64_t pc,
                                          std::shared_ptr<MemoryAccess> memory_access, size_t limit,
                                          std::string_view stop_function_name, bool extract_variables) {
    std::vector<CallstackEntry> callstack;

    // Chain of frames inner to the one being inspected.
    std::vector<FrameSnapshot> inner_frames;

    // Find top frame.
    std::optional<ElfFrame> located = get_elf_and_frame_snapshot(nullptr, elfs, pc, pc, memory_access);

    while (located.has_value() && (limit == 0 || callstack.size() < limit)) {
        const ElfFile* elf = located->elf;
        FrameSnapshot& current_frame = located->frame;
        DwarfDiePtr function_die =
            append_frame_callstack(*elf, current_frame, callstack, memory_access, inner_frames, extract_variables);

        // We want to stop when we print the specified function as frame descriptor might not be
        // correct afterwards.
        if (!stop_function_name.empty() && function_die && function_die->get_path() == stop_function_name) {
            break;
        }

        // We want to stop when we are at the end of frames list.
        if (current_frame.cfa == 0) {
            break;
        }

        // Read return address for the next frame.
        std::optional<uint16_t> ra_register = current_frame.fde.get_return_address_register();
        if (!ra_register.has_value()) {
            break;
        }
        std::optional<uint64_t> return_address = current_frame.fde.read_register(*ra_register, current_frame.cfa);
        if (!return_address.has_value()) {
            break;
        }

        // The return address points to the instruction *after* the call.
        // Subtracting one byte moves the lookup PC inside the call instruction
        // (RISC-V instructions are >= 2 bytes), so the FDE / function / line
        // lookups resolve to the call site instead of spilling into whatever
        // follows. The true return address is preserved as reported_pc for display.
        pc = *return_address - 1;
        const uint64_t inner_cfa = current_frame.cfa;
        inner_frames.push_back(std::move(current_frame));
        located = get_elf_and_frame_snapshot(elf, elfs, pc, *return_address, memory_access, inner_cfa);
    }

    return callstack;
}

}  // namespace ttexalens::native_elf
