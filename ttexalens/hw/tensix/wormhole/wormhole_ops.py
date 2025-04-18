# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# mostly autogenerated using following command:
"""
grep -A1 "#define TT_OP" ~/tt-llk-wh-b0/common/inc/ckernel_ops.h \
  | sed 's/#define/def/g;s/\ *\\\ */:/g;s/--//g;s/^  /  return /g;s/\([^)]\):/\1():/g' > wormhole_ops.py
"""


def TT_OP(opcode, params):
    return int.to_bytes((opcode << 24) + params, 4, byteorder="little")


def TT_OP_ADDDMAREG(OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex):
    return TT_OP(0x58, (((OpBisConst) << 23) + ((ResultRegIndex) << 12) + ((OpBRegIndex) << 6) + ((OpARegIndex) << 0)))


def TT_OP_ADDRCRXY(CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask):
    return TT_OP(
        0x53,
        (((CntSetMask) << 21) + ((Ch1_Y) << 15) + ((Ch1_X) << 12) + ((Ch0_Y) << 9) + ((Ch0_X) << 6) + ((BitMask) << 0)),
    )


def TT_OP_ADDRCRZW(CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask):
    return TT_OP(
        0x56,
        (((CntSetMask) << 21) + ((Ch1_Y) << 15) + ((Ch1_X) << 12) + ((Ch0_Y) << 9) + ((Ch0_X) << 6) + ((BitMask) << 0)),
    )


def TT_OP_APOOL3S1(clear_dvalid, addr_mode, index_en, dst):
    return TT_OP(0x25, (((clear_dvalid) << 22) + ((addr_mode) << 15) + ((index_en) << 14) + ((dst) << 0)))


def TT_OP_APOOL3S2(clear_dvalid, addr_mode, index_en, dst):
    return TT_OP(0x32, (((clear_dvalid) << 22) + ((addr_mode) << 15) + ((index_en) << 14) + ((dst) << 0)))


def TT_OP_ATCAS(MemHierSel, SwapVal, CmpVal, Sel32b, DataRegIndex, AddrRegIndex):
    return TT_OP(
        0x64,
        (
            ((MemHierSel) << 23)
            + ((SwapVal) << 18)
            + ((CmpVal) << 14)
            + ((Sel32b) << 12)
            + ((DataRegIndex) << 6)
            + ((AddrRegIndex) << 0)
        ),
    )


def TT_OP_ATGETM(mutex_index):
    return TT_OP(0xA0, (((mutex_index) << 0)))


def TT_OP_ATINCGET(MemHierSel, WrapVal, Sel32b, DataRegIndex, AddrRegIndex):
    return TT_OP(
        0x61,
        (((MemHierSel) << 23) + ((WrapVal) << 14) + ((Sel32b) << 12) + ((DataRegIndex) << 6) + ((AddrRegIndex) << 0)),
    )


def TT_OP_ATINCGETPTR(MemHierSel, NoIncr, IncrVal, WrapVal, Sel32b, DataRegIndex, AddrRegIndex):
    return TT_OP(
        0x62,
        (
            ((MemHierSel) << 23)
            + ((NoIncr) << 22)
            + ((IncrVal) << 18)
            + ((WrapVal) << 14)
            + ((Sel32b) << 12)
            + ((DataRegIndex) << 6)
            + ((AddrRegIndex) << 0)
        ),
    )


def TT_OP_ATRELM(mutex_index):
    return TT_OP(0xA1, (((mutex_index) << 0)))


def TT_OP_ATSWAP(MemHierSel, SwapMask, DataRegIndex, AddrRegIndex):
    return TT_OP(0x63, (((MemHierSel) << 23) + ((SwapMask) << 14) + ((DataRegIndex) << 6) + ((AddrRegIndex) << 0)))


