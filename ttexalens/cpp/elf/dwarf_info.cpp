// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_info.hpp"

#include <dwarf.h>  // DW_END_* constants
#include <libdwarf.h>

#include <algorithm>
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
#include "memory_access.hpp"
#include "private/dwarf_info_impl.hpp"

namespace ttexalens::native_elf {

DwarfInfo::DwarfInfo(std::weak_ptr<details::ElfFileImpl> elf_impl)
    : impl(std::make_shared<details::DwarfInfoImpl>(std::move(elf_impl))) {}

DwarfInfo::~DwarfInfo() = default;
DwarfInfo::DwarfInfo(DwarfInfo&&) noexcept = default;
DwarfInfo& DwarfInfo::operator=(DwarfInfo&&) noexcept = default;

std::optional<DwarfFileLine> DwarfInfo::find_file_line_by_address(uint64_t address) const {
    const Dwarf_Addr target = static_cast<Dwarf_Addr>(address);
    const auto& ranges = impl->get_line_ranges();

    // Ranges are sorted by `low` but may overlap (inlining/LTO/COMDAT can make
    // line tables from different CUs describe the same address). Binary search to
    // the last range with low <= target, then walk left to the NARROWEST range
    // still covering target -- the most-specific source location, matching
    // find_function_by_address's narrowest-wins policy.
    //
    // The left-walk is bounded: any range covering target that starts at `low`
    // has width > target - low, and target - low only grows as we move left. So
    // once a candidate of width W is found, the first range with target - low >= W
    // ends the scan; nothing further left can be narrower. On the common
    // non-overlapping input this stops right after the single covering range.
    // (An address in a gap has no candidate to bound the scan and walks to the
    // start; that is acceptable here as lookups are per-frame, not in a hot loop.)
    auto it = std::upper_bound(ranges.begin(), ranges.end(), target,
                               [](Dwarf_Addr t, const details::LineRange& r) { return t < r.low; });

    const details::LineRange* best = nullptr;
    Dwarf_Addr best_width = 0;
    while (it != ranges.begin()) {
        --it;
        // Every range here has low <= target, so target - it->low is well-defined
        // and non-decreasing as we move left.
        if (best != nullptr && target - it->low >= best_width) {
            break;
        }
        if (target < it->high) {  // covers target (low <= target already holds)
            const Dwarf_Addr width = it->high - it->low;
            if (best == nullptr || width < best_width) {
                best = &(*it);
                best_width = width;
            }
        }
    }
    if (best == nullptr) {
        return std::nullopt;  // target precedes all ranges or lies in a gap
    }

    Dwarf_Debug dbg = impl->dbg;
    DwarfErrorHandle error(dbg);
    Dwarf_Unsigned ln = 0;
    Dwarf_Unsigned col = 0;
    DwarfString src(dbg);
    dwarf_lineno(best->line, &ln, &error);
    dwarf_lineoff_b(best->line, &col, &error);
    dwarf_linesrc(best->line, &src, &error);
    return DwarfFileLine{std::string(src.get()), static_cast<uint32_t>(ln), static_cast<uint32_t>(col)};
}

DwarfDiePtr DwarfInfo::find_function_by_address(uint64_t address) const {
    const Dwarf_Addr target = static_cast<Dwarf_Addr>(address);
    DwarfDiePtr best;
    Dwarf_Addr best_width = 0;

    auto range_contains = [target](const std::pair<Dwarf_Addr, Dwarf_Addr>& r) {
        return r.first <= target && target < r.second;
    };

    for (auto& cu : impl->get_cus()) {
        DwarfDiePtr match;
        std::pair<Dwarf_Addr, Dwarf_Addr> match_range{0, 0};
        bool found = true;
        while (found) {
            found = false;
            const DwarfDie& current = match ? *match : *cu.get_die();
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

namespace {

// Finds `parent`'s child named `name`. When `want_variable` is set, a
// DW_TAG_variable is preferred over a same-named non-variable (e.g. a
// `constexpr uint8_t noc_mode` over an `enum noc_mode` that precedes it),
// falling back to the first name-match if there is no variable.
DwarfDiePtr find_named_child(const DwarfDiePtr& parent, std::string_view name, bool want_variable) {
    if (!want_variable) {
        return parent->find_child_by_name(name);
    }
    DwarfDiePtr fallback;
    for (auto child = parent->get_first_child(); child; child = child->get_next_sibling()) {
        if (child->get_name() != name) {
            continue;
        }
        if (child->get_tag() == DwarfDieTag::variable) {
            return child;
        }
        if (!fallback) {  // copy, not move: `child` still advances the loop
            fallback = child;
        }
    }
    return fallback;
}

}  // namespace

DwarfDiePtr DwarfInfo::get_die_by_name(std::string_view name) const {
    return resolve_die_by_name(name, DieNameFilter::Any);
}

DwarfDiePtr DwarfInfo::resolve_die_by_name(std::string_view name, DieNameFilter filter) const {
    const bool prefer_variable = filter == DieNameFilter::Variable;

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

    DwarfDiePtr declaration_die;   // fallback if all matches are declarations
    DwarfDiePtr non_variable_die;  // fallback if nothing resolves to a variable

    for (auto& cu : impl->get_cus()) {
        // First part is matched against the CU's root DIE; subsequent parts
        // chain off the previous match. Only the final part prefers a variable.
        const auto want_variable = [&](size_t index) { return prefer_variable && index + 1 == parts.size(); };
        auto current = find_named_child(cu.get_die(), parts[0], want_variable(0));
        bool matched_all = static_cast<bool>(current);
        for (size_t i = 1; matched_all && i < parts.size(); ++i) {
            auto next = find_named_child(current, parts[i], want_variable(i));
            if (!next) {
                matched_all = false;
                break;
            }
            current = std::move(next);
        }
        if (!matched_all) {
            continue;
        }

        // Follow DwarfAttributeTag::abstract_origin OR DwarfAttributeTag::specification (mutually
        // exclusive). If the attribute is present but the reference can't be resolved, give up entirely — matching the
        // Python implementation's defensive behavior.
        if (current->has_attribute(DwarfAttributeTag::abstract_origin)) {
            auto origin = current->get_die_from_attribute(DwarfAttributeTag::abstract_origin);
            if (!origin) {
                return nullptr;
            }
            current = std::move(origin);
        } else if (current->has_attribute(DwarfAttributeTag::specification)) {
            auto spec = current->get_die_from_attribute(DwarfAttributeTag::specification);
            if (!spec) {
                return nullptr;
            }
            current = std::move(spec);
        }

        if (current->is_declaration()) {
            declaration_die = std::move(current);
            continue;
        }

        if (prefer_variable && current->get_tag() != DwarfDieTag::variable) {
            if (!non_variable_die) {
                non_variable_die = std::move(current);
            }
            continue;
        }

        return current;
    }

    if (non_variable_die) {
        return non_variable_die;
    }
    return declaration_die;
}

std::optional<FrameDescription> DwarfInfo::get_frame_description(uint64_t pc,
                                                                 std::shared_ptr<MemoryAccess> memory_access) const {
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
    return FrameDescription(impl, fde, pc, std::move(memory_access));
}

const ElfSymbol* DwarfInfo::find_symbol_by_name(std::string_view name) const { return impl->find_symbol_by_name(name); }

std::optional<uint64_t> DwarfInfo::get_enum_value(std::string_view name) const {
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

DwarfDie::ConstantValue DwarfInfo::get_constant(std::string_view name) const {
    auto die = resolve_die_by_name(name, DieNameFilter::Variable);
    if (!die) {
        throw SymbolNotFoundException(std::string(name));
    }
    auto type_die = die->get_resolved_type();
    if (!type_die || type_die->get_tag() != DwarfDieTag::base_type) {
        throw TypeMismatchException("get_constant", type_die ? type_die->get_path() : std::string("<unknown>"));
    }
    auto value = die->get_constant_value();
    if (std::holds_alternative<std::monostate>(value)) {
        throw TypeMismatchException("get_constant", "<not-constant>");
    }
    return value;
}

ElfVariable DwarfInfo::get_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const {
    auto die = resolve_die_by_name(name, DieNameFilter::Variable);
    if (!die) {
        throw SymbolNotFoundException(std::string(name));
    }
    // If the name only resolves to a type (no variable exists), it's not a
    // readable global — say so instead of reading a type DIE as memory.
    if (die->is_type()) {
        throw SymbolNotFoundException(std::string(name) + " (resolves to a type, not a variable)");
    }
    auto resolved_type = die->get_resolved_type();

    if (auto address = die->get_address()) {
        // Hard-coded-pointer pattern: `T* const g = (T*)0xADDR;` — the DIE's
        // resolved type is pointer_type AND it carries a constant value (which
        // get_address() surfaces as the target address). Return a variable of
        // the pointee type.
        if (resolved_type && resolved_type->get_tag() == DwarfDieTag::pointer_type) {
            auto cv = die->get_constant_value();
            if (!std::holds_alternative<std::monostate>(cv)) {
                auto pointee = resolved_type->get_dereference_type();
                if (pointee) {
                    return ElfVariable(std::move(pointee), *address, std::move(memory_access));
                }
            }
        }
        return ElfVariable(std::move(resolved_type), *address, std::move(memory_access));
    }

    // No runtime storage (folded constexpr): mask the difference by serving
    // the compile-time DW_AT_const_value from a synthesized buffer. Read-only
    // (writes raise via NoMemoryAccess), since there is nothing on device.
    if (resolved_type) {
        if (auto bytes = serialize_constant_value(die->get_constant_value(), resolved_type->get_size().value_or(4))) {
            auto cache = std::make_shared<CachedReadMemoryAccess>(0, std::move(*bytes), NoMemoryAccess::instance());
            return ElfVariable(std::move(resolved_type), 0, std::move(cache));
        }
    }
    throw SymbolNotFoundException(std::string(name));
}

ElfVariable DwarfInfo::read_global(std::string_view name, std::shared_ptr<MemoryAccess> memory_access) const {
    return get_global(name, std::move(memory_access)).read();
}

}  // namespace ttexalens::native_elf
