# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Wormhole Tensix perf-counter block descriptions.

Counter-id maps copied from the production tt-metal reference at
``tools/triage/check_perf_counters.py``. The ids are RTL bank indices from
``tt_instruction_thread.sv`` and the surrounding perf-counter generators —
see ``perf_counters.md`` in the tensix RTL repo for the full reference.

Blackhole shares this exact layout; ``ttexalens/hardware/blackhole/perf_counters.py``
re-exports from this module.
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
        0: "cfg_instrn[0]",
        1: "cfg_instrn[1]",
        2: "cfg_instrn[2]",
        4: "sync_instrn[0]",
        5: "sync_instrn[1]",
        6: "sync_instrn[2]",
        8: "thcon_instrn[0]",
        9: "thcon_instrn[1]",
        10: "thcon_instrn[2]",
        12: "xsrch_instrn[0]",
        13: "xsrch_instrn[1]",
        14: "xsrch_instrn[2]",
        16: "instissue_instrn[0]",
        17: "instissue_instrn[1]",
        18: "instissue_instrn[2]",
        20: "math_instrn[0]",
        21: "math_instrn[1]",
        22: "math_instrn[2]",
        24: "unpack_instrn[0]",
        25: "unpack_instrn[1]",
        26: "unpack_instrn[2]",
        28: "pack_instrn[0]",
        29: "pack_instrn[1]",
        30: "pack_instrn[2]",
        32: "thread_stalls[0]",
        33: "thread_stalls[1]",
        34: "thread_stalls[2]",
        36: "srca_stall_math",
        37: "dvalid_stall_math",
        38: "srca_stall_unpack",
        39: "srcb_stall_unpack",
        40: "fpu_data_hazard_stall",
        41: "sfpu_data_hazard_stall",
        42: "dest_stall_unpack",
        43: "dest_stall_math",
        44: "dest_stall_sfpu",
        45: "dest_stall_pack",
        46: "srcs_stall_unpack",
        47: "srcs_stall_sfpu",
        48: "srcs_stall_pack",
        49: "tile_counter_stall_unpack",
        50: "tile_counter_stall_pack",
        256: "thread_instr[0]",
        257: "thread_instr[1]",
        258: "thread_instr[2]",
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
        0: "fpu_op_valid",
        1: "sfpu_op_valid",
        257: "fpu_or_sfpu_instrn",
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
        # Unpacker busy: tdma_unpack_busy[3..0] -> banks 0..3 (MSB first in i_req concatenation).
        0: "unpack_busy[3]",
        1: "unpack_busy[2]",
        2: "unpack_busy[1]",
        3: "unpack_busy[0]",
        4: "srca_write_req",
        5: "srcb_write_req",
        6: "math_instrn_avail",
        7: "math_instrn_started",
        9: "math_no_post_stall",
        10: "math_no_data_hazard",
        261: "srca_write",
        263: "srcb_write",
    },
)

TDMA_PACK = PerfCounterBlockDescription(
    name="TDMA_PACK",
    reg0="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK0",
    reg1="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK1",
    reg2="RISCV_DEBUG_REG_PERF_CNT_TDMA_PACK2",
    out_l="RISCV_DEBUG_REG_PERF_CNT_OUT_L_TDMA_PACK",
    out_h="RISCV_DEBUG_REG_PERF_CNT_OUT_H_TDMA_PACK",
    counters={
        0: "packer_dest_read_avail",
        7: "packer_busy",
        260: "math_no_dest_wr_stall",
        261: "math_no_scoreboard_stall",
    },
)

ALL_BLOCKS = [FPU, INSTRN_THREAD, TDMA_UNPACK, TDMA_PACK]

initialization = TensixPerfCounters.create_initialization(ALL_BLOCKS)
