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

#include "dwarf_cfi.hpp"
#include "dwarf_cu.hpp"
#include "dwarf_die.hpp"

namespace ttexalens::native_elf {

namespace {

// Adapter that lets libdwarf read DWARF data from an already-parsed
// ELFIO::elfio without opening the file again (path-loaded) or needing a path
// at all (from_bytes). Implements the Dwarf_Obj_Access_Interface_a vtable.
class ElfObjAccess {
   public:
    ElfObjAccess(ELFIO::elfio& elf, uint64_t file_size) : elf(elf), file_size(file_size) {
        // libdwarf returns `as_name` as a const char* — cache section names in
        // a member that lives as long as this object so the pointers stay valid.
        const size_t n = elf.sections.size();
        names.reserve(n);
        for (size_t i = 0; i < n; ++i) {
            names.emplace_back(elf.sections[static_cast<unsigned int>(i)]->get_name());
        }

        methods.om_get_section_info = &ElfObjAccess::om_get_section_info;
        methods.om_get_byte_order = &ElfObjAccess::om_get_byte_order;
        methods.om_get_length_size = &ElfObjAccess::om_get_length_size;
        methods.om_get_pointer_size = &ElfObjAccess::om_get_pointer_size;
        methods.om_get_filesize = &ElfObjAccess::om_get_filesize;
        methods.om_get_section_count = &ElfObjAccess::om_get_section_count;
        methods.om_load_section = &ElfObjAccess::om_load_section;
        methods.om_relocate_a_section = nullptr;  // we don't apply relocations
        methods.om_load_section_a = nullptr;      // not needed; om_load_section suffices
        methods.om_finish = nullptr;              // we manage our own cleanup

        iface.ai_object = this;
        iface.ai_methods = &methods;
    }

    Dwarf_Obj_Access_Interface_a* interface() { return &iface; }

   private:
    static int om_get_section_info(void* obj, Dwarf_Unsigned section_index, Dwarf_Obj_Access_Section_a* out,
                                   int* /*error*/) {
        auto* self = static_cast<ElfObjAccess*>(obj);
        if (section_index >= self->elf.sections.size()) {
            return DW_DLV_NO_ENTRY;
        }
        const ELFIO::section* sec = self->elf.sections[static_cast<unsigned int>(section_index)];
        if (sec == nullptr) {
            return DW_DLV_NO_ENTRY;
        }
        out->as_name = self->names[section_index].c_str();
        out->as_type = static_cast<Dwarf_Unsigned>(sec->get_type());
        out->as_flags = static_cast<Dwarf_Unsigned>(sec->get_flags());
        out->as_addr = static_cast<Dwarf_Addr>(sec->get_address());
        out->as_offset = static_cast<Dwarf_Unsigned>(sec->get_offset());
        out->as_size = static_cast<Dwarf_Unsigned>(sec->get_size());
        out->as_link = static_cast<Dwarf_Unsigned>(sec->get_link());
        out->as_info = static_cast<Dwarf_Unsigned>(sec->get_info());
        out->as_addralign = static_cast<Dwarf_Unsigned>(sec->get_addr_align());
        out->as_entrysize = static_cast<Dwarf_Unsigned>(sec->get_entry_size());
        return DW_DLV_OK;
    }

    static Dwarf_Small om_get_byte_order(void* obj) {
        auto* self = static_cast<ElfObjAccess*>(obj);
        return self->elf.get_encoding() == ELFIO::ELFDATA2LSB ? DW_END_little : DW_END_big;
    }

    static Dwarf_Small om_get_length_size(void* obj) {
        auto* self = static_cast<ElfObjAccess*>(obj);
        return self->elf.get_class() == ELFIO::ELFCLASS64 ? 8 : 4;
    }

    static Dwarf_Small om_get_pointer_size(void* obj) {
        auto* self = static_cast<ElfObjAccess*>(obj);
        return self->elf.get_class() == ELFIO::ELFCLASS64 ? 8 : 4;
    }

    static Dwarf_Unsigned om_get_filesize(void* obj) { return static_cast<ElfObjAccess*>(obj)->file_size; }

    static Dwarf_Unsigned om_get_section_count(void* obj) {
        return static_cast<ElfObjAccess*>(obj)->elf.sections.size();
    }

    // libdwarf wants section bytes via malloc — copy from ELFIO's own
    // (lazily-loaded) data. ELFIO reads from its stream (our file_stream or
    // our memory stream depending on the source), so libdwarf never touches
    // the file/buffer directly.
    static int om_load_section(void* obj, Dwarf_Unsigned section_index, Dwarf_Small** return_data, int* /*error*/) {
        auto* self = static_cast<ElfObjAccess*>(obj);
        if (section_index >= self->elf.sections.size()) {
            return DW_DLV_NO_ENTRY;
        }
        const ELFIO::section* sec = self->elf.sections[static_cast<unsigned int>(section_index)];
        if (sec == nullptr) {
            return DW_DLV_NO_ENTRY;
        }
        const Dwarf_Unsigned size = static_cast<Dwarf_Unsigned>(sec->get_size());
        if (size == 0) {
            return DW_DLV_NO_ENTRY;
        }
        const char* src = sec->get_data();
        if (src == nullptr) {
            return DW_DLV_NO_ENTRY;
        }
        Dwarf_Small* dst = static_cast<Dwarf_Small*>(std::malloc(size));
        if (dst == nullptr) {
            return DW_DLV_ERROR;
        }
        std::memcpy(dst, src, size);
        *return_data = dst;
        return DW_DLV_OK;
    }