def TT_OP_BITWOPDMAREG(OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex):
    return TT_OP(
        0x5B,
        (
            ((OpBisConst) << 23)
            + ((OpSel) << 18)
            + ((ResultRegIndex) << 12)
            + ((OpBRegIndex) << 6)
            + ((OpARegIndex) << 0)
        ),
    )


def TT_OP_CLEARDVALID(cleardvalid, reset):
    return TT_OP(0x36, (((cleardvalid) << 22) + ((reset) << 0)))


def TT_OP_CLREXPHIST():
    return TT_OP(0x21, 0)


def TT_OP_CMPDMAREG(OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex):
    return TT_OP(
        0x5D,
        (
            ((OpBisConst) << 23)
            + ((OpSel) << 18)
            + ((ResultRegIndex) << 12)
            + ((OpBRegIndex) << 6)
            + ((OpARegIndex) << 0)
        ),
    )


def TT_OP_CONV3S1(clear_dvalid, rotate_weights, addr_mode, dst):
    return TT_OP(0x22, (((clear_dvalid) << 22) + ((rotate_weights) << 17) + ((addr_mode) << 15) + ((dst) << 0)))


def TT_OP_CONV3S2(clear_dvalid, rotate_weights, addr_mode, dst):
    return TT_OP(0x23, (((clear_dvalid) << 22) + ((rotate_weights) << 17) + ((addr_mode) << 15) + ((dst) << 0)))


def TT_OP_DMANOP():
    return TT_OP(0x60, 0)


def TT_OP_DOTPV(clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst):
    return TT_OP(
        0x29,
        (((clear_dvalid) << 22) + ((dest_accum_en) << 21) + ((instr_mod19) << 19) + ((addr_mode) << 15) + ((dst) << 0)),
    )


def TT_OP_ELWADD(clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst):
    return TT_OP(
        0x28,
        (((clear_dvalid) << 22) + ((dest_accum_en) << 21) + ((instr_mod19) << 19) + ((addr_mode) << 15) + ((dst) << 0)),
    )


def TT_OP_ELWMUL(clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst):
    return TT_OP(
        0x27,
        (((clear_dvalid) << 22) + ((dest_accum_en) << 21) + ((instr_mod19) << 19) + ((addr_mode) << 15) + ((dst) << 0)),
    )


def TT_OP_ELWSUB(clear_dvalid, dest_accum_en, instr_mod19, addr_mode, dst):
    return TT_OP(
        0x30,
        (((clear_dvalid) << 22) + ((dest_accum_en) << 21) + ((instr_mod19) << 19) + ((addr_mode) << 15) + ((dst) << 0)),
    )


def TT_OP_FLUSHDMA(FlushSpec):
    return TT_OP(0x46, (((FlushSpec) << 0)))


def TT_OP_GAPOOL(clear_dvalid, instr_mod19, addr_mode, max_pool_index_en, dst):
    return TT_OP(
        0x34,
        (
            ((clear_dvalid) << 22)
            + ((instr_mod19) << 19)
            + ((addr_mode) << 15)
            + ((max_pool_index_en) << 14)
            + ((dst) << 0)
        ),
    )


def TT_OP_GATESRCRST(reset_srcb_gate_control, reset_srca_gate_control):
    return TT_OP(0x35, (((reset_srcb_gate_control) << 1) + ((reset_srca_gate_control) << 0)))


def TT_OP_GMPOOL(clear_dvalid, instr_mod19, addr_mode, max_pool_index_en, dst):
    return TT_OP(
        0x33,
        (
            ((clear_dvalid) << 22)
            + ((instr_mod19) << 19)
            + ((addr_mode) << 15)
            + ((max_pool_index_en) << 14)
            + ((dst) << 0)
        ),
    )


def TT_OP_INCADCXY(CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X):
    return TT_OP(0x52, (((CntSetMask) << 21) + ((Ch1_Y) << 15) + ((Ch1_X) << 12) + ((Ch0_Y) << 9) + ((Ch0_X) << 6)))


