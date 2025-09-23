# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.debug_bus_signal_store import DebugBusSignalDescription


# The commented-out signals are either duplicates (have the same name) or signals that span across more than one 32-bit word (where different parts of the signal use different rd_sel values). In the current implementation, it is not possible to read both parts in a synchronized way (the result would not be consistent), so reading them is not recommended.
debug_bus_signal_map = {
    # For the other signals applying the pc_mask.
    "brisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 5, mask=0x7FFFFFFF),
    "trisc0_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 6, mask=0x7FFFFFFF),
    "trisc1_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 7, mask=0x7FFFFFFF),
    "trisc2_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 8, mask=0x7FFFFFFF),
    "ncrisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 12, mask=0x7FFFFFFF),

    # "brisc_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x200
    # ),
    # "brisc_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x100
    # ),
    "brisc_if_rts": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x80
    ),
    "brisc_if_ex_predicted": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x20
    ),
    # "brisc_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x1F
    # ),
    # "brisc_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=11, mask=0xFFFFFFFF
    # ),
    # "brisc_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x80000000
    # ),
    # "brisc_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x40000000
    # ),
    "brisc_id_ex_pc": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x3FFFFFFF
    ),
    "brisc_id_rf_wr_flag": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x10000000
    ),
    "brisc_id_rf_wraddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F00000
    ),
    "brisc_id_rf_p1_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x40000
    ),
    "brisc_id_rf_p1_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x7C00                                  
    ),
    "brisc_id_rf_p0_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x100
    ),
    "brisc_id_rf_p0_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F
    ),
    "brisc_i_instrn_vld": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x80000000
    ),
    "brisc_i_instrn": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF
    ),
    "brisc_i_instrn_req_rtr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x80000000
    ),
     "brisc_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x40000000                              
    ), 
    "brisc_o_instrn_addr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF
    ),
    "brisc_dbg_obs_mem_wren": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x80000000
    ),
    "brisc_dbg_obs_mem_rden": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x40000000
    ),
    "brisc_dbg_obs_mem_addr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF
    ),
    "brisc_dbg_obs_cmt_vld": DebugBusSignalDescription(           
        rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x80000000
    ),
    "brisc_dbg_obs_cmt_pc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF
    ),
    "brisc_o_par_err_risc_localmem": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x80000000
    ),
    "brisc_i_mailbox_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x78000000
    ),
    "brisc_i_mailbox_rd_type": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x7800000
    ),
    "brisc_o_mailbox_rd_req_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x780000
    ),
    "brisc_o_mailbox_rdvalid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x78000
    ),
    "brisc_o_mailbox_rddata": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x7F00
    ),
    # "brisc_intf_wrack_brisc": DebugBusSignalDescription(
    #     rd_sel=0, daisy_sel=7, sig_sel=1, mask=0xFFE00000
    # ),
    # "brisc_intf_wrack_brisc": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=1, mask=0x3F
    # ),
    "brisc_dmem_tensix_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x100000
    ),
    "brisc_dmem_tensix_wren": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x80000
    ),
    "brisc_icache_req_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x2
    ),
    "brisc_icache_req_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x1
    ),
    # "trisc0_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x200
    # ),
    # "trisc0_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x100
    # ),
    "trisc0_if_rts": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x80
    ),
    "trisc0_if_ex_predicted": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x20
    ),
    # "trisc0_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x1F
    # ),
    # "trisc0_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=13, mask=0xFFFFFFFF
    # ),
    # "trisc0_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x80000000
    # ),
    # "trisc0_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x40000000
    # ),
    "trisc0_id_ex_pc": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x3FFFFFFF
    ),
    "trisc0_id_rf_wr_flag": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x10000000
    ),
    "trisc0_id_rf_wraddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F00000
    ),
    "trisc0_id_rf_p1_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x40000
    ),
    "trisc0_id_rf_p1_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x7C00
    ),
    "trisc0_id_rf_p0_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x100
    ),
    "trisc0_id_rf_p0_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F
    ),
    "trisc0_i_instrn_vld": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x80000000
    ),
    "trisc0_i_instrn": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF
    ),
    "trisc0_i_instrn_req_rtr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x80000000
    ),
    "trisc0_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x40000000
    ),
    "trisc0_o_instrn_addr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF
    ),
    "trisc0_dbg_obs_mem_wren": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x80000000
    ),
    "trisc0_dbg_obs_mem_rden": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x40000000
    ),
    "trisc0_dbg_obs_mem_addr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF
    ),
    "trisc0_dbg_obs_cmt_vld": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x80000000
    ),
    "trisc0_dbg_obs_cmt_pc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF
    ),
    "trisc0_trisc_mop_buf_empty": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x40000000
    ),
    "trisc0_trisc_mop_buf_full": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x20000000
    ),
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
    "trisc0_mop_decode_debug_bus_o_instrn_opcode": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFFF80000
    ),
    "trisc0_mop_decode_debug_bus_o_instrn_opcode": DebugBusSignalDescription(
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
    "trisc0_pc_buffer_debug_bus_i_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x4000000
    ),
    "trisc0_pc_buffer_debug_bus_i_mops_outstanding": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x2000000
    ),
    "trisc0_pc_buffer_debug_bus_cmd_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1000000
    ),
    "trisc0_pc_buffer_debug_bus_cmd_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x800000
    ),
    "trisc0_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x7FFFFF
    ),
    "trisc0_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0xFF800000
    ),
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
    # "trisc0_risc_wrapper_debug_bus_trisc_o_mailbox_rddata": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=18, mask=0xFFFF0000
    # ),
    # "trisc0_risc_wrapper_debug_bus_trisc_o_mailbox_rddata": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3F
    # ),
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
    # "trisc1_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x200
    # ),
    # "trisc1_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x100
    # ),
    "trisc1_if_rts": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x80
    ),
    "trisc1_if_ex_predicted": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x20
    ),
    # "trisc1_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=15, mask=0x1F
    # ),
    # "trisc1_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=15, mask=0xFFFFFFFF
    # ),
    # "trisc1_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x80000000
    # ),
    # "trisc1_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x40000000
    # ),
    "trisc1_id_ex_pc": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=15, mask=0x3FFFFFFF
    ),
    "trisc1_id_rf_wr_flag": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x10000000
    ),
    "trisc1_id_rf_wraddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x1F00000
    ),
    "trisc1_id_rf_p1_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x40000
    ),
    "trisc1_id_rf_p1_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x7C00
    ),
    "trisc1_id_rf_p0_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x100
    ),
    "trisc1_id_rf_p0_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=15, mask=0x1F
    ),
    "trisc1_i_instrn_vld": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=14, mask=0x80000000
    ),
    "trisc1_i_instrn": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=14, mask=0x7FFFFFFF
    ),
    "trisc1_i_instrn_req_rtr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x80000000
    ),
    "trisc1_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x40000000
    ),
    "trisc1_o_instrn_addr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=14, mask=0x3FFFFFFF
    ),
    "trisc1_dbg_obs_mem_wren": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x80000000
    ),
    "trisc1_dbg_obs_mem_rden": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x40000000
    ),
    "trisc1_dbg_obs_mem_addr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=14, mask=0x3FFFFFFF
    ),
    "trisc1_dbg_obs_cmt_vld": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=14, mask=0x80000000
    ),
    "trisc1_dbg_obs_cmt_pc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=14, mask=0x7FFFFFFF
    ),
    "trisc1_trisc_mop_buf_empty": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x40000000
    ),
    "trisc1_trisc_mop_buf_full": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x20000000
    ),
    "trisc1_mop_decode_debug_bus_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x1C000000
    ),
    "trisc1_mop_decode_debug_bus_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3800000
    ),
    "trisc1_mop_decode_debug_bus_mop_stage_valid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x400000
    ),
    # "trisc1_mop_decode_debug_bus_mop_stage_opcode": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=21, mask=0xFFC00000
    # ),
    # "trisc1_mop_decode_debug_bus_mop_stage_opcode": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=21, mask=0x3FFFFF
    # ),
    "trisc1_mop_decode_debug_bus_math_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x200000
    ),
    "trisc1_mop_decode_debug_bus_unpack_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x100000
    ),
    "trisc1_mop_decode_debug_bus_o_instrn_valid": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x80000
    ),
    # "trisc1_mop_decode_debug_bus_o_instrn_opcode": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=21, mask=0xFFF80000
    # ),
    # "trisc1_mop_decode_debug_bus_o_instrn_opcode": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=21, mask=0x7FFFF
    # ),
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
    "trisc1_pc_buffer_debug_bus_i_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x4000000
    ),
    "trisc1_pc_buffer_debug_bus_i_mops_outstanding": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x2000000
    ),
    "trisc1_pc_buffer_debug_bus_cmd_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x1000000
    ),
    "trisc1_pc_buffer_debug_bus_cmd_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=21, mask=0x800000
    ),
    # "trisc1_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=20, mask=0xFF800000
    # ),
    # "trisc1_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(
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
    # "trisc1_risc_wrapper_debug_bus_trisc_o_mailbox_rddata": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=20, mask=0xFFFF0000
    # ),
    # "trisc1_risc_wrapper_debug_bus_trisc_o_mailbox_rddata": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=20, mask=0x3F
    # ),
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
    "trisc2_trisc_mop_buf_empty": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x40000000
    ),
    "trisc2_trisc_mop_buf_full": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x20000000
    ),
    "trisc2_mop_decode_debug_bus_debug_math_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x1C000000
    ),
    "trisc2_mop_decode_debug_bus_debug_unpack_loop_state": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3800000
    ),
    "trisc2_mop_decode_debug_bus_mop_stage_valid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x400000
    ),
    # "trisc2_mop_decode_debug_bus_mop_stage_opcode": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=23, mask=0xFFC00000
    # ),
    # "trisc2_mop_decode_debug_bus_mop_stage_opcode": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=23, mask=0x3FFFFF
    # ),
    "trisc2_mop_decode_debug_bus_math_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x200000
    ),
    "trisc2_mop_decode_debug_bus_unpack_loop_active": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x100000
    ),
    "trisc2_mop_decode_debug_bus_o_instrn_valid": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x80000
    ),
    # "trisc2_mop_decode_debug_bus_o_instrn_opcode": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=23, mask=0xFFF80000
    # ),
    # "trisc2_mop_decode_debug_bus_o_instrn_opcode": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=23, mask=0x7FFFF
    # ),
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
    "trisc2_pc_buffer_debug_bus_i_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x4000000
    ),
    "trisc2_pc_buffer_debug_bus_i_mops_outstanding": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x2000000
    ),
    "trisc2_pc_buffer_debug_bus_cmd_fifo_full": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x1000000
    ),
    "trisc2_pc_buffer_debug_bus_cmd_fifo_empty": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=23, mask=0x800000
    ),
    # "trisc2_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=22, mask=0xFF800000
    # ),
    # "trisc2_pc_buffer_debug_bus_next_cmd_fifo_data": DebugBusSignalDescription(
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
    # "trisc2_risc_wrapper_debug_bus_trisc_o_mailbox_rddata": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=22, mask=0xFFFF0000
    # ),
    # "trisc2_risc_wrapper_debug_bus_trisc_o_mailbox_rddata": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=22, mask=0x3F
    # ),
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
    # "trisc2_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x200
    # ),
    # "trisc2_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x100
    # ),
    "trisc2_if_rts": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x80
    ),
    "trisc2_if_ex_predicted": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x20
    ),
    # "trisc2_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=17, mask=0x1F
    # ),
    # "trisc2_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=17, mask=0xFFFFFFFF
    # ),
    # "trisc2_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x80000000
    # ),
    # "trisc2_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x40000000
    # ),
    "trisc2_id_ex_pc": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=17, mask=0x3FFFFFFF
    ),
    "trisc2_id_rf_wr_flag": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x10000000
    ),
    "trisc2_id_rf_wraddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x1F00000
    ),
    "trisc2_id_rf_p1_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x40000
    ),
    "trisc2_id_rf_p1_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x7C00
    ),
    "trisc2_id_rf_p0_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x100
    ),
    "trisc2_id_rf_p0_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=17, mask=0x1F
    ),
    "trisc2_i_instrn_vld": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=16, mask=0x80000000
    ),
    "trisc2_i_instrn": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=16, mask=0x7FFFFFFF
    ),
    "trisc2_i_instrn_req_rtr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x80000000
    ),
    "trisc2_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x40000000
    ),
    "trisc2_o_instrn_addr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=16, mask=0x3FFFFFFF
    ),
    "trisc2_dbg_obs_mem_wren": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x80000000
    ),
    "trisc2_dbg_obs_mem_rden": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x40000000
    ),
    "trisc2_dbg_obs_mem_addr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=16, mask=0x3FFFFFFF
    ),
    "trisc2_dbg_obs_cmt_vld": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=16, mask=0x80000000
    ),
    "trisc2_dbg_obs_cmt_pc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=16, mask=0x7FFFFFFF
    ),
    # "ncrisc_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x200
    # ),
    # "ncrisc_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x100
    # ),
    "ncrisc_if_rts": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x80
    ),
    "ncrisc_if_ex_predicted": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x20
    ),
    # "ncrisc_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=7, sig_sel=25, mask=0x1F
    # ),
    # "ncrisc_if_ex_deco": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=7, sig_sel=25, mask=0xFFFFFFFF
    # ),
    # "ncrisc_id_ex_rts": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x80000000
    # ),
    # "ncrisc_ex_id_rtr": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x40000000
    # ),
    "ncrisc_id_ex_pc": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=25, mask=0x3FFFFFFF
    ),
    "ncrisc_id_rf_wr_flag": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x10000000
    ),
    "ncrisc_id_rf_wraddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x1F00000
    ),
    "ncrisc_id_rf_p1_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x40000
    ),
    "ncrisc_id_rf_p1_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x7C00
    ),
    "ncrisc_id_rf_p0_rden": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x100
    ),
    "ncrisc_id_rf_p0_rdaddr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=25, mask=0x1F
    ),
    "ncrisc_i_instrn_vld": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x80000000
    ),
    "ncrisc_i_instrn": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=24, mask=0x7FFFFFFF
    ),
    "ncrisc_i_instrn_req_rtr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x80000000
    ),
    "ncrisc_(o_instrn_req_early&~o_instrn_req_cancel)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x40000000
    ),
    "ncrisc_o_instrn_addr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=24, mask=0x3FFFFFFF
    ),
    "ncrisc_dbg_obs_mem_wren": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x80000000
    ),
    "ncrisc_dbg_obs_mem_rden": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x40000000
    ),
    "ncrisc_dbg_obs_mem_addr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=24, mask=0x3FFFFFFF
    ),
    "ncrisc_dbg_obs_cmt_vld": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x80000000
    ),
    "ncrisc_dbg_obs_cmt_pc": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=24, mask=0x7FFFFFFF
    ),
    "tensix_frontend_t0_i_cg_trisc_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x80000000
    ),
    "tensix_frontend_t0_machine_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x40000000
    ),
    "tensix_frontend_t0_req_iramd_buffer_not_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x20000000
    ),
    "tensix_frontend_t0_gpr_file_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x10000000
    ),
    "tensix_frontend_t0_cfg_exu_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x8000000
    ),
    "tensix_frontend_t0_req_iramd_buffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x4000000
    ),
    "tensix_frontend_t0_req_iramd_buffer_full": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x2000000
    ),
    "tensix_frontend_t0_~ibuffer_rtr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x1000000
    ),
    "tensix_frontend_t0_ibuffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x800000
    ),
    # "tensix_frontend_t0_thread_inst": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=1, sig_sel=12, mask=0x7fffff
    # ),
    # "tensix_frontend_t0_thread_inst": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=1, sig_sel=12, mask=0xff800000
    # ),
    "tensix_frontend_t0_math_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x400000
    ),
    "tensix_frontend_t0_tdma_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x200000
    ),
    "tensix_frontend_t0_pack_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x1e0000
    ),  
    "tensix_frontend_t0_move_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x10000
    ),
    "tensix_frontend_t0_sfpu_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x8000
    ),
    "tensix_frontend_t0_unpack_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x6000
    ),
    "tensix_frontend_t0_xsearch_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x1000
    ),
    "tensix_frontend_t0_thcon_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x800
    ),
    "tensix_frontend_t0_sync_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x400
    ),
    "tensix_frontend_t0_cfg_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x200
    ),
    "tensix_frontend_t0_stalled_pack_inst": DebugBusSignalDescription(      
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x1e0
    ),
    "tensix_frontend_t0_stalled_unpack_inst": DebugBusSignalDescription( 
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x18
    ),
    "tensix_frontend_t0_stalled_math_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x4
    ),
    "tensix_frontend_t0_stalled_tdma_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x2
    ),
    "tensix_frontend_t0_stalled_move_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=12, mask=0x1
    ),
    "tensix_frontend_t0_stalled_xsearch_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x80000000
    ),
    "tensix_frontend_t0_stalled_thcon_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x40000000
    ),
    "tensix_frontend_t0_stalled_sync_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x20000000
    ),
    "tensix_frontend_t0_stalled_cfg_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x10000000
    ),
    "tensix_frontend_t0_stalled_sfpu_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x8000000
    ),
    "tensix_frontend_t0_tdma_kick_move": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x4000000
    ),
    "tensix_frontend_t0_tdma_kick_pack": DebugBusSignalDescription(      
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x3c00000
    ),
    "tensix_frontend_t0_tdma_kick_unpack": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x300000
    ),
    "tensix_frontend_t0_tdma_kick_xsearch": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x80000
    ),
    "tensix_frontend_t0_tdma_kick_thcon": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x40000
    ),
    "tensix_frontend_t0_tdma_status_busy": DebugBusSignalDescription(  
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x3fc00
    ),
    "tensix_frontend_t0_packer_busy": DebugBusSignalDescription(     
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x3c0 
    ),
    "tensix_frontend_t0_unpacker_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x30
    ),
    "tensix_frontend_t0_thcon_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x8
    ),
    "tensix_frontend_t0_move_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x4
    ),
    "tensix_frontend_t0_xsearch_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=12, mask=0x3
    ),
    "tensix_frontend_t1_i_cg_trisc_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x80000000
    ),
    "tensix_frontend_t1_machine_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x40000000
    ),
    "tensix_frontend_t1_req_iramd_buffer_not_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x20000000
    ),
    "tensix_frontend_t1_gpr_file_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x10000000
    ),
    "tensix_frontend_t1_cfg_exu_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x8000000
    ),
    "tensix_frontend_t1_req_iramd_buffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x4000000
    ),
    "tensix_frontend_t1_req_iramd_buffer_full": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x2000000
    ),
    "tensix_frontend_t1_~ibuffer_rtr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x1000000
    ),
    "tensix_frontend_t1_ibuffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x800000
    ),
    # "tensix_frontend_t1_thread_inst": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=1, sig_sel=8, mask=0x7fffff
    # ),
    # "tensix_frontend_t1_thread_inst": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=1, sig_sel=8, mask=0xff800000
    # ),
    "tensix_frontend_t1_math_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x400000
    ),
    "tensix_frontend_t1_tdma_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x200000
    ),
    "tensix_frontend_t1_pack_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x1e0000
    ),  
    "tensix_frontend_t1_move_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x10000
    ),
    "tensix_frontend_t1_sfpu_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x8000
    ),
    "tensix_frontend_t1_unpack_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x6000
    ),
    "tensix_frontend_t1_xsearch_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x1000
    ),
    "tensix_frontend_t1_thcon_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x800
    ),
    "tensix_frontend_t1_sync_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x400
    ),
    "tensix_frontend_t1_cfg_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x200
    ),
    "tensix_frontend_t1_stalled_pack_inst": DebugBusSignalDescription(      
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x1e0
    ),
    "tensix_frontend_t1_stalled_unpack_inst": DebugBusSignalDescription( 
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x18
    ),
    "tensix_frontend_t1_stalled_math_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x4
    ),
    "tensix_frontend_t1_stalled_tdma_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x2
    ),
    "tensix_frontend_t1_stalled_move_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=8, mask=0x1
    ),
    "tensix_frontend_t1_stalled_xsearch_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x80000000
    ),
    "tensix_frontend_t1_stalled_thcon_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x40000000
    ),
    "tensix_frontend_t1_stalled_sync_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x20000000
    ),
    "tensix_frontend_t1_stalled_cfg_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x10000000
    ),
    "tensix_frontend_t1_stalled_sfpu_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x8000000
    ),
    "tensix_frontend_t1_tdma_kick_move": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x4000000
    ),
    "tensix_frontend_t1_tdma_kick_pack": DebugBusSignalDescription(      
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x3c00000
    ),
    "tensix_frontend_t1_tdma_kick_unpack": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x300000
    ),
    "tensix_frontend_t1_tdma_kick_xsearch": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x80000
    ),
    "tensix_frontend_t1_tdma_kick_thcon": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x40000
    ),
    "tensix_frontend_t1_tdma_status_busy": DebugBusSignalDescription(  
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x3fc00
    ),
    "tensix_frontend_t1_packer_busy": DebugBusSignalDescription(     
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x3c0 
    ),
    "tensix_frontend_t1_unpacker_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x30
    ),
    "tensix_frontend_t1_thcon_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x8
    ),
    "tensix_frontend_t1_move_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x4
    ),
    "tensix_frontend_t1_xsearch_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=8, mask=0x3
    ),
    "tensix_frontend_t2_i_cg_trisc_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x80000000
    ),
    "tensix_frontend_t2_machine_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x40000000
    ),
    "tensix_frontend_t2_req_iramd_buffer_not_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x20000000
    ),
    "tensix_frontend_t2_gpr_file_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x10000000
    ),
    "tensix_frontend_t2_cfg_exu_busy": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x8000000
    ),
    "tensix_frontend_t2_req_iramd_buffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x4000000
    ),
    "tensix_frontend_t2_req_iramd_buffer_full": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x2000000
    ),
    "tensix_frontend_t2_~ibuffer_rtr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x1000000
    ),
    "tensix_frontend_t2_ibuffer_empty": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x800000
    ),
    # "tensix_frontend_t2_thread_inst": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=1, sig_sel=4, mask=0x7fffff
    # ),
    # "tensix_frontend_t2_thread_inst": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=1, sig_sel=4, mask=0xff800000
    # ),
    "tensix_frontend_t2_math_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x400000
    ),
    "tensix_frontend_t2_tdma_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x200000
    ),
    "tensix_frontend_t2_pack_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x1e0000
    ),  
    "tensix_frontend_t2_move_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x10000
    ),
    "tensix_frontend_t2_sfpu_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x8000
    ),
    "tensix_frontend_t2_unpack_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x6000
    ),
    "tensix_frontend_t2_xsearch_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x1000
    ),
    "tensix_frontend_t2_thcon_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x800
    ),
    "tensix_frontend_t2_sync_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x400
    ),
    "tensix_frontend_t2_cfg_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x200
    ),
    "tensix_frontend_t2_stalled_pack_inst": DebugBusSignalDescription(      
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x1e0
    ),
    "tensix_frontend_t2_stalled_unpack_inst": DebugBusSignalDescription( 
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x18
    ),
    "tensix_frontend_t2_stalled_math_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x4
    ),
    "tensix_frontend_t2_stalled_tdma_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x2
    ),
    "tensix_frontend_t2_stalled_move_inst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=1, sig_sel=4, mask=0x1
    ),
    "tensix_frontend_t2_stalled_xsearch_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x80000000
    ),
    "tensix_frontend_t2_stalled_thcon_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x40000000
    ),
    "tensix_frontend_t2_stalled_sync_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x20000000
    ),
    "tensix_frontend_t2_stalled_cfg_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x10000000
    ),
    "tensix_frontend_t2_stalled_sfpu_inst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x8000000
    ),
    "tensix_frontend_t2_tdma_kick_move": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x4000000
    ),
    "tensix_frontend_t2_tdma_kick_pack": DebugBusSignalDescription(      
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x3c00000
    ),
    "tensix_frontend_t2_tdma_kick_unpack": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x300000
    ),
    "tensix_frontend_t2_tdma_kick_xsearch": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x80000
    ),
    "tensix_frontend_t2_tdma_kick_thcon": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x40000
    ),
    "tensix_frontend_t2_tdma_status_busy": DebugBusSignalDescription(  
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x3fc00
    ),
    "tensix_frontend_t2_packer_busy": DebugBusSignalDescription(     
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x3c0 
    ),
    "tensix_frontend_t2_unpacker_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x30
    ),
    "tensix_frontend_t2_thcon_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x8
    ),
    "tensix_frontend_t2_move_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x4
    ),
    "tensix_frontend_t2_xsearch_busy": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=1, sig_sel=4, mask=0x3
    ),
}