    ELFIO::elfio& elf;
    uint64_t file_size;
    std::vector<std::string> names;
    Dwarf_Obj_Access_Methods_a methods{};
    Dwarf_Obj_Access_Interface_a iface{};
};

}  // namespace

class NativeDwarfInfo::Impl : public std::enable_shared_from_this<NativeDwarfInfo::Impl> {
   public:
    Impl(ELFIO::elfio& elf, uint64_t file_size) : obj_access(elf, file_size) {
        Dwarf_Error error = nullptr;
        int res = dwarf_object_init_b(obj_access.interface(),
                                      /*errhand=*/nullptr,
                                      /*errarg=*/nullptr, DW_GROUPNUMBER_ANY, &dbg, &error);

        if (res != DW_DLV_OK) {
            std::string msg = "Failed to initialize libdwarf from ELF object";
            if (res == DW_DLV_ERROR && error != nullptr) {
                msg += ": ";
                msg += dwarf_errmsg(error);
                dwarf_dealloc_error(dbg, error);
            } else if (res == DW_DLV_NO_ENTRY) {
                msg += ": no DWARF info present";
            }
            if (dbg != nullptr) {
                dwarf_object_finish(dbg);
                dbg = nullptr;
            }
            throw std::runtime_error(msg);
        }
    }

    ~Impl() {
        // DIE allocations must be released before dwarf_object_finish
        // invalidates dbg. Caller MUST not keep DIE shared_ptrs alive past
        // ~NativeDwarfInfo — nanobind's reference_internal handles this
        // automatically on the Python side.
        die_cache.clear();
        cus.clear();
        if (fdes != nullptr || cies != nullptr) {
            dwarf_dealloc_fde_cie_list(dbg, cies, cie_count, fdes, fde_count);
        }
        if (dbg != nullptr) {
            dwarf_object_finish(dbg);
        }
    }

    Impl(const Impl&) = delete;
    Impl& operator=(const Impl&) = delete;

    // Lazy CU cache (libdwarf's CU cursor is stateful and one-shot).
    std::vector<NativeDwarfCompileUnit>& get_cus() {
        if (!loaded_cus) {
            loaded_cus = true;
            load_compile_units();
        }
        return cus;
    }

    // Lazy CFI loader. Returns the FDE array (libdwarf-owned, lifetime tied
    // to ~Impl) plus its count. Tries .debug_frame first, then .eh_frame —
    // both produce the same Dwarf_Fde shape, so callers don't care which.
    // Returns (nullptr, 0) when neither section is present.
    std::pair<Dwarf_Fde*, Dwarf_Signed> get_fdes() {
        if (!loaded_cfi) {
            loaded_cfi = true;
            DwarfErrorHandle error(dbg);
            int res = dwarf_get_fde_list(dbg, &cies, &cie_count, &fdes, &fde_count, &error);
            if (res != DW_DLV_OK) {
                // Reset on partial failure so the EH path starts clean.
                cies = nullptr;
                cie_count = 0;
                fdes = nullptr;
                fde_count = 0;
                DwarfErrorHandle eh_error(dbg);
                if (dwarf_get_fde_list_eh(dbg, &cies, &cie_count, &fdes, &fde_count, &eh_error) != DW_DLV_OK) {
                    cies = nullptr;
                    cie_count = 0;
                    fdes = nullptr;
                    fde_count = 0;
                }
            }
        }
        return {fdes, fde_count};
    }

    ElfObjAccess obj_access;
    Dwarf_Debug dbg = nullptr;

   private:
    friend class NativeDwarfDie;

    void load_compile_units() {
        DwarfErrorHandle error(dbg);
        while (true) {
            DwarfDieHandle die_handle(dbg);
            NativeDwarfCompileUnit cu;
            int res =
                dwarf_next_cu_header_e(dbg, /*is_info=*/true, &die_handle, &cu.header_length, &cu.version,
                                       &cu.abbrev_offset, &cu.address_size, &cu.length_size, &cu.extension_size,
                                       &cu.signature, &cu.type_offset, &cu.next_cu_offset, &cu.header_cu_type, &error);
            if (res != DW_DLV_OK) {
                break;  // NO_ENTRY (cursor done) or ERROR (auto-cleaned by ~error)
            }
            cu.die = NativeDwarfDie::register_die(shared_from_this(), std::move(die_handle));
            cus.push_back(std::move(cu));
        }
    }

    std::vector<NativeDwarfCompileUnit> cus;
    std::unordered_map<Dwarf_Off, NativeDwarfDiePtr> die_cache;
    bool loaded_cus = false;

