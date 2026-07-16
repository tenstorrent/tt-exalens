# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.debug_bus_signal_store import DebugBusSignalDescription


debug_bus_signal_map = {
    # TRISC0
    "trisc0_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x3FFFFFFF),
    "trisc0_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x200),
    "trisc0_id_ex_rts_dup": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x100),
    "trisc0_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x80),
    "trisc0_if_invalid_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x40),
    "trisc0_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x20),
    "trisc0_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x1F),
    "trisc0_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=11, mask=0xFFFFFFFF),
    "trisc0_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x80000000),
    "trisc0_ex_id_rtr_dup": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x40000000),
    "trisc0_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x3FFFFFFF),
    "trisc0_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x10000000),
    "trisc0_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F00000),
    "trisc0_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x40000),
    "trisc0_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x7C00),
    "trisc0_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x100),
    "trisc0_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F),
    "trisc0_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x80000000),
    "trisc0_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF),
    "trisc0_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x80000000),
    "trisc0_o_instrn_req": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x40000000),
    "trisc0_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF),
    "trisc0_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x80000000),
    "trisc0_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x40000000),
    "trisc0_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF),
    "trisc0_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x80000000),
    "trisc0_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF),
    "trisc0_trisc_mop_buf_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x40000000),
    "trisc0_trisc_mop_buf_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x20000000),
    "trisc0_mop_decode_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x1C000000
    ),
    "trisc0_mop_decode_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3800000
    ),
    "trisc0_mop_decode_mop_stage_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x400000),
    "trisc0_mop_decode_mop_stage_opcode": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3FFFFF),
    "trisc0_mop_decode_math_loop_active": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x200000),
    "trisc0_mop_decode_unpack_loop_active": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x100000),
    "trisc0_mop_decode_o_instrn_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x80000),
    "trisc0_mop_decode_o_instrn_opcode/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFFF80000
    ),
    "trisc0_mop_decode_o_instrn_opcode/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x7FFFF),
    "trisc0_pc_buffer_sempost_pending": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFF00),
    "trisc0_pc_buffer_semget_pending": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFF),
    "trisc0_pc_buffer_trisc_read_request_pending": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x80000000
    ),
    "trisc0_pc_buffer_trisc_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x40000000
    ),
    "trisc0_pc_buffer_trisc_sync_type": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x20000000),
    "trisc0_pc_buffer_riscv_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x10000000
    ),
    "trisc0_pc_buffer_pc_buffer_idle": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x8000000),
    "trisc0_pc_buffer_i_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x4000000),
    "trisc0_pc_buffer_i_mops_outstanding": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x2000000),
    "trisc0_pc_buffer_cmd_fifo_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1000000),
    "trisc0_pc_buffer_cmd_fifo_empty": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x800000),
    "trisc0_risc_wrapper_trisc_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x400000
    ),
    "trisc0_risc_wrapper_trisc_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C0000
    ),
    "trisc0_risc_wrapper_trisc_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C000
    ),
    "trisc0_risc_wrapper_trisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C00
    ),
    "trisc0_risc_wrapper_trisc_o_mailbox_rdvalid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C0
    ),
    "trisc0_risc_wrapper_trisc_o_mailbox_rddata/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=18, mask=0xFFFF0000
    ),
    "trisc0_risc_wrapper_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3F
    ),
    "trisc0_risc_wrapper_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x3FFE0000
    ),
    "trisc0_risc_wrapper_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x10000
    ),
    "trisc0_risc_wrapper_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x8000
    ),
    "trisc0_risc_wrapper_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x2
    ),
    "trisc0_risc_wrapper_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x1
    ),
    # TRISC1
    "trisc1_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x3FFFFFFF),
    "trisc1_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x200),
    "trisc1_id_ex_rts_dup": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x100),
    "trisc1_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x80),
    "trisc1_if_invalid_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x40),
    "trisc1_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x20),
    "trisc1_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x1F),
    "trisc1_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=13, mask=0xFFFFFFFF),
    "trisc1_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x80000000),
    "trisc1_ex_id_rtr_dup": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x40000000),
    "trisc1_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x3FFFFFFF),
    "trisc1_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x10000000),
    "trisc1_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F00000),
    "trisc1_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x40000),
    "trisc1_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x7C00),
    "trisc1_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x100),
    "trisc1_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F),
    "trisc1_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x80000000),
    "trisc1_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF),
    "trisc1_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x80000000),
    "trisc1_o_instrn_req": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x40000000),
    "trisc1_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF),
    "trisc1_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x80000000),
    "trisc1_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x40000000),
    "trisc1_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF),
    "trisc1_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x80000000),
    "trisc1_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF),
    "trisc1_trisc_mop_buf_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x40000000),
    "trisc1_trisc_mop_buf_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x20000000),
    "trisc1_mop_decode_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x1C000000
    ),
    "trisc1_mop_decode_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3800000
    ),
    "trisc1_mop_decode_mop_stage_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x400000),
    "trisc1_mop_decode_mop_stage_opcode": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3FFFFF),
    "trisc1_mop_decode_math_loop_active": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x200000),
    "trisc1_mop_decode_unpack_loop_active": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x100000),
    "trisc1_mop_decode_o_instrn_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x80000),
    "trisc1_mop_decode_o_instrn_opcode/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFFF80000
    ),
    "trisc1_mop_decode_o_instrn_opcode/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x7FFFF),
    "trisc1_pc_buffer_sempost_pending": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFF00),
    "trisc1_pc_buffer_semget_pending": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFF),
    "trisc1_pc_buffer_trisc_read_request_pending": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x80000000
    ),
    "trisc1_pc_buffer_trisc_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x40000000
    ),
    "trisc1_pc_buffer_trisc_sync_type": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x20000000),
    "trisc1_pc_buffer_riscv_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x10000000
    ),
    "trisc1_pc_buffer_pc_buffer_idle": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x8000000),
    "trisc1_pc_buffer_i_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x4000000),
    "trisc1_pc_buffer_i_mops_outstanding": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x2000000),
    "trisc1_pc_buffer_cmd_fifo_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x1000000),
    "trisc1_pc_buffer_cmd_fifo_empty": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x800000),
    "trisc1_risc_wrapper_trisc_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x400000
    ),
    "trisc1_risc_wrapper_trisc_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C0000
    ),
    "trisc1_risc_wrapper_trisc_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C000
    ),
    "trisc1_risc_wrapper_trisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C00
    ),
    "trisc1_risc_wrapper_trisc_o_mailbox_rdvalid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3C0
    ),
    "trisc1_risc_wrapper_trisc_o_mailbox_rddata/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=20, mask=0xFFFF0000
    ),
    "trisc1_risc_wrapper_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3F
    ),
    "trisc1_risc_wrapper_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x3FFE0000
    ),
    "trisc1_risc_wrapper_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x10000
    ),
    "trisc1_risc_wrapper_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x8000
    ),
    "trisc1_risc_wrapper_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x2
    ),
    "trisc1_risc_wrapper_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x1
    ),
    # TRISC2
    "trisc2_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x3FFFFFFF),
    "trisc2_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x200),
    "trisc2_id_ex_rts_dup": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x100),
    "trisc2_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x80),
    "trisc2_if_invalid_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x40),
    "trisc2_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x20),
    "trisc2_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x1F),
    "trisc2_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=15, mask=0xFFFFFFFF),
    "trisc2_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x80000000),
    "trisc2_ex_id_rtr_dup": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x40000000),
    "trisc2_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x3FFFFFFF),
    "trisc2_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x10000000),
    "trisc2_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x1F00000),
    "trisc2_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x40000),
    "trisc2_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x7C00),
    "trisc2_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x100),
    "trisc2_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x1F),
    "trisc2_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=14, mask=0x80000000),
    "trisc2_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=14, mask=0x7FFFFFFF),
    "trisc2_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x80000000),
    "trisc2_o_instrn_req": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x40000000),
    "trisc2_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x3FFFFFFF),
    "trisc2_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x80000000),
    "trisc2_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x40000000),
    "trisc2_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x3FFFFFFF),
    "trisc2_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=14, mask=0x80000000),
    "trisc2_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=14, mask=0x7FFFFFFF),
    "trisc2_trisc_mop_buf_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x40000000),
    "trisc2_trisc_mop_buf_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x20000000),
    "trisc2_mop_decode_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x1C000000
    ),
    "trisc2_mop_decode_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3800000
    ),
    "trisc2_mop_decode_mop_stage_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x400000),
    "trisc2_mop_decode_mop_stage_opcode": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3FFFFF),
    "trisc2_mop_decode_math_loop_active": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x200000),
    "trisc2_mop_decode_unpack_loop_active": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x100000),
    "trisc2_mop_decode_o_instrn_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x80000),
    "trisc2_mop_decode_o_instrn_opcode/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFFF80000
    ),
    "trisc2_mop_decode_o_instrn_opcode/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x7FFFF),
    "trisc2_pc_buffer_sempost_pending": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFF00),
    "trisc2_pc_buffer_semget_pending": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFF),
    "trisc2_pc_buffer_trisc_read_request_pending": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x80000000
    ),
    "trisc2_pc_buffer_trisc_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x40000000
    ),
    "trisc2_pc_buffer_trisc_sync_type": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x20000000),
    "trisc2_pc_buffer_riscv_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x10000000
    ),
    "trisc2_pc_buffer_pc_buffer_idle": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x8000000),
    "trisc2_pc_buffer_i_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x4000000),
    "trisc2_pc_buffer_i_mops_outstanding": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x2000000),
    "trisc2_pc_buffer_cmd_fifo_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x1000000),
    "trisc2_pc_buffer_cmd_fifo_empty": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x800000),
    "trisc2_risc_wrapper_trisc_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x400000
    ),
    "trisc2_risc_wrapper_trisc_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C0000
    ),
    "trisc2_risc_wrapper_trisc_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C000
    ),
    "trisc2_risc_wrapper_trisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C00
    ),
    "trisc2_risc_wrapper_trisc_o_mailbox_rdvalid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3C0
    ),
    "trisc2_risc_wrapper_trisc_o_mailbox_rddata/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=22, mask=0xFFFF0000
    ),
    "trisc2_risc_wrapper_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3F
    ),
    "trisc2_risc_wrapper_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x3FFE0000
    ),
    "trisc2_risc_wrapper_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x10000
    ),
    "trisc2_risc_wrapper_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x8000
    ),
    "trisc2_risc_wrapper_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x2
    ),
    "trisc2_risc_wrapper_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x1
    ),
    # TRISC3
    "trisc3_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x3FFFFFFF),
    "trisc3_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x200),
    "trisc3_id_ex_rts_dup": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x100),
    "trisc3_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x80),
    "trisc3_if_invalid_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x40),
    "trisc3_if_ex_predicted": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x20),
    "trisc3_if_ex_deco/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x1F),
    "trisc3_if_ex_deco/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=17, mask=0xFFFFFFFF),
    "trisc3_id_ex_rts": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x80000000),
    "trisc3_ex_id_rtr_dup": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x40000000),
    "trisc3_id_ex_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x3FFFFFFF),
    "trisc3_id_rf_wr_flag": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x10000000),
    "trisc3_id_rf_wraddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x1F00000),
    "trisc3_id_rf_p1_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x40000),
    "trisc3_id_rf_p1_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x7C00),
    "trisc3_id_rf_p0_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x100),
    "trisc3_id_rf_p0_rdaddr": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x1F),
    "trisc3_i_instrn_vld": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=16, mask=0x80000000),
    "trisc3_i_instrn": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=16, mask=0x7FFFFFFF),
    "trisc3_i_instrn_req_rtr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x80000000),
    "trisc3_o_instrn_req": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x40000000),
    "trisc3_o_instrn_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x3FFFFFFF),
    "trisc3_dbg_obs_mem_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x80000000),
    "trisc3_dbg_obs_mem_rden": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x40000000),
    "trisc3_dbg_obs_mem_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x3FFFFFFF),
    "trisc3_dbg_obs_cmt_vld": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=16, mask=0x80000000),
    "trisc3_dbg_obs_cmt_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=16, mask=0x7FFFFFFF),
    "trisc3_trisc_mop_buf_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x40000000),
    "trisc3_trisc_mop_buf_full": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x20000000),
    "trisc3_mop_decode_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x1C000000
    ),
    "trisc3_mop_decode_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x3800000
    ),
    "trisc3_mop_decode_mop_stage_valid": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x400000),
    "trisc3_mop_decode_mop_stage_opcode": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x3FFFFF),
    "trisc3_mop_decode_math_loop_active": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=25, mask=0x200000),
    "trisc3_mop_decode_unpack_loop_active": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=25, mask=0x100000),
    "trisc3_mop_decode_o_instrn_valid": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=25, mask=0x80000),
    "trisc3_mop_decode_o_instrn_opcode/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=25, mask=0xFFF80000
    ),
    "trisc3_mop_decode_o_instrn_opcode/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=25, mask=0x7FFFF),
    "trisc3_pc_buffer_sempost_pending": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=25, mask=0xFF00),
    "trisc3_pc_buffer_semget_pending": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=25, mask=0xFF),
    "trisc3_pc_buffer_trisc_read_request_pending": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x80000000
    ),
    "trisc3_pc_buffer_trisc_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x40000000
    ),
    "trisc3_pc_buffer_trisc_sync_type": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x20000000),
    "trisc3_pc_buffer_riscv_sync_activated": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x10000000
    ),
    "trisc3_pc_buffer_pc_buffer_idle": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x8000000),
    "trisc3_pc_buffer_i_busy": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x4000000),
    "trisc3_pc_buffer_i_mops_outstanding": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x2000000),
    "trisc3_pc_buffer_cmd_fifo_full": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x1000000),
    "trisc3_pc_buffer_cmd_fifo_empty": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x800000),
    "trisc3_risc_wrapper_trisc_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x400000
    ),
    "trisc3_risc_wrapper_trisc_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x3C0000
    ),
    "trisc3_risc_wrapper_trisc_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x3C000
    ),
    "trisc3_risc_wrapper_trisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x3C00
    ),
    "trisc3_risc_wrapper_trisc_o_mailbox_rdvalid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x3C0
    ),
    "trisc3_risc_wrapper_trisc_o_mailbox_rddata/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=24, mask=0xFFFF0000
    ),
    "trisc3_risc_wrapper_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x3F
    ),
    "trisc3_risc_wrapper_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x3FFE0000
    ),
    "trisc3_risc_wrapper_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x10000
    ),
    "trisc3_risc_wrapper_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x8000
    ),
    "trisc3_risc_wrapper_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x2
    ),
    "trisc3_risc_wrapper_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x1
    ),
}
