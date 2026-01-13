// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Register aliasing test - validates REGISTER rule in optimized builds.
//
// Tests:
// - Release builds (-O3): REGISTER rules (value moved to different register)
// - Callee-saved register restoration across frames
// - Register aliasing patterns where multiple variables share registers
//
// In optimized builds, the compiler may:
// - Move values between registers (REGISTER rule: R5 is stored in R8)
// - Reuse registers for different variables
// - Keep frequently-used values in callee-saved registers

#include <cstdint>

// Volatile to prevent compiler from optimizing away the entire program
volatile uint32_t g_result = 0;

// Compute function - uses multiple parameters to create register pressure
__attribute__((noinline)) uint32_t compute(uint32_t x, uint32_t y, uint32_t z, uint32_t w) {
    // Multiple operations to encourage register aliasing
    uint32_t a = x + y;
    uint32_t b = z + w;
    uint32_t c = x * 2;
    uint32_t d = y * 3;

    uint32_t result = a + b + c + d;

    // Capture callstack here - optimizer will have moved values around
    asm volatile("ebreak" ::: "memory");

    g_result = result;
    return result;
}

// Wrapper function - creates scenario for register aliasing
__attribute__((noinline)) uint32_t wrapper(uint32_t value) {
    // Create multiple related values from same input
    // In optimized code, these encourage the compiler to use REGISTER rules
    uint32_t a = value;
    uint32_t b = value + 1;
    uint32_t c = value + 2;
    uint32_t d = value + 3;

    // Pass to compute - forces register shuffling
    return compute(a, b, c, d);
}

int main() {
    // Simple entry - creates 3-frame callstack: main → wrapper → compute
    return wrapper(100);
}
