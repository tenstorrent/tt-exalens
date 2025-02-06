// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Simple program to test call stack printing
#include <stdint.h>

volatile uint32_t* g_MAILBOX = (volatile uint32_t*)0x4000;

// Registers for debug register access

void halt() {
    // Halt core with ebrake instruction
    asm volatile("ebreak");
}

int f1(int a) {
    if (a <= 1) {
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

void infloop() {
    for (;;) {
    }
}

int main() {
    int sum = recurse(*g_MAILBOX);

    *g_MAILBOX = sum;
    infloop();
    return 0;
}
