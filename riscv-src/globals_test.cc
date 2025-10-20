// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// An example RISC-V program that is used to debug memory access to global variables.
#include <cstdint>

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

struct GlobalStruct {
    uint32_t a;
    uint64_t b;
    uint8_t c[16];
    InnerStruct d[4];
    float f;
    double g;
    bool h[8];
    InnerStruct* p;
    UnionTest u;
};

GlobalStruct g_global_struct;

void halt() {
    // Halt core with ebrake instruction
    asm volatile("ebreak");
}

int main() {
    // Fill in some test data
    g_global_struct.a = 0x11223344;
    g_global_struct.b = 0x5566778899AABBCC;
    for (int i = 0; i < 16; i++) {
        g_global_struct.c[i] = static_cast<uint8_t>(i);
    }
    for (int i = 0; i < 4; i++) {
        g_global_struct.d[i].x = static_cast<uint16_t>(i * 2);
        g_global_struct.d[i].y = static_cast<uint16_t>(i * 2 + 1);
    }
    g_global_struct.f = 2.0f;
    g_global_struct.g = 2.718281828459;
    for (int i = 0; i < 8; i++) {
        g_global_struct.h[i] = (i % 2 == 0);
    }
    g_global_struct.p = &g_global_struct.d[2];
    g_global_struct.u.f32 = 0.5f;
    halt();
    return 0;
}
