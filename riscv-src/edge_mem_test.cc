// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <array>
#include <cstdint>

volatile std::array<std::uint8_t, 16>* g_p_wormhole =
    reinterpret_cast<volatile std::array<std::uint8_t, 16>*>(0x0016DFF8);  // 8 bytes in L1, 8 bytes past L1

volatile std::array<std::uint8_t, 16>* g_p_blackhole =
    reinterpret_cast<volatile std::array<std::uint8_t, 16>*>(0x0017FFF8);  // 8 bytes in L1, 8 bytes past L1

volatile std::array<std::uint8_t, 16>* g_in_l1_wormhole =
    reinterpret_cast<volatile std::array<std::uint8_t, 16>*>(0x00010000);  // entirely in L1

volatile std::array<std::uint8_t, 16>* g_in_l1_blackhole =
    reinterpret_cast<volatile std::array<std::uint8_t, 16>*>(0x00010000);  // entirely in L1

int main() {
    while (true) {
        asm volatile("nop");
    }
    return 0;
}
