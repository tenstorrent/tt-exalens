// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// An example RISC-V program that is used to debug memory access to global variables.
#include <cstdint>

constexpr uint32_t c_uint32_t = 0x11223344;
constexpr uint64_t c_uint64_t = 0x5566778899AABBCC;
constexpr float c_float = 0.5f;
constexpr double c_double = 2.718281828459;

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
}

int main() {
    update_struct(&g_global_struct);
    update_struct(g_global_const_struct_ptr);
    halt();
    return 0;
}