    // Call Frame Information state. cies/fdes are libdwarf-owned arrays
    // (allocated by dwarf_get_fde_list[_eh]) freed in ~Impl via
    // dwarf_dealloc_fde_cie_list. The pointers themselves are stable for
    // Impl's lifetime, so we hand raw Dwarf_Fde out to NativeFrameDescription
    // — its weak_ptr<Impl> gates whether they're still valid.
    Dwarf_Cie* cies = nullptr;
    Dwarf_Signed cie_count = 0;
    Dwarf_Fde* fdes = nullptr;
    Dwarf_Signed fde_count = 0;
    bool loaded_cfi = false;
};

NativeDwarfInfo::NativeDwarfInfo(ELFIO::elfio& elf, uint64_t file_size)
    : impl(std::make_shared<Impl>(elf, file_size)) {}

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
        return NativeDwarfFileLine{std::move(src), static_cast<uint32_t>(ln), static_cast<uint32_t>(col)};
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

        // Follow DW_AT_abstract_origin OR DW_AT_specification (mutually exclusive).
        // If the attribute is present but the reference can't be resolved, give up
        // entirely — matching the Python implementation's defensive behavior.
        if (current->has_attribute(DW_AT_abstract_origin)) {
            auto origin = current->get_die_from_attribute(DW_AT_abstract_origin);
            if (!origin) {
                return nullptr;
            }
            current = std::move(origin);
        } else if (current->has_attribute(DW_AT_specification)) {
            auto spec = current->get_die_from_attribute(DW_AT_specification);
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
    uint64_t pc, std::function<uint64_t(int)> read_gpr,
    std::function<std::optional<uint64_t>(uint64_t)> read_memory) const {
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
    return NativeFrameDescription(impl, impl->dbg, fde, pc, std::move(read_gpr), std::move(read_memory));
}

// Cache-interaction helpers for NativeDwarfDie. Defined here because they
// touch Impl's die_cache (private; NativeDwarfDie is a friend). The dwarf
// logic that calls these lives in dwarf_die.cpp.

NativeDwarfDiePtr NativeDwarfDie::register_die(std::shared_ptr<NativeDwarfInfo::Impl> info, DwarfDieHandle handle) {
    DwarfErrorHandle error(info->dbg);
    Dwarf_Off offset = 0;
    dwarf_dieoffset(handle, &offset, &error);
    auto it = info->die_cache.find(offset);
    if (it != info->die_cache.end()) {
        return it->second;  // libdwarf hands out a fresh Dwarf_Die per call — drop the dup
    }
    auto die = std::make_shared<NativeDwarfDie>(std::move(handle), info);
    info->die_cache.emplace(offset, die);
    return die;
}

NativeDwarfDiePtr NativeDwarfDie::get_or_create_die(std::shared_ptr<NativeDwarfInfo::Impl> info, Dwarf_Off offset) {
    auto it = info->die_cache.find(offset);
    if (it != info->die_cache.end()) {
        return it->second;
    }
    DwarfErrorHandle error(info->dbg);
    DwarfDieHandle handle(info->dbg);
    if (dwarf_offdie_b(info->dbg, offset, /*is_info=*/true, &handle, &error) != DW_DLV_OK) {
        return nullptr;
    }
    auto die = std::make_shared<NativeDwarfDie>(std::move(handle), info);
    info->die_cache.emplace(offset, die);
    return die;
}

NativeDwarfDiePtr NativeDwarfDie::find_parent(std::shared_ptr<NativeDwarfInfo::Impl> info, Dwarf_Off target_offset) {
    for (auto& cu : info->get_cus()) {
        // Check if target_offset is within this CU's DIE range.
        // DIEs in a CU live in [cu_root_offset, next_cu_offset).
        const auto& cu_root = cu.get_die();
        if (!cu_root) {
            continue;
        }
        const Dwarf_Off cu_root_offset = cu_root->get_offset();
        if (target_offset < cu_root_offset || target_offset >= cu.get_next_cu_offset()) {
            continue;
        }
        if (target_offset == cu_root_offset) {
            return nullptr;  // CU root has no parent.
        }

        // Search the CU's DIE tree for the target DIE, tracking the last DIE whose offset is <= target_offset.
        NativeDwarfDiePtr current = cu_root;
        while (current) {
            NativeDwarfDiePtr last_smaller;
            for (auto child = current->get_first_child(); child; child = child->get_next_sibling()) {
                const Dwarf_Off child_offset = child->get_offset();
                if (child_offset == target_offset) {
                    // Child is the target — parent is `current`
                    return current;
                }
                if (child_offset > target_offset) {
                    // Target is inside last_smaller's subtree
                    break;
                }
                last_smaller = child;
            }
            if (!last_smaller) {
                // This should never happen if target_offset is valid
                return nullptr;
            }
            current = std::move(last_smaller);
        }
        return nullptr;
    }
    return nullptr;
}

}  // namespace ttexalens::native_elf
