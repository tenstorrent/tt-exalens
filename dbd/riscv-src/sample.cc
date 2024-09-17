// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

// An example of a simple C++ program that can be compiled with the RISC-V GCC toolchain.
#include <cstdint>
#include <stdint.h>

// Registers for debug register access

#define RISC_DBG_CNTL0                          0xFFB12080
#define RISC_DBG_CNTL1                          0xFFB12084
#define RISC_DBG_STATUS0                        0xFFB12088
#define RISC_DBG_STATUS1                        0xFFB1208C
#define RISCV_DEBUG_REGS_START_ADDR             0xFFB12000
#define RISCV_DEBUG_REG_WALL_CLOCK_L            (RISCV_DEBUG_REGS_START_ADDR | 0x1F0)
#define RISCV_DEBUG_REG_WALL_CLOCK_H            (RISCV_DEBUG_REGS_START_ADDR | 0x1F8)

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
    asm volatile ("ebreak");
}


void decrement_mailbox() {
    g_MAILBOX--;
}

extern "C" void infloop() {
    for (;;);
}

int main() {

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

  // STEP END: Set the mailbox to RISC_DBG_STATUS0
  g_MAILBOX = (uint32_t) RISC_DBG_STATUS0;
  infloop();
  return 0;
}
