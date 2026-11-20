# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Blackhole Tensix perf-counter block descriptions.

Counter ids and names follow tt-llk ``tools/include/perf_counters/blackhole.h``. A counter id is the bank select
written to REG1; ids of 256 and up are the grant view of bank (id - 256). Not every select has a name; any
select can still be read by its numeric id.

The register names and offsets and the FPU counter ids are the same as on Wormhole, so FPU is taken from the
Wormhole module. INSTRN_THREAD and TDMA_PACK differ from Wormhole: the SrcA/SrcB stall conditions take one select
each, so the per-thread stall reasons start at 31 rather than 39, and Blackhole has a single packer.
"""

from ttexalens.hardware.perf_counters import (
    PerfCounterBlockDescription,
    TensixPerfCounters,
)
from ttexalens.hardware.wormhole.perf_counters import FPU

INSTRN_THREAD = PerfCounterBlockDescription(
    name="INSTRN_THREAD",
    reg0="RISCV_DEBUG_REG_PERF_CNT_INSTRN_THREAD0",
    reg1="RISCV_DEBUG_REG_PERF_CNT_INSTRN_THREAD1",
    reg2="RISCV_DEBUG_REG_PERF_CNT_INSTRN_THREAD2",
    out_l="RISCV_DEBUG_REG_PERF_CNT_OUT_L_INSTRN_THREAD",
    out_h="RISCV_DEBUG_REG_PERF_CNT_OUT_H_INSTRN_THREAD",
    counters={
        # Selects 0-23 are instruction class x thread (3 * class + thread) for the classes cfg, sync, thcon,
        # xsearch, move, math, unpack and pack. The xsearch selects read 0; the move selects are not listed.
        0: "cfg_instrn_available_0",
        1: "cfg_instrn_available_1",
        2: "cfg_instrn_available_2",
        3: "sync_instrn_available_0",
        4: "sync_instrn_available_1",
        5: "sync_instrn_available_2",
        6: "thcon_instrn_available_0",
        7: "thcon_instrn_available_1",
        8: "thcon_instrn_available_2",
        15: "math_instrn_available_0",
        16: "math_instrn_available_1",
        17: "math_instrn_available_2",
        18: "unpack_instrn_available_0",
        19: "unpack_instrn_available_1",
        20: "unpack_instrn_available_2",
        21: "pack_instrn_available_0",
        22: "pack_instrn_available_1",
        23: "pack_instrn_available_2",
        24: "thread_stalls_0",
        25: "thread_stalls_1",
        26: "thread_stalls_2",
        27: "waiting_for_srca_clear",
        28: "waiting_for_srcb_clear",
        29: "waiting_for_srca_valid",
        30: "waiting_for_srcb_valid",
        # Per-thread stall reasons: 31 + 9 * thread + reason, for the reasons thcon, unpack, pack, math,
        # non-zero semaphore, non-full semaphore, mover, config and SFPU. The mover and config waits are not listed.
        31: "waiting_for_thcon_idle_0",
        32: "waiting_for_unpack_idle_0",
        33: "waiting_for_pack_idle_0",
        34: "waiting_for_math_idle_0",
        35: "waiting_for_nonzero_sem_0",
        36: "waiting_for_nonfull_sem_0",
        39: "waiting_for_sfpu_idle_0",
        40: "waiting_for_thcon_idle_1",
        41: "waiting_for_unpack_idle_1",
        42: "waiting_for_pack_idle_1",
        43: "waiting_for_math_idle_1",
        44: "waiting_for_nonzero_sem_1",
        45: "waiting_for_nonfull_sem_1",
        48: "waiting_for_sfpu_idle_1",
        49: "waiting_for_thcon_idle_2",
        50: "waiting_for_unpack_idle_2",
        51: "waiting_for_pack_idle_2",
        52: "waiting_for_math_idle_2",
        53: "waiting_for_nonzero_sem_2",
        54: "waiting_for_nonfull_sem_2",
        57: "waiting_for_sfpu_idle_2",
        # Grant view: selects 256, 264 and 272 count the instructions each thread issued.
        256: "thread_instructions_0",
        264: "thread_instructions_1",
        272: "thread_instructions_2",
        283: "any_thread_stall",
    },
)

TDMA_UNPACK = PerfCounterBlockDescription(
    name="TDMA_UNPACK",
    reg0="RISCV_DEBUG_REG_PERF_CNT_TDMA_UNPACK0",
    reg1="RISCV_DEBUG_REG_PERF_CNT_TDMA_UNPACK1",
    reg2="RISCV_DEBUG_REG_PERF_CNT_TDMA_UNPACK2",
    out_l="RISCV_DEBUG_REG_PERF_CNT_OUT_L_TDMA_UNPACK",
    out_h="RISCV_DEBUG_REG_PERF_CNT_OUT_H_TDMA_UNPACK",
    counters={
        0: "math_src_data_ready",
        1: "math_not_d2s_stalled",
        3: "math_instrn_started",
        4: "math_instrn_available",
        5: "srcb_write_req",
        6: "srca_write_req",
        7: "unpack0_busy_thread0",
        8: "unpack1_busy_thread0",
        9: "unpack0_busy_thread1",
        10: "unpack1_busy_thread1",
        259: "srcb_write_not_blocked_ovr",
        260: "srcb_write_not_blocked_port",
        261: "srca_write_not_blocked_ovr",
        262: "srca_write_not_blocked_port",
        263: "srca_write_tid_even",
        264: "srcb_write_tid_even",
        265: "srca_write_tid_odd",
        266: "srcb_write_tid_odd",
    },
)

# TDMA_UNPACK and TDMA_PACK index one shared readout: entries 0..10 belong to unpack, 11..18 to pack.
# Blackhole has a single packer, so only the first packer's counters are live.
TDMA_PACK = PerfCounterBlockDescription(
    name="TDMA_PACK",
    reg0="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK0",
    reg1="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK1",
    reg2="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK2",
    out_l="RISCV_DEBUG_REG_PERF_CNT_OUT_L_TDMA_PACK",
    out_h="RISCV_DEBUG_REG_PERF_CNT_OUT_H_TDMA_PACK",
    counters={
        11: "packer0_dest_read_req",
        18: "packer_busy",
        267: "dest_read_granted_0",
        271: "math_not_stalled_dest_wr_port",
        272: "math_not_scoreboard_stalled",
    },
)

ALL_BLOCKS = [FPU, INSTRN_THREAD, TDMA_UNPACK, TDMA_PACK]

initialization = TensixPerfCounters.create_initialization(ALL_BLOCKS)
