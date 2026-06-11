// SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0

#include <cstdint>

thread_local volatile uint32_t mailbox;

int main() { mailbox = 0x12345678; }
