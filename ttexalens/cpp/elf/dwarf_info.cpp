// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_info.hpp"

#include <dwarf.h>  // DW_END_* constants
#include <libdwarf.h>

#include <cstdlib>
#include <cstring>
#include <elfio/elfio.hpp>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "dwarf_cu.hpp"
#include "dwarf_die.hpp"
#include "dwarf_frame.hpp"
#include "private/dwarf_info_impl.hpp"

namespace ttexalens::native_elf {

NativeDwarfInfo::NativeDwarfInfo(std::weak_ptr<details::NativeElfFileImpl> elf_impl)
    : impl(std::make_shared<details::NativeDwarfInfoImpl>(std::move(elf_impl))) {}

NativeDwarfInfo::~NativeDwarfInfo() = default;
NativeDwarfInfo::NativeDwarfInfo(NativeDwarfInfo&&) noexcept = default;
NativeDwarfInfo& NativeDwarfInfo::operator=(NativeDwarfInfo&&) noexcept = default;

std::optional<NativeDwarfFileLine> NativeDwarfInfo::find_file_line_by_address(uint64_t address) const {
    Dwarf_Debug dbg = impl->dbg;
    const Dwarf_Addr target = static_cast<Dwarf_Addr>(address);

    for (auto& cu : impl->get_cus()) {
        DwarfLineContextHandle& line_context = cu.get_line_context();
        if (!line_context) {
            continue;
        }

        DwarfErrorHandle error(dbg);
        Dwarf_Line* lines = nullptr;
        Dwarf_Signed line_count = 0;
        if (dwarf_srclines_from_linecontext(line_context, &lines, &line_count, &error) != DW_DLV_OK ||
            line_count == 0) {
            continue;
        }

        auto line_addr = [&](Dwarf_Signed i) -> Dwarf_Addr {
            Dwarf_Addr a = 0;
            dwarf_lineaddr(lines[i], &a, &error);
            return a;
        };

        // Quick reject: target outside this CU's line-table address range
        // (the +4 mirrors the last-entry fallback applied below). Both
        // bounds are pulled from the line context, which has them cached
        // — no extra parsing cost.
        if (target < line_addr(0) || target >= line_addr(line_count - 1) + 4) {
            continue;
        }

        // Binary search for the largest entry with address <= target
        // (upper_bound semantics: lo ends at the first entry whose addr > target).
        // Assumes line addresses within a CU are monotonically non-decreasing,
        // which holds for our RISC-V kernel ELFs.
        Dwarf_Signed lo = 0;
        Dwarf_Signed hi = line_count;
        while (lo < hi) {
            Dwarf_Signed mid = lo + (hi - lo) / 2;
            if (line_addr(mid) > target) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        if (lo == 0) {
            continue;  // target precedes every entry in this CU
        }
        const Dwarf_Signed match_idx = lo - 1;
        const Dwarf_Addr match_addr = line_addr(match_idx);

        // The matching entry covers [match_addr, next_addr). For the very last
        // entry there's no successor, so apply the +4 heuristic from the
        // existing Python ElfDwarf.file_lines_ranges.
        const Dwarf_Addr upper = (lo < line_count) ? line_addr(lo) : (match_addr + 4);
        if (target >= upper) {
            continue;
        }

        Dwarf_Line match = lines[match_idx];
        Dwarf_Unsigned ln = 0;
        Dwarf_Unsigned col = 0;
        NativeDwarfString src(dbg);
        dwarf_lineno(match, &ln, &error);
        dwarf_lineoff_b(match, &col, &error);
        dwarf_linesrc(match, &src, &error);
        return NativeDwarfFileLine{std::string(src.get()), static_cast<uint32_t>(ln), static_cast<uint32_t>(col)};
    }

    return std::nullopt;
}

NativeDwarfDiePtr NativeDwarfInfo::find_function_by_address(uint64_t address) const {
    const Dwarf_Addr target = static_cast<Dwarf_Addr>(address);
    NativeDwarfDiePtr best;
    Dwarf_Addr best_width = 0;

    auto range_contains = [target](const std::pair<Dwarf_Addr, Dwarf_Addr>& r) {
        return r.first <= target && target < r.second;
    };

    for (auto& cu : impl->get_cus()) {
        NativeDwarfDiePtr match;
        std::pair<Dwarf_Addr, Dwarf_Addr> match_range{0, 0};
        bool found = true;
        while (found) {
            found = false;
            const NativeDwarfDie& current = match ? *match : *cu.get_die();
            for (auto child = current.get_first_child(); child; child = child->get_next_sibling()) {
                bool child_matches = false;
                for (auto& r : child->get_address_ranges()) {
                    if (range_contains(r)) {
                        match_range = r;
                        child_matches = true;
                        break;
                    }
                }
                if (child_matches) {
                    match = std::move(child);
                    found = true;
                    break;
                }
            }
        }

        if (!match) {
            continue;
        }
        const Dwarf_Addr width = match_range.second - match_range.first;
        if (!best || width < best_width) {
            best_width = width;
            best = std::move(match);
        }
    }

    return best;
}

NativeDwarfDiePtr NativeDwarfInfo::get_die_by_name(std::string_view name) const {
    // Split "Foo::Bar::baz" into ["Foo", "Bar", "baz"]. An empty input yields
    // one empty part and ends up finding nothing.
    std::vector<std::string_view> parts;
    size_t start = 0;
    while (true) {
        size_t pos = name.find("::", start);
        if (pos == std::string_view::npos) {
            parts.push_back(name.substr(start));
            break;
        }
        parts.push_back(name.substr(start, pos - start));
        start = pos + 2;
    }

    NativeDwarfDiePtr declaration_die;  // fallback if all matches are declarations

    for (auto& cu : impl->get_cus()) {
        // First part is matched against the CU's root DIE; subsequent parts
        // chain off the previous match.
        auto current = cu.get_die()->find_child_by_name(parts[0]);
        bool matched_all = static_cast<bool>(current);
        for (size_t i = 1; matched_all && i < parts.size(); ++i) {
            auto next = current->find_child_by_name(parts[i]);
            if (!next) {
                matched_all = false;
                break;
            }
            current = std::move(next);
        }
        if (!matched_all) {
            continue;
        }

        // Follow NativeDwarfAttributeTag::abstract_origin OR NativeDwarfAttributeTag::specification (mutually
        // exclusive). If the attribute is present but the reference can't be resolved, give up entirely — matching the
        // Python implementation's defensive behavior.
        if (current->has_attribute(NativeDwarfAttributeTag::abstract_origin)) {
            auto origin = current->get_die_from_attribute(NativeDwarfAttributeTag::abstract_origin);
            if (!origin) {
                return nullptr;
            }
            current = std::move(origin);
        } else if (current->has_attribute(NativeDwarfAttributeTag::specification)) {
            auto spec = current->get_die_from_attribute(NativeDwarfAttributeTag::specification);
            if (!spec) {
                return nullptr;
            }
            current = std::move(spec);
        }

        if (current->is_declaration()) {
            declaration_die = std::move(current);
            continue;
        }

        return current;
    }

    return declaration_die;
}

std::optional<NativeFrameDescription> NativeDwarfInfo::get_frame_description(
    uint64_t pc, std::shared_ptr<MemoryAccess> memory_access) const {
    auto [fdes, fde_count] = impl->get_fdes();
    if (fdes == nullptr || fde_count == 0) {
        return std::nullopt;
    }
    DwarfErrorHandle error(impl->dbg);
    Dwarf_Fde fde = nullptr;
    Dwarf_Addr lopc = 0;
    Dwarf_Addr hipc = 0;
    if (dwarf_get_fde_at_pc(fdes, static_cast<Dwarf_Addr>(pc), &fde, &lopc, &hipc, &error) != DW_DLV_OK) {
        return std::nullopt;
    }
    return NativeFrameDescription(impl, fde, pc, std::move(memory_access));
}

const NativeElfSymbol* NativeDwarfInfo::find_symbol_by_name(std::string_view name) const {
    return impl->find_symbol_by_name(name);
}

std::optional<uint64_t> NativeDwarfInfo::get_enum_value(std::string_view name) const {
    auto die = get_die_by_name(name);
    if (!die) {
        return std::nullopt;
    }
    return std::visit(
        [](const auto& v) -> std::optional<uint64_t> {
            using T = std::decay_t<decltype(v)>;
            if constexpr (std::is_same_v<T, std::monostate>) {
                return std::nullopt;
            } else {
                return static_cast<uint64_t>(v);
            }
        },
        die->get_constant_value());
}

NativeDwarfDie::ConstantValue NativeDwarfInfo::get_constant(std::string_view name) const {
    auto die = get_die_by_name(name);
    if (!die) {
        throw SymbolNotFoundException(std::string(name));
    }
    auto type_die = die->get_resolved_type();
    if (!type_die || type_die->get_tag() != NativeDwarfDieTag::base_type) {
        throw TypeMismatchException("get_constant", type_die ? type_die->get_path() : std::string("<unknown>"));
    }
    auto value = die->get_constant_value();
    if (std::holds_alternative<std::monostate>(value)) {
        throw TypeMismatchException("get_constant", "<not-constant>");
    }
    return value;
}

NativeElfVariable NativeDwarfInfo::get_global(std::string_view name,
                                              std::shared_ptr<MemoryAccess> memory_access) const {
    auto die = get_die_by_name(name);
    if (!die) {
        throw SymbolNotFoundException(std::string(name));
    }
    auto address = die->get_address();
    if (!address) {
        throw SymbolNotFoundException(std::string(name));
    }
    auto resolved_type = die->get_resolved_type();

    // Hard-coded-pointer pattern: `T* const g = (T*)0xADDR;` — the DIE's
    // resolved type is pointer_type AND it carries a constant value. Treat
    // the constant as the target address and return a variable of the
    // pointee type.
    if (resolved_type && resolved_type->get_tag() == NativeDwarfDieTag::pointer_type) {
        auto cv = die->get_constant_value();
        if (!std::holds_alternative<std::monostate>(cv)) {
            auto pointee = resolved_type->get_dereference_type();
            if (pointee) {
                return NativeElfVariable(std::move(pointee), *address, std::move(memory_access));
            }
        }
    }
    return NativeElfVariable(std::move(resolved_type), *address, std::move(memory_access));
}

NativeElfVariable NativeDwarfInfo::read_global(std::string_view name,
                                               std::shared_ptr<MemoryAccess> memory_access) const {
    return get_global(name, std::move(memory_access)).read();
}

}  // namespace ttexalens::native_elf
