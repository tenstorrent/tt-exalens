// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_cfi.hpp"

#include <utility>

#include "dwarf_handle.hpp"

namespace ttexalens::native_elf {

NativeFrameDescription::NativeFrameDescription(std::weak_ptr<NativeDwarfInfo::Impl> info, Dwarf_Debug dbg,
                                               Dwarf_Fde fde, uint64_t pc, ReadGprFn read_gpr, ReadMemoryFn read_memory)
    : info(std::move(info)),
      dbg(dbg),
      fde(fde),
      pc(pc),
      read_gpr(std::move(read_gpr)),
      read_memory(std::move(read_memory)) {}

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

}  // namespace

std::optional<uint64_t> NativeFrameDescription::read_register(int register_index, uint64_t cfa) const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return std::nullopt;
    }
    auto q = query_rule(dbg, fde, static_cast<Dwarf_Half>(register_index), pc);

    if (q.status == DW_DLV_OK && q.value_type == DW_EXPR_OFFSET && q.offset_relevant != 0) {
        uint64_t address = cfa + static_cast<uint64_t>(q.offset);
        if (auto v = read_memory(address)) {
            return v;
        }
        return std::nullopt;
    }
    return read_gpr(register_index);
}

std::optional<uint64_t> NativeFrameDescription::try_read_register(int /*register_index*/,
                                                                  std::optional<uint64_t> /*cfa*/) const {
    // TODO #761: handle the full rule taxonomy.
    return std::nullopt;
}

std::optional<uint64_t> NativeFrameDescription::read_previous_cfa(std::optional<uint64_t> current_cfa) const {
    auto info_ptr = info.lock();
    if (!info_ptr) {
        return std::nullopt;
    }

    // The CFA rule lives in column DW_FRAME_CFA_COL. For an
    // "address-of-register + offset" CFA the rule comes back as
    // DW_EXPR_OFFSET with q.reg set to the source register.
    auto cfa_rule = query_rule(dbg, fde, DW_FRAME_CFA_COL, pc);
    if (cfa_rule.status != DW_DLV_OK || cfa_rule.value_type != DW_EXPR_OFFSET || cfa_rule.offset_relevant == 0 ||
        !is_real_register(cfa_rule.reg)) {
        return std::nullopt;
    }
    const int cfa_register = static_cast<int>(cfa_rule.reg);
    const int64_t cfa_offset = cfa_rule.offset;

    // Top frame: register holds its live value.
    if (!current_cfa.has_value()) {
        return read_gpr(cfa_register) + static_cast<uint64_t>(cfa_offset);
    }

    // Non-top frame: does the current frame save the CFA-source register?
    auto reg_rule = query_rule(dbg, fde, static_cast<Dwarf_Half>(cfa_register), pc);
    const bool has_saved_rule =
        reg_rule.status == DW_DLV_OK && reg_rule.value_type == DW_EXPR_OFFSET && reg_rule.offset_relevant != 0;
    if (!has_saved_rule) {
        return *current_cfa + static_cast<uint64_t>(cfa_offset);
    }

    uint64_t address = *current_cfa + static_cast<uint64_t>(reg_rule.offset);
    auto saved = read_memory(address);

    if (!saved.has_value()) {
        return std::nullopt;
    }
    return *saved + static_cast<uint64_t>(cfa_offset);
}

}  // namespace ttexalens::native_elf
