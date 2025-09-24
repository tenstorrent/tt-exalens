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
    "adcs2_packers_channel1_w_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF000000
    ),
    "adcs2_packers_channel1_w_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF0000
    ),
    "adcs2_packers_channel1_z_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF00
    ),
    "adcs2_packers_channel1_z_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=5, mask=0xFF
    ),
    "adcs2_packers_channel1_y_cr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=5, mask=0x1FFF0000
    ),
    "adcs2_packers_channel1_y_counter": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=5, mask=0x1FFF
    ),
    "adcs2_packers_channel1_x_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=5, mask=0xFFFC0000
    ),
    "adcs2_packers_channel1_x_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=6, sig_sel=5, mask=0xF
    ),
    "adcs2_packers_channel1_x_counter": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=5, mask=0x3FFFF
    ),
    "adcs2_packers_channel0_w_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF000000
    ),
    "adcs2_packers_channel0_w_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF0000
    ),
    "adcs2_packers_channel0_z_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF00
    ),
    "adcs2_packers_channel0_z_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=4, mask=0xFF
    ),
    "adcs2_packers_channel0_y_cr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=4, mask=0x1FFF0000
    ),
    "adcs2_packers_channel0_y_counter": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=4, mask=0x1FFF
    ),
    "adcs2_packers_channel0_x_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=4, mask=0xFFFC0000
    ),
    "adcs2_packers_channel0_x_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=6, sig_sel=4, mask=0xF
    ),
    "adcs2_packers_channel0_x_counter": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=4, mask=0x3FFFF
    ),
    "adcs0_unpacker1_channel1_w_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF000000
    ),
    "adcs0_unpacker1_channel1_w_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF0000
    ),
    "adcs0_unpacker1_channel1_z_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF00
    ),
    "adcs0_unpacker1_channel1_z_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=3, mask=0xFF
    ),
    "adcs0_unpacker1_channel1_y_cr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=3, mask=0x1FFF0000
    ),
    "adcs0_unpacker1_channel1_y_counter": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=3, mask=0x1FFF
    ),
    "adcs0_unpacker1_channel1_x_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=3, mask=0xFFFC0000
    ),
    "adcs0_unpacker1_channel1_x_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=6, sig_sel=3, mask=0xF
    ),
    "adcs0_unpacker1_channel1_x_counter": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=3, mask=0x3FFFF
    ),
    "adcs0_unpacker1_channel0_w_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF000000
    ),
    "adcs0_unpacker1_channel0_w_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF0000
    ),
    "adcs0_unpacker1_channel0_z_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF00
    ),
    "adcs0_unpacker1_channel0_z_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=2, mask=0xFF
    ),
    "adcs0_unpacker1_channel0_y_cr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=2, mask=0x1FFF0000
    ),
    "adcs0_unpacker1_channel0_y_counter": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=2, mask=0x1FFF
    ),
    "adcs0_unpacker1_channel0_x_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=2, mask=0xFFFC0000
    ),
    "adcs0_unpacker1_channel0_x_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=6, sig_sel=2, mask=0xF
    ),
    "adcs0_unpacker1_channel0_x_counter": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=2, mask=0x3FFFF
    ),
    "adcs0_unpacker0_channel1_w_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF000000
    ),
    "adcs0_unpacker0_channel1_w_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF0000
    ),
    "adcs0_unpacker0_channel1_z_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF00
    ),
    "adcs0_unpacker0_channel1_z_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=1, mask=0xFF
    ),
    "adcs0_unpacker0_channel1_y_cr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=1, mask=0x1FFF0000
    ),
    "adcs0_unpacker0_channel1_y_counter": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=1, mask=0x1FFF
    ),
    "adcs0_unpacker0_channel1_x_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=1, mask=0xFFFC0000
    ),
    "adcs0_unpacker0_channel1_x_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=6, sig_sel=1, mask=0xF
    ),
    "adcs0_unpacker0_channel1_x_counter": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=1, mask=0x3FFFF
    ),
    "adcs0_unpacker0_channel0_w_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF000000
    ),
    "adcs0_unpacker0_channel0_w_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF0000
    ),
    "adcs0_unpacker0_channel0_z_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF00
    ),
    "adcs0_unpacker0_channel0_z_counter": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=6, sig_sel=0, mask=0xFF
    ),
    "adcs0_unpacker0_channel0_y_cr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=0, mask=0x1FFF0000
    ),
    "adcs0_unpacker0_channel0_y_counter": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=6, sig_sel=0, mask=0x1FFF
    ),
    "adcs0_unpacker0_channel0_x_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=6, sig_sel=0, mask=0xF
    ),
    "adcs0_unpacker0_channel0_x_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=0, mask=0xFFFC0000
    ),
    "adcs0_unpacker0_channel0_x_counter": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=6, sig_sel=0, mask=0x3FFFF
    ),
    "rwc_(|math_winner_combo&math_instrn_pipe_ack)": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x10000000
    ),
    # "rwc_debug_daisy_stop_issue0_debug_issue0_in[0]_math_instrn_pipe_ack": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x8000000
    # ),
    "rwc_o_math_instrnbuf_rden": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x4000000
    ),
    "rwc_math_instrn_valid": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x2000000
    ),
    "rwc_src_data_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x1000000
    ),
    "rwc_srcb_data_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x800000
    ),
    "rwc_srca_data_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x400000
    ),
    "rwc_debug_issue0_in[0]_srcb_write_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x200000
    ),
    "rwc_debug_issue0_in[0]_srca_write_ready": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x100000
    ),
    "rwc_srca_update_inst": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x80000
    ),
    "rwc_srcb_update_inst": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x40000
    ),
    "rwc_allow_regfile_update": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x20000
    ),
    "rwc_math_srca_wr_port_avail": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x10000
    ),
    "rwc_debug_issue0_in[0]_dma_srca_wr_port_avail": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x8000
    ),
    "rwc_math_srcb_wr_port_avail": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x4000
    ),
    "rwc_debug_issue0_in[0]_dma_srcb_wr_port_avail": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x2000
    ),
    "rwc_s0_alu_inst_decoded": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x1C00
    ),
    "rwc_s0_sfpu_inst_decoded": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x380
    ),
    "rwc_regw_incr_inst_decoded": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0x70
    ),
    "rwc_regmov_inst_decoded": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=1, mask=0xE
    ),
    "rwc_math_instr_valid_th": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE0000000
    ),
    "rwc_math_winner_thread_combo": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x18000000
    ),
    # "rwc_debug_daisy_stop_issue0_debug_issue0_in[0]_math_instrn_pipe_ack": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x800000
    # ),
    "rwc_math_winner_wo_pipe_stall": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x380000
    ),
    "rwc_s0_srca_data_ready": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x70000
    ),
    "rwc_s0_srcb_data_ready": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE000
    ),
    "rwc_math_thread_inst_data_valid": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=1, mask=0xE00
    ),
    # "rwc_i_dest_target_reg_cfg_pack_sec0_offset": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=3, sig_sel=1, mask=0xE0000000
    # ),
    # "rwc_i_dest_target_reg_cfg_pack_sec0_offset": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=3, sig_sel=1, mask=0x1FF
    # ),
    "rwc_i_dest_target_reg_cfg_pack_sec1_offset": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1FFE0000
    ),
    "rwc_i_dest_target_reg_cfg_pack_sec2_offset": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1FFE0
    ),
    # "rwc_i_dest_target_reg_cfg_pack_sec3_offset": DebugBusSignalDescription(
    #     rd_sel=0, daisy_sel=3, sig_sel=1, mask=0xFE000000
    # ),
    # "rwc_i_dest_target_reg_cfg_pack_sec3_offset": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=3, sig_sel=1, mask=0x1F
    # ),
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
    # "rwc_i_dest_target_reg_cfg_math_offset": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=3, sig_sel=0, mask=0xFFE00000
    # ),
    # "rwc_i_dest_target_reg_cfg_math_offset": DebugBusSignalDescription(
    #     rd_sel=0, daisy_sel=3, sig_sel=1, mask=0x1
    # ),
    # "rwc_i_dest_target_reg_cfg_math_offset": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=3, sig_sel=0, mask=0x1FFE00
    # ),
    # "rwc_i_dest_target_reg_cfg_math_offset": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=3, sig_sel=0, mask=0xE0000000
    # ),
    # "rwc_i_dest_target_reg_cfg_math_offset": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=3, sig_sel=0, mask=0x1FF
    # ),
    "rwc_i_thread_state_id": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=0, mask=0xE000000
    ),
    # "rwc_i_opcode": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=3, sig_sel=0, mask=0x1FE0000
    # ),
    # "rwc_i_instrn_payload": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=3, sig_sel=0, mask=0xFE000000
    # ),
    # "rwc_i_instrn_payload": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=3, sig_sel=0, mask=0x1FFFF
    # ),
    # "rwc_i_opcode": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=3, sig_sel=0, mask=0x1FE0000
    # ),
    # "rwc_i_instrn_payload": DebugBusSignalDescription(
    #     rd_sel=0, daisy_sel=3, sig_sel=0, mask=0xFE000000
    # ),
    # "rwc_i_instrn_payload": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=3, sig_sel=0, mask=0x1FFFF
    # ),
    # "rwc_i_opcode": DebugBusSignalDescription(
    #     rd_sel=0, daisy_sel=3, sig_sel=0, mask=0x1000000
    # ),
    # "rwc_i_instrn_payload": DebugBusSignalDescription(
    #     rd_sel=0, daisy_sel=3, sig_sel=0, mask=0xFFFFFF
    # ),
    "rwcs0_dst_cr": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=2, mask=0x3FF0000
    ),
    "rwcs0_dst": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=3, sig_sel=2, mask=0x3FF
    ),
    "rwcs2_srcb_cr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=2, mask=0x3F000000
    ),
    "rwcs2_srcb": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=2, mask=0x3F0000
    ),
    "rwcs1_srcb_cr": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=2, mask=0x3F00
    ),
    "rwcs1_srcb": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=3, sig_sel=2, mask=0x3F
    ),
    "rwcs0_srcb_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=2, mask=0x3F000000
    ),
    "rwcs0_srcb": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=2, mask=0x3F0000
    ),
    "rwcs2_srca_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=2, mask=0x3F00
    ),
    "rwcs2_srca": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=2, mask=0x3F
    ),
    "rwcs1_srca_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=2, mask=0x3F000000
    ),
    "rwcs1_srca": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=2, mask=0x3F0000
    ),
    "rwcs0_srca_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=2, mask=0x3F00
    ),
    "rwcs0_srca": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=2, mask=0x3F
    ),
    "rwcs2_dst_cr": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=3, mask=0x3FF0000
    ),
    "rwcs2_dst": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=3, mask=0x3FF
    ),
    "rwcs1_dst_cr": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=3, mask=0x3FF0000
    ),
    "rwcs1_dst": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=3, sig_sel=3, mask=0x3FF
    ),
    "rwcs2_fidelity_phase": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=4, mask=0xC0000000
    ),
    "rwcs1_fidelity_phase": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=4, mask=0x30000000
    ),
    "rwcs0_fidelity_phase": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=3, sig_sel=4, mask=0xC000000
    ),
    "sfpu_lane_enabled[31]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x80000000
    ),
    "sfpu_lane_enabled[23]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x40000000
    ),
    "sfpu_lane_enabled[15]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x20000000
    ),
    "sfpu_lane_enabled[7]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x10000000
    ),
    "sfpu_lane_enabled[30]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x8000000
    ),
    "sfpu_lane_enabled[22]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x4000000
    ),
    "sfpu_lane_enabled[14]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x2000000
    ),
    "sfpu_lane_enabled[6]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x1000000
    ),
    "sfpu_lane_enabled[29]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x800000
    ),
    "sfpu_lane_enabled[21]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x400000
    ),
    "sfpu_lane_enabled[13]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x200000
    ),
    "sfpu_lane_enabled[5]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x100000
    ),
    "sfpu_lane_enabled[28]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x80000
    ),
    "sfpu_lane_enabled[20]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x40000
    ),
    "sfpu_lane_enabled[12]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x20000
    ),
    "sfpu_lane_enabled[4]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x10000
    ),
    "sfpu_lane_enabled[27]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x8000
    ),
    "sfpu_lane_enabled[19]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x4000
    ),
    "sfpu_lane_enabled[11]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x2000
    ),
    "sfpu_lane_enabled[3]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x1000
    ),
    "sfpu_lane_enabled[26]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x800
    ),
    "sfpu_lane_enabled[18]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x400
    ),
    "sfpu_lane_enabled[10]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x200
    ),
    "sfpu_lane_enabled[2]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x100
    ),
    "sfpu_lane_enabled[25]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x80
    ),
    "sfpu_lane_enabled[17]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x40
    ),
    "sfpu_lane_enabled[9]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x20
    ),
    "sfpu_lane_enabled[1]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x10
    ),
    "sfpu_lane_enabled[24]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x8
    ),
    "sfpu_lane_enabled[16]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x4
    ),
    "sfpu_lane_enabled[8]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x2
    ),
    "sfpu_lane_enabled[0]": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=28, mask=0x1
    ),
    # "l1_access_port_l1_at_instrn_p12": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=8, sig_sel=3, mask=0xFFF
    # ),
    # "l1_access_port_l1_at_instrn_p12": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=8, sig_sel=3, mask=0xF8000000
    # ),
    "l1_access_port_l1_at_instrn_p11": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=8, sig_sel=3, mask=0x7FFFC00
    ),
    # "l1_access_port_l1_at_instrn_p10": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=8, sig_sel=3, mask=0x3FF
    # ),
    # "l1_access_port_l1_at_instrn_p10": DebugBusSignalDescription(
    #     rd_sel=0, daisy_sel=8, sig_sel=3, mask=0xFE000000
    # ),
    "l1_access_port_l1_at_instrn_p9": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=8, sig_sel=3, mask=0x1FFFF00
    ),
    "l1_access_port_l1_at_instrn_p8": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=8, sig_sel=3, mask=0xFF
    ),
    "l1_access_port_l1_addr_p7": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=8, sig_sel=2, mask=0xFF800000  
    ),
    "l1_access_port_l1_addr_p6": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=8, sig_sel=2, mask=0x7FFFC0      
    ),
    # "l1_access_port_l1_addr_p5": DebugBusSignalDescription(
    #     rd_sel=3, daisy_sel=8, sig_sel=2, mask=0x3F
    # ),
    # "l1_access_port_l1_addr_p5": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=8, sig_sel=2, mask=0xFFE00000
    # ),
    "l1_access_port_l1_addr_p4": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=8, sig_sel=2, mask=0x1FFFF0
    ),
    # "l1_access_port_l1_addr_p3": DebugBusSignalDescription(
    #     rd_sel=2, daisy_sel=8, sig_sel=2, mask=0xF
    # ),
    # "l1_access_port_l1_addr_p3": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=8, sig_sel=2, mask=0xFFF80000
    # ),
    "l1_access_port_l1_addr_p2": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=8, sig_sel=2, mask=0x7FFFC
    ),
    # "l1_access_port_l1_addr_p1": DebugBusSignalDescription(
    #     rd_sel=1, daisy_sel=8, sig_sel=2, mask=0x3
    # ),
    # "l1_access_port_l1_addr_p1": DebugBusSignalDescription(
    #     rd_sel=0, daisy_sel=8, sig_sel=2, mask=0xFFFE0000
    # ),
    "l1_access_port_l1_addr_p0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=8, sig_sel=2, mask=0x1FFFF
    ),
}
