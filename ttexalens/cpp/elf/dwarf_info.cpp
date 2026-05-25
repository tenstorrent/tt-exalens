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
#include <utility>
#include <vector>

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

class NativeDwarfInfo::Impl {
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
        // CU DIE allocations must be released before dwarf_object_finish
        // invalidates dbg.
        cus.clear();
        if (dbg != nullptr) {
            dwarf_object_finish(dbg);
        }
    }

    Impl(const Impl&) = delete;
    Impl& operator=(const Impl&) = delete;

    // Lazy CU cache. First call walks libdwarf's stateful CU cursor to
    // completion; later calls return the cached vector. loaded_cus is set
    // before the walk so a mid-walk throw doesn't trigger an infinite
    // reload against a mid-iteration cursor.
    std::vector<NativeDwarfCompileUnit>& get_cus() {
        if (!loaded_cus) {
            loaded_cus = true;
            load_compile_units();
        }
        return cus;
    }

    ElfObjAccess obj_access;
    Dwarf_Debug dbg = nullptr;

   private:
    void load_compile_units() {
        DwarfErrorHandle error(dbg);
        while (true) {
            // libdwarf wants raw out-parameter slots; we let it write into a
            // local DwarfDieHandle + scalars, then assemble a
            // NativeDwarfCompileUnit from them. NativeDwarfCompileUnit /
            // NativeDwarfDie are immutable after construction.
            DwarfDieHandle die_handle(dbg);
            Dwarf_Unsigned header_length = 0;
            Dwarf_Half version = 0;
            Dwarf_Unsigned abbrev_offset = 0;
            Dwarf_Half address_size = 0;
            Dwarf_Half length_size = 0;
            Dwarf_Half extension_size = 0;
            Dwarf_Sig8 signature{};
            Dwarf_Unsigned type_offset = 0;
            Dwarf_Unsigned next_cu_offset = 0;
            Dwarf_Half header_cu_type = 0;
            int res = dwarf_next_cu_header_e(dbg, /*is_info=*/true, &die_handle, &header_length, &version,
                                             &abbrev_offset, &address_size, &length_size, &extension_size, &signature,
                                             &type_offset, &next_cu_offset, &header_cu_type, &error);
            if (res != DW_DLV_OK) {
                break;  // NO_ENTRY (cursor done) or ERROR (auto-cleaned by ~error)
            }
            NativeDwarfCompileUnit cu(NativeDwarfDie(std::move(die_handle)));
            cu.header_length = header_length;
            cu.version = version;
            cu.abbrev_offset = abbrev_offset;
            cu.address_size = address_size;
            cu.length_size = length_size;
            cu.extension_size = extension_size;
            cu.signature = signature;
            cu.type_offset = type_offset;
            cu.next_cu_offset = next_cu_offset;
            cu.header_cu_type = header_cu_type;
            cus.push_back(std::move(cu));
        }
    }

    std::vector<NativeDwarfCompileUnit> cus;
    bool loaded_cus = false;
};

NativeDwarfInfo::NativeDwarfInfo(ELFIO::elfio& elf, uint64_t file_size)
    : impl(std::make_unique<Impl>(elf, file_size)) {}

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

std::optional<NativeDwarfDie> NativeDwarfInfo::get_die_by_name(std::string_view name) const {
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

    std::optional<NativeDwarfDie> declaration_die;  // fallback if all matches are declarations

    for (auto& cu : impl->get_cus()) {
        // First part is matched against the CU's root DIE; subsequent parts
        // chain off the previous match.
        auto current = cu.get_die().find_child_by_name(parts[0]);
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
                return std::nullopt;
            }
            current = std::move(origin);
        } else if (current->has_attribute(DW_AT_specification)) {
            auto spec = current->get_die_from_attribute(DW_AT_specification);
            if (!spec) {
                return std::nullopt;
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

}  // namespace ttexalens::native_elf
