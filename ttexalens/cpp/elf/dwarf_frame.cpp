// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_frame.hpp"

#include <utility>

#include "dwarf_handle.hpp"
#include "memory_access.hpp"
#include "private/dwarf_info_impl.hpp"

namespace ttexalens::native_elf {

FrameDescription::FrameDescription(std::weak_ptr<details::DwarfInfoImpl> info, Dwarf_Fde fde, uint64_t pc,
                                   std::shared_ptr<MemoryAccess> memory_access)
    : info(std::move(info)), fde(fde), pc(pc), memory_access(std::move(memory_access)) {}

namespace {

// Queries the CFI table for `register_index` at `pc` inside `fde`.
// Returns DW_DLV_OK plus value_type / reg / offset; on failure returns
// non-OK and the out-params are left at their default-zero state.
struct CfiRuleQuery {
    Dwarf_Small value_type = 0;
    Dwarf_Unsigned offset_relevant = 0;
    Dwarf_Unsigned reg = 0;
    Dwarf_Signed offset = 0;
    Dwarf_Block block{};
    Dwarf_Addr row_pc = 0;
    Dwarf_Bool has_more_rows = 0;
    Dwarf_Addr subsequent_pc = 0;
    int status = DW_DLV_ERROR;
};

CfiRuleQuery query_rule(Dwarf_Debug dbg, Dwarf_Fde fde, Dwarf_Half column, uint64_t pc) {
    CfiRuleQuery q;
    DwarfErrorHandle error(dbg);
    q.status = dwarf_get_fde_info_for_reg3_c(fde, column, static_cast<Dwarf_Addr>(pc), &q.value_type,
                                             &q.offset_relevant, &q.reg, &q.offset, &q.block, &q.row_pc,
                                             &q.has_more_rows, &q.subsequent_pc, &error);
    return q;
}

// True iff `reg` is a real machine register — i.e. not one of libdwarf's
// sentinel column numbers for UNDEFINED / SAME_VAL / CFA.
bool is_real_register(Dwarf_Unsigned reg) {
    return reg != DW_FRAME_UNDEFINED_VAL && reg != DW_FRAME_SAME_VAL && reg != DW_FRAME_CFA_COL;
}

// True iff `register_index` is callee-saved per the RISC-V calling
// convention. Used to fix up libdwarf's `dwarf_set_frame_rule_initial_value`
// default — GCC's RISC-V CIE doesn't declare an initial rule for unmentioned
// registers, so libdwarf would report them all as Undefined. ABI-wise,
// callee-saved registers should default to SameValue (preserved across the
// call), only volatiles to Undefined.
//
// RISC-V psABI: x2 (sp), x3 (gp), x4 (tp), x8 (s0/fp), x9 (s1), x18..x27
// (s2..s11). Other registers (ra, ta, ax, tx) are volatile.
bool is_callee_saved_register(uint16_t reg) {
    if (reg == 2 || reg == 3 || reg == 4) return true;  // sp, gp, tp
    if (reg == 8 || reg == 9) return true;              // s0, s1
    if (reg >= 18 && reg <= 27) return true;            // s2..s11
    return false;
}

}  // namespace

std::optional<uint64_t> FrameDescription::read_register(uint16_t register_index, uint64_t cfa) const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return std::nullopt;
    }
    auto q = query_rule(info_ptr->dbg, fde, static_cast<Dwarf_Half>(register_index), pc);

    if (q.status == DW_DLV_OK && q.value_type == DW_EXPR_OFFSET && q.offset_relevant != 0) {
        uint64_t address = cfa + q.offset;
        return memory_access->try_read_word(address, info_ptr->pointer_size);
    }
    return memory_access->read_register(register_index);
}

std::optional<uint64_t> FrameDescription::try_read_register(uint16_t register_index,
                                                            std::optional<uint64_t> cfa) const {
    if (!cfa.has_value()) {
        return std::nullopt;
    }
    const RegisterRule rule = classify_register_rule(register_index, *cfa);
    if (rule.kind != RegisterRuleKind::Saved) {
        return std::nullopt;
    }
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return std::nullopt;
    }
    return memory_access->try_read_word(rule.saved_address, info_ptr->pointer_size);
}

