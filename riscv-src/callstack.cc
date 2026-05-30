// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Simple program to test call stack printing
#include <stdint.h>

extern uint32_t* __firmware_end;

volatile uint32_t* g_MAILBOX = (volatile uint32_t*)&__firmware_end;
static volatile uint32_t g_MAILBOX_anchor __attribute__((used)) = (uint32_t)(uintptr_t)&g_MAILBOX;

volatile uint8_t* g_MAILBOX_value = (volatile uint8_t*)(((uintptr_t)&__firmware_end + 4 + 16) & ~(uintptr_t)15);
static volatile uint32_t g_MAILBOX_value_anchor __attribute__((used)) = (uint32_t)(uintptr_t)&g_MAILBOX_value;

// Reads a value of type T from the host-written g_MAILBOX_value buffer at the given byte offset.
template <typename T>
static T host_value(unsigned offset) {
    return *reinterpret_cast<volatile T*>(g_MAILBOX_value + offset);
}

// A real string that the const char* value tests point at, so a test can read and verify its
// contents (rather than a pointer to nowhere). The single-frame and callee-saved tests get its
// address from the host (which resolves this symbol), the chained tests point at it directly.
char g_test_string[] __attribute__((used)) = "Tenstorrent callstack string";

void halt() {
    // Halt core with ebreak
    asm volatile("ebreak");
}

int f1(int a) {
    constexpr int recursion_end = 1;
    if (a <= recursion_end) {
        halt();
        return a;
    } else
        return f1(a - 1) + f1(a - 2);
}

int recurse(int depth) {
    if (depth > 0) {
        return f1(depth) + recurse(depth - 1);
    } else {
        halt();
        return 0;
    }
}

namespace ns {
int ns_int;
void foo() { halt(); }
}  // namespace ns

namespace template_test {
template <int ClassT1>
class TemplateClass {
   public:
    template <int FunctionT1>
    static void static_method() {
        recurse(ClassT1 + FunctionT1);
    }
};
}  // namespace template_test

#define TTEXALENS_KEEP_ON_STACK(arg, local) asm volatile("" : : "r"(&(arg)), "r"(&(local)) : "memory")

namespace value_test {

__attribute__((noinline, noclone)) void value_test_bool(bool arg) {
    bool local = false;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    halt();
}

__attribute__((noinline, noclone)) void value_test_uint8(uint8_t arg) {
    uint8_t local = 17;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_bool(true);
}

__attribute__((noinline, noclone)) void value_test_int8(int8_t arg) {
    int8_t local = 50;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_uint8(200);
}

__attribute__((noinline, noclone)) void value_test_uint16(uint16_t arg) {
    uint16_t local = 1234;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_int8(-100);
}

__attribute__((noinline, noclone)) void value_test_int16(int16_t arg) {
    int16_t local = 5678;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_uint16(60000);
}

__attribute__((noinline, noclone)) void value_test_uint32(uint32_t arg) {
    uint32_t local = 12345678;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_int16(-30000);
}

__attribute__((noinline, noclone)) void value_test_int32(int32_t arg) {
    int32_t local = 87654321;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_uint32(4000000000u);
}

__attribute__((noinline, noclone)) void value_test_uint64(uint64_t arg) {
    uint64_t local = 1234567890123ull;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_int32(-2000000000);
}

__attribute__((noinline, noclone)) void value_test_int64(int64_t arg) {
    int64_t local = 9876543210ll;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_uint64(18000000000000000000ull);
}

__attribute__((noinline, noclone)) void value_test_float(float arg) {
    float local = -1.25f;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_int64(-9000000000000000000ll);
}

__attribute__((noinline, noclone)) void value_test_double(double arg) {
    double local = -7.75;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_float(3.5f);
}

__attribute__((noinline, noclone)) void value_test_charptr(const char* arg) {
    const char* local = g_test_string;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_double(2.5);
}
}  // namespace value_test

namespace inline_value_test {

__attribute__((always_inline)) inline void value_test_bool(bool arg) {
    bool local = false;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    halt();
}

__attribute__((always_inline)) inline void value_test_uint8(uint8_t arg) {
    uint8_t local = 17;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_bool(true);
}

__attribute__((always_inline)) inline void value_test_int8(int8_t arg) {
    int8_t local = 50;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_uint8(200);
}

__attribute__((always_inline)) inline void value_test_uint16(uint16_t arg) {
    uint16_t local = 1234;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_int8(-100);
}

__attribute__((always_inline)) inline void value_test_int16(int16_t arg) {
    int16_t local = 5678;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_uint16(60000);
}

__attribute__((always_inline)) inline void value_test_uint32(uint32_t arg) {
    uint32_t local = 12345678;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_int16(-30000);
}

__attribute__((always_inline)) inline void value_test_int32(int32_t arg) {
    int32_t local = 87654321;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_uint32(4000000000u);
}

__attribute__((always_inline)) inline void value_test_uint64(uint64_t arg) {
    uint64_t local = 1234567890123ull;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_int32(-2000000000);
}

__attribute__((always_inline)) inline void value_test_int64(int64_t arg) {
    int64_t local = 9876543210ll;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_uint64(18000000000000000000ull);
}

__attribute__((always_inline)) inline void value_test_float(float arg) {
    float local = -1.25f;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_int64(-9000000000000000000ll);
}

__attribute__((always_inline)) inline void value_test_double(double arg) {
    double local = -7.75;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_float(3.5f);
}

__attribute__((always_inline)) inline void value_test_charptr(const char* arg) {
    const char* local = g_test_string;
    TTEXALENS_KEEP_ON_STACK(arg, local);
    value_test_double(2.5);
}

__attribute__((noinline)) void run() { value_test_charptr(g_test_string); }
}  // namespace inline_value_test

