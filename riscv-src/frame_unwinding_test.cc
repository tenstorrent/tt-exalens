// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// Test program for DWARF frame unwinding with both debug and optimized code.
// This program is designed to test that variables and function arguments can be
// read correctly from non-top stack frames in both debug (-O0) and release (-O3) builds.
//
// In debug builds:
//   - Variables are typically saved to the stack (OFFSET rules)
//   - Tests that existing OFFSET rule support works correctly
//
// In release builds:
//   - Variables may stay in registers (SAME_VALUE, REGISTER rules)
//   - Tests the new frame state caching and previous frame reference implementation

#include <cstdint>

// Volatile to prevent compiler from optimizing away the entire program
volatile uint32_t g_result = 0;
volatile uint32_t g_checkpoint = 0;

// Leaf function - deepest in the callstack
// Uses multiple parameters to force register usage
__attribute__((noinline)) uint32_t leaf_function(uint32_t a, uint32_t b, uint32_t c, uint32_t d) {
    // Create local variables that will test different DWARF rules:
    // - In debug: likely stored on stack (OFFSET)
    // - In release: may stay in registers (SAME_VALUE, REGISTER)
    uint32_t local_x = a * 2;
    uint32_t local_y = b * 3;
    uint32_t local_z = c * 4;
    uint32_t local_w = d * 5;

    uint32_t result = local_x + local_y + local_z + local_w;

    // Set checkpoint so we can verify we reached this point
    g_checkpoint = 1;

    // Trigger ebreak - this is where we'll capture the callstack
    // The debugger should be able to read all the local variables above
    // as well as the function parameters a, b, c, d
    // Use memory clobber to prevent optimization across ebreak
    asm volatile("ebreak" ::: "memory");

    // Use result in a way that compiler can't optimize away
    // The volatile write ensures this code is not eliminated
    g_result += result;

    return result;
}

// Middle function - uses callee-saved registers in optimized builds
// This will generate interesting DWARF rules for register unwinding
__attribute__((noinline)) uint32_t middle_function(uint32_t param1, uint32_t param2) {
    // Use multiple variables to increase register pressure
    uint32_t temp1 = param1 + 100;
    uint32_t temp2 = param2 + 200;
    uint32_t temp3 = param1 * 2;
    uint32_t temp4 = param2 * 3;

    // Call leaf with computed values
    uint32_t result = leaf_function(temp1, temp2, temp3, temp4);

    // Use temps after the call to prevent optimization
    result += (temp1 + temp2 + temp3 + temp4) / 10;

    return result;
}

// Top function - entry point for the test
// Creates a multi-level callstack with various local variables
__attribute__((noinline)) uint32_t top_function(uint32_t input_value) {
    // Create multiple local variables with different lifetimes
    uint32_t local_a = input_value + 10;
    uint32_t local_b = input_value * 2;
    uint32_t local_c = input_value - 5;
    uint32_t local_d = input_value / 2;

    // Call middle function
    uint32_t result = middle_function(local_a, local_b);

    // Use remaining locals
    result += local_c + local_d;

    return result;
}

// Test function with nested calls and register aliasing
// In optimized builds, this should generate REGISTER rules where
// one register's value is stored in another register
__attribute__((noinline)) uint32_t compute_sum(uint32_t x, uint32_t y, uint32_t z) {
    uint32_t sum = x;
    sum += y;
    sum += z;

    // Set checkpoint
    g_checkpoint = 2;

    // Use memory clobber to prevent optimization across ebreak
    asm volatile("ebreak" ::: "memory");

    // Use sum after ebreak to prevent dead code elimination
    g_result += sum;

    return sum;
}

__attribute__((noinline)) uint32_t wrapper_function(uint32_t value) {
    // In optimized code, these might cause register aliasing
    uint32_t a = value;
    uint32_t b = value + 1;
    uint32_t c = value + 2;

    return compute_sum(a, b, c);
}

int main() {
    // Test 1: Multi-level callstack with complex register usage
    g_result = top_function(42);

    // Test 2: Register aliasing scenario
    g_result += wrapper_function(100);

    return 0;
}
