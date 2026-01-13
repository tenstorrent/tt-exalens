// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Deep callstack test - validates recursive frame unwinding through many frames.
//
// Tests:
// - 5-frame deep callstack (main → level4 → level3 → level2 → level1)
// - Recursive frame state caching
// - SAME_VALUE chain resolution through multiple frames
// - Stack unwinding with consistent variable propagation
//
// This stress-tests the frame state caching implementation by requiring
// the unwinder to walk through multiple frames to resolve register values.

#include <cstdint>

// Volatile to prevent compiler from optimizing away the entire program
volatile uint32_t g_result = 0;

// Level 1 - deepest function where we capture the callstack
__attribute__((noinline)) uint32_t level1(uint32_t n, uint32_t m) {
    uint32_t result = n * m;

    // Capture callstack - should see all 5 frames
    asm volatile("ebreak" ::: "memory");

    g_result = result;
    return result;
}

// Level 2 - passes values through, adds computation
__attribute__((noinline)) uint32_t level2(uint32_t n, uint32_t m) {
    uint32_t temp = n + 1;
    return level1(temp, m + 2);
}

// Level 3 - passes values through, adds computation
__attribute__((noinline)) uint32_t level3(uint32_t n, uint32_t m) {
    uint32_t temp = n + 3;
    return level2(temp, m + 4);
}

// Level 4 - passes values through, adds computation
__attribute__((noinline)) uint32_t level4(uint32_t n, uint32_t m) {
    uint32_t temp = n + 5;
    return level3(temp, m + 6);
}

int main() {
    // Entry point - creates 5-frame callstack
    return level4(10, 20);
}
