// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include <cstdint>
#include <stdint.h>

extern void (* __init_array_start[])();
extern void (* __init_array_end[])();

#define RISCV_L1_REG_START_ADDR             0x00000000

extern "C" void wzerorange(uint32_t *start, uint32_t *end)
{
    for (; start != end; start++)
    {
        *start = 0;
    }
}

int main() {

	// Initialize some intrinsic functions
	for (void (** fptr)() = __init_array_start; fptr < __init_array_end; fptr++) {
 	    (**fptr)();
	}

    volatile uint32_t *MAILBOX = reinterpret_cast<volatile uint32_t *> (RISCV_L1_REG_START_ADDR);
	*VAR = 0x12345678;

	for (;;);	
}