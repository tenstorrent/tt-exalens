// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_location.hpp"

#include <libdwarf.h>

#include <cstdio>
#include <cstring>

#include "dwarf_attribute.hpp"
#include "dwarf_cu.hpp"
#include "dwarf_die.hpp"
#include "dwarf_frame.hpp"
#include "dwarf_handle.hpp"

namespace ttexalens::native_elf {

namespace {

// Pulls (address_size, version, offset_size) — the three values the libdwarf
// location-list APIs need — from the DIE's owning compile unit.
struct CompileUnitDims {
    Dwarf_Half address_size = 0;
    Dwarf_Half version = 4;
    Dwarf_Half offset_size = 4;
};

std::optional<CompileUnitDims> cu_dims_for(const DwarfDie& die) {
    const DwarfCompileUnit* cu = die.get_cu();
    if (cu == nullptr) {
        return std::nullopt;
    }
    CompileUnitDims d;
    d.address_size = cu->get_address_size();
    d.version = cu->get_version();
    d.offset_size = cu->get_length_size();
    return d;
}

// Single parsed opcode + its operands. Mirrors what
// dwarf_get_location_op_value_c yields.
struct Op {
    Dwarf_Small op = 0;
    Dwarf_Unsigned a = 0;
    Dwarf_Unsigned b = 0;
    Dwarf_Unsigned c = 0;
};

// Maps DwarfAttributeTag to libdwarf's raw DW_AT_* number. Reusing the
// integer values directly — DwarfAttributeTag is a typed copy of
// libdwarf's DW_AT_* with matching numeric values.
Dwarf_Half raw_attr(DwarfAttributeTag tag) { return static_cast<Dwarf_Half>(tag); }

// Re-queries `attr_tag` from the live DIE, parses it as a location attribute
// (handling both plain exprloc and location lists), and returns the opcode
// list whose live range covers `pc`. Returns nullopt when the attribute is
// absent, can't be parsed, or has no entry covering `pc`.
std::optional<std::vector<Op>> parse_die_attribute_location(const DwarfDie& die, DwarfAttributeTag attr_tag,
                                                            uint64_t pc) {
    Dwarf_Debug dbg = die.get_state();
    DwarfErrorHandle error(dbg);
    DwarfAttributeHandle attr(dbg);
    if (dwarf_attr(static_cast<Dwarf_Die>(die), raw_attr(attr_tag), &attr, &error) != DW_DLV_OK || !attr) {
        return std::nullopt;
    }
    DwarfLocHeadHandle head;
    Dwarf_Unsigned list_len = 0;
    if (dwarf_get_loclist_c(attr.get(), &head, &list_len, &error) != DW_DLV_OK || !head || list_len == 0) {
        return std::nullopt;
    }
    unsigned int lkind = DW_LKIND_unknown;
    dwarf_get_loclist_head_kind(head.get(), &lkind, &error);
    for (Dwarf_Unsigned i = 0; i < list_len; ++i) {
        Dwarf_Small lle = 0;
        Dwarf_Unsigned raw_lopc = 0, raw_hipc = 0;
        Dwarf_Bool addr_unavail = 0;
        Dwarf_Addr cooked_lopc = 0, cooked_hipc = 0;
        Dwarf_Unsigned op_count = 0;
        Dwarf_Locdesc_c locdesc = nullptr;
        Dwarf_Small loclist_source = 0;
        Dwarf_Unsigned expr_offset = 0, locdesc_offset = 0;
        if (dwarf_get_locdesc_entry_d(head.get(), i, &lle, &raw_lopc, &raw_hipc, &addr_unavail, &cooked_lopc,
                                      &cooked_hipc, &op_count, &locdesc, &loclist_source, &expr_offset, &locdesc_offset,
                                      &error) != DW_DLV_OK) {
            continue;
        }
        // For a plain expression (DW_LKIND_expression) the range covers
        // everything — accept it. For a location list, the cooked range
        // selects which entry applies at `pc`.
        const bool in_range =
            (lkind == DW_LKIND_expression) || (pc >= cooked_lopc && (cooked_hipc == 0 || pc < cooked_hipc));
        if (!in_range) {
            continue;
        }
        std::vector<Op> ops;
        ops.reserve(op_count);
        for (Dwarf_Unsigned j = 0; j < op_count; ++j) {
            Op op;
            Dwarf_Unsigned op_offset = 0;
            if (dwarf_get_location_op_value_c(locdesc, j, &op.op, &op.a, &op.b, &op.c, &op_offset, &error) !=
                DW_DLV_OK) {
                return std::nullopt;
            }
            ops.push_back(op);
        }
        return ops;
    }
    return std::nullopt;
}

// Walks up DIE parents until we hit the enclosing subprogram or
// inlined_subroutine that actually carries a DW_AT_frame_base. Inlined
// frames share their parent's stack, so a fbreg inside an inlined body
// must resolve against the enclosing real function's frame_base, not the
// inlined declaration. We also peek through DW_AT_abstract_origin, since
// concrete subprogram instances frequently delegate the attribute to the
// out-of-line definition.
DwarfDiePtr find_enclosing_function(const DwarfDie& die) {
    auto has_frame_base = [](const DwarfDie& d) {
        if (d.has_attribute(DwarfAttributeTag::frame_base)) return true;
        if (auto origin = d.get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
            if (origin->has_attribute(DwarfAttributeTag::frame_base)) return true;
        }
        return false;
    };
    DwarfDiePtr current = die.get_parent();
    while (current) {
        const auto tag = current->get_tag();
        if ((tag == DwarfDieTag::subprogram || tag == DwarfDieTag::inlined_subroutine) && has_frame_base(*current)) {
            return current;
        }
        current = current->get_parent();
    }
    return nullptr;
}

class Evaluator {
   public:
    Evaluator(const DwarfDie& die, const FrameInspection* frame, Dwarf_Debug dbg, CompileUnitDims dims)
        : die(die), frame(frame), dbg(dbg), dims(dims) {}

