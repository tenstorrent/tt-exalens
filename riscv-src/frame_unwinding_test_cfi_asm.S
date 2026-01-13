// SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

# Test program with explicit CFI directives to generate SAME_VALUE and REGISTER rules

    # Tell assembler to emit CFI directives into .debug_frame section
    .cfi_sections .debug_frame

    .text
    .align 2

# Global variables for testing
    .data
g_result:
    .word 0
g_input:
    .word 100

    .text

# Leaf function that triggers ebreak
    .globl leaf_function
    .type leaf_function, @function
leaf_function:
    .cfi_startproc
    # Simple leaf function with no stack frame
    # All callee-saved registers maintain SAME_VALUE

    # Compute result: a0 + a1 + a2 + a3
    add a0, a0, a1
    add a0, a0, a2
    add a0, a0, a3

    # Trigger ebreak to capture callstack
    ebreak

    ret
    .cfi_endproc
    .size leaf_function, .-leaf_function


# Middle function that demonstrates SAME_VALUE rules
    .globl middle_with_same_value
    .type middle_with_same_value, @function
middle_with_same_value:
    .cfi_startproc

    # Create minimal stack frame (only ra and sp)
    addi sp, sp, -16
    .cfi_def_cfa_offset 16
    sw ra, 8(sp)
    .cfi_offset 1, -8

    # Explicitly mark callee-saved registers as SAME_VALUE
    # These registers are NOT saved to the stack
    .cfi_same_value 8   # s0/fp
    .cfi_same_value 9   # s1
    .cfi_same_value 18  # s2
    .cfi_same_value 19  # s3
    .cfi_same_value 20  # s4
    .cfi_same_value 21  # s5
    .cfi_same_value 22  # s6
    .cfi_same_value 23  # s7
    .cfi_same_value 24  # s8
    .cfi_same_value 25  # s9
    .cfi_same_value 26  # s10
    .cfi_same_value 27  # s11

    # VAL_OFFSET: Register value IS (CFA + offset), not stored at that address
    # This indicates that register 3 (gp) contains the value CFA + 16
    # Useful when a register holds a computed address/value based on CFA
    .cfi_val_offset 3, 16   # gp = CFA + 16

    # Call leaf function (only modifies argument registers)
    addi a0, a0, 1
    addi a1, a1, 2
    addi a2, a2, 3
    addi a3, a3, 4
    call leaf_function

    # Restore and return
    lw ra, 8(sp)
    addi sp, sp, 16
    .cfi_restore 1
    .cfi_def_cfa_offset 0
    ret

    .cfi_endproc
    .size middle_with_same_value, .-middle_with_same_value


# Function that demonstrates REGISTER rules
    .globl function_with_register_rule
    .type function_with_register_rule, @function
function_with_register_rule:
    .cfi_startproc

    # REGISTER rule: Save s1's value in s2 (not in memory) BEFORE modifying stack
    # After this, to read s1's original value, we need to read from s2
    mv s2, s1

    # Create stack frame (only save what we actually modify: s0, ra)
    addi sp, sp, -16
    .cfi_def_cfa_offset 16
    sw ra, 12(sp)
    .cfi_offset 1, -4
    sw s0, 8(sp)
    .cfi_offset 8, -8

    # Now declare CFI rules after stack is set up
    .cfi_register 9, 18  # s1's previous value (0x2000) is now in s2

    # SAME_VALUE rules: These registers are NOT saved and NOT modified
    # s3, s4 keep their values (0x4000, 0x5000) from top_level_asm
    .cfi_same_value 19  # s3 = 0x4000
    .cfi_same_value 20  # s4 = 0x5000
    .cfi_same_value 21  # s5
    .cfi_same_value 22  # s6
    .cfi_same_value 23  # s7
    .cfi_same_value 24  # s8
    .cfi_same_value 25  # s9
    .cfi_same_value 26  # s10
    .cfi_same_value 27  # s11

    # Now modify s1 (original value is saved in s2)
    li s1, 0x9999

    # Do some computation with s0 (we'll restore it later)
    mv s0, a0

    # Call middle function - passes the test that s3/s4/etc have SAME_VALUE
    mv a0, s0
    li a1, 10
    li a2, 20
    li a3, 30
    call middle_with_same_value

    # Restore s1 from s2 (REGISTER rule in action)
    mv s1, s2

    # Regular restore
    lw s0, 8(sp)
    lw ra, 12(sp)
    addi sp, sp, 16
    .cfi_restore 8
    .cfi_restore 1
    .cfi_def_cfa_offset 0
    ret

    .cfi_endproc
    .size function_with_register_rule, .-function_with_register_rule


# Top-level function
    .globl top_level_asm
    .type top_level_asm, @function
top_level_asm:
    .cfi_startproc

    # Create stack frame and save callee-saved registers
    addi sp, sp, -32
    .cfi_def_cfa_offset 32
    sw ra, 24(sp)
    .cfi_offset 1, -8
    sw s0, 16(sp)
    .cfi_offset 8, -16
    sw s1, 8(sp)
    .cfi_offset 9, -24
    sw s2, 0(sp)
    .cfi_offset 18, -32

    # Set up registers with KNOWN TEST VALUES for verification
    # These values will be tested through SAME_VALUE/REGISTER rules
    li s0, 0x1000  # s0 = 0x1000 (will have SAME_VALUE in deeper frames)
    li s1, 0x2000  # s1 = 0x2000 (will be stored in s2 via REGISTER rule)
    li s2, 0x3000  # s2 = 0x3000 (will hold s1's value)
    li s3, 0x4000  # s3 = 0x4000 (will have SAME_VALUE)
    li s4, 0x5000  # s4 = 0x5000 (will have SAME_VALUE)

    # Call function with REGISTER rule
    mv a0, s0
    call function_with_register_rule

    # Result in a0, restore and return
    lw s2, 0(sp)
    lw s1, 8(sp)
    lw s0, 16(sp)
    lw ra, 24(sp)
    addi sp, sp, 32
    .cfi_restore 18
    .cfi_restore 9
    .cfi_restore 8
    .cfi_restore 1
    .cfi_def_cfa_offset 0
    ret

    .cfi_endproc
    .size top_level_asm, .-top_level_asm


# Main function
    .globl main
    .type main, @function
main:
    .cfi_startproc

    addi sp, sp, -16
    .cfi_def_cfa_offset 16
    sw ra, 8(sp)
    .cfi_offset 1, -8

    # Load input and call top_level
    la t0, g_input
    lw a0, 0(t0)
    call top_level_asm

    # Store result
    la t0, g_result
    sw a0, 0(t0)

    # Return
    lw ra, 8(sp)
    addi sp, sp, 16
    .cfi_restore 1
    .cfi_def_cfa_offset 0
    ret

    .cfi_endproc
    .size main, .-main
