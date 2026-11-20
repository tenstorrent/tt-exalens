# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Wormhole Tensix perf-counter block descriptions.

Counter ids and names follow tt-llk ``tools/include/perf_counters/wormhole.h``. A counter id is the bank select
written to REG1; ids of 256 and up are the grant view of bank (id - 256). Not every select has a name; any
select can still be read by its numeric id.
"""

from ttexalens.hardware.perf_counters import (
    PerfCounterBlockDescription,
    TensixPerfCounters,
)


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
        # The SrcA/SrcB stall conditions are each replicated over three selects; only the first is listed.
        27: "waiting_for_srca_clear",
        30: "waiting_for_srcb_clear",
        33: "waiting_for_srca_valid",
        36: "waiting_for_srcb_valid",
        # Per-thread stall reasons: 39 + 9 * thread + reason, for the reasons thcon, unpack, pack, math,
        # non-zero semaphore, non-full semaphore, mover, config and SFPU. The mover and config waits are not listed.
        39: "waiting_for_thcon_idle_0",
        40: "waiting_for_unpack_idle_0",
        41: "waiting_for_pack_idle_0",
        42: "waiting_for_math_idle_0",
        43: "waiting_for_nonzero_sem_0",
        44: "waiting_for_nonfull_sem_0",
        47: "waiting_for_sfpu_idle_0",
        48: "waiting_for_thcon_idle_1",
        49: "waiting_for_unpack_idle_1",
        50: "waiting_for_pack_idle_1",
        51: "waiting_for_math_idle_1",
        52: "waiting_for_nonzero_sem_1",
        53: "waiting_for_nonfull_sem_1",
        56: "waiting_for_sfpu_idle_1",
        57: "waiting_for_thcon_idle_2",
        58: "waiting_for_unpack_idle_2",
        59: "waiting_for_pack_idle_2",
        60: "waiting_for_math_idle_2",
        61: "waiting_for_nonzero_sem_2",
        62: "waiting_for_nonfull_sem_2",
        65: "waiting_for_sfpu_idle_2",
        # Grant view: selects 256, 264 and 272 count the instructions each thread issued.
        256: "thread_instructions_0",
        264: "thread_instructions_1",
        272: "thread_instructions_2",
        283: "any_thread_stall",
    },
)

FPU = PerfCounterBlockDescription(
    name="FPU",
    reg0="RISCV_DEBUG_REG_PERF_CNT_FPU0",
    reg1="RISCV_DEBUG_REG_PERF_CNT_FPU1",
    reg2="RISCV_DEBUG_REG_PERF_CNT_FPU2",
    out_l="RISCV_DEBUG_REG_PERF_CNT_OUT_L_FPU",
    out_h="RISCV_DEBUG_REG_PERF_CNT_OUT_H_FPU",
    counters={
        0: "fpu_counter",
        1: "sfpu_counter",
        257: "math_counter",
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
# Select 18 does not count packer 0 activity on Wormhole and is not listed.
TDMA_PACK = PerfCounterBlockDescription(
    name="TDMA_PACK",
    reg0="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK0",
    reg1="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK1",
    reg2="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK2",
    out_l="RISCV_DEBUG_REG_PERF_CNT_OUT_L_TDMA_PACK",
    out_h="RISCV_DEBUG_REG_PERF_CNT_OUT_H_TDMA_PACK",
    counters={
        11: "packer0_dest_read_req",
        12: "packer_dest_read_1",
        13: "packer_dest_read_2",
        14: "packer_dest_read_3",
        15: "packer_busy_0",
        16: "packer_busy_1",
        17: "packer_busy_2",
        267: "dest_read_granted_0",
        268: "dest_read_granted_1",
        269: "dest_read_granted_2",
        270: "dest_read_granted_3",
        271: "math_not_stalled_dest_wr_port",
        272: "math_not_scoreboard_stalled",
    },
)

ALL_BLOCKS = [FPU, INSTRN_THREAD, TDMA_UNPACK, TDMA_PACK]

initialization = TensixPerfCounters.create_initialization(ALL_BLOCKS)