    std::optional<LocationResult> run(const std::vector<Op>& ops) {
        // Composite location: ops contain DW_OP_piece / DW_OP_bit_piece.
        // Each piece is an independent sub-expression contributing some
        // bytes to the assembled value.
        for (const Op& op : ops) {
            if (op.op == DW_OP_piece || op.op == DW_OP_bit_piece) {
                return run_composite(ops);
            }
        }
        LocationResult result;
        result.is_address = true;
        for (const Op& op : ops) {
            if (!step(op, result)) {
                return std::nullopt;
            }
        }
        if (!stack.empty()) {
            result.value = stack.back();
        }
        return result;
    }

   private:
    // Splits a composite expression at DW_OP_piece boundaries, evaluates
    // each sub-expression independently, and concatenates the resulting
    // bytes (little-endian) into a single materialised value.
    std::optional<LocationResult> run_composite(const std::vector<Op>& ops) {
        std::vector<std::byte> assembled;
        size_t start = 0;
        for (size_t i = 0; i < ops.size(); ++i) {
            const auto code = ops[i].op;
            if (code != DW_OP_piece && code != DW_OP_bit_piece) continue;
            std::vector<Op> piece_ops(ops.begin() + start, ops.begin() + i);
            start = i + 1;
            // DW_OP_bit_piece sizes in bits — round up to whole bytes; only
            // byte-aligned pieces are supported (the common case).
            const size_t byte_count =
                (code == DW_OP_piece) ? static_cast<size_t>(ops[i].a) : static_cast<size_t>((ops[i].a + 7) / 8);
            if (byte_count == 0) continue;
            // Empty sub-expression (`DW_OP_piece N` alone) means "this slice
            // is undefined" — emit zero bytes so the assembled width stays
            // correct. Callers reading typed values will see a partial-junk
            // payload, which matches the legacy Python behaviour.
            if (piece_ops.empty()) {
                assembled.resize(assembled.size() + byte_count, std::byte{0});
                continue;
            }
            Evaluator sub(die, frame, dbg, dims);
            auto sub_result = sub.run(piece_ops);
            if (!sub_result.has_value() || !sub_result->value.has_value()) {
                return std::nullopt;
            }
            // Materialise `byte_count` bytes from the sub-result. If the
            // sub-result is an address, read live memory; otherwise the
            // value itself supplies the bits.
            std::vector<std::byte> piece_bytes(byte_count, std::byte{0});
            if (sub_result->is_address) {
                if (frame == nullptr) return std::nullopt;
                auto bytes = frame->read_memory(*sub_result->value, static_cast<uint8_t>(byte_count));
                if (!bytes.has_value()) return std::nullopt;
                const uint64_t v = *bytes;
                for (size_t b = 0; b < byte_count && b < sizeof(uint64_t); ++b) {
                    piece_bytes[b] = static_cast<std::byte>((v >> (8 * b)) & 0xFF);
                }
            } else {
                const uint64_t v = *sub_result->value;
                for (size_t b = 0; b < byte_count && b < sizeof(uint64_t); ++b) {
                    piece_bytes[b] = static_cast<std::byte>((v >> (8 * b)) & 0xFF);
                }
            }
            assembled.insert(assembled.end(), piece_bytes.begin(), piece_bytes.end());
        }
        LocationResult result;
        result.is_address = false;
        result.raw_bytes = std::move(assembled);
        // Pack into the uint64 slot for callers that already work in
        // 64-bit space (the test suite reads single values up to 8 bytes).
        uint64_t packed = 0;
        for (size_t b = 0; b < result.raw_bytes.size() && b < sizeof(uint64_t); ++b) {
            packed |= static_cast<uint64_t>(result.raw_bytes[b]) << (8 * b);
        }
        result.value = packed;
        return result;
    }