def TT_OP_INCADCZW(CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X):
    return TT_OP(0x55, (((CntSetMask) << 21) + ((Ch1_Y) << 15) + ((Ch1_X) << 12) + ((Ch0_Y) << 9) + ((Ch0_X) << 6)))


def TT_OP_INCRWC(rwc_cr, rwc_d, rwc_b, rwc_a):
    return TT_OP(0x38, (((rwc_cr) << 18) + ((rwc_d) << 14) + ((rwc_b) << 10) + ((rwc_a) << 6)))


def TT_OP_LOADIND(SizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex):
    return TT_OP(
        0x49,
        (
            ((SizeSel) << 22)
            + ((OffsetIndex) << 14)
            + ((AutoIncSpec) << 12)
            + ((DataRegIndex) << 6)
            + ((AddrRegIndex) << 0)
        ),
    )


def TT_OP_LOADREG(TdmaDataRegIndex, RegAddr):
    return TT_OP(0x68, (((TdmaDataRegIndex) << 18) + ((RegAddr) << 0)))


def TT_OP_MFCONV3S1(clear_dvalid, rotate_weights, addr_mode, dst):
    return TT_OP(0x3A, (((clear_dvalid) << 22) + ((rotate_weights) << 17) + ((addr_mode) << 15) + ((dst) << 0)))


def TT_OP_MOP(mop_type, loop_count, zmask_lo16):
    return TT_OP(0x01, (((mop_type) << 23) + ((loop_count) << 16) + ((zmask_lo16) << 0)))


def TT_OP_MOP_CFG(zmask_hi16):
    return TT_OP(0x03, (((zmask_hi16) << 0)))


def TT_OP_MOVA2D(dest_32b_lo, src, addr_mode, instr_mod, dst):
    return TT_OP(
        0x12, (((dest_32b_lo) << 23) + ((src) << 17) + ((addr_mode) << 15) + ((instr_mod) << 12) + ((dst) << 0))
    )


def TT_OP_MOVB2A(srca, addr_mode, instr_mod, srcb):
    return TT_OP(0x0B, (((srca) << 17) + ((addr_mode) << 15) + ((instr_mod) << 12) + ((srcb) << 0)))


def TT_OP_MOVB2D(dest_32b_lo, src, addr_mode, instr_mod, dst):
    return TT_OP(
        0x13, (((dest_32b_lo) << 23) + ((src) << 17) + ((addr_mode) << 15) + ((instr_mod) << 12) + ((dst) << 0))
    )


def TT_OP_MOVD2A(dest_32b_lo, src, addr_mode, instr_mod, dst):
    return TT_OP(
        0x08, (((dest_32b_lo) << 23) + ((src) << 17) + ((addr_mode) << 15) + ((instr_mod) << 12) + ((dst) << 0))
    )


def TT_OP_MOVD2B(dest_32b_lo, src, addr_mode, instr_mod, dst):
    return TT_OP(
        0x0A, (((dest_32b_lo) << 23) + ((src) << 17) + ((addr_mode) << 15) + ((instr_mod) << 12) + ((dst) << 0))
    )


def TT_OP_MOVDBGA2D(dest_32b_lo, src, addr_mode, instr_mod, dst):
    return TT_OP(
        0x09, (((dest_32b_lo) << 23) + ((src) << 17) + ((addr_mode) << 15) + ((instr_mod) << 12) + ((dst) << 0))
    )


def TT_OP_MPOOL3S1(clear_dvalid, addr_mode, index_en, dst):
    return TT_OP(0x24, (((clear_dvalid) << 22) + ((addr_mode) << 15) + ((index_en) << 14) + ((dst) << 0)))


def TT_OP_MPOOL3S2(clear_dvalid, addr_mode, index_en, dst):
    return TT_OP(0x31, (((clear_dvalid) << 22) + ((addr_mode) << 15) + ((index_en) << 14) + ((dst) << 0)))


