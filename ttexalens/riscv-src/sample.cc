// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// An example of a simple C++ program that can be compiled with the RISC-V GCC toolchain.
#include <stdint.h>
//#include "tt-gcov.h"

// re build/riscv-src/wormhole/sample.trisc0.elf -r trisc0

//extern const volatile struct gcov_info *volatile const __gcov_info_start[];
//extern const volatile struct gcov_info *volatile const __gcov_info_end[];

// Registers for debug register access

#define RISC_DBG_CNTL0 0xFFB12080
#define RISC_DBG_CNTL1 0xFFB12084
#define RISC_DBG_STATUS0 0xFFB12088
#define RISC_DBG_STATUS1 0xFFB1208C
#define RISCV_DEBUG_REGS_START_ADDR 0xFFB12000
#define RISCV_DEBUG_REG_WALL_CLOCK_L (RISCV_DEBUG_REGS_START_ADDR | 0x1F0)
#define RISCV_DEBUG_REG_WALL_CLOCK_H (RISCV_DEBUG_REGS_START_ADDR | 0x1F8)

volatile uint32_t g_MAILBOX;
volatile union {
    uint64_t all_bytes;
    struct {
        uint32_t low_32;
        uint32_t high_32;
    };
    uint8_t bytes[8];
} g_TESTBYTEACCESS;

void halt() {
    // Halt core with ebrake instruction
    asm volatile("ebreak");
}

void decrement_mailbox() { g_MAILBOX--; }

extern "C" void infloop() { for (;;); }

//extern uint8_t __gcov_trisc0_start[];
//extern const unsigned long int __gcov_trisc0_size;

void l1_write(const void* data, unsigned int length, void* arg)
{
    static unsigned int l1_written = 0;
    //uint8_t* new_gcov_data = (uint8_t*) data;
    //uint8_t volatile* l1_gcov_base = (uint8_t volatile*) __gcov_trisc0_start;
    
    //for(unsigned int i = 0; i < length; i++) {
    //    l1_gcov_base[l1_written++] = new_gcov_data[i];
    //}
    
    void* volatile* ptr = (void* volatile*) 200000;
    for(int i = 1; i < 128; i++) ptr[i] = (void*) 0xdeadbeef;
    //ptr[0] = (void*) l1_gcov_base;
    asm volatile("fence rw, rw" ::: "memory");
}

void fname_callback(const char* fname, void* arg)
{
    //__gcov_filename_to_gcfn(fname, l1_write, nullptr);
}

void* alloc(unsigned idk, void* arg)
{
    (void) idk;
    (void) arg;
    return nullptr;
}

int main() {
    l1_write(nullptr, 0, nullptr);
    g_TESTBYTEACCESS.all_bytes = 0x0102030405060708;

    // STEP 1: Set the mailbox to RISC_DBG_STATUS1
    g_MAILBOX = RISC_DBG_STATUS1;

    // STEP 2: Wait for mailbox to become 0x1234
    while (g_MAILBOX != 0x1234) {
        // wait for mailbox to be set to 0x1234
    }

    // STEP 3: Set the mailbox to RISC_DBG_CNTL0
    g_MAILBOX = RISC_DBG_CNTL0;

    // STEP 4: Put the core in halted state
    halt();

    // STEP 5: Set the mailbox to 3
    g_MAILBOX = 3;

    // STEP 6: call decrement_mailbox until it gets to 0. The debugger will set breakpoints and watchpoints and
    // test that they have been observed by the core.
    while (g_MAILBOX > 0) {
        decrement_mailbox();
    }

    // STEP 7: Test byte access
    g_MAILBOX = 0xff000003;
    g_TESTBYTEACCESS.bytes[3] = 0x40;
    g_MAILBOX = 0xff000005;
    g_TESTBYTEACCESS.bytes[5] = 0x60;
    g_MAILBOX = 0xff000000;
    g_TESTBYTEACCESS.low_32 = 0x11223344;
    g_MAILBOX = 0xff000004;
    g_TESTBYTEACCESS.high_32 = 0x55667788;

    if(g_MAILBOX > 0x20) decrement_mailbox();

    // STEP END: Set the mailbox to RISC_DBG_STATUS0
    g_MAILBOX = (uint32_t)RISC_DBG_STATUS0;
    //const volatile struct gcov_info *volatile const *info = __gcov_info_start;
    //const volatile struct gcov_info *volatile const *end = __gcov_info_end;
    //__asm__ volatile ("" : "+r" (info));

        //while(info != end) {
        //__gcov_info_to_gcda(*((const struct gcov_info *const *) info), fname_callback, l1_write, alloc, nullptr);
        //info++;
    //}
    
    infloop();
    return 0;
}
