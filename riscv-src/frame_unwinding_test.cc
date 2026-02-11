// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Basic frame unwinding test - validates fundamental multi-frame unwinding.
//
// Tests:
// - Debug builds (-O0): OFFSET rules (variables saved to stack)
// - Release builds (-O3): OFFSET rules (compiler always generates OFFSET for saved registers)
// - 3-frame callstack: main → caller → callee
// - Reading arguments and local variables from non-top frames
//
// Note: Compilers do NOT generate SAME_VALUE or REGISTER rules automatically.
// See frame_unwinding_test_cfi_directives.S for tests with those rules.

#include <cstdint>

// Volatile to prevent compiler from optimizing away the entire program
volatile uint32_t g_result = 0;

// Callee function - deepest frame where we capture the callstack
__attribute__((noinline)) uint32_t callee(uint32_t a, uint32_t b, uint32_t c) {
    // Local variables - will test OFFSET DWARF rules (both debug and release)
    uint32_t sum = a + b + c;
    uint32_t product = a * b * c;
    uint32_t result = sum + product;

    // Capture callstack here
    asm volatile("ebreak" ::: "memory");

    // Use result to prevent dead code elimination
    g_result = result;
    return result;
}

// Caller function - middle frame with its own variables
__attribute__((noinline)) uint32_t caller(uint32_t x, uint32_t y) {
    // Variables that should be readable when we're in callee
    uint32_t temp1 = x + 10;
    uint32_t temp2 = y + 20;
    uint32_t temp3 = x * 2;

    // Call callee with computed values
    uint32_t result = callee(temp1, temp2, temp3);

    // Use temps to prevent optimization
    result += temp1 + temp2 + temp3;
    return result;
}

int main() {
    // Simple entry point - will be frame 2 in the callstack
    return caller(42, 17);
}
