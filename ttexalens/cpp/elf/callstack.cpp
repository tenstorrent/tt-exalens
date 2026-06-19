// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "callstack.hpp"

#include <cassert>
#include <set>
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

// Walks outward from `die` until it reaches the enclosing DW_TAG_subprogram
// (skipping lexical blocks and inlined subroutines). Returns nullptr if there
// is none.
DwarfDiePtr enclosing_subprogram(DwarfDiePtr die) {
    while (die && die->get_tag() != DwarfDieTag::subprogram) {
        die = die->get_parent();
    }
    return die;
}

// True when `site` carries the tail-call flag (DWARF 5 DW_AT_call_tail_call or
// the GNU DW_AT_GNU_tail_call extension). The flag is normally emitted as
// DW_FORM_flag_present, decoded to bool true.
bool is_tail_call_site(const DwarfDiePtr& site) {
    for (DwarfAttributeTag tag : {DwarfAttributeTag::call_tail_call, DwarfAttributeTag::GNU_tail_call}) {
        if (const DwarfAttribute* attr = site->get_attribute(tag)) {
            const bool* flag = std::get_if<bool>(&attr->get_value());
            return flag == nullptr || *flag;  // present-but-not-bool ⇒ treat as set
        }
    }
    return false;
}

// Recursively collects the tail-call call-site DIEs under `scope`, descending
// through lexical blocks and inlined subroutines (a tail call can be lexically
// nested inside an inlined function, as ra1's jump to pc1 lives inside the
// inlined ra3).
void collect_tail_call_sites(const DwarfDiePtr& scope, std::vector<DwarfDiePtr>& out) {
    for (DwarfDiePtr child = scope->get_first_child(); child; child = child->get_next_sibling()) {
        const DwarfDieTag tag = child->get_tag();
        if (tag == DwarfDieTag::call_site || tag == DwarfDieTag::GNU_call_site) {
            if (is_tail_call_site(child)) {
                out.push_back(child);
            }
        } else if (tag == DwarfDieTag::lexical_block || tag == DwarfDieTag::inlined_subroutine) {
            collect_tail_call_sites(child, out);
        }
    }
}

// Finds the call-site DIE in `scope` whose DW_AT_call_return_pc equals
// `return_pc` (a DWARF-space address). Descends through lexical blocks and
// inlined subroutines. nullptr on miss.
DwarfDiePtr find_call_site_by_return_pc(const DwarfDiePtr& scope, uint64_t return_pc) {
    for (DwarfDiePtr child = scope->get_first_child(); child; child = child->get_next_sibling()) {
        const DwarfDieTag tag = child->get_tag();
        if (tag == DwarfDieTag::call_site || tag == DwarfDieTag::GNU_call_site) {
            if (const uint64_t* rp = child->get_attribute_value<uint64_t>(DwarfAttributeTag::call_return_pc)) {
                if (*rp == return_pc) {
                    return child;
                }
            }
        } else if (tag == DwarfDieTag::lexical_block || tag == DwarfDieTag::inlined_subroutine) {
            if (DwarfDiePtr found = find_call_site_by_return_pc(child, return_pc)) {
                return found;
            }
        }
    }
    return nullptr;
}

// Resolves the function a call site invokes (DW_AT_call_origin, or the GNU
// DW_AT_GNU_call_site_target equivalent), as the enclosing subprogram DIE.
DwarfDiePtr get_call_site_origin(const DwarfDiePtr& site) {
    DwarfDiePtr origin = site->get_die_from_attribute(DwarfAttributeTag::call_origin);
    return enclosing_subprogram(origin);
}

// Searches for a chain of tail calls leading from `from_func` (the subprogram
// the caller actually invoked) down to `target` (the subprogram we are
// physically stopped in). On success `chain` holds the tail-call-site DIEs in
// caller-to-callee order: chain.front() is a site in `from_func`, chain.back()
// the site whose origin is `target`. `visited` guards against cycles.
bool find_tail_call_chain(const DwarfDiePtr& from_func, const DwarfDiePtr& target, std::vector<DwarfDiePtr>& chain,
                          std::set<Dwarf_Off>& visited, int depth) {
    if (!from_func || depth > 64) {
        return false;
    }
    std::vector<DwarfDiePtr> sites;
    collect_tail_call_sites(from_func, sites);
    for (const DwarfDiePtr& site : sites) {
        DwarfDiePtr origin = get_call_site_origin(site);
        if (!origin) {
            continue;
        }
        if (origin->get_offset() == target->get_offset()) {
            chain.push_back(site);
            return true;
        }
        if (visited.insert(origin->get_offset()).second) {
            chain.push_back(site);
            if (find_tail_call_chain(origin, target, chain, visited, depth + 1)) {
                return true;
            }
            chain.pop_back();
        }
    }
    return false;
}