namespace single_frame_value_test {

volatile uint64_t single_frame_sink;

template <typename T>
__attribute__((noinline)) void value_test(T arg) {
    T local = host_value<T>(8);
    TTEXALENS_KEEP_ON_STACK(arg, local);
    asm volatile("ebreak");
}

__attribute__((noinline)) void dispatch(uint32_t type_index) {
    switch (type_index) {
        case 0:
            value_test<bool>(host_value<bool>(0));
            break;
        case 1:
            value_test<uint8_t>(host_value<uint8_t>(0));
            break;
        case 2:
            value_test<int8_t>(host_value<int8_t>(0));
            break;
        case 3:
            value_test<uint16_t>(host_value<uint16_t>(0));
            break;
        case 4:
            value_test<int16_t>(host_value<int16_t>(0));
            break;
        case 5:
            value_test<uint32_t>(host_value<uint32_t>(0));
            break;
        case 6:
            value_test<int32_t>(host_value<int32_t>(0));
            break;
        case 7:
            value_test<uint64_t>(host_value<uint64_t>(0));
            break;
        case 8:
            value_test<int64_t>(host_value<int64_t>(0));
            break;
        case 9:
            value_test<float>(host_value<float>(0));
            break;
        case 10:
            value_test<double>(host_value<double>(0));
            break;
        case 11:
            value_test<const char*>(host_value<const char*>(0));
            break;
    }
}
}  // namespace single_frame_value_test

// Declares reg_value, bound to the callee-saved register s2 and initialized from a distinct slot
// of the host-written g_MAILBOX_value buffer, then forces the value into the register.
#define DECLARE_CALLEE_SAVED_VALUE(type, slot)                        \
    register type reg_value asm("s2") = host_value<type>((slot) * 8); \
    asm volatile("" : "+r"(reg_value))

// Keeps reg_value live past the nested call so it is preserved in - or spilled from - s2.
#define USE_CALLEE_SAVED_VALUE() asm volatile("" : : "r"(reg_value))

namespace callee_saved_test {
// These functions form a chain that all reuse the same callee-saved register (s2), one value per
// type. Because every inner function reuses s2, it spills the caller's s2 in its prologue, so at
// the halt point every frame's value is recoverable by following the DWARF call-frame register
// rules - from where an inner frame spilled it (DW_CFA_offset), or, for the innermost frame, still
// live in s2 - exercising register recovery for all types in a single call stack evaluation. This
// is unlike a value left in a caller-saved register, which is lost once a deeper call clobbers it.

__attribute__((noinline, noclone)) void value_test_bool() {
    DECLARE_CALLEE_SAVED_VALUE(bool, 0);
    halt();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_uint8() {
    DECLARE_CALLEE_SAVED_VALUE(uint8_t, 1);
    value_test_bool();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_int8() {
    DECLARE_CALLEE_SAVED_VALUE(int8_t, 2);
    value_test_uint8();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_uint16() {
    DECLARE_CALLEE_SAVED_VALUE(uint16_t, 3);
    value_test_int8();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_int16() {
    DECLARE_CALLEE_SAVED_VALUE(int16_t, 4);
    value_test_uint16();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_uint32() {
    DECLARE_CALLEE_SAVED_VALUE(uint32_t, 5);
    value_test_int16();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_int32() {
    DECLARE_CALLEE_SAVED_VALUE(int32_t, 6);
    value_test_uint32();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_uint64() {
    DECLARE_CALLEE_SAVED_VALUE(uint64_t, 7);
    value_test_int32();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_int64() {
    DECLARE_CALLEE_SAVED_VALUE(int64_t, 8);
    value_test_uint64();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_float() {
    DECLARE_CALLEE_SAVED_VALUE(float, 9);
    value_test_int64();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_double() {
    DECLARE_CALLEE_SAVED_VALUE(double, 10);
    value_test_float();
    USE_CALLEE_SAVED_VALUE();
}

__attribute__((noinline, noclone)) void value_test_charptr() {
    DECLARE_CALLEE_SAVED_VALUE(const char*, 11);
    value_test_double();
    USE_CALLEE_SAVED_VALUE();
}
}  // namespace callee_saved_test

#undef DECLARE_CALLEE_SAVED_VALUE
#undef USE_CALLEE_SAVED_VALUE

int main() {
    if (*g_MAILBOX != 0xFFFFFFFF && *g_MAILBOX != 0xFFFFFFFE && *g_MAILBOX != 0xFFFFFFFD && *g_MAILBOX != 0xFFFFFFFC &&
        *g_MAILBOX != 0xFFFFFFFB && (*g_MAILBOX & 0xFFFFFF00) != 0xFFFFFE00 && (*g_MAILBOX < 0 || *g_MAILBOX > 1000)) {
        *g_MAILBOX = 10;
    }

    if (*g_MAILBOX == 0) {
        ns::foo();
    } else if (*g_MAILBOX == 0xFFFFFFFF) {
        template_test::TemplateClass<3>::static_method<-1>();
    } else if (*g_MAILBOX == 0xFFFFFFFE) {
        template_test::TemplateClass<4>::static_method<-3>();
    } else if (*g_MAILBOX == 0xFFFFFFFD) {
        value_test::value_test_charptr(g_test_string);
    } else if (*g_MAILBOX == 0xFFFFFFFC) {
        inline_value_test::run();
    } else if ((*g_MAILBOX & 0xFFFFFF00) == 0xFFFFFE00) {
        single_frame_value_test::dispatch(*g_MAILBOX & 0xFF);
    } else if (*g_MAILBOX == 0xFFFFFFFB) {
        callee_saved_test::value_test_charptr();
    } else {
        int sum = recurse(*g_MAILBOX);
        *g_MAILBOX = sum;
    }
    return 0;
}
