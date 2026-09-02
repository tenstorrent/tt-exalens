// SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
//
// A deliberately 4-frame-deep call chain for testing Rocket callstack unwinding.
//
// The innermost function spins forever, so the host can halt() the core and be
// certain it is parked inside f1 with f2/f3/main still live on the stack. We do
// NOT use ebreak: dcsr.ebreakm is 0 out of reset, so an M-mode ebreak traps to
// mtvec (=0) and re-runs crt0 instead of halting.
//
// Every function is extern "C" + noinline so the DWARF name, the ELF symbol and
// the name asserted by the test all agree, and so the chain survives as four
// real frames. f1 never returns, which makes the `return` statements in f2/f3
// unreachable -- that is fine at -O0 and is what stops GCC turning the calls
// into tail jumps (a tail call would collapse the frames).

extern "C" __attribute__((noinline)) void f1() {
    for (;;) {
        asm volatile("" ::: "memory");
    }
}

extern "C" __attribute__((noinline)) int f2() {
    f1();
    return 2;
}

extern "C" __attribute__((noinline)) int f3() { return f2() + 1; }

extern "C" int main() {
    volatile int r = f3();
    (void)r;
    for (;;) {
        asm volatile("" ::: "memory");
    }
}
