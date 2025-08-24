// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include <cstdint>

#define MAILBOX_ADDRESS 0x64000
volatile uint32_t *mailbox = reinterpret_cast<volatile uint32_t *>(MAILBOX_ADDRESS);

int main() {
    *mailbox = 0x12345678;
}
