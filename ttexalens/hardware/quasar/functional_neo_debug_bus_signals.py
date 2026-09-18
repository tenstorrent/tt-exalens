# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.debug_bus_signal_store import DebugBusSignalDescription

debug_bus_signal_map = {
    "trisc0_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x3FFFFFFF),
    "trisc0_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x200),
    "trisc0_id_ex_rts_dup": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x100),
    "trisc0_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x80),
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
    "trisc0_mop_decode_mop_stage_opcode/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3FFFFF),
    "trisc0_mop_decode_mop_stage_opcode/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0xFFC00000
    ),
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
        rd_sel=2, daisy_sel=7, sig_sel=18, mask=0xFFFFFFC0
    ),
    "trisc0_risc_wrapper_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3F
    ),
    "trisc0_risc_wrapper_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x3FF8000
    ),
    "trisc0_risc_wrapper_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x4000
    ),
    "trisc0_risc_wrapper_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x2000
    ),
    "trisc0_risc_wrapper_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x2
    ),
    "trisc0_risc_wrapper_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x1
    ),
    "trisc0_pc_buffer_next_cmd_fifo_data/1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x7FFFFF, across_groups=True
    ),
    "trisc0_pc_buffer_next_cmd_fifo_data/0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0xFF800000, across_groups=True
    ),
    "trisc0_risc_wrapper_trisc_intf_rden/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=18, mask=0x3F),
    "trisc0_risc_wrapper_trisc_intf_rden/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=18, mask=0xF8000000
    ),
    "trisc0_risc_wrapper_trisc_intf_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x7FF0000),
    "trisc0_risc_wrapper_trisc_intf_ready": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=18, mask=0xFFE0),
    "trisc0_risc_wrapper_trisc_intf_rd_data_vld/1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=18, mask=0x1F
    ),
    "trisc0_risc_wrapper_trisc_intf_rd_data_vld/0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0xFC000000
    ),
    "trisc0_risc_wrapper_trisc_target_intf": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x1FFC),
    # TRISC1
    "trisc1_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x3FFFFFFF),
    "trisc1_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x200),
    "trisc1_id_ex_rts_dup": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x100),
    "trisc1_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x80),
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
    "trisc1_mop_decode_mop_stage_opcode/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3FFFFF),
    "trisc1_mop_decode_mop_stage_opcode/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0xFFC00000
    ),
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
        rd_sel=2, daisy_sel=7, sig_sel=20, mask=0xFFFFFFC0
    ),
    "trisc1_risc_wrapper_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3F
    ),
    "trisc1_risc_wrapper_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x3FF8000
    ),
    "trisc1_risc_wrapper_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x4000
    ),
    "trisc1_risc_wrapper_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x2000
    ),
    "trisc1_risc_wrapper_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x2
    ),
    "trisc1_risc_wrapper_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x1
    ),
    "trisc1_pc_buffer_next_cmd_fifo_data/1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x7FFFFF, across_groups=True
    ),
    "trisc1_pc_buffer_next_cmd_fifo_data/0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=20, mask=0xFF800000, across_groups=True
    ),
    "trisc1_risc_wrapper_trisc_intf_rden/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=20, mask=0x3F),
    "trisc1_risc_wrapper_trisc_intf_rden/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=20, mask=0xF8000000
    ),
    "trisc1_risc_wrapper_trisc_intf_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=20, mask=0x7FF0000),
    "trisc1_risc_wrapper_trisc_intf_ready": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=20, mask=0xFFE0),
    "trisc1_risc_wrapper_trisc_intf_rd_data_vld/1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=20, mask=0x1F
    ),
    "trisc1_risc_wrapper_trisc_intf_rd_data_vld/0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=20, mask=0xFC000000
    ),
    "trisc1_risc_wrapper_trisc_target_intf": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=20, mask=0x1FFC),
    # TRISC2
    "trisc2_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x3FFFFFFF),
    "trisc2_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x200),
    "trisc2_id_ex_rts_dup": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x100),
    "trisc2_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x80),
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
    "trisc2_mop_decode_mop_stage_opcode/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3FFFFF),
    "trisc2_mop_decode_mop_stage_opcode/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0xFFC00000
    ),
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
        rd_sel=2, daisy_sel=7, sig_sel=22, mask=0xFFFFFFC0
    ),
    "trisc2_risc_wrapper_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3F
    ),
    "trisc2_risc_wrapper_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x3FF8000
    ),
    "trisc2_risc_wrapper_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x4000
    ),
    "trisc2_risc_wrapper_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x2000
    ),
    "trisc2_risc_wrapper_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x2
    ),
    "trisc2_risc_wrapper_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x1
    ),
    "trisc2_pc_buffer_next_cmd_fifo_data/1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x7FFFFF, across_groups=True
    ),
    "trisc2_pc_buffer_next_cmd_fifo_data/0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=22, mask=0xFF800000, across_groups=True
    ),
    "trisc2_risc_wrapper_trisc_intf_rden/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=22, mask=0x3F),
    "trisc2_risc_wrapper_trisc_intf_rden/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=22, mask=0xF8000000
    ),
    "trisc2_risc_wrapper_trisc_intf_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=22, mask=0x7FF0000),
    "trisc2_risc_wrapper_trisc_intf_ready": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=22, mask=0xFFE0),
    "trisc2_risc_wrapper_trisc_intf_rd_data_vld/1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=22, mask=0x1F
    ),
    "trisc2_risc_wrapper_trisc_intf_rd_data_vld/0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=22, mask=0xFC000000
    ),
    "trisc2_risc_wrapper_trisc_target_intf": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=22, mask=0x1FFC),
    # TRISC3
    "trisc3_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x3FFFFFFF),
    "trisc3_ex_id_rtr": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x200),
    "trisc3_id_ex_rts_dup": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x100),
    "trisc3_if_rts": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x80),
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
    "trisc3_mop_decode_mop_stage_opcode/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x3FFFFF),
    "trisc3_mop_decode_mop_stage_opcode/0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=25, mask=0xFFC00000
    ),
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
        rd_sel=2, daisy_sel=7, sig_sel=24, mask=0xFFFFFFC0
    ),
    "trisc3_risc_wrapper_trisc_o_mailbox_rddata/1": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x3F
    ),
    "trisc3_risc_wrapper_trisc_intf_wrack_trisc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x3FF8000
    ),
    "trisc3_risc_wrapper_trisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x4000
    ),
    "trisc3_risc_wrapper_trisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x2000
    ),
    "trisc3_risc_wrapper_trisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x2
    ),
    "trisc3_risc_wrapper_trisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x1
    ),
    "trisc3_pc_buffer_next_cmd_fifo_data/1": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x7FFFFF, across_groups=True
    ),
    "trisc3_pc_buffer_next_cmd_fifo_data/0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0xFF800000, across_groups=True
    ),
    "trisc3_risc_wrapper_trisc_intf_rden/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x3F),
    "trisc3_risc_wrapper_trisc_intf_rden/0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=24, mask=0xF8000000
    ),
    "trisc3_risc_wrapper_trisc_intf_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x7FF0000),
    "trisc3_risc_wrapper_trisc_intf_ready": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=24, mask=0xFFE0),
    "trisc3_risc_wrapper_trisc_intf_rd_data_vld/1": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x1F
    ),
    "trisc3_risc_wrapper_trisc_intf_rd_data_vld/0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0xFC000000
    ),
    "trisc3_risc_wrapper_trisc_target_intf": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x1FFC),
    "trisc0_ldm_rddata": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=6),
    "trisc1_ldm_rddata": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=6),
    "trisc2_ldm_rddata": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=6),
    "trisc3_ldm_rddata": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=6),
    "trisc0_icache_debug_bus": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0x1FFFFFF0),
    "trisc1_icache_debug_bus/1": DebugBusSignalDescription(rd_sel=3, daisy_sel=7, sig_sel=26, mask=0xF),
    "trisc1_icache_debug_bus/0": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0xFFFFF800),
    "trisc2_icache_debug_bus/1": DebugBusSignalDescription(rd_sel=2, daisy_sel=7, sig_sel=26, mask=0x7FF),
    "trisc2_icache_debug_bus/0": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0xFFFC0000),
    "trisc3_icache_debug_bus/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=26, mask=0x3FFFF),
    "trisc3_icache_debug_bus/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=26, mask=0xFE000000),
    "fpu_sticky_bits": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=28, mask=0x1E000),
    "fpu_srca_wren": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=28, mask=0x1000),
    "fpu_mtile_dbg_bus": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=28, mask=0xFF),
    "sfpu_cc_satisfied_pair0": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=30, mask=0xF),
    "sfpu_cc_satisfied_pair1": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=30, mask=0xF0),
    "sfpu_cc_satisfied_pair2": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=30, mask=0xF00),
    "sfpu_cc_satisfied_pair3": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=30, mask=0xF000),
    "sfpu_cc_satisfied_pair4": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=30, mask=0xF0000),
    "sfpu_cc_satisfied_pair5": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=30, mask=0xF00000),
    "sfpu_cc_satisfied_pair6": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=30, mask=0xF000000),
    "sfpu_cc_satisfied_pair7": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=30, mask=0xF0000000),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_7_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=17, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_6_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=17, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_5_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=17, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_4_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=17, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_3_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=16, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_2_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=16, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_1_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=16, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_0_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=16, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_15_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=15, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts0_7_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=15, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_14_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=15, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts0_6_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=15, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_13_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=15, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts0_5_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=15, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_12_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=15, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts0_4_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=15, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_11_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts0_3_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_10_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts0_2_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_9_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts0_1_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts0_8_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts0_0_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=14, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_7_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_6_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_5_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_4_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=13, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_3_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_2_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_1_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_0_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_15_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts1_7_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_14_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts1_6_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_13_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts1_5_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_12_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts1_4_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=11, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_11_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts1_3_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_10_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts1_2_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_9_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts1_1_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts1_8_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts1_0_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=10, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_7_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_6_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_5_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_4_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=9, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_3_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_2_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_1_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_0_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_15_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts2_7_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_14_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts2_6_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_13_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts2_5_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_12_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts2_4_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=7, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_11_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts2_3_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_10_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts2_2_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_9_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts2_1_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts2_8_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts2_0_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=6, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_7_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_6_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_5_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_4_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=5, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_3_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_2_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_1_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_0_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_15_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts3_7_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_14_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts3_6_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_13_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts3_5_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_12_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts3_4_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=3, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_11_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts3_3_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_10_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts3_2_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_9_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts3_1_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_rsn_cnts3_8_when_perf_cnt_mux0_nonzero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_inst_cnts3_0_when_perf_cnt_mux0_zero": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=2, mask=0xFFFFFFFF
    ),
    "perf_cnt_instrn_thread_stall_cnts0": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF),
    "perf_cnt_instrn_thread_stall_cnts1": DebugBusSignalDescription(rd_sel=2, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF),
    "perf_cnt_instrn_thread_stall_cnts2": DebugBusSignalDescription(rd_sel=1, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF),
    "perf_cnt_instrn_thread_stall_cnts3": DebugBusSignalDescription(rd_sel=0, daisy_sel=1, sig_sel=1, mask=0xFFFFFFFF),
    "ibuffer_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=0, mask=0xF0),
    "instrn_reg_fifo_empty": DebugBusSignalDescription(rd_sel=3, daisy_sel=1, sig_sel=0, mask=0xF),
    "thcon_p0_tid": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x30000),
    "thcon_p0_wren": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x8000),
    "thcon_p0_rden": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x4000),
    "thcon_p0_gpr_addr": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x3C00),
    "thcon_p0_gpr_byten_15_6": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=16, mask=0x3FF),
    "thcon_p0_gpr_byten_5_0": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xFC000000),
    "p0_gpr_accept": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x2000000),
    "cfg_gpr_p0_req": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x1000000),
    "cfg_gpr_p0_tid": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xC00000),
    "cfg_gpr_p0_addr": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3C0000),
    "gpr_cfg_p0_accept": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x20000),
    "l1_ret_vld": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x10000),
    "l1_ret_tid": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0xC000),
    "l1_ret_gpr": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3C00),
    "l1_ret_byten_15_6": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=16, mask=0x3FF),
    "l1_ret_byten_5_0": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xFC000000),
    "l1_return_accept": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x2000000),
    "thcon_p1_req_vld": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x1000000),
    "thcon_p1_tid": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xC00000),
    "thcon_p1_gpr": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3C0000),
    "thcon_p1_req_accept": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x20000),
    "cfg_gpr_p1_req": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x10000),
    "cfg_gpr_p1_tid": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0xC000),
    "cfg_gpr_p1_addr": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3C00),
    "cfg_gpr_p1_byten_15_6": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=16, mask=0x3FF),
    "cfg_gpr_p1_byten_5_0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0xFC000000),
    "gpr_cfg_p1_accept": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x2000000),
    "i_risc_out_reg_rden": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1000000),
    "i_risc_out_reg_wren": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x800000),
    "riscv_tid": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x600000),
    "i_risc_out_reg_index_5_2": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1E0000),
    "i_risc_out_reg_byten": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1FFFE),
    "o_risc_in_reg_req_ready": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=16, mask=0x1),
    "thcon_p0_gpr_wrdata/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF),
    "thcon_p0_gpr_wrdata/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF),
    "thcon_p0_gpr_wrdata/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF),
    "thcon_p0_gpr_wrdata/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=14, mask=0xFFFFFFFF),
    "p0_gpr_ret/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
    "p0_gpr_ret/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
    "p0_gpr_ret/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
    "p0_gpr_ret/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=12, mask=0xFFFFFFFF),
    "gpr_cfg_p0_data/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF),
    "gpr_cfg_p0_data/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF),
    "gpr_cfg_p0_data/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF),
    "gpr_cfg_p0_data/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=10, mask=0xFFFFFFFF),
    "l1_ret_wrdata/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
    "l1_ret_wrdata/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
    "l1_ret_wrdata/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
    "l1_ret_wrdata/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=8, mask=0xFFFFFFFF),
    "thcon_p1_ret/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
    "thcon_p1_ret/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
    "thcon_p1_ret/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
    "thcon_p1_ret/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=6, mask=0xFFFFFFFF),
    "cfg_gpr_p1_data/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
    "cfg_gpr_p1_data/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
    "cfg_gpr_p1_data/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
    "cfg_gpr_p1_data/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=4, mask=0xFFFFFFFF),
    "i_risc_out_reg_wrdata/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF),
    "i_risc_out_reg_wrdata/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF),
    "i_risc_out_reg_wrdata/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF),
    "i_risc_out_reg_wrdata/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=2, mask=0xFFFFFFFF),
    "o_risc_in_reg_rddata/3": DebugBusSignalDescription(rd_sel=3, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF),
    "o_risc_in_reg_rddata/2": DebugBusSignalDescription(rd_sel=2, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF),
    "o_risc_in_reg_rddata/1": DebugBusSignalDescription(rd_sel=1, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF),
    "o_risc_in_reg_rddata/0": DebugBusSignalDescription(rd_sel=0, daisy_sel=2, sig_sel=0, mask=0xFFFFFFFF),
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
}

