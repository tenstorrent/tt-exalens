# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Quasar NEO Tensix perf-counter block descriptions.

Counter ids and names follow tt-llk ``tools/include/perf_counters/quasar.h``, which is verified against the
Quasar A0 RTL. Selects that are tied to a constant or duplicate another select are left out.
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
        0: "cfg_instrn_available_0",
        1: "cfg_instrn_available_1",
        2: "cfg_instrn_available_2",
        3: "cfg_instrn_available_3",
        4: "sync_instrn_available_0",
        5: "sync_instrn_available_1",
        6: "sync_instrn_available_2",
        7: "sync_instrn_available_3",
        8: "thcon_instrn_available_0",
        9: "thcon_instrn_available_1",
        10: "thcon_instrn_available_2",
        11: "thcon_instrn_available_3",
        16: "instissue_instrn_available_0",
        17: "instissue_instrn_available_1",
        18: "instissue_instrn_available_2",
        19: "instissue_instrn_available_3",
        20: "math_instrn_available_0",
        21: "math_instrn_available_1",
        22: "math_instrn_available_2",
        23: "math_instrn_available_3",
        24: "unpack_instrn_available_0",
        25: "unpack_instrn_available_1",
        26: "unpack_instrn_available_2",
        27: "unpack_instrn_available_3",
        28: "pack_instrn_available_0",
        29: "pack_instrn_available_1",
        30: "pack_instrn_available_2",
        31: "pack_instrn_available_3",
        32: "thread_stalls_0",
        33: "thread_stalls_1",
        34: "thread_stalls_2",
        35: "thread_stalls_3",
        36: "tile_counter_stall_pack",
        37: "tile_counter_stall_unpack",
        38: "srcs_stall_pack",
        39: "srcs_stall_sfpu",
        40: "srcs_stall_unpack",
        41: "dest_stall_pack",
        42: "dest_stall_sfpu",
        43: "dest_stall_math",
        44: "dest_stall_unpack",
        45: "sfpu_data_hazard_stall",
        46: "fpu_data_hazard_stall",
        47: "srcb_stall_unpack",
        48: "srca_stall_unpack",
        49: "dvalid_stall_math",
        50: "srca_stall_math",
        256: "thread_instructions_0",
        257: "thread_instructions_1",
        258: "thread_instructions_2",
        259: "thread_instructions_3",
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
        9: "unpack2_busy_thread0",
        10: "unpack0_busy_thread1",
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
