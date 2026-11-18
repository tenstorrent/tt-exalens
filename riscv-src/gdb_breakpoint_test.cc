// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <cstdint>

volatile uint32_t g_round;
volatile uint32_t g_index;
volatile uint32_t g_sum;
volatile uint32_t g_table[8] = {3, 5, 7, 11, 13, 17, 19, 23};

void halt() { asm volatile("ebreak"); }

[[gnu::noinline]] void add_element() { g_sum = g_sum + g_table[g_index]; }

[[gnu::noinline]] void round_done() { g_round = g_round + 1; }

int main() {
    halt();
    while (true) {
        g_sum = 0;
        for (g_index = 0; g_index < 8; g_index = g_index + 1) {
            add_element();
        }
        round_done();
    }
    return 0;
}