group_map: dict[str, tuple[int, int]] = {
    "trisc0_group_a": (7, 10),
    "trisc0_group_b": (7, 11),
    "trisc0_group_c": (7, 18),
    "trisc0_group_d": (7, 19),
    "trisc1_group_a": (7, 12),
    "trisc1_group_b": (7, 13),
    "trisc1_group_c": (7, 20),
    "trisc1_group_d": (7, 21),
    "trisc2_group_a": (7, 14),
    "trisc2_group_b": (7, 15),
    "trisc2_group_c": (7, 22),
    "trisc2_group_d": (7, 23),
    "trisc3_group_a": (7, 16),
    "trisc3_group_b": (7, 17),
    "trisc3_group_c": (7, 24),
    "trisc3_group_d": (7, 25),
    "trisc_ldm_rddata": (7, 6),
    "trisc_icache_debug": (7, 26),
    "fpu_debug": (7, 28),
    "sfpu_cc_satisfied": (7, 30),
    "instrn_thread_ibuffer_state": (1, 0),
    "instrn_thread_stall_cnts": (1, 1),
    "instrn_thread3_cnts1_lo": (1, 2),
    "instrn_thread3_cnts1_hi": (1, 3),
    "instrn_thread3_cnts0_lo": (1, 4),
    "instrn_thread3_cnts0_hi": (1, 5),
    "instrn_thread2_cnts1_lo": (1, 6),
    "instrn_thread2_cnts1_hi": (1, 7),
    "instrn_thread2_cnts0_lo": (1, 8),
    "instrn_thread2_cnts0_hi": (1, 9),
    "instrn_thread1_cnts1_lo": (1, 10),
    "instrn_thread1_cnts1_hi": (1, 11),
    "instrn_thread1_cnts0_lo": (1, 12),
    "instrn_thread1_cnts0_hi": (1, 13),
    "instrn_thread0_cnts1_lo": (1, 14),
    "instrn_thread0_cnts1_hi": (1, 15),
    "instrn_thread0_cnts0_lo": (1, 16),
    "instrn_thread0_cnts0_hi": (1, 17),
    "gpr_o_risc_in_reg_rddata": (2, 0),
    "gpr_i_risc_out_reg_wrdata": (2, 2),
    "gpr_cfg_gpr_p1_data": (2, 4),
    "gpr_thcon_p1_ret": (2, 6),
    "gpr_l1_ret_wrdata": (2, 8),
    "gpr_gpr_cfg_p0_data": (2, 10),
    "gpr_p0_gpr_ret": (2, 12),
    "gpr_thcon_p0_gpr_wrdata": (2, 14),
    "gpr_thcon": (2, 16),
    "instrn_issue_perf_cnt8_lo": (4, 2),
    "instrn_issue_perf_cnt9_lo": (4, 4),
    "instrn_issue_perf_cnt10_lo": (4, 6),
    "instrn_issue_perf_cnt11_lo": (4, 8),
    "instrn_issue_perf_cnt12_lo": (4, 10),
    "instrn_issue_perf_cnt13_lo": (4, 12),
    "instrn_issue_perf_cnt14_lo": (4, 14),
    "instrn_issue_perf_cnt15_lo": (4, 16),
    "instrn_issue_perf_cnt16_lo": (4, 18),
    "instrn_issue_perf_cnt17_lo": (4, 20),
    "instrn_issue_perf_cnt18_lo": (4, 22),
    "instrn_issue_perf_cnt0_lo": (5, 0),
    "instrn_issue_perf_cnt1_lo": (5, 2),
    "instrn_issue_perf_cnt2_lo": (5, 4),
    "instrn_issue_perf_cnt3_lo": (5, 6),
    "instrn_issue_perf_cnt4_lo": (5, 8),
    "instrn_issue_perf_cnt5_lo": (5, 10),
    "instrn_issue_perf_cnt6_lo": (5, 12),
    "instrn_issue_perf_cnt7_lo": (5, 14),
}
