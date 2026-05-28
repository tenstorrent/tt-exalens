// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include "dwarf_info_impl.hpp"

#include <elfio/elfio.hpp>

#include "elf_file_impl.hpp"

namespace ttexalens::native_elf::details {

ElfObjAccess::ElfObjAccess(std::weak_ptr<NativeElfFileImpl> elf_impl) : elf_impl(elf_impl) {
    auto locked = elf_impl.lock();

    if (!locked) {
        throw std::runtime_error("ElfObjAccess requires a valid NativeElfFileImpl");
    }

    // libdwarf returns `as_name` as a const char* — cache section names in
    // a member that lives as long as this object so the pointers stay valid.
    const size_t n = locked->sections.size();
    names.reserve(n);
    for (size_t i = 0; i < n; ++i) {
        names.emplace_back(locked->elf.sections[static_cast<unsigned int>(i)]->get_name());
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
    file_size = locked->file_size;
}

Dwarf_Small ElfObjAccess::pointer_size() const {
    auto locked = elf_impl.lock();

    if (!locked) {
        throw std::runtime_error("ElfObjAccess requires a valid NativeElfFileImpl");
    }

    return locked->elf.get_class() == ELFIO::ELFCLASS64 ? 8 : 4;
}

int ElfObjAccess::om_get_section_info(void* obj, Dwarf_Unsigned section_index, Dwarf_Obj_Access_Section_a* out,
                                      int* /*error*/) {
    auto* self = static_cast<ElfObjAccess*>(obj);
    auto locked = self->elf_impl.lock();

    if (!locked) {
        throw std::runtime_error("ElfObjAccess requires a valid NativeElfFileImpl");
    }

    if (section_index >= locked->elf.sections.size()) {
        return DW_DLV_NO_ENTRY;
    }
    const ELFIO::section* sec = locked->elf.sections[static_cast<unsigned int>(section_index)];
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

Dwarf_Small ElfObjAccess::om_get_byte_order(void* obj) {
    auto* self = static_cast<ElfObjAccess*>(obj);
    auto locked = self->elf_impl.lock();

    if (!locked) {
        throw std::runtime_error("ElfObjAccess requires a valid NativeElfFileImpl");
    }

    return locked->elf.get_encoding() == ELFIO::ELFDATA2LSB ? DW_END_little : DW_END_big;
}

Dwarf_Small ElfObjAccess::om_get_length_size(void* obj) {
    auto* self = static_cast<ElfObjAccess*>(obj);
    auto locked = self->elf_impl.lock();

    if (!locked) {
        throw std::runtime_error("ElfObjAccess requires a valid NativeElfFileImpl");
    }

    return locked->elf.get_class() == ELFIO::ELFCLASS64 ? 8 : 4;
}

Dwarf_Small ElfObjAccess::om_get_pointer_size(void* obj) {
    auto* self = static_cast<ElfObjAccess*>(obj);
    auto locked = self->elf_impl.lock();

    if (!locked) {
        throw std::runtime_error("ElfObjAccess requires a valid NativeElfFileImpl");
    }

    return locked->elf.get_class() == ELFIO::ELFCLASS64 ? 8 : 4;
}

Dwarf_Unsigned ElfObjAccess::om_get_filesize(void* obj) { return static_cast<ElfObjAccess*>(obj)->file_size; }

Dwarf_Unsigned ElfObjAccess::om_get_section_count(void* obj) {
    auto* self = static_cast<ElfObjAccess*>(obj);
    auto locked = self->elf_impl.lock();

    if (!locked) {
        throw std::runtime_error("ElfObjAccess requires a valid NativeElfFileImpl");
    }

    return locked->elf.sections.size();
}

// libdwarf wants section bytes via malloc — copy from ELFIO's own
// (lazily-loaded) data. ELFIO reads from its stream (our file_stream or
// our memory stream depending on the source), so libdwarf never touches
// the file/buffer directly.
int ElfObjAccess::om_load_section(void* obj, Dwarf_Unsigned section_index, Dwarf_Small** return_data, int* /*error*/) {
    auto* self = static_cast<ElfObjAccess*>(obj);
    auto locked = self->elf_impl.lock();

    if (!locked) {
        throw std::runtime_error("ElfObjAccess requires a valid NativeElfFileImpl");
    }

    if (section_index >= locked->elf.sections.size()) {
        return DW_DLV_NO_ENTRY;
    }
    const ELFIO::section* sec = locked->elf.sections[static_cast<unsigned int>(section_index)];
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

NativeDwarfInfoImpl::NativeDwarfInfoImpl(std::weak_ptr<NativeElfFileImpl> elf_impl)
    : obj_access(elf_impl), elf_impl(std::move(elf_impl)), pointer_size(obj_access.pointer_size()) {
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

NativeDwarfInfoImpl::~NativeDwarfInfoImpl() {
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

// Lazy CU cache (libdwarf's CU cursor is stateful and one-shot).
std::vector<NativeDwarfCompileUnit>& NativeDwarfInfoImpl::get_cus() {
    if (!loaded_cus) {
        loaded_cus = true;
        load_compile_units();
    }
    return cus;
}

std::pair<Dwarf_Fde*, Dwarf_Signed> NativeDwarfInfoImpl::get_fdes() {
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

void NativeDwarfInfoImpl::load_compile_units() {
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
        cu.die = register_die(std::move(die_handle));
        cus.push_back(std::move(cu));
    }
}

NativeDwarfDiePtr NativeDwarfInfoImpl::register_die(DwarfDieHandle handle) {
    DwarfErrorHandle error(dbg);
    Dwarf_Off offset = 0;
    dwarf_dieoffset(handle, &offset, &error);
    auto it = die_cache.find(offset);
    if (it != die_cache.end()) {
        return it->second;  // libdwarf hands out a fresh Dwarf_Die per call — drop the dup
    }
    auto die = std::make_shared<NativeDwarfDie>(std::move(handle), shared_from_this());
    die_cache.emplace(offset, die);
    return die;
}

NativeDwarfDiePtr NativeDwarfInfoImpl::get_or_create_die(Dwarf_Off offset) {
    auto it = die_cache.find(offset);
    if (it != die_cache.end()) {
        return it->second;
    }
    DwarfErrorHandle error(dbg);
    DwarfDieHandle handle(dbg);
    if (dwarf_offdie_b(dbg, offset, /*is_info=*/true, &handle, &error) != DW_DLV_OK) {
        return nullptr;
    }
    auto die = std::make_shared<NativeDwarfDie>(std::move(handle), shared_from_this());
    die_cache.emplace(offset, die);
    return die;
}

NativeDwarfCompileUnit* NativeDwarfInfoImpl::get_die_cu(Dwarf_Off target_offset) {
    // TODO: Implement a more efficient lookup than linear search through all CU headers. A sorted vector + binary
    // search would be a simple improvement, or we could build a more complex index if needed.
    for (auto& cu : get_cus()) {
        const auto& cu_root = cu.get_die();
        if (!cu_root) {
            continue;
        }
        // DIEs in a CU live in [cu_root_offset, next_cu_offset).
        if (target_offset >= cu_root->get_offset() && target_offset < cu.get_next_cu_offset()) {
            return &cu;
        }
    }
    return nullptr;
}

NativeDwarfDiePtr NativeDwarfInfoImpl::find_parent(Dwarf_Off target_offset) {
    NativeDwarfCompileUnit* cu = get_die_cu(target_offset);
    if (cu == nullptr) {
        return nullptr;
    }
    const NativeDwarfDiePtr& cu_root = cu->get_die();
    if (target_offset == cu_root->get_offset()) {
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

const NativeElfSymbol* NativeDwarfInfoImpl::find_symbol_by_name(std::string_view name) {
    if (!loaded_symbols) {
        loaded_symbols = true;
        if (auto elf_impl_locked = elf_impl.lock()) {
            symbols = elf_impl_locked->read_symbol_table_section(".symtab");
            symbol_by_name.reserve(symbols.size());
            for (const NativeElfSymbol& sym : symbols) {
                if (sym.name.empty()) {
                    continue;
                }

                // NOTE: Currently we haven't encountered that duplicate entry is the problem
                // as we are defaulting to find_symbol only for external defined variables.
                symbol_by_name.emplace(std::string_view(sym.name), &sym);
            }
        }
    }
    auto it = symbol_by_name.find(name);
    return it == symbol_by_name.end() ? nullptr : it->second;
}

}  // namespace ttexalens::native_elf::details
