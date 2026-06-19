// SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
// SPDX-License-Identifier: Apache-2.0

#include <array>
#include <cstdint>

volatile std::array<std::uint8_t, 16>* g_p_wormhole =
    reinterpret_cast<volatile std::array<std::uint8_t, 16>*>(0x0016DFF8);  // 8 bytes in L1, 8 bytes past L1

volatile std::array<std::uint8_t, 16>* g_p_blackhole =
    reinterpret_cast<volatile std::array<std::uint8_t, 16>*>(0x0017FFF8);  // 8 bytes in L1, 8 bytes past L1

// Scratch buffer in the per-core thread-local region: a stable, in-L1 window the
// host can read/write without colliding with code or data, however those sections
// grow. The GDB memory-access test uses its address (resolved from the linker
// symbol __thread_local_start) as its "entirely in L1" probe, instead of a
// hardcoded address that the data section could later be placed onto.
[[gnu::used]] thread_local volatile std::array<std::uint8_t, 64> g_scratch;

std::array<std::uint8_t, 16> g_data = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15};

int main() {
    while (true) {
        asm volatile("nop");
    }
    return 0;
}