   public:
   private:
    bool step(const Op& op, LocationResult& result) {
        const auto code = op.op;
        // Literal pushes -----------------------------------------------------
        if (code >= DW_OP_lit0 && code <= DW_OP_lit31) {
            stack.push_back(static_cast<uint64_t>(code - DW_OP_lit0));
            result.is_address = false;
            return true;
        }
        // Register direct ----------------------------------------------------
        if (code >= DW_OP_reg0 && code <= DW_OP_reg31) {
            return push_register(code - DW_OP_reg0, /*is_address=*/false, result);
        }
        if (code == DW_OP_regx) {
            return push_register(static_cast<int>(op.a), /*is_address=*/false, result);
        }
        // Register + offset --------------------------------------------------
        if (code >= DW_OP_breg0 && code <= DW_OP_breg31) {
            return push_register_offset(code - DW_OP_breg0, static_cast<int64_t>(op.a), result);
        }
        if (code == DW_OP_bregx) {
            return push_register_offset(static_cast<int>(op.a), static_cast<int64_t>(op.b), result);
        }
        switch (code) {
            case DW_OP_addr:
                stack.push_back(op.a);
                result.is_address = true;
                return true;
            case DW_OP_const1u:
            case DW_OP_const2u:
            case DW_OP_const4u:
            case DW_OP_const8u:
            case DW_OP_constu:
                stack.push_back(op.a);
                result.is_address = false;
                return true;
            case DW_OP_const1s:
            case DW_OP_const2s:
            case DW_OP_const4s:
            case DW_OP_const8s:
            case DW_OP_consts:
                // libdwarf hands signed constants back via the same Unsigned
                // slot; reinterpret as signed and let the stack store the
                // two's-complement bits.
                stack.push_back(static_cast<uint64_t>(static_cast<int64_t>(op.a)));
                result.is_address = false;
                return true;
            case DW_OP_fbreg: {
                auto fb = evaluate_frame_base();
                if (!fb.has_value()) return false;
                stack.push_back(*fb + static_cast<int64_t>(op.a));
                result.is_address = true;
                return true;
            }
            case DW_OP_call_frame_cfa: {
                if (frame == nullptr) return false;
                auto cfa = frame->get_cfa();
                if (!cfa.has_value()) return false;
                stack.push_back(*cfa);
                result.is_address = true;
                return true;
            }
            case DW_OP_deref:
                return op_deref(dims.address_size, result);
            case DW_OP_deref_size:
                return op_deref(static_cast<uint8_t>(op.a), result);
            case DW_OP_dup:
                if (stack.empty()) return false;
                stack.push_back(stack.back());
                return true;
            case DW_OP_drop:
                if (stack.empty()) return false;
                stack.pop_back();
                return true;
            case DW_OP_over:
                if (stack.size() < 2) return false;
                stack.push_back(stack[stack.size() - 2]);
                return true;
            case DW_OP_swap: {
                if (stack.size() < 2) return false;
                std::swap(stack[stack.size() - 1], stack[stack.size() - 2]);
                return true;
            }
            case DW_OP_rot: {
                if (stack.size() < 3) return false;
                uint64_t a = stack[stack.size() - 1];
                uint64_t b = stack[stack.size() - 2];
                uint64_t c = stack[stack.size() - 3];
                stack[stack.size() - 1] = b;
                stack[stack.size() - 2] = c;
                stack[stack.size() - 3] = a;
                return true;
            }
            case DW_OP_pick: {
                size_t depth = static_cast<size_t>(op.a);
                if (depth >= stack.size()) return false;
                stack.push_back(stack[stack.size() - 1 - depth]);
                return true;
            }
            case DW_OP_plus: {
                if (stack.size() < 2) return false;
                uint64_t a = stack.back();
                stack.pop_back();
                stack.back() = stack.back() + a;
                return true;
            }
            case DW_OP_plus_uconst:
                if (stack.empty()) return false;
                stack.back() = stack.back() + op.a;
                return true;
            case DW_OP_minus: {
                if (stack.size() < 2) return false;
                uint64_t a = stack.back();
                stack.pop_back();
                stack.back() = stack.back() - a;
                return true;
            }
            case DW_OP_mul: {
                if (stack.size() < 2) return false;
                uint64_t a = stack.back();
                stack.pop_back();
                stack.back() = stack.back() * a;
                return true;
            }
            case DW_OP_div: {
                if (stack.size() < 2) return false;
                int64_t a = static_cast<int64_t>(stack.back());
                stack.pop_back();
                if (a == 0) return false;
                int64_t b = static_cast<int64_t>(stack.back());
                stack.back() = static_cast<uint64_t>(b / a);
                return true;
            }
            case DW_OP_mod: {
                if (stack.size() < 2) return false;
                uint64_t a = stack.back();
                stack.pop_back();
                if (a == 0) return false;
                stack.back() = stack.back() % a;
                return true;
            }
            case DW_OP_and: {
                if (stack.size() < 2) return false;
                uint64_t a = stack.back();
                stack.pop_back();
                stack.back() &= a;
                return true;
            }
            case DW_OP_or: {
                if (stack.size() < 2) return false;
                uint64_t a = stack.back();
                stack.pop_back();
                stack.back() |= a;
                return true;
            }
            case DW_OP_xor: {
                if (stack.size() < 2) return false;
                uint64_t a = stack.back();
                stack.pop_back();
                stack.back() ^= a;
                return true;
            }
            case DW_OP_not:
                if (stack.empty()) return false;
                stack.back() = ~stack.back();
                return true;
            case DW_OP_neg:
                if (stack.empty()) return false;
                stack.back() = static_cast<uint64_t>(-static_cast<int64_t>(stack.back()));
                return true;
            case DW_OP_abs:
                if (stack.empty()) return false;
                stack.back() = static_cast<uint64_t>(std::llabs(static_cast<int64_t>(stack.back())));
                return true;
            case DW_OP_shl: {
                if (stack.size() < 2) return false;
                uint64_t shift = stack.back();
                stack.pop_back();
                stack.back() <<= (shift & 63);
                return true;
            }
            case DW_OP_shr: {
                if (stack.size() < 2) return false;
                uint64_t shift = stack.back();
                stack.pop_back();
                stack.back() >>= (shift & 63);
                return true;
            }
            case DW_OP_shra: {
                if (stack.size() < 2) return false;
                uint64_t shift = stack.back();
                stack.pop_back();
                stack.back() = static_cast<uint64_t>(static_cast<int64_t>(stack.back()) >> (shift & 63));
                return true;
            }
            case DW_OP_stack_value:
                // Top of stack IS the value; no memory deref.
                result.is_address = false;
                return true;
            case DW_OP_entry_value:
            case DW_OP_GNU_entry_value: {
                // operand1 = block-length; operand2 = byte offset of the
                // sub-expression within the original block. We don't
                // currently re-walk the function entry, so report
                // unresolved rather than synthesizing a wrong value.
                return false;
            }
            default:
                // Unhandled opcode (piece/bit_piece, regval_type, convert,
                // const_type, implicit_pointer, …). Bailing keeps
                // partial-evaluation results out of the caller's hands.
                return false;
        }
    }