// Appends synthetic frame(s) for the tail-call `site`. The reported PC is the
// site's DW_AT_call_return_pc (mapped back to a live address), while the
// function name and source line are resolved one byte earlier - inside the
// tail-jump instruction itself - so they name the (possibly inlined) function
// that issued the jump rather than the next frame.
//
// `function_die` (resolved at the jump) is the innermost (possibly inlined)
// function at the call site. When `expand_inline_frames` is false this emits a
// single entry named after it - matching GDB, which renders one artificial
// frame per tail call. When true it additionally walks the inline-parent chain
// (skipping lexical blocks) and emits one entry per enclosing inlined function
// up to the physical subprogram, mirroring how append_frame_callstack expands a
// real frame's inlined subroutines. The extra entries carry only names and
// source lines (no PC, no variables): a tail-called frame is gone from the
// stack, so there is no live state to read - but the inline structure recorded
// at the jump PC is exact, so this faithfully reconstructs the source-level call
// chain (the same one a -O0 build would show). Used when reconstructing a stack
// from a captured PC/RA pair without access to live registers or memory.
void append_tail_call_frame(const ElfFile& elf, const DwarfInfo& dwarf, const DwarfDiePtr& site,
                            bool expand_inline_frames, std::vector<CallstackEntry>& callstack) {
    const int64_t loaded_offset = elf.get_loaded_offset();

    std::optional<uint64_t> reported_pc;  // live address surfaced to callers
    std::optional<uint64_t> lookup_pc;    // DWARF-space address inside the jump
    if (const uint64_t* return_pc = site->get_attribute_value<uint64_t>(DwarfAttributeTag::call_return_pc)) {
        reported_pc = static_cast<uint64_t>(static_cast<int64_t>(*return_pc) - loaded_offset);
        lookup_pc = *return_pc - 1;
    } else if (const uint64_t* call_pc = site->get_attribute_value<uint64_t>(DwarfAttributeTag::call_pc)) {
        reported_pc = static_cast<uint64_t>(static_cast<int64_t>(*call_pc) - loaded_offset);
        lookup_pc = *call_pc;
    } else {
        return;
    }

    std::optional<DwarfFileLine> file_info = dwarf.find_file_line_by_address(*lookup_pc);
    DwarfDiePtr function_die = dwarf.find_function_by_address(*lookup_pc);

    auto push_entry = [&](std::optional<uint64_t> pc, const DwarfDiePtr& die,
                          std::optional<DwarfFileLine> entry_file_info) {
        std::optional<std::string> function_name;
        if (die) {
            function_name = die->get_path();
        }
        callstack.push_back(CallstackEntry{pc,
                                           std::move(function_name),
                                           std::move(entry_file_info),
                                           /*cfa=*/std::nullopt,
                                           {},
                                           {},
                                           {}});
    };

    if (!expand_inline_frames || !function_die) {
        push_entry(reported_pc, function_die, std::move(file_info));
        return;
    }

    // Skip lexical blocks (never printed), as append_frame_callstack does.
    while (function_die->get_tag() == DwarfDieTag::lexical_block) {
        DwarfDiePtr parent = function_die->get_parent();
        if (!parent) {
            break;
        }
        function_die = parent;
    }

    // Innermost virtual frame carries the reported PC; its source line is the
    // jump site. Each inline parent then takes the call-site location of the
    // child it inlined (where the inlining happened), exactly as for a real
    // frame's inlined-subroutine chain.
    push_entry(reported_pc, function_die, file_info);
    file_info = function_die->get_call_file_info();
    while (function_die->get_tag() == DwarfDieTag::inlined_subroutine) {
        DwarfDiePtr parent = function_die->get_parent();
        if (!parent) {
            break;
        }
        function_die = parent;
        while (function_die->get_tag() == DwarfDieTag::lexical_block) {
            DwarfDiePtr inner_parent = function_die->get_parent();
            if (!inner_parent) {
                break;
            }
            function_die = inner_parent;
        }
        push_entry(/*pc=*/std::nullopt, function_die, file_info);
        file_info = function_die->get_call_file_info();
    }
}

}  // namespace

void append_tail_call_frames(const ElfFile& elf, const DwarfDiePtr& callee_subprogram, uint64_t return_address,
                             std::vector<CallstackEntry>& callstack, bool expand_inline_frames) {
    if (!callee_subprogram || callee_subprogram->get_tag() != DwarfDieTag::subprogram) {
        return;
    }
    const DwarfInfo* dwarf = elf.get_dwarf_info();
    if (dwarf == nullptr) {
        return;
    }

    const uint64_t return_pc_dwarf =
        static_cast<uint64_t>(static_cast<int64_t>(return_address) + elf.get_loaded_offset());
    DwarfDiePtr caller = enclosing_subprogram(dwarf->find_function_by_address(return_pc_dwarf - 1));
    if (!caller) {
        return;
    }

    DwarfDiePtr call_site = find_call_site_by_return_pc(caller, return_pc_dwarf);
    if (!call_site) {
        return;
    }

    DwarfDiePtr origin = get_call_site_origin(call_site);
    // No origin, or the caller invoked our function directly: nothing was tail-called.
    if (!origin || origin->get_offset() == callee_subprogram->get_offset()) {
        return;
    }

    std::vector<DwarfDiePtr> chain;
    std::set<Dwarf_Off> visited;
    if (!find_tail_call_chain(origin, callee_subprogram, chain, visited, 0)) {
        return;
    }

    // chain is caller-to-callee; emit innermost (nearest the callee) first.
    for (auto it = chain.rbegin(); it != chain.rend(); ++it) {
        append_tail_call_frame(elf, *dwarf, *it, expand_inline_frames, callstack);
    }
}

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
                                          std::string_view stop_function_name, bool extract_variables,
                                          bool expand_tail_call_inline_frames) {
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

        // If the caller reached `function_die` through one or more tail calls,
        // those frames left no return address of their own; reconstruct them
        // from the DWARF call-site information before the next iteration appends
        // the caller. The call-site info lives in the caller's image, so this is
        // only valid when the caller resolved to the same ELF as the callee.
        if (located.has_value() && located->elf == elf) {
            append_tail_call_frames(*elf, function_die, *return_address, callstack, expand_tail_call_inline_frames);
        }
    }

    return callstack;
}

}  // namespace ttexalens::native_elf
