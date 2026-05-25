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

// CRTP base for libdwarf-owned resources. Holds the value + a `State` blob
// (defaults to Dwarf_Debug, since most cleanup functions need it) and
// provides the common RAII surface — destructor, move-only semantics,
// operator& that resets-and-exposes the slot, implicit conversion, get(),
// and explicit operator bool().
//
// Per-resource policy is supplied by the derived class via a static
//   static void do_cleanup(State, T);
// which the base calls from its destructor / move-assign / operator&. State
// lives in the base, so it stays alive through ~Derived → ~Base ordering.
//
// Usage:
//   class NativeDwarfError : public DwarfHandleBase<NativeDwarfError, Dwarf_Error> {
//      public:
//       using Base = DwarfHandleBase<NativeDwarfError, Dwarf_Error>;
//       using Base::Base;
//       static void do_cleanup(Dwarf_Debug dbg, Dwarf_Error e) { dwarf_dealloc_error(dbg, e); }
//   };
template <typename Derived, typename T, typename State = Dwarf_Debug>
class DwarfHandleBase {
   public:
    template <typename... Args>
    explicit DwarfHandleBase(Args&&... args) : state(std::forward<Args>(args)...) {}

    ~DwarfHandleBase() { reset(); }

    DwarfHandleBase(const DwarfHandleBase&) = delete;
    DwarfHandleBase& operator=(const DwarfHandleBase&) = delete;

    DwarfHandleBase(DwarfHandleBase&& other) noexcept : state(std::move(other.state)), value(other.value) {
        other.value = nullptr;
    }
    DwarfHandleBase& operator=(DwarfHandleBase&& other) noexcept {
        // std::addressof bypasses our custom operator&() which would reset other.
        if (this != std::addressof(other)) {
            reset();
            state = std::move(other.state);
            value = other.value;
            other.value = nullptr;
        }
        return *this;
    }

    void reset() {
        if (value != nullptr) {
            Derived::do_cleanup(state, value);
            value = nullptr;
        }
    }

    T* operator&() {
        reset();
        return &value;
    }

    T get() const { return value; }
    operator T() const { return value; }
    explicit operator bool() const { return value != nullptr; }

   protected:
    State state;
    T value = nullptr;
};

// Empty placeholder for handles that don't carry any per-instance state
// beyond the value pointer itself.
struct DwarfHandleNoState {};

// RAII wrappers around libdwarf resources. Each class specifies the cleanup policy via its static do_cleanup method.
template <typename T, Dwarf_Unsigned DwAllocType>
class DwarfAllocation : public DwarfHandleBase<DwarfAllocation<T, DwAllocType>, T> {
   public:
    explicit DwarfAllocation(Dwarf_Debug dbg) : DwarfHandleBase<DwarfAllocation<T, DwAllocType>, T>(dbg) {}
    static void do_cleanup(Dwarf_Debug dbg, T v) { dwarf_dealloc(dbg, v, DwAllocType); }
};

class NativeDwarfError : public DwarfHandleBase<NativeDwarfError, Dwarf_Error> {
   public:
    explicit NativeDwarfError(Dwarf_Debug dbg) : DwarfHandleBase(dbg) {}
    static void do_cleanup(Dwarf_Debug dbg, Dwarf_Error e) { dwarf_dealloc_error(dbg, e); }
};

class NativeDwarfLineContext : public DwarfHandleBase<NativeDwarfLineContext, Dwarf_Line_Context, DwarfHandleNoState> {
   public:
    static void do_cleanup(DwarfHandleNoState, Dwarf_Line_Context ctx) { dwarf_srclines_dealloc_b(ctx); }
};

class NativeDwarfDie {
   public:
    explicit NativeDwarfDie(Dwarf_Debug dbg) : die(dbg) {}

    Dwarf_Die* operator&() { return &die; }
    operator Dwarf_Die() const { return die.get(); }
    explicit operator bool() const { return static_cast<bool>(die); }

   private:
    DwarfAllocation<Dwarf_Die, DW_DLA_DIE> die;
};

class NativeDwarfCompileUnit {
   public:
    explicit NativeDwarfCompileUnit(Dwarf_Debug dbg) : cu_die(dbg), dbg(dbg) {}

    NativeDwarfDie cu_die;
    Dwarf_Unsigned cu_header_length = 0;
    Dwarf_Half version = 0;
    Dwarf_Unsigned abbrev_offset = 0;
    Dwarf_Half address_size = 0;
    Dwarf_Half length_size = 0;
    Dwarf_Half extension_size = 0;
    Dwarf_Sig8 signature{};
    Dwarf_Unsigned type_offset = 0;
    Dwarf_Unsigned next_cu_offset = 0;
    Dwarf_Half header_cu_type = 0;

    // Lazy line context. First call invokes dwarf_srclines_b; later calls
    // return the cached context. Test the returned wrapper with operator bool
    // — empty means dwarf_srclines_b failed (loaded_line_context is set
    // regardless so we don't retry on every call).
    NativeDwarfLineContext& get_line_context() {
        if (!loaded_line_context) {
            loaded_line_context = true;
            NativeDwarfError error(dbg);
            Dwarf_Unsigned line_version = 0;
            Dwarf_Small table_count = 0;
            dwarf_srclines_b(cu_die, &line_version, &table_count, &line_context, &error);
        }
        return line_context;
    }

   private:
    Dwarf_Debug dbg;
    NativeDwarfLineContext line_context;
    bool loaded_line_context = false;
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
        NativeDwarfError error(dbg);
        while (true) {
            NativeDwarfCompileUnit cu(dbg);
            int res =
                dwarf_next_cu_header_e(dbg, /*is_info=*/true, &cu.cu_die, &cu.cu_header_length, &cu.version,
                                       &cu.abbrev_offset, &cu.address_size, &cu.length_size, &cu.extension_size,
                                       &cu.signature, &cu.type_offset, &cu.next_cu_offset, &cu.header_cu_type, &error);
            if (res != DW_DLV_OK) {
                break;  // NO_ENTRY (cursor done) or ERROR (auto-cleaned by ~error)
            }
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
        NativeDwarfLineContext& line_context = cu.get_line_context();
        if (!line_context) {
            continue;
        }

        NativeDwarfError error(dbg);
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
        DwarfAllocation<char*, DW_DLA_STRING> raw_src(dbg);
        dwarf_lineno(match, &ln, &error);
        dwarf_lineoff_b(match, &col, &error);
        std::string src;
        if (dwarf_linesrc(match, &raw_src, &error) == DW_DLV_OK && raw_src) {
            src = raw_src;
        }
        return NativeDwarfFileLine{std::move(src), static_cast<uint32_t>(ln), static_cast<uint32_t>(col)};
    }

    return std::nullopt;
}

}  // namespace ttexalens::native_elf