    bool push_register(int reg_index, bool is_address, LocationResult& result) {
        if (frame == nullptr) return false;
        auto v = frame->read_register(reg_index);
        if (!v.has_value()) return false;
        stack.push_back(*v);
        result.is_address = is_address;
        return true;
    }

    bool push_register_offset(int reg_index, int64_t offset, LocationResult& result) {
        if (frame == nullptr) return false;
        auto v = frame->read_register(reg_index);
        if (!v.has_value()) return false;
        stack.push_back(*v + static_cast<uint64_t>(offset));
        result.is_address = true;
        return true;
    }

    bool op_deref(uint8_t size, LocationResult& result) {
        if (stack.empty() || frame == nullptr) return false;
        uint64_t addr = stack.back();
        stack.pop_back();
        auto v = frame->read_memory(addr, size);
        if (!v.has_value()) return false;
        stack.push_back(*v);
        result.is_address = false;
        return true;
    }

    // Recovers the enclosing function's frame_base value. DW_AT_frame_base is
    // itself a location expression: evaluate it and return whatever it
    // computed (the value, regardless of whether the inner expr labeled it
    // an address — frame_base IS the address by convention).
    std::optional<uint64_t> evaluate_frame_base() {
        auto func = find_enclosing_function(die);
        if (!func) return std::nullopt;
        // Concrete subprogram instances often delegate the frame_base via
        // DW_AT_abstract_origin to their out-of-line definition.
        DwarfDiePtr fb_die = func;
        if (!fb_die->has_attribute(DwarfAttributeTag::frame_base)) {
            if (auto origin = fb_die->get_die_from_attribute(DwarfAttributeTag::abstract_origin)) {
                if (origin->has_attribute(DwarfAttributeTag::frame_base)) {
                    fb_die = origin;
                }
            }
        }
        if (!fb_die->has_attribute(DwarfAttributeTag::frame_base)) return std::nullopt;
        const uint64_t pc = (frame != nullptr) ? frame->get_pc() : 0;
        auto fb_ops = parse_die_attribute_location(*fb_die, DwarfAttributeTag::frame_base, pc);
        if (!fb_ops.has_value()) return std::nullopt;
        // Frame-base sub-evaluation runs against the same frame context, but
        // anchored at `fb_die` for any nested fbreg (rare; safe to share).
        Evaluator sub(*fb_die, frame, dbg, dims);
        auto sub_result = sub.run(*fb_ops);
        if (!sub_result.has_value() || !sub_result->value.has_value()) {
            return std::nullopt;
        }
        return *sub_result->value;
    }