RegisterRule FrameDescription::classify_register_rule(uint16_t register_index, uint64_t cfa) const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return {RegisterRuleKind::Unknown, 0};
    }
    auto q = query_rule(info_ptr->dbg, fde, static_cast<Dwarf_Half>(register_index), pc);
    if (q.status != DW_DLV_OK) {
        return {RegisterRuleKind::Unknown, 0};
    }
    // libdwarf encodes UNDEFINED / SAME_VAL as sentinel register columns in
    // the rule's `reg` field.
    if (q.reg == DW_FRAME_UNDEFINED_VAL) {
        // Promote callee-saved-by-ABI registers from the libdwarf default
        // "undefined" back to SameValue so the chain walker can recover
        // them from frames that left them untouched.
        if (is_callee_saved_register(register_index)) {
            return {RegisterRuleKind::SameValue, 0};
        }
        return {RegisterRuleKind::Undefined, 0};
    }
    if (q.reg == DW_FRAME_SAME_VAL) {
        return {RegisterRuleKind::SameValue, 0};
    }
    if (q.value_type == DW_EXPR_OFFSET && q.offset_relevant != 0) {
        return {RegisterRuleKind::Saved, cfa + static_cast<uint64_t>(q.offset)};
    }
    // Register-to-register (DW_EXPR_OFFSET with offset_relevant=0), DWARF
    // expressions (DW_EXPR_EXPRESSION / DW_EXPR_VAL_*), etc. Treat as
    // unknown for now — chain-walking stops here. TODO #761.
    return {RegisterRuleKind::Unknown, 0};
}

uint16_t FrameDescription::get_pointer_size() const {
    auto info_ptr = info.lock();
    return info_ptr ? info_ptr->pointer_size : uint16_t{0};
}

std::optional<uint64_t> FrameDescription::compute_cfa(std::optional<uint64_t> inner_cfa) const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return std::nullopt;
    }

    // The CFA rule lives in column DW_FRAME_CFA_COL. For an
    // "address-of-register + offset" CFA the rule comes back as
    // DW_EXPR_OFFSET with q.reg set to the source register.
    auto cfa_rule = query_rule(info_ptr->dbg, fde, DW_FRAME_CFA_COL, pc);
    if (cfa_rule.status != DW_DLV_OK || cfa_rule.value_type != DW_EXPR_OFFSET || cfa_rule.offset_relevant == 0 ||
        !is_real_register(cfa_rule.reg)) {
        return std::nullopt;
    }
    const uint16_t cfa_register = static_cast<uint16_t>(cfa_rule.reg);
    const int64_t cfa_offset = cfa_rule.offset;

    // Top frame: register holds its live value.
    if (!inner_cfa.has_value()) {
        return memory_access->read_register(cfa_register) + cfa_offset;
    }

    // Non-top frame: does the current frame save the CFA-source register?
    auto reg_rule = query_rule(info_ptr->dbg, fde, static_cast<Dwarf_Half>(cfa_register), pc);
    const bool has_saved_rule =
        reg_rule.status == DW_DLV_OK && reg_rule.value_type == DW_EXPR_OFFSET && reg_rule.offset_relevant != 0;
    if (!has_saved_rule) {
        return *inner_cfa + static_cast<uint64_t>(cfa_offset);
    }

    uint64_t address = *inner_cfa + static_cast<uint64_t>(reg_rule.offset);
    auto saved = memory_access->try_read_word(address, info_ptr->pointer_size);

    if (!saved.has_value()) {
        return std::nullopt;
    }
    return *saved + static_cast<uint64_t>(cfa_offset);
}

FrameInspection::FrameInspection(std::shared_ptr<MemoryAccess> memory_access, std::optional<FrameSnapshot> inspected,
                                 std::vector<FrameSnapshot> inner_frames)
    : memory_access(std::move(memory_access)), inspected(std::move(inspected)), inner_frames(std::move(inner_frames)) {}

std::optional<uint64_t> FrameInspection::read_register(int register_index) const {
    const uint16_t reg = static_cast<uint16_t>(register_index);

    // The inspected frame's own CFI rule for X describes where its CALLER
    // will find X after this frame returns — i.e. the caller's view of X,
    // not this frame's. To recover the inspected frame's view we walk the
    // chain of frames it called into, starting from the immediate child:
    // the first callee that saved X preserved exactly the value the
    // inspected frame had at its call instruction. If none of them saved
    // it (or inner_frames is empty because this IS the live frame), no
    // one between here and live touched X, so the live register still
    // holds the inspected-frame value.
    //
    // inner_frames is stored in natural callstack order (live first,
    // immediate-child-of-inspected last) to match the Python convention,
    // so we iterate it in reverse to start at the immediate child and
    // walk toward live.
    for (auto it = inner_frames.rbegin(); it != inner_frames.rend(); ++it) {
        const RegisterRule rule = it->fde.classify_register_rule(reg, it->cfa);
        if (rule.kind == RegisterRuleKind::Saved) {
            return memory_access->try_read_word(rule.saved_address, it->fde.get_pointer_size());
        }
        if (rule.kind == RegisterRuleKind::SameValue) {
            continue;
        }
        // Undefined or unhandled rule kind — no recoverable value.
        return std::nullopt;
    }
    return memory_access->read_register(static_cast<uint64_t>(register_index));
}

std::optional<uint64_t> FrameInspection::read_memory(uint64_t address, uint8_t register_size) const {
    return memory_access->try_read_word(address, register_size);
}

}  // namespace ttexalens::native_elf
