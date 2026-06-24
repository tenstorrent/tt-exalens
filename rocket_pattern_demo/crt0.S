// SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
//
// SPDX-License-Identifier: Apache-2.0
# SPDX-License-Identifier: Apache-2.0
#
# Minimal bare-metal startup for a Quasar Rocket (RV64) core.
#
# Placed at TL1 0x0 (the reset vector / code start address). It sets up a stack,
# clears .bss, then calls main(). main() never returns; if it ever did we park
# in an infinite loop. We deliberately do NOT use `ebreak` to halt: dcsr.ebreakm
# is 0 out of reset, so an M-mode ebreak would trap to mtvec (=0) and re-run this
# code instead of halting.
.section .text.init, "ax", @progbits
.global _start
_start:
    li    sp, 0x40000             # stack top inside TL1 (cached), well above the code

    # zero .bss
    la    t0, __bss_start
    la    t1, __bss_end
    # Clear .bss with 4-byte stores. __bss_start is only 4-byte aligned (the
    # code is 60 bytes = 0x3c), so a 64-bit `sd` here is a MISALIGNED access:
    # the Rocket core traps it to mtvec (=0), which re-runs _start -> infinite
    # loop that never reaches main(). `sw`/4 keeps every store aligned.
1:
    bgeu  t0, t1, 2f
    sw    zero, 0(t0)
    addi  t0, t0, 4
    j     1b
2:
    call  main
3:
    j     3b                      # park forever if main ever returns
