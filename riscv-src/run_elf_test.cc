// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include <stdint.h>

#include <cstdint>

#include "coverage/coverage.h"

#define RISCV_L1_REG_START_ADDR 0x00000000

int main() {
    volatile uint32_t *MAILBOX = reinterpret_cast<volatile uint32_t *>(RISCV_L1_REG_START_ADDR);
    *MAILBOX = 0x12345678;

    gcov_dump();
    for (;;);
}