def TT_OP_MULDMAREG(OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex):
    return TT_OP(0x5A, (((OpBisConst) << 23) + ((ResultRegIndex) << 12) + ((OpBRegIndex) << 6) + ((OpARegIndex) << 0)))


def TT_OP_MVMUL(clear_dvalid, instr_mod19, addr_mode, dst):
    return TT_OP(0x26, (((clear_dvalid) << 22) + ((instr_mod19) << 19) + ((addr_mode) << 15) + ((dst) << 0)))


def TT_OP_NOP():
    return TT_OP(0x02, 0)


def TT_OP_PACR(AddrMode, ZeroWrite, PackSel, OvrdThreadId, Concat, Flush, Last):
    return TT_OP(
        0x41,
        (
            ((AddrMode) << 15)
            + ((ZeroWrite) << 12)
            + ((PackSel) << 8)
            + ((OvrdThreadId) << 7)
            + ((Concat) << 4)
            + ((Flush) << 1)
            + ((Last) << 0)
        ),
    )


def TT_OP_PACR_SETREG(Push, AddrSel, WrData, PackSel, StreamId, Flush, Last):
    return TT_OP(
        0x4A,
        (
            ((Push) << 23)
            + ((AddrSel) << 22)
            + ((WrData) << 12)
            + ((PackSel) << 8)
            + ((StreamId) << 2)
            + ((Flush) << 1)
            + ((Last) << 0)
        ),
    )


def TT_OP_RAREB():
    return TT_OP(0x15, 0)


def TT_OP_RDCFG(GprAddress, CfgReg):
    return TT_OP(0xB1, (((GprAddress) << 16) + ((CfgReg) << 0)))


def TT_OP_REG2FLOP(SizeSel, TargetSel, ByteOffset, ContextId_2, FlopIndex, RegIndex):
    return TT_OP(
        0x48,
        (
            ((SizeSel) << 22)
            + ((TargetSel) << 20)
            + ((ByteOffset) << 18)
            + ((ContextId_2) << 16)
            + ((FlopIndex) << 6)
            + ((RegIndex) << 0)
        ),
    )


def TT_OP_REPLAY(start_idx, len, execute_while_loading, load_mode):
    return TT_OP(0x04, (((start_idx) << 14) + ((len) << 4) + ((execute_while_loading) << 1) + ((load_mode) << 0)))


def TT_OP_RMWCIB0(Mask, Data, CfgRegAddr):
    return TT_OP(0xB3, (((Mask) << 16) + ((Data) << 8) + ((CfgRegAddr) << 0)))


def TT_OP_RMWCIB1(Mask, Data, CfgRegAddr):
    return TT_OP(0xB4, (((Mask) << 16) + ((Data) << 8) + ((CfgRegAddr) << 0)))


def TT_OP_RMWCIB2(Mask, Data, CfgRegAddr):
    return TT_OP(0xB5, (((Mask) << 16) + ((Data) << 8) + ((CfgRegAddr) << 0)))


def TT_OP_RMWCIB3(Mask, Data, CfgRegAddr):
    return TT_OP(0xB6, (((Mask) << 16) + ((Data) << 8) + ((CfgRegAddr) << 0)))


def TT_OP_RSTDMA():
    return TT_OP(0x44, 0)


def TT_OP_SEMGET(sem_sel):
    return TT_OP(0xA5, (((sem_sel) << 2)))


def TT_OP_SEMINIT(max_value, init_value, sem_sel):
    return TT_OP(0xA3, (((max_value) << 20) + ((init_value) << 16) + ((sem_sel) << 2)))


def TT_OP_SEMPOST(sem_sel):
    return TT_OP(0xA4, (((sem_sel) << 2)))


def TT_OP_SEMWAIT(stall_res, sem_sel, wait_sem_cond):
    return TT_OP(0xA6, (((stall_res) << 15) + ((sem_sel) << 2) + ((wait_sem_cond) << 0)))


