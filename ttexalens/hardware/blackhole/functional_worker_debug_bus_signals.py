# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.debug_bus_signal_store import DebugBusSignalDescription


debug_bus_signal_map = {
    # For the other signals applying the pc_mask.
    "brisc_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 5 + 1, mask=0x3FFFFFFF),
    "trisc0_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 6 + 1, mask=0x3FFFFFFF),
    "trisc1_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 7 + 1, mask=0x3FFFFFFF),
    "trisc2_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 8 + 1, mask=0x3FFFFFFF),
    "ncrisc_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 12 + 1, mask=0x3FFFFFFF),
    "tensix_frontend_t0_ibuffer_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=13, mask=0x80),
    "tensix_frontend_t0_risc_cfg_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=13, mask=0x40),
    "tensix_frontend_t0_risc_gpr_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=13, mask=0x20),
    "tensix_frontend_t0_risc_tdma_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=13, mask=0x10),
    # "tensix_frontend_t0_prev_gen_no/0": DebugBusSignalDescription(        # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xF0000000
    # ),
    # "tensix_frontend_t0_prev_gen_no/1": DebugBusSignalDescription(        # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=0, daisy_sel=1, sig_sel=13, mask=0xF
    # ),
    "tensix_frontend_t0_lsq_head_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x8000000),
    "tensix_frontend_t0_lsq_head_rsrcs_wr_tdma": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x4000000
    ),
    "tensix_frontend_t0_lsq_head_rsrcs_rd_tdma": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x2000000
    ),
    "tensix_frontend_t0_lsq_head_rsrcs_wr_gpr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x1000000
    ),
    "tensix_frontend_t0_lsq_head_rsrcs_rd_gpr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x800000
    ),
    "tensix_frontend_t0_lsq_head_rsrcs_target_cfg_space": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x700000
    ),
    "tensix_frontend_t0_lsq_head_rsrcs_cfg_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xC0000
    ),
    "tensix_frontend_t0_lsq_head_rsrcs_wr_cfg": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x20000
    ),
    "tensix_frontend_t0_lsq_head_rsrcs_rd_cfg": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x10000
    ),
    "tensix_frontend_t0_lsq_head_gen_no": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xFF00),
    "tensix_frontend_t0_lsq_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x80),
    "tensix_frontend_t0_rq_head_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x40),
    "tensix_frontend_t0_rq_head_rsrcs_wr_tdma": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x20),
    "tensix_frontend_t0_rq_head_rsrcs_rd_tdma": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x10),
    "tensix_frontend_t0_rq_head_rsrcs_wr_gpr": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x8),
    "tensix_frontend_t0_rq_head_rsrcs_rd_gpr": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x4),
    "tensix_frontend_t0_rq_head_rsrcs_target_cfg_space/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x80000000
    ),
    "tensix_frontend_t0_rq_head_rsrcs_target_cfg_space/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0x3
    ),
    "tensix_frontend_t0_rq_head_rsrcs_cfg_state": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x60000000
    ),
    "tensix_frontend_t0_rq_head_rsrcs_wr_cfg": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x10000000
    ),
    "tensix_frontend_t0_rq_head_rsrcs_rd_cfg": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x8000000
    ),
    "tensix_frontend_t0_rq_head_gen_no": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x7F80000),
    "tensix_frontend_t0_rq_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x40000),
    "tensix_frontend_t0_i_cg_trisc_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x20000),
    "tensix_frontend_t0_machine_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x10000),
    "tensix_frontend_t0_req_iramd_buffer_not_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x8000
    ),
    "tensix_frontend_t0_gpr_file_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x4000),
    "tensix_frontend_t0_cfg_exu_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x2000),
    "tensix_frontend_t0_req_iramd_buffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x1000
    ),
    "tensix_frontend_t0_req_iramd_buffer_full": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x800
    ),
    "tensix_frontend_t0_~ibuffer_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x400),
    "tensix_frontend_t0_ibuffer_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x200),
    "tensix_frontend_t0_ibuffer_empty_raw": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x1000000
    ),
    "tensix_frontend_t0_thread_inst/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0xFFFFFF00),
    "tensix_frontend_t0_thread_inst/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=12, mask=0xFF),
    "tensix_frontend_t0_math_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x80),
    "tensix_frontend_t0_tdma_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x40),
    "tensix_frontend_t0_pack_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x20),
    "tensix_frontend_t0_move_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x10),
    "tensix_frontend_t0_sfpu_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x8),
    "tensix_frontend_t0_unpack_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x6),
    "tensix_frontend_t0_xsearch_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x1),
    "tensix_frontend_t0_thcon_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x80000000),
    "tensix_frontend_t0_sync_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x40000000),
    "tensix_frontend_t0_cfg_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x20000000),
    "tensix_frontend_t0_stalled_pack_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x10000000
    ),
    "tensix_frontend_t0_stalled_unpack_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xC000000
    ),
    "tensix_frontend_t0_stalled_math_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x2000000
    ),
    "tensix_frontend_t0_stalled_tdma_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x1000000
    ),
    "tensix_frontend_t0_stalled_move_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x800000),
    "tensix_frontend_t0_stalled_xsearch_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x400000
    ),
    "tensix_frontend_t0_stalled_thcon_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x200000
    ),
    "tensix_frontend_t0_stalled_sync_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x100000),
    "tensix_frontend_t0_stalled_cfg_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x80000),
    "tensix_frontend_t0_stalled_sfpu_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x40000),
    "tensix_frontend_t0_tdma_kick_move": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x20000),
    "tensix_frontend_t0_tdma_kick_pack": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x10000),
    "tensix_frontend_t0_tdma_kick_unpack": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xC000),
    "tensix_frontend_t0_tdma_kick_xsearch": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x2000),
    "tensix_frontend_t0_tdma_kick_thcon": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x1000),
    "tensix_frontend_t0_tdma_status_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xF80),
    "tensix_frontend_t0_packer_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x40),
    "tensix_frontend_t0_unpacker_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x30),
    "tensix_frontend_t0_thcon_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x8),
    "tensix_frontend_t0_move_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x4),
    "tensix_frontend_t0_xsearch_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x3),
    "perf_cnt_instrn_thread_inst_pack_grant_cnt_stall_inst_cnt0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_unpack_grant_cnt_stall_inst_cnt0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_math_grant_cnt_stall_inst_cnt0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_move_grant_cnt_stall_inst_cnt0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_xsearch_grant_cnt_stall_inst_cnt0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_thcon_grant_cnt_stall_inst_cnt0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_sync_grant_cnt_stall_inst_cnt0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cfg_grant_cnt_stall_inst_cnt0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "tensix_frontend_t1_ibuffer_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=9, mask=0x80),
    "tensix_frontend_t1_risc_cfg_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=9, mask=0x40),
    "tensix_frontend_t1_risc_gpr_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=9, mask=0x20),
    "tensix_frontend_t1_risc_tdma_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=9, mask=0x10),
    # "tensix_frontend_t1_prev_gen_no/0": DebugBusSignalDescription(        # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xF0000000
    # ),
    # "tensix_frontend_t1_prev_gen_no/1": DebugBusSignalDescription(        # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=0, daisy_sel=1, sig_sel=9, mask=0xF
    # ),
    "tensix_frontend_t1_lsq_head_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x8000000),
    "tensix_frontend_t1_lsq_head_rsrcs_wr_tdma": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x4000000
    ),
    "tensix_frontend_t1_lsq_head_rsrcs_rd_tdma": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x2000000
    ),
    "tensix_frontend_t1_lsq_head_rsrcs_wr_gpr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x1000000
    ),
    "tensix_frontend_t1_lsq_head_rsrcs_rd_gpr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x800000
    ),
    "tensix_frontend_t1_lsq_head_rsrcs_target_cfg_space": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x700000
    ),
    "tensix_frontend_t1_lsq_head_rsrcs_cfg_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xC0000
    ),
    "tensix_frontend_t1_lsq_head_rsrcs_wr_cfg": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x20000
    ),
    "tensix_frontend_t1_lsq_head_rsrcs_rd_cfg": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x10000
    ),
    "tensix_frontend_t1_lsq_head_gen_no": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xFF00),
    "tensix_frontend_t1_lsq_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x80),
    "tensix_frontend_t1_rq_head_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x40),
    "tensix_frontend_t1_rq_head_rsrcs_wr_tdma": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x20),
    "tensix_frontend_t1_rq_head_rsrcs_rd_tdma": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x10),
    "tensix_frontend_t1_rq_head_rsrcs_wr_gpr": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x8),
    "tensix_frontend_t1_rq_head_rsrcs_rd_gpr": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x4),
    "tensix_frontend_t1_rq_head_rsrcs_target_cfg_space_0_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x80000000
    ),
    "tensix_frontend_t1_rq_head_rsrcs_target_cfg_space_2_1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0x3
    ),
    "tensix_frontend_t1_rq_head_rsrcs_cfg_state": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x60000000
    ),
    "tensix_frontend_t1_rq_head_rsrcs_wr_cfg": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x10000000
    ),
    "tensix_frontend_t1_rq_head_rsrcs_rd_cfg": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x8000000
    ),
    "tensix_frontend_t1_rq_head_gen_no": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x7F80000),
    "tensix_frontend_t1_rq_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x40000),
    "tensix_frontend_t1_i_cg_trisc_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x20000),
    "tensix_frontend_t1_machine_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x10000),
    "tensix_frontend_t1_req_iramd_buffer_not_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x8000
    ),
    "tensix_frontend_t1_gpr_file_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x4000),
    "tensix_frontend_t1_cfg_exu_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x2000),
    "tensix_frontend_t1_req_iramd_buffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x1000
    ),
    "tensix_frontend_t1_req_iramd_buffer_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x800),
    "tensix_frontend_t1_~ibuffer_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x400),
    "tensix_frontend_t1_ibuffer_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x200),
    "tensix_frontend_t1_ibuffer_empty_raw": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x100),
    "tensix_frontend_t1_thread_inst/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0xFFFFFF00),
    "tensix_frontend_t1_thread_inst/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=8, mask=0xFF),
    "tensix_frontend_t1_math_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x80),
    "tensix_frontend_t1_tdma_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x40),
    "tensix_frontend_t1_pack_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x20),
    "tensix_frontend_t1_move_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x10),
    "tensix_frontend_t1_sfpu_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x8),
    "tensix_frontend_t1_unpack_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x6),
    "tensix_frontend_t1_xsearch_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x1),
    "tensix_frontend_t1_thcon_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x80000000),
    "tensix_frontend_t1_sync_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x40000000),
    "tensix_frontend_t1_cfg_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x20000000),
    "tensix_frontend_t1_stalled_pack_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x10000000
    ),
    "tensix_frontend_t1_stalled_unpack_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xC000000
    ),
    "tensix_frontend_t1_stalled_math_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x2000000),
    "tensix_frontend_t1_stalled_tdma_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x1000000),
    "tensix_frontend_t1_stalled_move_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x800000),
    "tensix_frontend_t1_stalled_xsearch_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x400000
    ),
    "tensix_frontend_t1_stalled_thcon_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x200000),
    "tensix_frontend_t1_stalled_sync_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x100000),
    "tensix_frontend_t1_stalled_cfg_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x80000),
    "tensix_frontend_t1_stalled_sfpu_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x40000),
    "tensix_frontend_t1_tdma_kick_move": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x20000),
    "tensix_frontend_t1_tdma_kick_pack": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x10000),
    "tensix_frontend_t1_tdma_kick_unpack": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xC000),
    "tensix_frontend_t1_tdma_kick_xsearch": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x2000),
    "tensix_frontend_t1_tdma_kick_thcon": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x1000),
    "tensix_frontend_t1_tdma_status_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xF80),
    "tensix_frontend_t1_packer_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x40),
    "tensix_frontend_t1_unpacker_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x30),
    "tensix_frontend_t1_thcon_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x8),
    "tensix_frontend_t1_move_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x4),
    "tensix_frontend_t1_xsearch_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x3),
    "perf_cnt_instrn_thread_inst_pack_grant_cnt_stall_inst_cnt1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_unpack_grant_cnt_stall_inst_cnt1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_math_grant_cnt_stall_inst_cnt1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_move_grant_cnt_stall_inst_cnt1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_xsearch_grant_cnt_stall_inst_cnt1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_thcon_grant_cnt_stall_inst_cnt1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_sync_grant_cnt_stall_inst_cnt1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cfg_grant_cnt_stall_inst_cnt1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "tensix_frontend_t2_ibuffer_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=5, mask=0x80),
    "tensix_frontend_t2_risc_cfg_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=5, mask=0x40),
    "tensix_frontend_t2_risc_gpr_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=5, mask=0x20),
    "tensix_frontend_t2_risc_tdma_stall": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=5, mask=0x10),
    # "tensix_frontend_t2_prev_gen_no/0": DebugBusSignalDescription(              # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xF0000000
    # ),
    # "tensix_frontend_t2_prev_gen_no/1": DebugBusSignalDescription(              # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=0, daisy_sel=1, sig_sel=5, mask=0xF
    # ),
    "tensix_frontend_t2_lsq_head_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x8000000),
    "tensix_frontend_t2_lsq_head_rsrcs_wr_tdma": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x4000000
    ),
    "tensix_frontend_t2_lsq_head_rsrcs_rd_tdma": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x2000000
    ),
    "tensix_frontend_t2_lsq_head_rsrcs_wr_gpr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x1000000
    ),
    "tensix_frontend_t2_lsq_head_rsrcs_rd_gpr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x800000
    ),
    "tensix_frontend_t2_lsq_head_rsrcs_target_cfg_space": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x700000
    ),
    "tensix_frontend_t2_lsq_head_rsrcs_cfg_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xC0000
    ),
    "tensix_frontend_t2_lsq_head_rsrcs_wr_cfg": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x20000
    ),
    "tensix_frontend_t2_lsq_head_rsrcs_rd_cfg": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x10000
    ),
    "tensix_frontend_t2_lsq_head_gen_no": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xFF00),
    "tensix_frontend_t2_lsq_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x80),
    "tensix_frontend_t2_rq_head_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x40),
    "tensix_frontend_t2_rq_head_rsrcs_wr_tdma": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x20),
    "tensix_frontend_t2_rq_head_rsrcs_rd_tdma": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x10),
    "tensix_frontend_t2_rq_head_rsrcs_wr_gpr": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x8),
    "tensix_frontend_t2_rq_head_rsrcs_rd_gpr": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x4),
    "tensix_frontend_t2_rq_head_rsrcs_target_cfg_space/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x80000000
    ),
    "tensix_frontend_t2_rq_head_rsrcs_target_cfg_space/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0x3
    ),
    "tensix_frontend_t2_rq_head_rsrcs_cfg_state": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x60000000
    ),
    "tensix_frontend_t2_rq_head_rsrcs_wr_cfg": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x10000000
    ),
    "tensix_frontend_t2_rq_head_rsrcs_rd_cfg": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x8000000
    ),
    "tensix_frontend_t2_rq_head_gen_no": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x7F80000),
    "tensix_frontend_t2_rq_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x40000),
    "tensix_frontend_t2_i_cg_trisc_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x20000),
    "tensix_frontend_t2_machine_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x10000),
    "tensix_frontend_t2_req_iramd_buffer_not_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x8000
    ),
    "tensix_frontend_t2_gpr_file_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x4000),
    "tensix_frontend_t2_cfg_exu_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x2000),
    "tensix_frontend_t2_req_iramd_buffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x1000
    ),
    "tensix_frontend_t2_req_iramd_buffer_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x800),
    "tensix_frontend_t2_~ibuffer_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x400),
    "tensix_frontend_t2_ibuffer_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x200),
    "tensix_frontend_t2_ibuffer_empty_raw": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x100),
    "tensix_frontend_t2_thread_inst/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0xFFFFFF00),
    "tensix_frontend_t2_thread_inst/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=4, mask=0xFF),
    "tensix_frontend_t2_math_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x80),
    "tensix_frontend_t2_tdma_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x40),
    "tensix_frontend_t2_pack_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x20),
    "tensix_frontend_t2_move_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x10),
    "tensix_frontend_t2_sfpu_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x8),
    "tensix_frontend_t2_unpack_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x6),
    "tensix_frontend_t2_xsearch_inst": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x1),
    "tensix_frontend_t2_thcon_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x80000000),
    "tensix_frontend_t2_sync_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x40000000),
    "tensix_frontend_t2_cfg_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x20000000),
    "tensix_frontend_t2_stalled_pack_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x10000000
    ),
    "tensix_frontend_t2_stalled_unpack_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xC000000
    ),
    "tensix_frontend_t2_stalled_math_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x2000000),
    "tensix_frontend_t2_stalled_tdma_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x1000000),
    "tensix_frontend_t2_stalled_move_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x800000),
    "tensix_frontend_t2_stalled_xsearch_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x400000
    ),
    "tensix_frontend_t2_stalled_thcon_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x200000),
    "tensix_frontend_t2_stalled_sync_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x100000),
    "tensix_frontend_t2_stalled_cfg_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x80000),
    "tensix_frontend_t2_stalled_sfpu_inst": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x40000),
    "tensix_frontend_t2_tdma_kick_move": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x20000),
    "tensix_frontend_t2_tdma_kick_pack": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x10000),
    "tensix_frontend_t2_tdma_kick_unpack": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xC000),
    "tensix_frontend_t2_tdma_kick_xsearch": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x2000),
    "tensix_frontend_t2_tdma_kick_thcon": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x1000),
    "tensix_frontend_t2_tdma_status_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xF80),
    "tensix_frontend_t2_packer_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x40),
    "tensix_frontend_t2_unpacker_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x30),
    "tensix_frontend_t2_thcon_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x8),
    "tensix_frontend_t2_move_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x4),
    "tensix_frontend_t2_xsearch_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x3),
    "perf_cnt_instrn_thread_inst_grant_cnt_stall_inst_cnt2": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_unpack_grant_cnt_stall_inst_cnt2": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_math_grant_cnt_stall_inst_cnt2": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_move_grant_cnt_stall_inst_cnt2": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_xsearch_grant_cnt_stall_inst_cnt2": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_thcon_grant_cnt_stall_inst_cnt2": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_sync_grant_cnt_stall_inst_cnt2": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cfg_grant_cnt_stall_inst_cnt2": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_cnts0_req_cnt_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_cnts1_req_cnt_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_cnts2_req_cnt_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sem_zero_grant_cnt_stall_rsn_cnt0_0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sem_max_grant_cnt_stall_rsn_cnt0_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srca_cleared_grant_cnt_stall_rsn_cnt0_0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srcb_cleared_grant_cnt_stall_rsn_cnt0_0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srca_valid_grant_cnt_stall_rsn_cnt0_0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srcb_valid_grant_cnt_stall_rsn_cnt0_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_move_grant_cnt_stall_rsn_cnt0_0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_trisc_reg_access_grant_cnt_stall_rsn_cnt0_0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_thcon_grant_cnt_stall_rsn_cnt1_0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_unpack0_grant_cnt_stall_rsn_cnt1_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_pack0_grant_cnt_stall_rsn_cnt1_0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sfpu_grant_cnt_stall_rsn_cnt1_0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_math_grant_cnt_stall_rsn_cnt1_0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sem_zero_grant_cnt_stall_rsn_cnt0_1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sem_max_grant_cnt_stall_rsn_cnt0_1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srca_cleared_grant_cnt_stall_rsn_cnt0_1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srcb_cleared_grant_cnt_stall_rsn_cnt0_1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srca_valid_grant_cnt_stall_rsn_cnt0_1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srcb_valid_grant_cnt_stall_rsn_cnt0_1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_move_grant_cnt_stall_rsn_cnt0_1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_trisc_reg_access_grant_cnt_stall_rsn_cnt0_1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_thcon_grant_cnt_stall_rsn_cnt1_1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_unpack0_grant_cnt_stall_rsn_cnt1_1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_pack0_grant_cnt_stall_rsn_cnt1_1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sfpu_grant_cnt_stall_rsn_cnt1_1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_math_grant_cnt_stall_rsn_cnt1_1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sem_zero_grant_cnt_stall_rsn_cnt0_2": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sem_max_grant_cnt_stall_rsn_cnt0_2": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srca_cleared_grant_cnt_stall_rsn_cnt0_2": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srcb_cleared_grant_cnt_stall_rsn_cnt0_2": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srca_valid_grant_cnt_stall_rsn_cnt0_2": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_srcb_valid_grant_cnt_stall_rsn_cnt0_2": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_move_grant_cnt_stall_rsn_cnt0_2": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_trisc_reg_access_grant_cnt_stall_rsn_cnt0_2": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_thcon_grant_cnt_stall_rsn_cnt1_2": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_unpack0_grant_cnt_stall_rsn_cnt1_2": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_pack0_grant_cnt_stall_rsn_cnt1_2": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_sfpu_grant_cnt_stall_rsn_cnt1_2": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_math_grant_cnt_stall_rsn_cnt1_2": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_cnts0_req_cnt_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_cnts1_req_cnt_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_cnts2_req_cnt_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF
    ),
    "thcon_p0_tid": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x30000),
    "thcon_p0_wren": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x8000),
    "thcon_p0_rden": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x4000),
    "thcon_p0_gpr_addr": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x3C00),
    "thcon_p0_gpr_byten_5_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xFC000000),
    "thcon_p0_gpr_byten_15_6": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x3FF),
    "p0_gpr_accept": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x2000000),
    "cfg_gpr_p0_req": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x1000000),
    "cfg_gpr_p0_tid": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xC00000),
    "cfg_gpr_p0_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3C0000),
    "gpr_cfg_p0_accept": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x20000),
    "l1_ret_vld": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x10000),
    "l1_ret_tid": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xC000),
    "l1_ret_gpr": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3C00),
    "l1_ret_byten_5_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xFC000000),
    "l1_ret_byten_15_6": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3FF),
    "l1_return_accept": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x2000000),
    "thcon_p1_req_vld": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x1000000),
    "thcon_p1_tid": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xC00000),
    "thcon_p1_gpr": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3C0000),
    "thcon_p1_req_accept": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x20000),
    "cfg_gpr_p1_req": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x10000),
    "cfg_gpr_p1_tid": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xC000),
    "cfg_gpr_p1_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3C00),
    "cfg_gpr_p1_byten_5_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0xFC000000),
    "cfg_gpr_p1_byten_15_6": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3FF),
    "gpr_cfg_p1_accept": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x2000000),
    "i_risc_out_reg_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1000000),
    "i_risc_out_reg_wren": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x800000),
    "riscv_tid": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x600000),
    "i_risc_out_reg_index_5_2": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1E0000),
    "i_risc_out_reg_byten": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1FFFE),
    "o_risc_in_reg_req_ready": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1),
    "thcon_p0_gpr_wrdata/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF),
    "thcon_p0_gpr_wrdata/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF),
    "thcon_p0_gpr_wrdata/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF),
    "thcon_p0_gpr_wrdata/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF),
    "p0_gpr_ret/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
    "p0_gpr_ret/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
    "p0_gpr_ret/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
    "p0_gpr_ret/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
    "gpr_cfg_p0_data/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF),
    "gpr_cfg_p0_data/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF),
    "gpr_cfg_p0_data/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF),
    "gpr_cfg_p0_data/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF),
    "l1_ret_wrdata/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
    "l1_ret_wrdata/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
    "l1_ret_wrdata/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
    "l1_ret_wrdata/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
    "thcon_p1_ret/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
    "thcon_p1_ret/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
    "thcon_p1_ret/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
    "thcon_p1_ret/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
    "cfg_gpr_p1_data/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
    "cfg_gpr_p1_data/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
    "cfg_gpr_p1_data/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
    "cfg_gpr_p1_data/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
    "risc_out_reg_wrdata/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF),
    "risc_out_reg_wrdata/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF),
    "risc_out_reg_wrdata/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF),
    "risc_out_reg_wrdata/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF),
    "risc_in_reg_rddata/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF),
    "risc_in_reg_rddata/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF),
    "risc_in_reg_rddata/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF),
    "risc_in_reg_rddata/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF),
    "rwc_math_instrn/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0xFFFFF800),
    "rwc_math_instrn/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=7, mask=0x7FF),
    "rwc_math_winner_thread": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0x600),
    "rwc_math_winner": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0x1C0),
    "rwc0_fidelity_phase_d": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0x30),
    "rwc0_srca_reg_addr_d/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0xC0000000),
    "rwc0_srca_reg_addr_d/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=7, mask=0xF),
    "rwc0_srcb_reg_addr_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0x3F000000),
    "rwc0_dst_reg_addr_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0xFFC000),
    "rwc0_mov_dst_reg_addr_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0x3FF0),
    "rwc0_dec_instr_single_output_row_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0x8),
    "rwc0_fpu_rd_data_required_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=7, mask=0x7),
    "rwc0_tdma_srca_unpack_src_reg_set_upd": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x10),
    "rwc_debug_issue0_in_3_dma_srca_wr_port_avail": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x8
    ),
    "rwc_debug_issue0_in_3_srca_write_ready": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x4),
    "rwc_tdma_srca_unpack_if_sel": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x2),
    "rwc_tdma_srca_regif_state_id": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=6, mask=0x1),
    "rwc_tdma_srca_regif_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0xFFFC0000),
    "rwc_tdma_srca_regif_wren": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0x3C000),
    "rwc_tdma_srca_regif_thread_id": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0x3000),
    "rwc_tdma_srca_regif_out_data_format": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0xF00),
    "rwc_tdma_srca_regif_data_format": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0xF0),
    "rwc_tdma_srca_regif_shift_amount": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=6, mask=0xF),
    "rwc_tdma_srcb_unpack_src_reg_set_upd": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x80000000
    ),
    "rwc_debug_issue0_in_3_dmac_srcb_wr_port_avail": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x40000000
    ),
    "rwc_debug_issue0_in_3_srcb_write_ready": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x20000000
    ),
    "rwc_tdma_srcb_regif_state_id": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x10000000),
    "rwc_tdma_srcb_regif_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0xFFFC000),
    "rwc_tdma_srcb_regif_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x3C00),
    "rwc_tdma_srcb_regif_thread_id": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0x300),
    "rwc_tdma_srcb_regif_out_data_format": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0xF0),
    "rwc_tdma_srcb_regif_data_format": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=6, mask=0xF),
    "rwc_tdma_dstac_regif_rden_raw": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=6, mask=0x80),
    "rwc_tdma_dstac_regif_thread_id": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=6, mask=0x60),
    "rwc_tdma_dstac_regif_data_format": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=6, mask=0x1E),
    "rwc_dstac_regif_tdma_reqif_ready": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=6, mask=0x1),
    "rwc_tdma_pack_busy": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0x1000),
    "rwc_tdma_unpack_busy": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0xFC0),
    "rwc_tdma_tc_busy": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0x38),
    "rwc_tdma_move_busy": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0x4),
    "rwc_tdma_xsearch_busy/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0xF0000000),
    "rwc_tdma_xsearch_busy/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=5, mask=0x3),
    "rwc_i_cg_regblocks_en": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x2000000),
    "rwc_cg_regblocks_busy_d": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x1000000),
    "rwc_srcb_reg_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0xF80000),
    "rwc_srcb_reg_addr_d": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x7C000),
    "rwc_fpu_output_mode_d": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x3800),
    "rwc_fpu_output_mode": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x700),
    "rwc_srcb_single_row_rd_mode_d": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x80),
    "rwc_srcb_single_row_rd_mode": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=5, mask=0x40),
    "rwc_dest_apply_relu": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=5, mask=0x60),
    "rwc_tdma_dstac_regif_state_id": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=5, mask=0x10),
    # "rwc_relu_thresh/0": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0xFFF00000),        # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "rwc_relu_thresh/1": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=5, mask=0xF),              # Signal spans two consecutive groups, so its value cannot be read atomically.
    "rwc_dest_offset_state_id": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x80000),
    "rwc_dma_dest_offset_apply_en": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x40000),
    "rwc_srca_fpu_output_alu_s1": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x3C000),
    "rwc_srcb_fpu_output_alu_s1": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x3C00),
    "rwc_dest_fpu_output_alu_s1": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x3C0),
    "rwc_dest_dma_output_alu": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=4, mask=0x3C),
    "rwc_srca_gate_src_pipeline_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x10000000),
    "rwc_srca_gate_src_pipeline_1": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x8000000),
    "rwc_srcb_gate_src_pipeline_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x4000000),
    "rwc_srcb_gate_src_pipeline_1": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x2000000),
    "rwc_squash_alu_instrn": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x1000000),
    "rwc_alu_instr_issue_ready": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x800000),
    "rwc_alu_instr_issue_ready_src": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x400000),
    "rwc_sfpu_instr_issue_ready_s1": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x200000),
    "rwc_sfpu_instr_store_ready_s1": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x100000),
    "rwc_lddest_instr_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x80000),
    "rwc_rddest_instr_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x40000),
    "rwc_dest_reg_deps_scoreboard_bank_pending": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x30000
    ),
    "rwc_dest_reg_deps_scoreboard_something_pending": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x8000
    ),
    "rwc_dest_reg_deps_scoreboard_pending_thread": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x7000
    ),
    "rwc_all_buffers_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0xE00),
    "rwc_dest_reg_deps_scoreboard_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x100),
    "rwc_dest_wr_port_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x80),
    "rwc_dest_fpu_rd_port_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x40),
    "rwc_dest2src_post_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x20),
    "rwc_post_shiftxb_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x10),
    "rwc_dest2src_dest_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x8),
    "rwc_post_alu_instr_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x4),
    "rwc_fidelity_phase_cnt/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=4, mask=0xF0000000),
    "rwc_fidelity_phase_cnt/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=4, mask=0x3),
    "rwc_math_instrn": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=4, mask=0xC000000),
    "rwc_math_winner_thread/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0xFC000000),
    "rwc_math_winner_thread/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=4, mask=0x3FFFFFF),
    "rwc0_srca": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x1F80000),
    "rwc0_srcb": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x7E000),
    "rwc0_dst": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x1FF8),
    "rwc0_fidelity_phase": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x6),
    "rwc0_dec_instr_single_output_row": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=4, mask=0x1),
    "rwc0_(math_winner_combo&math_instrn_pipe_ack)": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x10000000
    ),
    "rwc_debug_daisy_stop_issue0_debug_issue0_in0_math_instrn_pipe_ack": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x8000000
    ),
    "rwc_o_math_instrnbuf_rden": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x4000000),
    "rwc_math_instrn_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x2000000),
    "rwc_src_data_ready": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x1000000),
    "rwc_srcb_data_ready": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x800000),
    "rwc_srca_data_ready": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x400000),
    "rwc_debug_issue0_in0_srcb_write_ready": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x200000),
    "rwc_debug_issue0_in0_srca_write_ready": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x100000),
    "rwc_srca_update_inst": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x80000),
    "rwc_srcb_update_inst": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x40000),
    "rwc_allow_regfile_update": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x20000),
    "rwc_math_srca_wr_port_avail": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x10000),
    "rwc_debug_issue0_in0_dma_srca_wr_port_avail": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x8000
    ),
    "rwc_math_srcb_wr_port_avail": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x4000),
    "rwc_debug_issue0_in0_dma_srcb_wr_port_avail": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x2000
    ),
    "rwc0_alu_inst_decoded": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x1C00),
    "rwc0_sfpu_inst_decoded": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x380),
    "rwc_regw_incr_inst_decoded": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x70),
    "rwc_regmov_inst_decoded": DebugBusSignalDescription(rd_sel=3, daisy_sel=3, sig_sel=1, mask=0xE),
    "rwc_math_instr_valid_th": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE0000000),
    "rwc_math_winner_thread_combo": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x18000000),
    "rwc_debug_daisy_stop_issue0_debug_issue0_in0_dup": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x800000
    ),
    "rwc_math_winner_wo_pipe_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x380000),
    "rwc0_srca_data_ready": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x70000),
    "rwc0_srcb_data_ready": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE000),
    "rwc_math_thread_inst_data_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE00),
    "rwc_i_dest_target_reg_cfg_pack_sec0_offset/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=1, mask=0xE0000000
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec0_offset/1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x1FF
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec1_offset": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1FFE0000
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec2_offset": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1FFE0
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec3_offset/0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=1, mask=0xFE000000
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec3_offset/1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1F
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec0_zoffset": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x1F80000
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec1_zoffset": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x7E000
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec2_zoffset": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x1F80
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec3_zoffset": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x7E
    ),
    # "rwc_i_dest_target_reg_cfg_math_offset/2": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x1), # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "rwc_i_dest_target_reg_cfg_math_offset/1": DebugBusSignalDescription(             # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=3, daisy_sel=3, sig_sel=0, mask=0xFFFFFFFF
    # ),
    # "rwc_i_dest_target_reg_cfg_math_offset/0": DebugBusSignalDescription(         # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=2, daisy_sel=3, sig_sel=0, mask=0xE0000000
    # ),
    "rwc_i_thread_state_id": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=0, mask=0xE000000),
    "rwc_i_opcode[23..16]": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=0, mask=0x1FE0000),
    "rwc_i_instrn_payload[54..48]": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=0, mask=0xFE000000),
    "rwc_i_instrn_payload[71..55]": DebugBusSignalDescription(rd_sel=2, daisy_sel=3, sig_sel=0, mask=0x1FFFF),
    "rwc_i_opcode[15..8]": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=0, mask=0x1FE0000),
    "rwc_i_instrn_payload[30..24]": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=0, mask=0xFE000000),
    "rwc_i_instrn_payload[47..31]": DebugBusSignalDescription(rd_sel=1, daisy_sel=3, sig_sel=0, mask=0x1FFFF),
    "rwc_i_opcode[8]": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=0, mask=0x1000000),
    "rwc_i_instrn_payload[23..0]": DebugBusSignalDescription(rd_sel=0, daisy_sel=3, sig_sel=0, mask=0xFFFFFF),
    "perf_cnt_instrn_thread_issue_dbg18_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=22, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg18_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=22, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg18_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=22, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg18_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=22, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg17_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=20, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg17_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=20, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg17_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=20, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg17_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=20, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg16_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=18, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg16_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=18, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg16_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=18, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg16_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=18, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg15_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=16, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg15_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=16, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg15_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=16, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg15_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=16, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg14_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg14_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg14_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg14_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg13_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg13_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg13_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg13_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg12_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg12_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg12_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg12_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg11_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg11_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg11_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg11_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg10_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg10_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg10_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg10_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg9_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg9_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg9_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg9_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg8_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=4, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg8_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=4, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg8_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=4, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg8_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=4, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg7_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=5, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg7_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=5, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg7_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=5, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg7_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=5, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg6_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=5, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg6_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=5, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg6_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=5, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg6_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=5, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg5_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=5, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg5_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=5, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg5_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=5, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg5_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=5, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg4_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=5, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg4_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=5, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg4_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=5, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg4_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=5, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg3_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=5, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg3_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=5, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg3_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=5, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg3_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=5, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg2_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=5, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg2_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=5, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg2_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=5, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg2_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=5, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg1_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=5, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg1_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=5, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg1_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=5, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg1_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=5, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg0_stall_cnt": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=5, sig_sel=0, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg0_grant_cnt": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=5, sig_sel=0, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg0_req_cnt": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=5, sig_sel=0, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_issue_dbg0_ref_cnt": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=5, sig_sel=0, mask=0xFFFFFFFF
    ),
    "adcs_dbg_dest_sfpu_zero_return": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=11, mask=0x1FE),
    # "adcs_dest_sfpu_wr_en/0": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0xFE000000),  # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "adcs_dest_sfpu_wr_en/1": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=11, mask=0x1),     # Signal spans two consecutive groups, so its value cannot be read atomically.
    "adcs_dest_sfpu_rd_en": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x1FE0000),
    "adcs_sfpu_store_32bits_s1": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x10000),
    "adcs_sfpu_load_32bits_s1": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x8000),
    "adcs_sfpu_dst_reg_addr_s1_q": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x1FF8),
    "adcs_sfpu_update_zero_flags_s1": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x4),
    "adcs_sfpu_instr_valid_th_s1s4/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x80000000),
    "adcs_sfpu_instr_valid_th_s1s4/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=10, mask=0x3),
    "adcs_sfpu_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x70000000),
    "adcs_sfpu_active_q": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0xE000000),
    "adcs_sfpu_winner_combo_s0": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x1C00000),
    "adcs_i_sfpu_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x200000),
    "adcs_sfpu_instrn_pipe_ack_s0": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x100000),
    "adcs_sfpu_instrnbuf_rden_s1": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x80000),
    "adcs_sfpu_instruction_issue_stall": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x40000),
    "adcs_sfpu_instrn_valid_s1": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=10, mask=0x20000),
    "adcs_math_srcb_done": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x30000000),
    "adcs_srcb_write_done": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x8000000),
    "adcs_clr_src_b": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x4000000),
    "adcs_tdma_unpack_clr_src_b_ctrl": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x3E00000),
    "adcs_clr_all_banks": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x100000),
    "adcs_reset_datavalid": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x80000),
    "adcs_disable_srcb_dvalid_clear": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x60000),
    "adcs_disable_srcb_bank_switch": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x18000),
    "adcs_fpu_op_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x6000),
    "adcs_i_cg_src_pipeline_gatesrcbpipeen": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x1000),
    "adcs_gate_srcb_src_pipeline_rst": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x800),
    "adcs_srcb_data_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x600),
    "adcs_srcb_data_valid_exp": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x180),
    "adcs_srcb_write_math_id": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x40),
    "adcs_srcb_read_math_id": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x20),
    "adcs_srcb_read_math_id_exp": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x10),
    "adcs_srcb_addr_chg_track_state_exp": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0xC),
    "adcs_srcb_addr_chg_track_state_man": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=9, mask=0x3),
    "adcs_i_dest_fp32_read_en": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=9, mask=0xF000),
    "adcs_i_pack_unsigned": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=9, mask=0xF00),
    "adcs_i_dest_read_int8": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=9, mask=0xF0),
    "adcs_i_gasket_round_10b_mant": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=9, mask=0xF),
    "adcs_i_pack_req_dest_output_alu_format": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=6, sig_sel=9, mask=0xFFFF0000
    ),
    "adcs_i_pack_req_dest_x_pos": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=9, mask=0xFF00),
    "adcs_i_pack_req_dest_ds_rate/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=9, mask=0xF0000000),
    "adcs_i_pack_req_dest_ds_rate/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=9, mask=0xFF),
    # "adcs_i_pack_req_dest_ds_mask/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=8, mask=0xF0000000),   # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "adcs_i_pack_req_dest_ds_mask/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=8, mask=0xFFFFFFFF),   # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "adcs_i_pack_req_dest_ds_mask/2": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=9, mask=0xFFFFFFF),    # Signal spans two consecutive groups, so its value cannot be read atomically.
    "adcs_i_packer_z_pos": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=8, mask=0xFFFFFF0),
    "adcs_i_packer_edge_mask/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=8, mask=0xFFFFFFF0),
    "adcs_i_packer_edge_mask/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=8, mask=0xFFFFFFFF),
    "adcs_i_packer_edge_mask/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=8, mask=0xF),
    "adcs_i_packer_edge_mask_mode": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=8, mask=0xF),
    "adcs_dec_instr_single_output_row": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=7, mask=0x10),
    "adcs_curr_issue_instr_dest_fpu_addr/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=6, sig_sel=7, mask=0xFC000000
    ),
    "adcs_curr_issue_instr_dest_fpu_addr/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=7, mask=0xF),
    "adcs_dest_wrmask": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x1E000),
    "adcs_dest_fpu_wr_en": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x1FE0),
    "adcs_dest_fpu_rd_en": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x18),
    "adcs_pack_req_fifo_wren": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x4),
    "adcs_pack_req_fifo_rden": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x2),
    "adcs_pack_req_fifo_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=6, mask=0x1),
    "adcs_pack_req_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=6, mask=0x80000000),
    "adcs2_packers_channel1_w_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF000000),
    "adcs2_packers_channel1_w_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF0000),
    "adcs2_packers_channel1_z_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF00),
    "adcs2_packers_channel1_z_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF),
    "adcs2_packers_channel1_y_cr": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=5, mask=0x1FFF0000),
    "adcs2_packers_channel1_y_counter": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=5, mask=0x1FFF),
    "adcs2_packers_channel1_x_cr/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=5, mask=0xFFFC0000),
    "adcs2_packers_channel1_x_cr/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=5, mask=0xF),
    "adcs2_packers_channel1_x_counter": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=5, mask=0x3FFFF),
    "adcs2_packers_channel0_w_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF000000),
    "adcs2_packers_channel0_w_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF0000),
    "adcs2_packers_channel0_z_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF00),
    "adcs2_packers_channel0_z_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF),
    "adcs2_packers_channel0_y_cr": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=4, mask=0x1FFF0000),
    "adcs2_packers_channel0_y_counter": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=4, mask=0x1FFF),
    "adcs2_packers_channel0_x_cr/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=4, mask=0xFFFC0000),
    "adcs2_packers_channel0_x_cr/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=4, mask=0xF),
    "adcs2_packers_channel0_x_counter": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=4, mask=0x3FFFF),
    "adcs0_unpacker1_channel1_w_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF000000),
    "adcs0_unpacker1_channel1_w_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF0000),
    "adcs0_unpacker1_channel1_z_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF00),
    "adcs0_unpacker1_channel1_z_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF),
    "adcs0_unpacker1_channel1_y_cr": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=3, mask=0x1FFF0000),
    "adcs0_unpacker1_channel1_y_counter": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=3, mask=0x1FFF),
    "adcs0_unpacker1_channel1_x_cr/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=3, mask=0xFFFC0000),
    "adcs0_unpacker1_channel1_x_cr/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=3, mask=0xF),
    "adcs0_unpacker1_channel1_x_counter": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=3, mask=0x3FFFF),
    "adcs0_unpacker1_channel0_w_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF000000),
    "adcs0_unpacker1_channel0_w_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF0000),
    "adcs0_unpacker1_channel0_z_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF00),
    "adcs0_unpacker1_channel0_z_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF),
    "adcs0_unpacker1_channel0_y_cr": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=2, mask=0x1FFF0000),
    "adcs0_unpacker1_channel0_y_counter": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=2, mask=0x1FFF),
    "adcs0_unpacker1_channel0_x_cr/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=2, mask=0xFFFC0000),
    "adcs0_unpacker1_channel0_x_cr/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=2, mask=0xF),
    "adcs0_unpacker1_channel0_x_counter": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=2, mask=0x3FFFF),
    "adcs0_unpacker0_channel1_w_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF000000),
    "adcs0_unpacker0_channel1_w_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF0000),
    "adcs0_unpacker0_channel1_z_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF00),
    "adcs0_unpacker0_channel1_z_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF),
    "adcs0_unpacker0_channel1_y_cr": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=1, mask=0x1FFF0000),
    "adcs0_unpacker0_channel1_y_counter": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=1, mask=0x1FFF),
    "adcs0_unpacker0_channel1_x_cr/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=1, mask=0xFFFC0000),
    "adcs0_unpacker0_channel1_x_cr/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=1, mask=0xF),
    "adcs0_unpacker0_channel1_x_counter": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=1, mask=0x3FFFF),
    "adcs0_unpacker0_channel0_w_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF000000),
    "adcs0_unpacker0_channel0_w_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF0000),
    "adcs0_unpacker0_channel0_z_cr": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF00),
    "adcs0_unpacker0_channel0_z_counter": DebugBusSignalDescription(rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF),
    "adcs0_unpacker0_channel0_y_cr": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=0, mask=0x1FFF0000),
    "adcs0_unpacker0_channel0_y_counter": DebugBusSignalDescription(rd_sel=2, daisy_sel=6, sig_sel=0, mask=0x1FFF),
    "adcs0_unpacker0_channel0_x_cr/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=0, mask=0xFFFC0000),
    "adcs0_unpacker0_channel0_x_cr/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=6, sig_sel=0, mask=0xF),
    "adcs0_unpacker0_channel0_x_counter": DebugBusSignalDescription(rd_sel=0, daisy_sel=6, sig_sel=0, mask=0x3FFFF),
    "srca_wren_resh_d7": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=28, mask=0x1000),
    "srca_wr_datum_en_resh_d7/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=28, mask=0xFC000000),
    "srca_wr_datum_en_resh_d7/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=28, mask=0x3FF),
    "srca_wraddr_resh_d7": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=28, mask=0x3FFF000),
    "srca_wr_format_resh_d7": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=28, mask=0xF00),
    "h2_sfpu_dbg_bus7": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF0000000),
    "h2_sfpu_dbg_bus6": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF000000),
    "h2_sfpu_dbg_bus5": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF00000),
    "h2_sfpu_dbg_bus4": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF0000),
    "h2_sfpu_dbg_bus3": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF000),
    "h2_sfpu_dbg_bus2": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF00),
    "h2_sfpu_dbg_bus1": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF0),
    "h2_sfpu_dbg_bus0": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xF),
    "risc_wrapper_noc_ctrl_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x80000000
    ),
    "risc_wrapper_noc_ctrl_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x78000000
    ),
    "risc_wrapper_noc_ctrl_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x7800000
    ),
    "risc_wrapper_noc_ctrl_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x780000
    ),
    "risc_wrapper_noc_ctrl_o_mailbox_rd_valid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x78000
    ),
    "risc_wrapper_noc_ctrl_o_mailbox_rd_data": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=27, mask=0x7F00
    ),
    "risc_wrapper_noc_ctrl_intf_wrack_brisc/0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=27, mask=0xFFE00000
    ),
    "risc_wrapper_noc_ctrl_intf_wrack_brisc/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=27, mask=0x3F),
    "risc_wrapper_noc_ctrl_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=27, mask=0x100000
    ),
    "risc_wrapper_noc_ctrl_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=27, mask=0x80000
    ),
    "risc_wrapper_noc_ctrl_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=27, mask=0x2
    ),
    "risc_wrapper_noc_ctrl_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=27, mask=0x1
    ),
    "trisc2_icache_o_busy": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x200000),
    "trisc2_icache_req_fifo_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x100000),
    "trisc2_icache_req_fifo_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x80000),
    "trisc2_icache_mshr_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x40000),
    "trisc2_icache_mshr_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x20000),
    "trisc2_icache_way_hit": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x18000),
    "trisc2_icache_mshr_pf_hit": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x4000),
    "trisc2_icache_mshr_cpu_hit": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x2000),
    "trisc2_icache_some_mshr_allocated": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x1000),
    "trisc2_icache_latched_req_cpu_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x800),
    "trisc2_icache_cpu_req_dispatched": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x400),
    "trisc2_icache_latched_req_pf_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x200),
    "trisc2_icache_pf_req_dispatched": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x100),
    "trisc2_icache_qual_rden": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x80),
    "trisc2_icache_i_mispredict": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x40),
    "trisc2_icache_o_req_ready": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x20),
    "trisc2_icache_o_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x10),
    "trisc1_icache_o_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x10000000),
    "trisc1_icache_req_fifo_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x8000000),
    "trisc1_icache_req_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x4000000),
    "trisc1_icache_mshr_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x2000000),
    "trisc1_icache_mshr_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x1000000),
    "trisc1_icache_way_hit": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0xC00000),
    "trisc1_icache_mshr_pf_hit": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x200000),
    "trisc1_icache_mshr_cpu_hit": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x100000),
    "trisc1_icache_some_mshr_allocated": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x80000),
    "trisc1_icache_latched_req_cpu_vld": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x40000),
    "trisc1_icache_cpu_req_dispatched": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x20000),
    "trisc1_icache_latched_req_pf_vld": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x10000),
    "trisc1_icache_pf_req_dispatched": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x8000),
    "trisc1_icache_qual_rden": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x4000),
    "trisc1_icache_i_mispredict": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x2000),
    "trisc1_icache_o_req_ready": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x1000),
    "trisc1_icache_o_instrn_vld": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x800),
    "trisc0_icache_o_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x8),
    "trisc0_icache_req_fifo_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x4),
    "trisc0_icache_req_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x2),
    "trisc0_icache_mshr_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x1),
    "trisc0_icache_mshr_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x80000000),
    "trisc0_icache_way_hit": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x60000000),
    "trisc0_icache_mshr_pf_hit": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x10000000),
    "trisc0_icache_mshr_cpu_hit": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x8000000),
    "trisc0_icache_some_mshr_allocated": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x4000000),
    "trisc0_icache_latched_req_cpu_vld": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x2000000),
    "trisc0_icache_cpu_req_dispatched": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x1000000),
    "trisc0_icache_latched_req_pf_vld": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x800000),
    "trisc0_icache_pf_req_dispatched": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x400000),
    "trisc0_icache_qual_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x200000),
    "trisc0_icache_i_mispredict": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x100000),
    "trisc0_icache_o_req_ready": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x80000),
    "trisc0_icache_o_instrn_vld": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x40000),
    "brisc_icache_o_busy": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x400),
    "brisc_icache_req_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x200),
    "brisc_icache_req_fifo_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x100),
    "brisc_icache_mshr_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x80),
    "brisc_icache_mshr_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x40),
    "brisc_icache_way_hit": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x30),
    "brisc_icache_mshr_pf_hit": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x8),
    "brisc_icache_mshr_cpu_hit": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x4),
    "brisc_icache_some_mshr_allocated": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x2),
    "brisc_icache_latched_req_cpu_vld": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x1),
    "brisc_icache_cpu_req_dispatched": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x80000000),
    "brisc_icache_latched_req_pf_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x40000000),
    "brisc_icache_pf_req_dispatched": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x20000000),
    "brisc_icache_qual_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x10000000),
    "brisc_icache_i_mispredict": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x8000000),
    "brisc_icache_o_req_ready": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x4000000),
    "brisc_icache_o_instrn_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x2000000),
    "brisc_icache_noc_ctrl_o_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x20000),
    "brisc_icache_noc_ctrl_req_fifo_empty": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x10000),
    "brisc_icache_noc_ctrl_req_fifo_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x8000),
    "brisc_icache_noc_ctrl_mshr_empty": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x4000),
    "brisc_icache_noc_ctrl_mshr_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x2000),
    "brisc_icache_noc_ctrl_way_hit": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x1800),
    "brisc_icache_noc_ctrl_mshr_pf_hit": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x400),
    "brisc_icache_noc_ctrl_mshr_cpu_hit": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x200),
    "brisc_icache_noc_ctrl_some_mshr_allocated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x100
    ),
    "brisc_icache_noc_ctrl_latched_req_cpu_vld": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x80
    ),
    "brisc_icache_noc_ctrl_cpu_req_dispatched": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x40),
    "brisc_icache_noc_ctrl_latched_req_pf_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x20),
    "brisc_icache_noc_ctrl_pf_req_dispatched": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x10),
    "brisc_icache_noc_ctrl_qual_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x8),
    "brisc_icache_noc_ctrl_i_mispredict": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x4),
    "brisc_icache_noc_ctrl_o_req_ready": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x2),
    "brisc_icache_noc_ctrl_o_instrn_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0x1),
    "ncrisc_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x200),
    "ncrisc_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x100
    ),
    "ncrisc_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x80),
    "ncrisc_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x20),
    "ncrisc_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x1F),
    "ncrisc_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=25, mask=0xFFFFFFFF),
    "ncrisc_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x80000000),
    "ncrisc_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x40000000
    ),
    "ncrisc_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x3FFFFFFF),
    "ncrisc_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x10000000),
    "ncrisc_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x1F00000),
    "ncrisc_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x40000),
    "ncrisc_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x7C00),
    "ncrisc_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x100),
    "ncrisc_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x1F),
    "ncrisc_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x80000000),
    "ncrisc_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x7FFFFFFF),
    "ncrisc_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x80000000),
    "ncrisc_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x40000000
    ),
    "ncrisc_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x3FFFFFFF),
    "ncrisc_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x80000000),
    "ncrisc_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x40000000),
    "ncrisc_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x3FFFFFFF),
    "ncrisc_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x80000000),
    "ncrisc_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x7FFFFFFF),
    "trisc2_trisc_mop_buf_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x40000000),
    "trisc2_trisc_mop_buf_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x20000000),
    "trisc2_mop_decode_debug_bus_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x1C000000
    ),
    "trisc2_mop_decode_debug_bus_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3800000
    ),
    "trisc2_mop_decode_debug_bus_mop_stage_valid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x400000
    ),
    "trisc2_mop_decode_debug_bus_mop_stage_opcode/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0xFFC00000
    ),
    "trisc2_mop_decode_debug_bus_mop_stage_opcode/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3FFFFF
    ),
    "trisc2_mop_decode_debug_bus_math_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x200000
    ),
    "trisc2_mop_decode_debug_bus_unpack_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x100000
    ),
    "trisc2_mop_decode_debug_bus_o_instrn_valid": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x80000
    ),
    "trisc2_mop_decode_debug_bus_o_instrn_opcode/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFFF80000
    ),
    "trisc2_mop_decode_debug_bus_o_instrn_opcode/1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x7FFFF
    ),
    "trisc2_pc_buffer_debug_bus_sempost_pending": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFF00
    ),
    "trisc2_pc_buffer_debug_bus_semget_pending": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFF
    ),
    "trisc2_pc_buffer_debug_bus_trisc_read_request_pending": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x80000000
    ),
    "trisc2_pc_buffer_debug_bus_trisc_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x40000000
    ),
    "trisc2_pc_buffer_debug_bus_trisc_sync_type": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x20000000
    ),
    "trisc2_pc_buffer_debug_bus_riscv_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x10000000
    ),
    "trisc2_pc_buffer_debug_bus_pc_buffer_idle": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x8000000
    ),
    "trisc2_pc_buffer_debug_bus_i_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x4000000),
    "trisc2_pc_buffer_debug_bus_i_mops_outstanding": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x2000000
    ),
    "trisc2_pc_buffer_debug_bus_cmd_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x1000000
    ),
    "trisc2_pc_buffer_debug_bus_cmd_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x800000
    ),
    # "trisc2_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(  # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=3, daisy_sel=7, sig_sel=22, mask=0xFF800000
    # ),
    # "trisc2_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(  # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x7FFFFF
    # ),
    "trisc2_risc_wrapper_debug_bus_trisc_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x400000
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C0000
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C000
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C00
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_o_mailbox_rdvalid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C0
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_o_mailbox_rddata/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=22, mask=0xFFFF0000
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3F
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x3FFE0000
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x10000
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x8000
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x2
    ),
    "trisc2_risc_wrapper_debug_bus_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x1
    ),
    "trisc1_trisc_mop_buf_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x40000000),
    "trisc1_trisc_mop_buf_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x20000000),
    "trisc1_mop_decode_debug_bus_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x1C000000
    ),
    "trisc1_mop_decode_debug_bus_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3800000
    ),
    "trisc1_mop_decode_debug_bus_mop_stage_valid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x400000
    ),
    "trisc1_mop_decode_debug_bus_mop_stage_opcode/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0xFFC00000
    ),
    "trisc1_mop_decode_debug_bus_mop_stage_opcode/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3FFFFF
    ),
    "trisc1_mop_decode_debug_bus_math_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x200000
    ),
    "trisc1_mop_decode_debug_bus_unpack_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x100000
    ),
    "trisc1_mop_decode_debug_bus_o_instrn_valid": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x80000
    ),
    "trisc1_mop_decode_debug_bus_o_instrn_opcode/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFFF80000
    ),
    "trisc1_mop_decode_debug_bus_o_instrn_opcode/1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x7FFFF
    ),
    "trisc1_pc_buffer_debug_bus_sempost_pending": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFF00
    ),
    "trisc1_pc_buffer_debug_bus_semget_pending": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFF
    ),
    "trisc1_pc_buffer_debug_bus_trisc_read_request_pending": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x80000000
    ),
    "trisc1_pc_buffer_debug_bus_trisc_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x40000000
    ),
    "trisc1_pc_buffer_debug_bus_trisc_sync_type": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x20000000
    ),
    "trisc1_pc_buffer_debug_bus_riscv_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x10000000
    ),
    "trisc1_pc_buffer_debug_bus_pc_buffer_idle": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x8000000
    ),
    "trisc1_pc_buffer_debug_bus_i_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x4000000),
    "trisc1_pc_buffer_debug_bus_i_mops_outstanding": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x2000000
    ),
    "trisc1_pc_buffer_debug_bus_cmd_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x1000000
    ),
    "trisc1_pc_buffer_debug_bus_cmd_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x800000
    ),
    # "trisc1_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(   # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=3, daisy_sel=7, sig_sel=20, mask=0xFF800000
    # ),
    # "trisc1_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(  # Signal spans two consecutive groups, so its value cannot be read atomically.
    #     rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x7FFFFF
    # ),
    "trisc1_risc_wrapper_debug_bus_trisc_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x400000
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C0000
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C000
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C00
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_o_mailbox_rdvalid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C0
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_o_mailbox_rddata/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=20, mask=0xFFFF0000
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3F
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x3FFE0000
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x10000
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x8000
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x2
    ),
    "trisc1_risc_wrapper_debug_bus_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x1
    ),
    "trisc0_trisc_mop_buf_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x40000000),
    "trisc0_trisc_mop_buf_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x20000000),
    "trisc0_mop_decode_debug_bus_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x1C000000
    ),
    "trisc0_mop_decode_debug_bus_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3800000
    ),
    "trisc0_mop_decode_debug_bus_mop_stage_valid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x400000
    ),
    "trisc0_mop_decode_debug_bus_mop_stage_opcode": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0xFFC00000
    ),
    "trisc0_mop_decode_debug_bus_mop_stage_opcode": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3FFFFF
    ),
    "trisc0_mop_decode_debug_bus_math_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x200000
    ),
    "trisc0_mop_decode_debug_bus_unpack_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x100000
    ),
    "trisc0_mop_decode_debug_bus_o_instrn_valid": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x80000
    ),
    "trisc0_mop_decode_debug_bus_o_instrn_opcode/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFFF80000
    ),
    "trisc0_mop_decode_debug_bus_o_instrn_opcode/1": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x7FFFF
    ),
    "trisc0_pc_buffer_debug_bus_sempost_pending": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFF00
    ),
    "trisc0_pc_buffer_debug_bus_semget_pending": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFF
    ),
    "trisc0_pc_buffer_debug_bus_trisc_read_request_pending": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x80000000
    ),
    "trisc0_pc_buffer_debug_bus_trisc_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x40000000
    ),
    "trisc0_pc_buffer_debug_bus_trisc_sync_type": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x20000000
    ),
    "trisc0_pc_buffer_debug_bus_riscv_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x10000000
    ),
    "trisc0_pc_buffer_debug_bus_pc_buffer_idle": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x8000000
    ),
    "trisc0_pc_buffer_debug_bus_i_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x4000000),
    "trisc0_pc_buffer_debug_bus_i_mops_outstanding": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x2000000
    ),
    "trisc0_pc_buffer_debug_bus_cmd_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1000000
    ),
    "trisc0_pc_buffer_debug_bus_cmd_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x800000
    ),
    # "trisc0_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(       # Signal spans two consecutive groups, so its value cannot be read atomically." are duplicates
    #     rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x7FFFFF
    # ),
    # "trisc0_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(       # Signal spans two consecutive groups, so its value cannot be read atomically." are duplicates
    #     rd_sel=3, daisy_sel=7, sig_sel=18, mask=0xFF800000
    # ),
    "trisc0_risc_wrapper_debug_bus_trisc_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x400000
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C0000
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C000
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C00
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_o_mailbox_rdvalid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C0
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_o_mailbox_rddata/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=18, mask=0xFFFF0000
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3F
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x3FFE0000
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x10000
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x8000
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x2
    ),
    "trisc0_risc_wrapper_debug_bus_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x1
    ),
    "trisc2_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x200),
    "trisc2_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x100
    ),
    "trisc2_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x80),
    "trisc2_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x20),
    "trisc2_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x1F),
    "trisc2_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=17, mask=0xFFFFFFFF),
    "trisc2_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x80000000),
    "trisc2_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x40000000
    ),
    "trisc2_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x3FFFFFFF),
    "trisc2_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x10000000),
    "trisc2_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x1F00000),
    "trisc2_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x40000),
    "trisc2_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x7C00),
    "trisc2_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x100),
    "trisc2_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x1F),
    "trisc2_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=16, mask=0x80000000),
    "trisc2_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=16, mask=0x7FFFFFFF),
    "trisc2_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x80000000),
    "trisc2_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x40000000
    ),
    "trisc2_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x3FFFFFFF),
    "trisc2_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x80000000),
    "trisc2_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x40000000),
    "trisc2_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x3FFFFFFF),
    "trisc2_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=16, mask=0x80000000),
    "trisc2_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=16, mask=0x7FFFFFFF),
    "trisc1_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x200),
    "trisc1_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x100
    ),
    "trisc1_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x80),
    "trisc1_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x20),
    "trisc1_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x1F),
    "trisc1_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=15, mask=0xFFFFFFFF),
    "trisc1_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x80000000),
    "trisc1_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x40000000
    ),
    "trisc1_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x3FFFFFFF),
    "trisc1_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x10000000),
    "trisc1_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x1F00000),
    "trisc1_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x40000),
    "trisc1_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x7C00),
    "trisc1_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x100),
    "trisc1_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x1F),
    "trisc1_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=14, mask=0x80000000),
    "trisc1_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=14, mask=0x7FFFFFFF),
    "trisc1_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x80000000),
    "trisc1_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x40000000
    ),
    "trisc1_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x3FFFFFFF),
    "trisc1_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x80000000),
    "trisc1_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x40000000),
    "trisc1_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x3FFFFFFF),
    "trisc1_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=14, mask=0x80000000),
    "trisc1_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=14, mask=0x7FFFFFFF),
    "trisc0_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x200),
    "trisc0_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x100
    ),
    "trisc0_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x80),
    "trisc0_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x20),
    "trisc0_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x1F),
    "trisc0_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=13, mask=0xFFFFFFFF),
    "trisc0_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x80000000),
    "trisc0_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x40000000
    ),
    "trisc0_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x3FFFFFFF),
    "trisc0_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x10000000),
    "trisc0_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F00000),
    "trisc0_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x40000),
    "trisc0_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x7C00),
    "trisc0_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x100),
    "trisc0_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F),
    "trisc0_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x80000000),
    "trisc0_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF),
    "trisc0_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x80000000),
    "trisc0_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x40000000
    ),
    "trisc0_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF),
    "trisc0_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x80000000),
    "trisc0_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x40000000),
    "trisc0_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF),
    "trisc0_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x80000000),
    "trisc0_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF),
    "brisc_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x200),
    "brisc_id_ex_rts_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x100
    ),
    "brisc_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x80),
    "brisc_if_invalid_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x40),
    "brisc_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x20),
    "brisc_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x1F),
    "brisc_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=11, mask=0xFFFFFFFF),
    "brisc_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x80000000),
    "brisc_ex_id_rtr_dup": DebugBusSignalDescription(  # Duplicate signal name
        rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x40000000
    ),
    "brisc_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x3FFFFFFF),
    "brisc_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x10000000),
    "brisc_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F00000),
    "brisc_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x40000),
    "brisc_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x7C00),
    "brisc_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x100),
    "brisc_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F),
    "brisc_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x80000000),
    "brisc_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF),
    "brisc_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x80000000),
    "brisc_o_instrn_req": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x40000000),
    "brisc_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF),
    "brisc_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x80000000),
    "brisc_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x40000000),
    "brisc_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF),
    "brisc_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x80000000),
    "brisc_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF),
    "perf_cnt_tensix_in4_l1_stall_cnt0": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=9, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in4_l1_grant_cnt0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=9, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in4_l1_req_cnt0": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=9, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in4_l1_ref_cnt0": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=9, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in4_l1_stall_cnt1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=8, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in4_l1_grant_cnt1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=8, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in4_l1_req_cnt1": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=8, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in4_l1_ref_cnt1": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=8, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in3_l1_stall_cnt0": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=7, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in3_l1_grant_cnt0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=7, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in3_l1_req_cnt0": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=7, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in3_l1_ref_cnt0": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=7, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in3_l1_stall_cnt1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=6, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in3_l1_grant_cnt1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=6, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in3_l1_req_cnt1": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=6, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in3_l1_ref_cnt1": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=6, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in2_l1_stall_cnt0": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=5, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in2_l1_grant_cnt0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=5, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in2_l1_req_cnt0": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=5, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in2_l1_ref_cnt0": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=5, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in2_l1_stall_cnt1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=4, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in2_l1_grant_cnt1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=4, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in2_l1_req_cnt1": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=4, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in2_l1_ref_cnt1": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=4, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in1_l1_stall_cnt0": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=3, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in1_l1_grant_cnt0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=3, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in1_l1_req_cnt0": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=3, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in1_l1_ref_cnt0": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=3, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in1_l1_stall_cnt1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=2, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in1_l1_grant_cnt1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=2, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in1_l1_req_cnt1": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2, mask=0xFFFFFFFF),
    "perf_cnt_tensix_in1_l1_ref_cnt1": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2, mask=0xFFFFFFFF),
    "brisc_o_par_err_risc_localmem": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x80000000),
    "brisc_i_mailbox_rden": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x78000000),
    "brisc_i_mailbox_rd_type": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x7800000),
    "brisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x780000),
    "brisc_o_mailbox_rdvalid": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x78000),
    "brisc_o_mailbox_rddata[DEBUG_MAILBOX_DATA_W-1:0]": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x7F00
    ),
    "brisc_intf_wrack/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=1, mask=0xFFE00000),
    "brisc_intf_wrack/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=1, mask=0x3F),
    "brisc_rv_out_dmem_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x100000),
    "brisc_rv_out_dmem_wren": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x80000),
    "brisc_icache_req_fifo_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x2),
    "brisc_icache_req_fifo_empty": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x1),
    "perf_cnt_fpu_dbg0_stall_cnt": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFF),
    "perf_cnt_fpu_dbg0_grant_cnt": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFF),
    "perf_cnt_fpu_dbg0_req_cnt": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFF),
    "perf_cnt_fpu_dbg0_ref_cnt": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=0, mask=0xFFFFFFFF),
    "l1_addr_p41/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=13, mask=0xFFFE0000),
    "l1_addr_p41/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=13, mask=0x3),
    "l1_addr_p40": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=13, mask=0x1FFFF),
    "l1_addr_p39": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=13, mask=0xFFFF8000),
    # "l1_addr_p38/1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=13, mask=0x7FFF),       # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "l1_addr_p38/0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=11, mask=0xC0000000),   # Signal spans two consecutive groups, so its value cannot be read atomically.
    "l1_addr_p37": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=11, mask=0x3FFFE000),
    "l1_addr_p36/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=11, mask=0xF0000000),
    "l1_addr_p36/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=11, mask=0x1FFF),
    "l1_addr_p35": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=11, mask=0xFFFF800),
    "l1_addr_p34/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=11, mask=0xFC000000),
    "l1_addr_p34/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=11, mask=0x7FF),
    "l1_addr_p33": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=11, mask=0x3FFFE00),
    "l1_addr_p32/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=11, mask=0xFF000000),
    "l1_addr_p32/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=11, mask=0x1FF),
    "l1_addr_p31": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=11, mask=0xFFFF80),
    # "l1_addr_p30/0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=10, mask=0xFFC00000),       # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "l1_addr_p30/1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=11, mask=0x7F),     # Signal spans two consecutive groups, so its value cannot be read atomically.
    "l1_addr_p29": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=10, mask=0x3FFFE0),
    "l1_addr_p28/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=10, mask=0xFFF00000),
    "l1_addr_p28/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=10, mask=0x1F),
    "l1_addr_p27": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=10, mask=0xFFFF8),
    "l1_addr_p26/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=10, mask=0xFFFC0000),
    "l1_addr_p26/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=10, mask=0x7),
    "l1_addr_p25": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=10, mask=0x3FFFE),
    "l1_addr_p24/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=10, mask=0xFFFF0000),
    "l1_addr_p24/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=10, mask=0x1),
    # "l1_addr_p23/1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=10, mask=0xFFFF),    # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "l1_addr_p23/0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=9, mask=0x80000000),  # Signal spans two consecutive groups, so its value cannot be read atomically.
    "l1_addr_p22": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=9, mask=0x7FFFC000),
    "l1_addr_p21/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=9, mask=0xE0000000),
    "l1_addr_p21/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=9, mask=0x3FFF),
    "l1_addr_p20": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=9, mask=0x1FFFF000),
    "l1_addr_p19/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=9, mask=0xF8000000),
    "l1_addr_p19/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=9, mask=0xFFF),
    "l1_addr_p18": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=9, mask=0x7FFFC00),
    "l1_addr_p17/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=9, mask=0xFE000000),
    "l1_addr_p17/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=9, mask=0x3FF),
    "l1_addr_p16": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=9, mask=0x1FFFF00),
    # "l1_addr_p15/0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=8, mask=0xFF800000),   # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "l1_addr_p15/1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=9, mask=0xFF),          # Signal spans two consecutive groups, so its value cannot be read atomically.
    "l1_addr_p14": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=8, mask=0x7FFFC0),
    "l1_addr_p13/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=8, mask=0xFFE00000),
    "l1_addr_p13/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=8, mask=0x3F),
    "l1_addr_p12": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=8, mask=0x1FFFF0),
    "l1_addr_p11/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=8, mask=0xFFF80000),
    "l1_addr_p11/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=8, mask=0xF),
    "l1_addr_p10": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=8, mask=0x7FFFC),
    "l1_addr_p9/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=8, mask=0xFFFE0000),
    "l1_addr_p9/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=8, mask=0x3),
    "l1_addr_p8": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=8, mask=0x1FFFF),
    "l1_addr_p7": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=7, mask=0xFFE00000),
    "l1_addr_p6": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=7, mask=0x1FFFF0),
    "l1_addr_p5/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=7, mask=0xFFF80000),
    "l1_addr_p5/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=7, mask=0xF),
    "l1_addr_p4": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=7, mask=0x7FFFC),
    "l1_addr_p3/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=7, mask=0xFFFE0000),
    "l1_addr_p3/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=7, mask=0x3),
    "l1_addr_p2": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=7, mask=0x1FFFF),
    "l1_addr_p1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=7, mask=0xFFFF8000),
    # "l1_addr_p0/0": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=6, mask=0xC0000000),     # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "l1_addr_p0/1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=7, mask=0x7FFF),         # Signal spans two consecutive groups, so its value cannot be read atomically.
    "t_l1_reqif_ready/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=6, mask=0xFFF00000),
    "t_l1_reqif_ready/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=6, mask=0x3FFFFFFF),
    "t_l1_rden/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=6, mask=0xFFFFFC00),
    "t_l1_rden/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=6, mask=0xFFFFF),
    "t_l1_wren/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=6, mask=0xFFFFFFFF),
    "t_l1_wren/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=6, mask=0x3FF),
    "t_l1_at_instrn_p9": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=5, mask=0xFFFF0000),
    "t_l1_at_instrn_p8": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=5, mask=0xFFFF),
    "t_l1_at_instrn_p7": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=4, mask=0xFFFF0000),
    "t_l1_at_instrn_p6": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=4, mask=0xFFFF),
    "t_l1_at_instrn_p5": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=4, mask=0xFFFF0000),
    "t_l1_at_instrn_p4": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=4, mask=0xFFFF),
    "t_l1_at_instrn_p3": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=4, mask=0xFFFF0000),
    "t_l1_at_instrn_p2": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=4, mask=0xFFFF),
    "t_l1_at_instrn_p1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=4, mask=0xFFFF0000),
    "t_l1_at_instrn_p0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=4, mask=0xFFFF),
    "l1_access_port_l1_addr_p15": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=3, mask=0xFFFF0000),
    "l1_access_port_l1_addr_p14": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=3, mask=0xFFFF),
    "l1_access_port_l1_addr_p13": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=3, mask=0xFFFF0000),
    "l1_access_port_l1_addr_p12": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=3, mask=0xFFFF),
    "l1_access_port_l1_addr_p11": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=3, mask=0xFFFF0000),
    "l1_access_port_l1_addr_p10": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=3, mask=0xFFFF),
    "l1_access_port_l1_addr_p9": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=3, mask=0xFFFF0000),
    "l1_access_port_l1_addr_p8": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=3, mask=0xFFFF),
    "l1_access_port_l1_addr_p7": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=2, mask=0xFFFF0000),
    "l1_access_port_l1_addr_p6": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=2, mask=0xFFFF),
    "l1_access_port_l1_addr_p5": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=2, mask=0xFFFF0000),
    "l1_access_port_l1_addr_p4": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=2, mask=0xFFFF),
    "l1_access_port_l1_addr_p3": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=2, mask=0xFFFF0000),
    "l1_access_port_l1_addr_p2": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=2, mask=0xFFFF),
    "l1_access_port_l1_addr_p1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=2, mask=0xFFFF0000),
    "l1_access_port_l1_addr_p0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=2, mask=0xFFFF),
    "tensix_w_l1_at_instrn_p15": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=1, mask=0xFFFF0000),
    "tensix_w_l1_at_instrn_p14": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=1, mask=0xFFFF),
    "tensix_w_l1_at_instrn_p13": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=1, mask=0xFFFF0000),
    "tensix_w_l1_at_instrn_p12": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=1, mask=0xFFFF),
    "tensix_w_l1_at_instrn_p11": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=1, mask=0xFFFF0000),
    "tensix_w_l1_at_instrn_p10": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=1, mask=0xFFFF),
    "tensix_w_l1_at_instrn_p9": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=1, mask=0xFFFF0000),
    "tensix_w_l1_at_instrn_p8": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=1, mask=0xFFFF),
    "tensix_w_l1_at_instrn_p7": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=0, mask=0xFFFF0000),
    "tensix_w_l1_at_instrn_p6": DebugBusSignalDescription(rd_sel=3, daisy_sel=8, sig_sel=0, mask=0xFFFF),
    "tensix_w_l1_at_instrn_p5": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=0, mask=0xFFFF0000),
    "tensix_w_l1_at_instrn_p4": DebugBusSignalDescription(rd_sel=2, daisy_sel=8, sig_sel=0, mask=0xFFFF),
    "tensix_w_l1_at_instrn_p3": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=0, mask=0xFFFF0000),
    "tensix_w_l1_at_instrn_p2": DebugBusSignalDescription(rd_sel=1, daisy_sel=8, sig_sel=0, mask=0xFFFF),
    "tensix_w_l1_at_instrn_p1": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=0, mask=0xFFFF0000),
    "tensix_w_l1_at_instrn_p0": DebugBusSignalDescription(rd_sel=0, daisy_sel=8, sig_sel=0, mask=0xFFFF),
    "o_exp_section_size/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=10, sig_sel=3, mask=0xFFF00000),
    "o_exp_section_size/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=10, sig_sel=3, mask=0xFFFFF),
    "o_rowstart_section_size/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=10, sig_sel=3, mask=0xFFF00000),
    "o_rowstart_section_size/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=10, sig_sel=3, mask=0xFFFFF),
    "o_add_l1_destination_addr_offset": DebugBusSignalDescription(rd_sel=0, daisy_sel=10, sig_sel=2, mask=0xF),
    "in_thcon_instrn": DebugBusSignalDescription(rd_sel=1, daisy_sel=10, sig_sel=0, mask=0xFFFFFFFF),
    "o_first_datum_prefix_zeros": DebugBusSignalDescription(rd_sel=2, daisy_sel=11, sig_sel=2, mask=0x1FFFE),
    "o_start_datum_index/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=11, sig_sel=2, mask=0xFFFE0000),
    "o_start_datum_index/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=11, sig_sel=2, mask=0x1),
    "o_end_datum_index": DebugBusSignalDescription(rd_sel=1, daisy_sel=11, sig_sel=2, mask=0x1FFFE),
    "o_first_data_skip_one_phase/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0xE0000000),
    "o_first_data_skip_one_phase/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=11, sig_sel=2, mask=0x1),
    "x_start_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0x1FFF0000),
    "x_end_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0xFFF8),
    "unpack_sel_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0x4),
    "thread_id_d": DebugBusSignalDescription(rd_sel=0, daisy_sel=11, sig_sel=2, mask=0x3),
    "unp0_unpack0_demux_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=12, sig_sel=1, mask=0xE0000000),
    "unp0_unpack0_demux_fifo_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=12, sig_sel=1, mask=0x1C000000),
    "unp0_unpack0_and_demux_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=12, sig_sel=1, mask=0x2000000),
    "unp0_unpack0_or_demux_fifo_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=12, sig_sel=1, mask=0x10000000),
    "unp0_unpack0_req_param_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=12, sig_sel=0, mask=0x80000000),
    "unp0_unpack0_req_param_fifo_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=12, sig_sel=0, mask=0x40000000),
    "unp0_unpack0_param_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=12, sig_sel=0, mask=0x20000000),
    "unp0_unpack0_param_fifo_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=12, sig_sel=0, mask=0x10000000),
    "unp1_unpack0_demux_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=13, sig_sel=1, mask=0xE0000000),
    "unp1_unpack0_demux_fifo_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=13, sig_sel=1, mask=0x1C000000),
    "unp1_unpack0_and_demux_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=13, sig_sel=1, mask=0x2000000),
    "unp1_unpack0_or_demux_fifo_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=13, sig_sel=1, mask=0x10000000),
    "unp1_unpack0_req_param_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=13, sig_sel=0, mask=0x80000000),
    "unp1_unpack0_req_param_fifo_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=13, sig_sel=0, mask=0x40000000),
    "unp1_unpack0_param_fifo_empty": DebugBusSignalDescription(rd_sel=1, daisy_sel=13, sig_sel=0, mask=0x20000000),
    "unp1_unpack0_param_fifo_full": DebugBusSignalDescription(rd_sel=1, daisy_sel=13, sig_sel=0, mask=0x10000000),
    "tdma_packer_z_pos/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=14, sig_sel=6, mask=0xFFFF0000),
    "tdma_packer_z_pos/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=14, sig_sel=6, mask=0xFF),
    "tdma_packer_y_pos": DebugBusSignalDescription(rd_sel=0, daisy_sel=14, sig_sel=6, mask=0xFFFF),
    "packed_exps_p5/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=14, sig_sel=5, mask=0xFFFFFFFC),
    "packed_exps_p5/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=5, mask=0xFFFFFFFF),
    # "packed_data_p5/0": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0xFFFFFFF0),        # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "packed_data_p5/1": DebugBusSignalDescription(rd_sel=0, daisy_sel=14, sig_sel=5, mask=0xFFFFFFFF),        # Signal spans two consecutive groups, so its value cannot be read atomically.
    # "packed_data_p5/2": DebugBusSignalDescription(rd_sel=1, daisy_sel=14, sig_sel=5, mask=0x3),               # Signal spans two consecutive groups, so its value cannot be read atomically.
    "dram_data_fifo_rden": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0x8),
    "dram_rden": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0x4),
    "dram_data_fifo_rden_p2": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0x2),
    "dram_rdata_phase_adj_asmbld_any_valid_p2": DebugBusSignalDescription(rd_sel=3, daisy_sel=14, sig_sel=4, mask=0x1),
    "pipe_data_clken_p2": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x80000000),
    "pipe_clken_p2": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x40000000),
    "pipe_clken_p3": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x20000000),
    "pipe_busy_p3": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x10000000),
    "pipe_clken_p4": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x8000000),
    "pipe_busy_p4": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x4000000),
    "pipe_busy_p5": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x2000000),
    "pipe_busy_p6": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x1000000),
    "pipe_busy_p6p7": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x800000),
    "pipe_busy_p8": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x400000),
    "in_param_fifo_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x200000),
    "fmt_bw_expand_in_param_fifo_empty_p1": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x100000),
    "and_l1_req_fifo_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x80000),
    "dram_req_fifo_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x40000),
    "and_l1_to_l1_pack_resp_fifo_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x20000),
    "and_l1_to_l1_pack_resp_demux_fifo_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x10000
    ),
    "or_requester_busy": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x8000),
    "stall_on_tile_end_drain_q": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x4000),
    "stall_on_tile_end_drain_nxt": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x2000),
    "last_row_end_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x1000),
    "set_last_row_end_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x800),
    "data_conv_busy_c0": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x400),
    "data_conv_busy_c1": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x200),
    "in_param_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x100),
    "fmt_bw_expand_in_param_fifo_full_p1": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x80),
    "or_l1_req_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x40),
    "dram_req_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x20),
    "or_l1_to_l1_pack_resp_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x10),
    "or_l1_to_l1_pack_resp_demux_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x8),
    "reg_fifo_empty": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x4),
    "reg_fifo_full": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x2),
    "param_fifo_flush_wa_buffers_vld_p2": DebugBusSignalDescription(rd_sel=2, daisy_sel=14, sig_sel=4, mask=0x1),
}

