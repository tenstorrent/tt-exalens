# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.debug_bus_signal_store import DebugBusSignalDescription


debug_bus_signal_map = {
    # For the other signals applying the pc_mask.
    "brisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 5, mask=0x7FFFFFFF),
    "trisc0_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 6, mask=0x7FFFFFFF),
    "trisc1_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 7, mask=0x7FFFFFFF),
    "trisc2_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 8, mask=0x7FFFFFFF),
    "ncrisc_pc": DebugBusSignalDescription(rd_sel=0, daisy_sel=7, sig_sel=2 * 12, mask=0x7FFFFFFF),

    "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_5_EX_ID_RTR__1513": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x200
    ),
    "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_5_ID_EX_RTS__1512": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x100
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_IF_RTS": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x80
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_IF_EX_PREDICTED": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x20
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_IF_EX_DECO__36_32": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=11, mask=0x1F
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_IF_EX_DECO__31_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=11, mask=0xFFFFFFFF
    ),
    "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_5_ID_EX_RTS__1471": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_5_EX_ID_RTR__1470": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x40000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_EX_PC__29_0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=11, mask=0x3FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_WR_FLAG": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x10000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_WRADDR": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F00000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_P1_RDEN": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x40000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_P1_RDADDR": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x7C00                                  
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_P0_RDEN": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x100
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_ID_RF_P0_RDADDR": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=11, mask=0x1F
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_I_INSTRN_VLD": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_I_INSTRN__30_0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_I_INSTRN_REQ_RTR": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x80000000
    ),
     "DEBUG_BUS_DEBUG_TENSIX_IN_5_(O_INSTRN_REQ_EARLY&~O_INSTRN_REQ_CANCEL)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x40000000                              
    ), 
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_O_INSTRN_ADDR__29_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_MEM_WREN": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_MEM_RDEN": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x40000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_MEM_ADDR__29_0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=10, mask=0x3FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_CMT_VLD": DebugBusSignalDescription(           
        rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_5_DBG_OBS_CMT_PC__30_0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=10, mask=0x7FFFFFFF
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_O_PAR_ERR_RISC_LOCALMEM": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x80000000
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_I_MAILBOX_RDEN": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x78000000
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_I_MAILBOX_RD_TYPE": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x7800000
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_O_MAILBOX_RD_REQ_READY": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x780000
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_O_MAILBOX_RDVALID": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x78000
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_O_MAILBOX_RDDATA__6_0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=1, mask=0x7F00
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_INTF_WRACK_BRISC__10_0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0xFFE00000
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_INTF_WRACK_BRISC__16_11": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=1, mask=0x3F
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_DMEM_TENSIX_RDEN": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x100000
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_DMEM_TENSIX_WREN": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x80000
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_ICACHE_REQ_FIFO_FULL": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x2
    ),
    "DEBUG_BUS_RISC_WRAPPER_DEBUG_BUS_ICACHE_REQ_FIFO_EMPTY": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=1, mask=0x1
    ),
    "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_6_EX_ID_RTR__1769": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x200
    ),
    "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_6_ID_EX_RTS__1768": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x100
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_IF_RTS": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x80
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_IF_EX_PREDICTED": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x20
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_IF_EX_DECO__36_32": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=13, mask=0x1F
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_IF_EX_DECO__31_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=13, mask=0xFFFFFFFF
    ),
    "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_6_ID_EX_RTS__1727": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_DAISY_STOP_TENSIX_DEBUG_TENSIX_IN_6_EX_ID_RTR__1726": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x40000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_EX_PC__29_0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=13, mask=0x3FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_WR_FLAG": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x10000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_WRADDR": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F00000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_P1_RDEN": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x40000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_P1_RDADDR": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x7C00
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_P0_RDEN": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x100
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_ID_RF_P0_RDADDR": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=13, mask=0x1F
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_I_INSTRN_VLD": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_I_INSTRN__30_0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_I_INSTRN_REQ_RTR": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_(O_INSTRN_REQ_EARLY&~O_INSTRN_REQ_CANCEL)": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x40000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_O_INSTRN_ADDR__29_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_MEM_WREN": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_MEM_RDEN": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x40000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_MEM_ADDR__29_0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=12, mask=0x3FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_CMT_VLD": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_6_DBG_OBS_CMT_PC__30_0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=12, mask=0x7FFFFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_TRISC_MOP_BUF_EMPTY": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x40000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_TRISC_MOP_BUF_FULL": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x20000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_DEBUG_MATH_LOOP_STATE": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x1C000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_DEBUG_UNPACK_LOOP_STATE": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3800000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_MOP_STAGE_VALID": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x400000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_MOP_STAGE_OPCODE__9_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0xFFC00000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_MOP_STAGE_OPCODE__31_10": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=19, mask=0x3FFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_MATH_LOOP_ACTIVE": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x200000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_UNPACK_LOOP_ACTIVE": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x100000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_O_INSTRN_VALID": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x80000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_O_INSTRN_OPCODE__12_0": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFFF80000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_MOP_DECODE_DEBUG_BUS_O_INSTRN_OPCODE__31_13": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=19, mask=0x7FFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_SEMPOST_PENDING": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFF00
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_SEMGET_PENDING": DebugBusSignalDescription(
        rd_sel=1, daisy_sel=7, sig_sel=19, mask=0xFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_TRISC_READ_REQUEST_PENDING": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x80000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_TRISC_SYNC_ACTIVATED": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x40000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_TRISC_SYNC_TYPE": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x20000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_RISCV_SYNC_ACTIVATED": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x10000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_PC_BUFFER_IDLE": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x8000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_I_BUSY": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x4000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_I_MOPS_OUTSTANDING": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x2000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_CMD_FIFO_FULL": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x1000000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_CMD_FIFO_EMPTY": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x800000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_NEXT_CMD_FIFO_DATA__31_9": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=19, mask=0x7FFFFF
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_PC_BUFFER_DEBUG_BUS_NEXT_CMD_FIFO_DATA__8_0": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0xFF800000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_PAR_ERR_RISC_LOCALMEM": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x400000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_I_MAILBOX_RDEN": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C0000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_I_MAILBOX_RD_TYPE": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RD_REQ_READY": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C00
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDVALID": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3C0
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDDATA__15_0": DebugBusSignalDescription(
        rd_sel=2, daisy_sel=7, sig_sel=18, mask=0xFFFF0000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_O_MAILBOX_RDDATA__21_16": DebugBusSignalDescription(
        rd_sel=3, daisy_sel=7, sig_sel=18, mask=0x3F
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_INTF_WRACK_TRISC__12_0": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x3FFE0000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_DMEM_TENSIX_RDEN": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x10000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_DMEM_TENSIX_WREN": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x8000
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_ICACHE_REQ_FIFO_FULL": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x2
    ),
    "DEBUG_BUS_DEBUG_TENSIX_IN_9_RISC_WRAPPER_DEBUG_BUS_TRISC_ICACHE_REQ_FIFO_EMPTY": DebugBusSignalDescription(
        rd_sel=0, daisy_sel=7, sig_sel=18, mask=0x1
    ),
}