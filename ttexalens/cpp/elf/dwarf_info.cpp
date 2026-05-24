// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_info.hpp"

#include <dwarf.h>  // DW_END_little / DW_END_big constants
#include <libdwarf.h>

#include <cstdlib>
#include <cstring>
#include <elfio/elfio.hpp>
#include <stdexcept>
#include <string>
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

// All NativeDwarfInfo state lives here. Impl is a private nested class, so
// neither libdwarf nor ELFIO appears in dwarf_info.hpp's surface.
//
// Member declaration order: obj_access first, dbg second. Destructor closes
// dbg via dwarf_object_finish before obj_access goes out of scope, so
// libdwarf still has a valid callback context during finish.
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
        if (dbg != nullptr) {
            dwarf_object_finish(dbg);
        }
    }

    Impl(const Impl&) = delete;
    Impl& operator=(const Impl&) = delete;

    ElfObjAccess obj_access;
    Dwarf_Debug dbg = nullptr;
};

NativeDwarfInfo::NativeDwarfInfo(ELFIO::elfio& elf, uint64_t file_size)
    : impl(std::make_unique<Impl>(elf, file_size)) {}

NativeDwarfInfo::~NativeDwarfInfo() = default;
NativeDwarfInfo::NativeDwarfInfo(NativeDwarfInfo&&) noexcept = default;
NativeDwarfInfo& NativeDwarfInfo::operator=(NativeDwarfInfo&&) noexcept = default;

}  // namespace ttexalens::native_elf