# Group name mapping (daisy_sel, sig_sel)
group_map: dict[str, tuple[int, int]] = {
    # Tensix Frontend (DaisySel == 1)
    "perf_counter_thread_stall_requests": (1, 1),
    "perf_counter_stall_grant_mixed": (1, 2),
    "perf_counter_instruction_stall_grants": (1, 3),
    "tensix_frontend_t2": (1, 4),
    "tensix_frontend_t2_stall_signals": (1, 5),
    "perf_counter_instruction_grants": (1, 6),
    "perf_counter_mixed_stall_grant_operations": (1, 7),
    "tensix_frontend_t1": (1, 8),
    "tensix_frontend_perf_counters": (1, 9),
    "perf_counter_instruction_stall_reason_mixed": (1, 10),
    "perf_counter_thread_execution_stalls": (1, 11),
    "tensix_frontend_t0": (1, 12),
    "tensix_frontend_t0_risc_stall": (1, 13),
    # Math Engine Controls (DaisySel == 2)
    "risc_in_reg_rddata": (2, 0),
    "risc_out_reg_wrdata": (2, 2),
    "cfg_gpr_p1_data": (2, 4),
    "thcon_p1_ret": (2, 6),
    "l1_ret_wrdata": (2, 8),
    "gpr_cfg_p0_data": (2, 10),
    "p0_gpr_ret": (2, 12),
    "thcon_p0_gpr_wrdata": (2, 14),
    "risc_thcon_gpr_interface": (2, 16),
    # RWCs and Control (DaisySel == 3)
    "rwc_control_signals": (3, 0),
    "rwc_status_signals": (3, 1),
    "rwc_fidelity_phase": (3, 4),
    "rwc_pack_unpack_signals": (3, 5),
    "rwc_tdma_core_signals": (3, 6),
    "rwc_math_pipeline": (3, 7),
    # Issue debug performance counters from 8 to 18 (DaisySel == 4)
    "perf_counter_instrn_thread_issue_dbg8": (4, 2),
    "perf_counter_instrn_thread_issue_dbg9": (4, 4),
    "perf_counter_instrn_thread_issue_dbg10": (4, 6),
    "perf_counter_instrn_thread_issue_dbg11": (4, 8),
    "perf_counter_instrn_thread_issue_dbg12": (4, 10),
    "perf_counter_instrn_thread_issue_dbg13": (4, 12),
    "perf_counter_instrn_thread_issue_dbg14": (4, 14),
    "perf_counter_instrn_thread_issue_dbg15": (4, 16),
    "perf_counter_instrn_thread_issue_dbg16": (4, 18),
    "perf_counter_instrn_thread_issue_dbg17": (4, 20),
    "perf_counter_instrn_thread_issue_dbg18": (4, 22),
    # UIssue debug performance counters from 0 to 7 (DaisySel == 5)
    "perf_counter_instrn_thread_issue_dbg0": (5, 0),
    "perf_counter_instrn_thread_issue_dbg1": (5, 2),
    "perf_counter_instrn_thread_issue_dbg2": (5, 4),
    "perf_counter_instrn_thread_issue_dbg3": (5, 6),
    "perf_counter_instrn_thread_issue_dbg4": (5, 8),
    "perf_counter_instrn_thread_issue_dbg5": (5, 10),
    "perf_counter_instrn_thread_issue_dbg6": (5, 12),
    "perf_counter_instrn_thread_issue_dbg7": (5, 14),
    # ADCs and Data Converters (DaisySel == 6)
    "adcs0_unpacker0_channel0": (6, 0),
    "adcs0_unpacker0_channel1": (6, 1),
    "adcs0_unpacker1_channel0": (6, 2),
    "adcs0_unpacker1_channel1": (6, 3),
    "adcs2_packers_channel0": (6, 4),
    "adcs2_packers_channel1": (6, 5),
    "adcs_dest_pack_fifo_signals": (6, 6),
    "adcs_dest_fpu_instr_signals": (6, 7),
    "adcs_i_pack_req_signals": (6, 8),
    "adcs_srcb_fpu_pack_ctrl_signals": (6, 9),
    "adcs_sfpu_issue_ctrl_signals": (6, 10),
    "adcs_sfpu_dbg_signals": (6, 11),
    # RISCV Execution State (DaisySel == 7)
    "fpu_dbg0_perf_counters": (7, 0),
    "brisc_group_c": (7, 1),
    "tensix_in1_cnt1_perf_counters": (7, 2),
    "tensix_in1_cnt0_perf_counters": (7, 3),
    "tensix_in2_cnt1_perf_counters": (7, 4),
    "tensix_in2_cnt0_perf_counters": (7, 5),
    "tensix_in3_cnt1_perf_counters": (7, 6),
    "tensix_in3_cnt0_perf_counters": (7, 7),
    "tensix_in4_cnt1_perf_counters": (7, 8),
    "tensix_in4_cnt0_perf_counters": (7, 9),
    # RISC Groups (DaisySel == 7)
    "brisc_group_a": (7, 10),
    "brisc_group_b": (7, 11),
    "trisc0_group_a": (7, 12),
    "trisc0_group_b": (7, 13),
    "trisc1_group_a": (7, 14),
    "trisc1_group_b": (7, 15),
    "trisc2_group_a": (7, 16),
    "trisc2_group_b": (7, 17),
    "trisc0_group_c": (7, 18),
    "trisc0_group_d": (7, 19),
    "trisc1_group_c": (7, 20),
    "trisc1_group_d": (7, 21),
    "trisc2_group_c": (7, 22),
    "trisc2_group_d": (7, 23),
    "ncrisc_group_a": (7, 24),
    "ncrisc_group_b": (7, 25),
    "tensix_icache_ctrl": (7, 26),
    "risc_wrapper_noc_ctrl": (7, 27),
    "srca_resh_d7_and_h2_sfpu_dbg": (7, 28),
    # L1 Memory Access Ports (DaisySel == 8)
    "tensix_w_l1_at_instrn_group_a": (8, 0),
    "tensix_w_l1_at_instrn_group_b": (8, 1),
    "l1_access_ports_addr_a": (8, 2),
    "l1_access_ports_addr_b": (8, 3),
    "t_l1_access_ports_addr_a": (8, 4),
    "t_l1_access_ports_addr_b": (8, 5),
    "l1_addr_group_a": (8, 6),
    "l1_addr_group_b": (8, 7),
    "l1_addr_group_c": (8, 8),
    "l1_addr_group_d": (8, 9),
    "l1_addr_group_e": (8, 10),
    "l1_addr_group_f": (8, 11),
    "l1_addr_group_g": (8, 13),
    # Stream Interface (DaisySel == 10)
    "in_thcon_instrn": (10, 0),
    "o_add_l1_destination_addr_offset": (10, 2),
    "l1_section_sizes": (10, 3),
    # Output Interface (DaisySel == 11)
    "datum_index_and_phase_control": (11, 2),
    # Unpacker Debug (DaisySel == 12)
    "unp0_unpack0_fifo_status": (12, 0),
    "unp0_unpack0_demux_fifo_status": (12, 1),
    # Unpacker Debug Extended (DaisySel == 13)
    "unp1_unpack0_fifo_status": (13, 0),
    "unp1_unpack0_demux_fifo_status": (13, 1),
    # TDMA Packer (DaisySel == 14)
    "core_fifo_pipe_status": (14, 4),
    "packed_p5_signals": (14, 5),
    "tdma_packer_pos": (14, 6),
}