def TT_OP_SETADC(CntSetMask, ChannelIndex, DimensionIndex, Value):
    return TT_OP(0x50, (((CntSetMask) << 21) + ((ChannelIndex) << 20) + ((DimensionIndex) << 18) + ((Value) << 0)))


def TT_OP_SETADCXX(CntSetMask, x_end2, x_start):
    return TT_OP(0x5E, (((CntSetMask) << 21) + ((x_end2) << 10) + ((x_start) << 0)))


def TT_OP_SETADCXY(CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask):
    return TT_OP(
        0x51,
        (((CntSetMask) << 21) + ((Ch1_Y) << 15) + ((Ch1_X) << 12) + ((Ch0_Y) << 9) + ((Ch0_X) << 6) + ((BitMask) << 0)),
    )


def TT_OP_SETADCZW(CntSetMask, Ch1_Y, Ch1_X, Ch0_Y, Ch0_X, BitMask):
    return TT_OP(
        0x54,
        (((CntSetMask) << 21) + ((Ch1_Y) << 15) + ((Ch1_X) << 12) + ((Ch0_Y) << 9) + ((Ch0_X) << 6) + ((BitMask) << 0)),
    )


def TT_OP_SETASHRMH(reg_mask, halo_mask):
    return TT_OP(0x1E, (((reg_mask) << 1) + ((halo_mask) << 0)))


def TT_OP_SETASHRMH0(reg_mask, halo_mask):
    return TT_OP(0x1A, (((reg_mask) << 1) + ((halo_mask) << 0)))


def TT_OP_SETASHRMH1(reg_mask, halo_mask):
    return TT_OP(0x1B, (((reg_mask) << 1) + ((halo_mask) << 0)))


def TT_OP_SETASHRMV(reg_mask2):
    return TT_OP(0x1C, (((reg_mask2) << 0)))


def TT_OP_SETC16(setc16_reg, setc16_value):
    return TT_OP(0xB2, (((setc16_reg) << 16) + ((setc16_value) << 0)))


def TT_OP_SETDMAREG(Payload_SigSelSize, Payload_SigSel, SetSignalsMode, RegIndex16b):
    return TT_OP(
        0x45, (((Payload_SigSelSize) << 22) + ((Payload_SigSel) << 8) + ((SetSignalsMode) << 7) + ((RegIndex16b) << 0))
    )


def TT_OP_SETDVALID(setvalid):
    return TT_OP(0x57, (((setvalid) << 0)))


def TT_OP_SETIBRWC(rwc_cr, rwc_bias, set_inc_ctrl):
    return TT_OP(0x39, (((rwc_cr) << 18) + ((rwc_bias) << 6) + ((set_inc_ctrl) << 0)))


def TT_OP_SETPKEDGOF(y_end, y_start, x_end, x_start):
    return TT_OP(0x1D, (((y_end) << 12) + ((y_start) << 8) + ((x_end) << 4) + ((x_start) << 0)))


def TT_OP_SETRWC(clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask):
    return TT_OP(
        0x37,
        (
            ((clear_ab_vld) << 22)
            + ((rwc_cr) << 18)
            + ((rwc_d) << 14)
            + ((rwc_b) << 10)
            + ((rwc_a) << 6)
            + ((BitMask) << 0)
        ),
    )


