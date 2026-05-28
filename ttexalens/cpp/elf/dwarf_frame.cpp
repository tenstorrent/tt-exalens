// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_frame.hpp"

#include <utility>

#include "dwarf_handle.hpp"
#include "memory_access.hpp"
#include "private/dwarf_info_impl.hpp"

namespace ttexalens::native_elf {

NativeFrameDescription::NativeFrameDescription(std::weak_ptr<details::NativeDwarfInfoImpl> info, Dwarf_Fde fde,
                                               uint64_t pc, std::shared_ptr<MemoryAccess> memory_access)
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

}  // namespace

std::optional<uint64_t> NativeFrameDescription::read_register(uint16_t register_index, uint64_t cfa) const {
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

std::optional<uint64_t> NativeFrameDescription::try_read_register(uint16_t /*register_index*/,
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
    auto cfa_rule = query_rule(info_ptr->dbg, fde, DW_FRAME_CFA_COL, pc);
    if (cfa_rule.status != DW_DLV_OK || cfa_rule.value_type != DW_EXPR_OFFSET || cfa_rule.offset_relevant == 0 ||
        !is_real_register(cfa_rule.reg)) {
        return std::nullopt;
    }
    const uint16_t cfa_register = static_cast<uint16_t>(cfa_rule.reg);
    const int64_t cfa_offset = cfa_rule.offset;

    // Top frame: register holds its live value.
    if (!current_cfa.has_value()) {
        return memory_access->read_register(cfa_register) + cfa_offset;
    }

    // Non-top frame: does the current frame save the CFA-source register?
    auto reg_rule = query_rule(info_ptr->dbg, fde, static_cast<Dwarf_Half>(cfa_register), pc);
    const bool has_saved_rule =
        reg_rule.status == DW_DLV_OK && reg_rule.value_type == DW_EXPR_OFFSET && reg_rule.offset_relevant != 0;
    if (!has_saved_rule) {
        return *current_cfa + static_cast<uint64_t>(cfa_offset);
    }

    uint64_t address = *current_cfa + static_cast<uint64_t>(reg_rule.offset);
    auto saved = memory_access->try_read_word(address, info_ptr->pointer_size);

    if (!saved.has_value()) {
        return std::nullopt;
    }
    return *saved + static_cast<uint64_t>(cfa_offset);
}

NativeFrameInspection::NativeFrameInspection(std::shared_ptr<MemoryAccess> memory_access,
                                             std::optional<NativeFrameDescription> frame_description,
                                             std::optional<uint64_t> cfa, uint64_t pc)
    : memory_access(std::move(memory_access)), frame_description(std::move(frame_description)), cfa(cfa), pc(pc) {}

std::optional<uint64_t> NativeFrameInspection::read_register(int register_index) const {
    if (frame_description.has_value()) {
        return frame_description->try_read_register(register_index, cfa);
    }
    return memory_access->read_register(static_cast<uint64_t>(register_index));
}

std::optional<uint64_t> NativeFrameInspection::read_memory(uint64_t address, uint8_t register_size) const {
    return memory_access->try_read_word(address, register_size);
}

}  // namespace ttexalens::native_elf
