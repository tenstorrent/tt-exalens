// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include <cstdint>

// L1 scratch address, kept below the 256 KiB Ethernet L1 so this program also runs on Ethernet cores.
#define MAILBOX_ADDRESS 0x20000
volatile uint32_t *mailbox = reinterpret_cast<volatile uint32_t *>(MAILBOX_ADDRESS);

int main() { *mailbox = 0x12345678; }