    const DwarfDie& die;
    const FrameInspection* frame;
    Dwarf_Debug dbg;
    CompileUnitDims dims;
    std::vector<uint64_t> stack;
};

}  // namespace

std::optional<LocationResult> evaluate_die_location(const DwarfDie& die, const FrameInspection* frame) {
    if (!die.has_attribute(DwarfAttributeTag::location)) {
        return std::nullopt;
    }
    auto dims = cu_dims_for(die);
    if (!dims.has_value()) {
        return std::nullopt;
    }
    // Pick the locdesc whose live PC range applies (plain expressions match
    // unconditionally; location lists require a frame PC).
    const uint64_t pc = (frame != nullptr) ? frame->get_pc() : 0;
    auto ops = parse_die_attribute_location(die, DwarfAttributeTag::location, pc);
    if (!ops.has_value()) {
        std::fprintf(stderr, "[loc] %s @0x%lx: parse failed\n", std::string(die.get_name()).c_str(), (unsigned long)pc);
        return std::nullopt;
    }
    std::fprintf(stderr, "[loc] %s @0x%lx: %zu ops, first=0x%02x a=0x%llx\n", std::string(die.get_name()).c_str(),
                 (unsigned long)pc, ops->size(), ops->empty() ? 0 : ops->front().op,
                 ops->empty() ? 0ULL : (unsigned long long)ops->front().a);
    Dwarf_Debug dbg = die.get_state();
    Evaluator evaluator(die, frame, dbg, *dims);
    auto r = evaluator.run(*ops);
    if (r.has_value() && r->value.has_value()) {
        std::fprintf(stderr, "[loc] %s @0x%lx: result is_address=%d value=0x%llx\n",
                     std::string(die.get_name()).c_str(), (unsigned long)pc, r->is_address,
                     (unsigned long long)*r->value);
    }
    return r;
}

}  // namespace ttexalens::native_elf
