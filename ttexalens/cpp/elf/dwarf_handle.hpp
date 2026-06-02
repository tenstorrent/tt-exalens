// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <libdwarf.h>

#include <memory>
#include <utility>

namespace ttexalens::native_elf {

// Empty placeholder for handles that don't carry any per-instance state
// beyond the value pointer itself (e.g. DwarfLineContextHandle, whose
// cleanup function takes only the context).
struct DwarfHandleNoState {};

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

    // Like std::unique_ptr::release — relinquish ownership without invoking
    // do_cleanup.
    T release() noexcept {
        T tmp = value;
        value = nullptr;
        return tmp;
    }

    T* operator&() {
        reset();
        return &value;
    }

    T get() const { return value; }
    operator T() const { return value; }
    explicit operator bool() const { return value != nullptr; }

    // The blob libdwarf needs to release this resource — typically the
    // owning Dwarf_Debug. Exposed so wrapper classes (DwarfDie etc.)
    // can reuse it for further libdwarf calls instead of storing it twice.
    const State& get_state() const { return state; }

   protected:
    State state;
    T value = nullptr;
};

// RAII wrapper around Dwarf_Error. Released via dwarf_dealloc_error.
class DwarfErrorHandle : public DwarfHandleBase<DwarfErrorHandle, Dwarf_Error> {
   public:
    explicit DwarfErrorHandle(Dwarf_Debug dbg) : DwarfHandleBase(dbg) {}
    static void do_cleanup(Dwarf_Debug dbg, Dwarf_Error e) { dwarf_dealloc_error(dbg, e); }
};

// RAII wrapper around Dwarf_Line_Context. Released via dwarf_srclines_dealloc_b.
class DwarfLineContextHandle : public DwarfHandleBase<DwarfLineContextHandle, Dwarf_Line_Context, DwarfHandleNoState> {
   public:
    static void do_cleanup(DwarfHandleNoState, Dwarf_Line_Context ctx) { dwarf_srclines_dealloc_b(ctx); }
};

// RAII wrapper around a libdwarf allocation released via dwarf_dealloc.
template <typename T, Dwarf_Unsigned DwAllocType>
class DwarfAllocationHandle : public DwarfHandleBase<DwarfAllocationHandle<T, DwAllocType>, T> {
   public:
    explicit DwarfAllocationHandle(Dwarf_Debug dbg) : DwarfHandleBase<DwarfAllocationHandle<T, DwAllocType>, T>(dbg) {}
    static void do_cleanup(Dwarf_Debug dbg, T v) { dwarf_dealloc(dbg, v, DwAllocType); }
};

using DwarfDieHandle = DwarfAllocationHandle<Dwarf_Die, DW_DLA_DIE>;
using DwarfStringHandle = DwarfAllocationHandle<char*, DW_DLA_STRING>;
using DwarfAttributeHandle = DwarfAllocationHandle<Dwarf_Attribute, DW_DLA_ATTR>;
using DwarfBlockHandle = DwarfAllocationHandle<Dwarf_Block*, DW_DLA_BLOCK>;

// RAII wrapper around Dwarf_Loc_Head_c. Released via dwarf_dealloc_loc_head_c.
class DwarfLocHeadHandle : public DwarfHandleBase<DwarfLocHeadHandle, Dwarf_Loc_Head_c, DwarfHandleNoState> {
   public:
    static void do_cleanup(DwarfHandleNoState, Dwarf_Loc_Head_c head) { dwarf_dealloc_loc_head_c(head); }
};

struct DwarfAttributeListState {
    Dwarf_Debug dbg = nullptr;
    Dwarf_Signed count = 0;
};

// RAII for the (list, count) pair returned by dwarf_attrlist.
class DwarfAttributeListHandle
    : public DwarfHandleBase<DwarfAttributeListHandle, Dwarf_Attribute*, DwarfAttributeListState> {
   public:
    explicit DwarfAttributeListHandle(Dwarf_Debug dbg)
        : DwarfHandleBase<DwarfAttributeListHandle, Dwarf_Attribute*, DwarfAttributeListState>(
              DwarfAttributeListState{dbg, 0}) {}

    static void do_cleanup(DwarfAttributeListState state, Dwarf_Attribute* list) {
        for (Dwarf_Signed i = 0; i < state.count; ++i) {
            if (list[i] != nullptr) {
                dwarf_dealloc(state.dbg, list[i], DW_DLA_ATTR);
            }
        }
        dwarf_dealloc(state.dbg, list, DW_DLA_LIST);
    }

    // dwarf_attrlist writes the entry count through this slot.
    Dwarf_Signed* count_ptr() { return &state.count; }

    Dwarf_Signed size() const { return state.count; }
    Dwarf_Attribute operator[](Dwarf_Signed i) const { return get()[i]; }
};

}  // namespace ttexalens::native_elf
