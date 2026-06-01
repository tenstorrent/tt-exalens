// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <memory>
#include <string_view>
#include <utility>

#include "dwarf_handle.hpp"

namespace ttexalens::native_elf {

class NativeDwarfString {
   public:
    explicit NativeDwarfString(Dwarf_Debug dbg) : handle(dbg) {}

    explicit NativeDwarfString(DwarfStringHandle handle) : handle(std::move(handle)) { sync_view(); }

    NativeDwarfString(NativeDwarfString&& other) noexcept : handle(std::move(other.handle)), view(other.view) {
        other.view = {};
    }
    NativeDwarfString& operator=(NativeDwarfString&& other) noexcept {
        if (this != std::addressof(other)) {
            handle = std::move(other.handle);
            view = other.view;
            other.view = {};
        }
        return *this;
    }
    NativeDwarfString(const NativeDwarfString&) = delete;
    NativeDwarfString& operator=(const NativeDwarfString&) = delete;

    // Out-parameter access for libdwarf calls. handle.operator&() resets the
    // C-string slot; we mirror that here by clearing the cached view so the
    // next read re-syncs from the freshly-written handle.
    char** operator&() {
        view = {};
        return &handle;
    }

    operator std::string_view() const { return get(); }
    std::string_view get() const {
        if (view.empty()) {
            sync_view();
        }
        return view;
    }

    bool empty() const { return get().empty(); }

    // Like std::unique_ptr::release — relinquish ownership without invoking
    // dwarf_dealloc.
    void release() noexcept {
        (void)handle.release();
        view = {};
    }

   private:
    void sync_view() const {
        const char* p = handle.get();
        if (p != nullptr) {
            view = std::string_view(p);
        }
    }

    DwarfStringHandle handle;
    mutable std::string_view view;
};

}  // namespace ttexalens::native_elf
