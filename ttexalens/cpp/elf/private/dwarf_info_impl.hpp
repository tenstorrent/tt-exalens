// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <memory>
#include <unordered_map>

#include "../dwarf_cu.hpp"
#include "../dwarf_die.hpp"
#include "../dwarf_frame.hpp"
#include "../dwarf_info.hpp"

namespace ttexalens::native_elf::details {

class ElfFileImpl;

// A half-open address range [low, high) mapped to the line-table row covering
// it. `line` is owned by the originating CU's cached line context and stays
// valid for the DwarfInfoImpl lifetime.
struct LineRange {
    Dwarf_Addr low;
    Dwarf_Addr high;
    Dwarf_Line line;
};

// Adapter that lets libdwarf read DWARF data from an already-parsed
// ELFIO::elfio without opening the file again (path-loaded) or needing a path
// at all (from_bytes). Implements the Dwarf_Obj_Access_Interface_a vtable.
class ElfObjAccess {
   public:
    ElfObjAccess(std::weak_ptr<ElfFileImpl> elf_impl);

    Dwarf_Obj_Access_Interface_a* interface() { return &iface; }

    Dwarf_Small pointer_size() const;

   private:
    static int om_get_section_info(void* obj, Dwarf_Unsigned section_index, Dwarf_Obj_Access_Section_a* out,
                                   int* /*error*/);
    static Dwarf_Small om_get_byte_order(void* obj);
    static Dwarf_Small om_get_length_size(void* obj);
    static Dwarf_Small om_get_pointer_size(void* obj);
    static Dwarf_Unsigned om_get_filesize(void* obj);
    static Dwarf_Unsigned om_get_section_count(void* obj);
    static int om_load_section(void* obj, Dwarf_Unsigned section_index, Dwarf_Small** return_data, int* /*error*/);

    std::weak_ptr<ElfFileImpl> elf_impl;
    uint64_t file_size;
    std::vector<std::string> names;
    Dwarf_Obj_Access_Methods_a methods{};
    Dwarf_Obj_Access_Interface_a iface{};
};

class DwarfInfoImpl : public std::enable_shared_from_this<DwarfInfoImpl> {
   public:
    DwarfInfoImpl(std::weak_ptr<ElfFileImpl> elf_impl);
    ~DwarfInfoImpl();

    DwarfInfoImpl(const DwarfInfoImpl&) = delete;
    DwarfInfoImpl& operator=(const DwarfInfoImpl&) = delete;

    // Lazy CU cache (libdwarf's CU cursor is stateful and one-shot).
    std::vector<DwarfCompileUnit>& get_cus();

    // Lazy, sorted address->line index across all CUs (see LineRange).
    const std::vector<LineRange>& get_line_ranges();

    // Lazy CFI loader. Returns the FDE array (libdwarf-owned, lifetime tied
    // to ~Impl) plus its count. Tries .debug_frame first, then .eh_frame —
    // both produce the same Dwarf_Fde shape, so callers don't care which.
    // Returns (nullptr, 0) when neither section is present.
    std::pair<Dwarf_Fde*, Dwarf_Signed> get_fdes();

    Dwarf_Debug get_dbg() const { return dbg; }

    DwarfDiePtr register_die(DwarfDieHandle handle);
    DwarfDiePtr get_or_create_die(Dwarf_Off offset);
    DwarfDiePtr find_parent(Dwarf_Off target_offset);
    DwarfCompileUnit* get_die_cu(Dwarf_Off target_offset);
    const ElfSymbol* find_symbol_by_name(std::string_view name);
    const ElfSymbol* find_symbol_by_demangled_name(std::string_view demangled);

   private:
    friend class ttexalens::native_elf::DwarfInfo;
    friend class ttexalens::native_elf::FrameDescription;

    void load_compile_units();
    void load_line_ranges();
    void load_symbols_table();

    ElfObjAccess obj_access;
    Dwarf_Debug dbg = nullptr;
    uint8_t pointer_size;

    std::vector<DwarfCompileUnit> cus;
    std::unordered_map<Dwarf_Off, DwarfDiePtr> die_cache;
    bool loaded_cus = false;

    // Sorted (by low) address->line index; see get_line_ranges().
    std::vector<LineRange> line_ranges;
    bool loaded_line_ranges = false;

    // Call Frame Information state. cies/fdes are libdwarf-owned arrays
    // (allocated by dwarf_get_fde_list[_eh]) freed in ~Impl via
    // dwarf_dealloc_fde_cie_list. The pointers themselves are stable for
    // Impl's lifetime, so we hand raw Dwarf_Fde out to FrameDescription
    // — its weak_ptr<Impl> gates whether they're still valid.
    Dwarf_Cie* cies = nullptr;
    Dwarf_Signed cie_count = 0;
    Dwarf_Fde* fdes = nullptr;
    Dwarf_Signed fde_count = 0;
    bool loaded_cfi = false;

    // Cache for loaded symbols
    bool loaded_symbols = false;
    std::vector<ElfSymbol> symbols;
    std::unordered_map<std::string_view, const ElfSymbol*> symbol_by_name;
    std::unordered_map<std::string_view, const ElfSymbol*> symbol_by_demangled_name;

    std::weak_ptr<ElfFileImpl> elf_impl;
};

}  // namespace ttexalens::native_elf::details
