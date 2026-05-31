// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// An example RISC-V program that is used to debug memory access to global variables.
#include <cstdint>

// Testing global variables that don't have DW_AT_location attributes, so
// their addresses have to be resolved via .symtab name or linkage name
// matching. C++ side declares them `extern`, so the compiler emits DIEs
// without DW_AT_location. The actual definitions are emitted via top-level
// asm() below without the compiler seeing their addresses.
extern "C" volatile uint32_t g_symtab_var_by_name;
namespace ttexalens_symtab_test {
extern volatile uint32_t g_symtab_var_by_linkage;
}

// Itanium-ABI mangling of `ttexalens_symtab_test::g_symtab_var_by_linkage`
// is _ZN<21>ttexalens_symtab_test<23>g_symtab_var_by_linkageE.
asm(R"(
.pushsection .data,"aw",@progbits
.global g_symtab_var_by_name
.type   g_symtab_var_by_name, @object
.size   g_symtab_var_by_name, 4
g_symtab_var_by_name: .word 0x11223344

.global _ZN21ttexalens_symtab_test23g_symtab_var_by_linkageE
.type   _ZN21ttexalens_symtab_test23g_symtab_var_by_linkageE, @object
.size   _ZN21ttexalens_symtab_test23g_symtab_var_by_linkageE, 4
_ZN21ttexalens_symtab_test23g_symtab_var_by_linkageE: .word 0x55667788
.popsection
)");

// File-static variables examples.
[[gnu::used]] static volatile uint32_t g_symtab_var_file_static = 0x99AABBCC;
namespace ttexalens_symtab_test {
[[gnu::used]] static volatile uint32_t g_symtab_var_ns_file_static = 0xDDEEFF00;
}
namespace ttexalens_symtab_test {
[[gnu::used]] volatile uint32_t* touch_local_static([[maybe_unused]] volatile int const* unused) {
    static volatile uint32_t g_symtab_local_static = 0xCAFE1234;
    return &g_symtab_local_static;
}
}  // namespace ttexalens_symtab_test

// These anchors for linking are never actually read by the test.
[[gnu::used]] static volatile uintptr_t g_symtab_test_anchors[] = {
    reinterpret_cast<uintptr_t>(&g_symtab_var_by_name),
    reinterpret_cast<uintptr_t>(&ttexalens_symtab_test::g_symtab_var_by_linkage),
    reinterpret_cast<uintptr_t>(&g_symtab_var_file_static),
    reinterpret_cast<uintptr_t>(&ttexalens_symtab_test::g_symtab_var_ns_file_static),
    reinterpret_cast<uintptr_t>(ttexalens_symtab_test::touch_local_static(nullptr)),
};

// Tests for constants.
constexpr uint32_t c_uint32_t = 0x11223344;
constexpr uint64_t c_uint64_t = 0x5566778899AABBCC;
constexpr float c_float = 0.5f;
constexpr double c_double = 2.718281828459;
constexpr bool c_bool_true = true;
constexpr bool c_bool_false = false;
constexpr int8_t c_int8_t = -100;
constexpr int16_t c_int16_t = -12345;
constexpr int32_t c_int32_t = -1234567;
constexpr int64_t c_int64_t = -1234567890123456789;

enum class EnumClass : uint32_t { VALUE_A = 0, VALUE_B = 1, VALUE_C = 2, VALUE_D = 3 };

enum EnumType : uint32_t { TYPE_X = 10, TYPE_Y = 20, TYPE_Z = 30 };

struct InnerStruct {
    uint16_t x;
    uint16_t y;
};

union UnionTest {
    uint32_t u32;
    float f32;
    uint8_t bytes[4];
    uint16_t words[2];
};

struct go_msg_t {
    uint32_t test;
    union {
        uint32_t packed;
        struct {
            uint8_t dispatch_message_offset;
            uint8_t master_x;
            uint8_t master_y;
            uint8_t signal;  // INIT, GO, DONE, RESET_RD_PTR
        };
    };
    uint32_t test2;
} __attribute__((packed));

struct BaseStruct {
    uint8_t base_field1;
    uint16_t base_field2;
    union {
        uint32_t packed;
        struct {
            uint8_t v1;
            uint8_t v2;
            uint8_t v3;
            uint8_t v4;
        };
    };
};

struct BaseStruct2 {
    uint8_t bs2_base_field1;
    uint16_t bs2_base_field2;
    union {
        uint32_t bs2_packed;
        struct {
            uint8_t bs2_v1;
            uint8_t bs2_v2;
            uint8_t bs2_v3;
            uint8_t bs2_v4;
        };
    };
};

struct GlobalStruct : public BaseStruct, public BaseStruct2 {
    uint32_t a;
    uint64_t b;
    uint8_t c[16];
    InnerStruct d[4];
    float f;
    double g;
    bool h[8];
    InnerStruct* p;
    UnionTest u;
    go_msg_t msg;
    uint32_t uint_array[4];
    uint32_t* uint_pointer;
    EnumClass enum_class_field;
    EnumType enum_type_field;
    uint32_t* invalid_memory_ptr;
    InnerStruct* wrong_type_ptr;
    int64_t signed_int_field;
};

GlobalStruct g_global_struct;
GlobalStruct* const g_global_const_struct_ptr = (GlobalStruct*)(0x60000);

void halt() {
    // Halt core with ebrake instruction
    asm volatile("ebreak");
}

void update_struct(GlobalStruct* gs) {
    // Fill in some test data
    gs->base_field1 = 0xAA;
    gs->base_field2 = 0xBBBB;
    gs->packed = 0x04030201;
    gs->bs2_base_field1 = 0xCC;
    gs->bs2_base_field2 = 0xDDDD;
    gs->bs2_packed = 0x08070605;
    gs->a = c_uint32_t;
    gs->b = c_uint64_t;
    for (int i = 0; i < 16; i++) {
        gs->c[i] = static_cast<uint8_t>(i);
    }
    for (int i = 0; i < 4; i++) {
        gs->d[i].x = static_cast<uint16_t>(i * 2);
        gs->d[i].y = static_cast<uint16_t>(i * 2 + 1);
    }
    gs->f = 2.0f;
    gs->g = 2.718281828459;
    for (int i = 0; i < 8; i++) {
        gs->h[i] = (i % 2 == 0);
    }
    gs->p = &gs->d[2];
    gs->u.f32 = 0.5f;
    gs->msg.test = 0x12345678;
    gs->msg.packed = 0xAABBCCDD;
    gs->msg.test2 = 0x87654321;
    gs->uint_array[0] = 0x11111111;
    gs->uint_array[1] = 0x22222222;
    gs->uint_array[2] = 0x33333333;
    gs->uint_array[3] = 0x44444444;
    gs->uint_pointer = &gs->uint_array[0];
    gs->enum_class_field = EnumClass::VALUE_C;
    gs->enum_type_field = TYPE_Y;
    gs->invalid_memory_ptr = reinterpret_cast<uint32_t*>(0xFFFF0000);
    gs->wrong_type_ptr = reinterpret_cast<InnerStruct*>(&gs->uint_array[0]);
    gs->signed_int_field = -123456789;
}

int main() {
    update_struct(&g_global_struct);
    update_struct(g_global_const_struct_ptr);
    halt();
    return 0;
}
