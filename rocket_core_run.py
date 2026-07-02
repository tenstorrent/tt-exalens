# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

"""
Load a simple counter loop onto rocket core 0, run it, halt, then continue.
Uses raw NOC reads/writes only — no debug API abstractions.

Addresses from tt-metal: tt_metal/hw/inc/internal/tt-2xx/quasar/dev_mem_map.h
"""

import time

from ttexalens import tt_exalens_lib as lib
from ttexalens.tt_exalens_init import init_ttexalens_remote

# ---------------------------------------------------------------------------
# Addresses (from dev_mem_map.h)
# MEM_DM_FIRMWARE_BASE = MEM_LLK_DEBUG_BASE + MEM_LLK_DEBUG_SIZE
#                      = (MEM_ZEROS_BASE + MEM_ZEROS_SIZE) + 1024
#                      = (MEM_MAILBOX_END + 512) + 1024
#                      = (16 + 57680 + 512) + 1024  = 0xE760
# ---------------------------------------------------------------------------
DM_FIRMWARE_BASE = 0xE760  # where rocket core 0 firmware lives in L1

# Cluster ctrl — reset vectors (one 64-bit slot per core, 8-byte stride)
RESET_VECTOR_0 = 0x03000000  # TT_CLUSTER_CTRL_RESET_VECTOR_0

# Debug Module APB (base 0x0300A000)
DMCONTROL = 0x0300A040
DMSTATUS = 0x0300A044
HALTSUMMARY0 = 0x0300A100

# DMCONTROL bit fields
DMACTIVE = 1 << 0
NDMRESET = 1 << 1
ACKHAVERESET = 1 << 28
RESUMEREQ = 1 << 30
HALTREQ = 1 << 31
HART0_SEL = 0 << 16  # hartsello = core index

# HALTSUMMARY0: bit N = core N is halted
CORE0_HALTED = 1 << 0

# ---------------------------------------------------------------------------
# Program: infinite counter loop
#   0x00: addi x1, x0, 0    — x1 = 0
#   0x04: addi x1, x1, 1    — x1 += 1   <- loop target
#   0x08: jal  x0, -4       — jump back to 0x04
# ---------------------------------------------------------------------------
PROGRAM = [
    0x00000093,  # addi x1, x0, 0
    0x00108093,  # addi x1, x1, 1
    0xFFDFF06F,  # jal  x0, -4
]

# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------
context = init_ttexalens_remote()
loc = "0,0"


def rd(addr):
    return lib.read_word_from_device(loc, addr, context=context)


def wr(addr, val):
    lib.write_words_to_device(loc, addr, val, context=context)


# ---------------------------------------------------------------------------
# Assert reset via DMCONTROL.ndmreset
# ---------------------------------------------------------------------------
wr(DMCONTROL, DMACTIVE | HART0_SEL | NDMRESET)
print(f"Reset asserted. DMSTATUS = {rd(DMSTATUS):#010x}")

# ---------------------------------------------------------------------------
# Set reset vector and write program into L1
# ---------------------------------------------------------------------------
wr(RESET_VECTOR_0, DM_FIRMWARE_BASE)

for i, word in enumerate(PROGRAM):
    wr(DM_FIRMWARE_BASE + i * 4, word)
    assert rd(DM_FIRMWARE_BASE + i * 4) == word

print(f"Program written to {DM_FIRMWARE_BASE:#x}")

# ---------------------------------------------------------------------------
# De-assert reset — core starts executing at DM_FIRMWARE_BASE
# ---------------------------------------------------------------------------
wr(DMCONTROL, DMACTIVE | HART0_SEL)
wr(DMCONTROL, DMACTIVE | HART0_SEL | ACKHAVERESET)

time.sleep(0.1)
print(f"Core running. DMSTATUS = {rd(DMSTATUS):#010x}")

# ---------------------------------------------------------------------------
# Halt
# ---------------------------------------------------------------------------
wr(DMCONTROL, DMACTIVE | HART0_SEL | HALTREQ)
wr(DMCONTROL, DMACTIVE | HART0_SEL)  # clear haltreq

haltsummary = rd(HALTSUMMARY0)
assert haltsummary & CORE0_HALTED, f"Core 0 did not halt! HALTSUMMARY0 = {haltsummary:#010x}"
print(f"Halted. HALTSUMMARY0 = {haltsummary:#010x}")

# ---------------------------------------------------------------------------
# Continue
# ---------------------------------------------------------------------------
wr(DMCONTROL, DMACTIVE | HART0_SEL | RESUMEREQ)
wr(DMCONTROL, DMACTIVE | HART0_SEL)  # clear resumereq

time.sleep(0.05)
haltsummary = rd(HALTSUMMARY0)
print(f"Resumed. HALTSUMMARY0 = {haltsummary:#010x}")