def TT_OP_SFPABS(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x7D, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPADD(lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1):
    return TT_OP(
        0x85,
        (((lreg_src_a) << 16) + ((lreg_src_b) << 12) + ((lreg_src_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)),
    )


def TT_OP_SFPADDI(imm16_math, lreg_dest, instr_mod1):
    return TT_OP(0x75, (((imm16_math) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPAND(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x7E, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPCAST(lreg_src_c, lreg_dest, instr_mod1):
    return TT_OP(0x90, (((lreg_src_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPCOMPC(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x8B, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPCONFIG(imm16_math, config_dest, instr_mod1):
    return TT_OP(0x91, (((imm16_math) << 8) + ((config_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPDIVP2(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x76, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPENCC(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x8A, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPEXEXP(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x77, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPEXMAN(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x78, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPIADD(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x79, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPLOAD(lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr):
    return TT_OP(0x70, (((lreg_ind) << 20) + ((instr_mod0) << 16) + ((sfpu_addr_mode) << 14) + ((dest_reg_addr) << 0)))


def TT_OP_SFPLOADI(lreg_ind, instr_mod0, imm16):
    return TT_OP(0x71, (((lreg_ind) << 20) + ((instr_mod0) << 16) + ((imm16) << 0)))


def TT_OP_SFPLOADMACRO(lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr):
    return TT_OP(0x93, (((lreg_ind) << 20) + ((instr_mod0) << 16) + ((sfpu_addr_mode) << 14) + ((dest_reg_addr) << 0)))


def TT_OP_SFPLUT(lreg_ind, instr_mod0, dest_reg_addr):
    return TT_OP(0x73, (((lreg_ind) << 20) + ((instr_mod0) << 16) + ((dest_reg_addr) << 0)))


def TT_OP_SFPLUTFP32(lreg_dest, instr_mod1):
    return TT_OP(0x95, (((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPLZ(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x81, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPMAD(lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1):
    return TT_OP(
        0x84,
        (((lreg_src_a) << 16) + ((lreg_src_b) << 12) + ((lreg_src_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)),
    )


def TT_OP_SFPMOV(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x7C, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPMUL(lreg_src_a, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1):
    return TT_OP(
        0x86,
        (((lreg_src_a) << 16) + ((lreg_src_b) << 12) + ((lreg_src_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)),
    )


def TT_OP_SFPMULI(imm16_math, lreg_dest, instr_mod1):
    return TT_OP(0x74, (((imm16_math) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPNOP():
    return TT_OP(0x8F, 0)


def TT_OP_SFPNOT(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x80, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPOR(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x7F, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPPOPC(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x88, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPPUSHC(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x87, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPSETCC(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x7B, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPSETEXP(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x82, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPSETMAN(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x83, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPSETSGN(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x89, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPSHFT(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x7A, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPSHFT2(imm12_math, lreg_src_c, lreg_dest, instr_mod1):
    return TT_OP(0x94, (((imm12_math) << 12) + ((lreg_src_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPSTORE(lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr):
    return TT_OP(0x72, (((lreg_ind) << 20) + ((instr_mod0) << 16) + ((sfpu_addr_mode) << 14) + ((dest_reg_addr) << 0)))


def TT_OP_SFPSWAP(imm12_math, lreg_src_c, lreg_dest, instr_mod1):
    return TT_OP(0x92, (((imm12_math) << 12) + ((lreg_src_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPTRANSP(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x8C, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFPXOR(imm12_math, lreg_c, lreg_dest, instr_mod1):
    return TT_OP(0x8D, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))


def TT_OP_SFP_STOCH_RND(rnd_mode, imm8_math, lreg_src_b, lreg_src_c, lreg_dest, instr_mod1):
    return TT_OP(
        0x8E,
        (
            ((rnd_mode) << 21)
            + ((imm8_math) << 16)
            + ((lreg_src_b) << 12)
            + ((lreg_src_c) << 8)
            + ((lreg_dest) << 4)
            + ((instr_mod1) << 0)
        ),
    )


def TT_OP_SHIFTDMAREG(OpBisConst, OpSel, ResultRegIndex, OpBRegIndex, OpARegIndex):
    return TT_OP(
        0x5C,
        (
            ((OpBisConst) << 23)
            + ((OpSel) << 18)
            + ((ResultRegIndex) << 12)
            + ((OpBRegIndex) << 6)
            + ((OpARegIndex) << 0)
        ),
    )


def TT_OP_SHIFTXA(log2_amount2, shift_mode):
    return TT_OP(0x17, (((log2_amount2) << 2) + ((shift_mode) << 0)))


def TT_OP_SHIFTXB(addr_mode, rot_shift, shift_row):
    return TT_OP(0x18, (((addr_mode) << 15) + ((rot_shift) << 10) + ((shift_row) << 0)))


def TT_OP_STALLWAIT(stall_res, wait_res):
    return TT_OP(0xA2, (((stall_res) << 15) + ((wait_res) << 0)))


def TT_OP_STOREIND(MemHierSel, SizeSel, RegSizeSel, OffsetIndex, AutoIncSpec, DataRegIndex, AddrRegIndex):
    return TT_OP(
        0x66,
        (
            ((MemHierSel) << 23)
            + ((SizeSel) << 22)
            + ((RegSizeSel) << 21)
            + ((OffsetIndex) << 14)
            + ((AutoIncSpec) << 12)
            + ((DataRegIndex) << 6)
            + ((AddrRegIndex) << 0)
        ),
    )


def TT_OP_STOREREG(TdmaDataRegIndex, RegAddr):
    return TT_OP(0x67, (((TdmaDataRegIndex) << 18) + ((RegAddr) << 0)))


def TT_OP_SUBDMAREG(OpBisConst, ResultRegIndex, OpBRegIndex, OpARegIndex):
    return TT_OP(0x59, (((OpBisConst) << 23) + ((ResultRegIndex) << 12) + ((OpBRegIndex) << 6) + ((OpARegIndex) << 0)))


def TT_OP_TBUFCMD():
    return TT_OP(0x4B, 0)


def TT_OP_TRNSPSRCA():
    return TT_OP(0x14, 0)


def TT_OP_TRNSPSRCB():
    return TT_OP(0x16, 0)


def TT_OP_UNPACR(
    Unpack_block_selection,
    AddrMode,
    CfgContextCntInc,
    CfgContextId,
    AddrCntContextId,
    OvrdThreadId,
    SetDatValid,
    rareb_en,
    ZeroWrite2,
    AutoIncContextID,
    RowSearch,
    SearchCacheFlush,
    Last,
):
    return TT_OP(
        0x42,
        (
            ((Unpack_block_selection) << 23)
            + ((AddrMode) << 15)
            + ((CfgContextCntInc) << 13)
            + ((CfgContextId) << 10)
            + ((AddrCntContextId) << 8)
            + ((OvrdThreadId) << 7)
            + ((SetDatValid) << 6)
            + ((rareb_en) << 5)
            + ((ZeroWrite2) << 4)
            + ((AutoIncContextID) << 3)
            + ((RowSearch) << 2)
            + ((SearchCacheFlush) << 1)
            + ((Last) << 0)
        ),
    )


def TT_OP_UNPACR_NOP(Unpack_block_selection, NoOp):
    return TT_OP(0x43, (((Unpack_block_selection) << 23) + ((NoOp) << 0)))


def TT_OP_WRCFG(GprAddress, wr128b, CfgReg):
    return TT_OP(0xB0, (((GprAddress) << 16) + ((wr128b) << 15) + ((CfgReg) << 0)))


def TT_OP_XMOV(Mov_block_selection, Last):
    return TT_OP(0x40, (((Mov_block_selection) << 23) + ((Last) << 0)))


def TT_OP_ZEROACC(clear_mode, AddrMode, dst):
    return TT_OP(0x10, (((clear_mode) << 19) + ((AddrMode) << 15) + ((dst) << 0)))


def TT_OP_ZEROSRC(zero_val, write_mode, bank_mask, src_mask):
    return TT_OP(0x11, (((zero_val) << 4) + ((write_mode) << 3) + ((bank_mask) << 2) + ((src_mask) << 0)))
