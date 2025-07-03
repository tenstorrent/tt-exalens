#define TRISC_OP_SWIZZLE(x) ( (((x) >> 30) & 0x3) | (((x) & 0x3FFFFFFF) << 2) )
#define TT_OP(opcode, params) ( (opcode << 24) + params )
#define TT_OP_SFPLOAD(lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr) \
  TT_OP(0x70, (((lreg_ind) << 20) + ((instr_mod0) << 16) + ((sfpu_addr_mode) << 14) + ((dest_reg_addr) << 0)))
#define TT_OP_SFPLOADI(lreg_ind, instr_mod0, imm16) \
  TT_OP(0x71, (((lreg_ind) << 20) + ((instr_mod0) << 16) + ((imm16) << 0)))
#define TT_OP_SFPAND(imm12_math, lreg_c, lreg_dest, instr_mod1) \
  TT_OP(0x7e, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))
#define TT_OP_SFPSTORE(lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr) \
  TT_OP(0x72, (((lreg_ind) << 20) + ((instr_mod0) << 16) + ((sfpu_addr_mode) << 14) + ((dest_reg_addr) << 0)))
#define TT_OP_INCRWC(rwc_cr, rwc_d, rwc_b, rwc_a) \
  TT_OP(0x38, (((rwc_cr) << 18) + ((rwc_d) << 14) + ((rwc_b) << 10) + ((rwc_a) << 6)))
#define TT_OP_SETRWC(clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask) \
  TT_OP(0x37, (((clear_ab_vld) << 22) + ((rwc_cr) << 18) + ((rwc_d) << 14) + ((rwc_b) << 10) + ((rwc_a) << 6) + ((BitMask) << 0)))
#define TT_OP_SETC16(setc16_reg, setc16_value) \
  TT_OP(0xb2, (((setc16_reg) << 16) + ((setc16_value) << 0)))
#define TT_OP_SFPCONFIG(imm16_math, config_dest, instr_mod1) \
  TT_OP(0x91, (((imm16_math) << 8) + ((config_dest) << 4) + ((instr_mod1) << 0)))
#define TT_OP_SFPSWAP(imm12_math, lreg_src_c, lreg_dest, instr_mod1) \
  TT_OP(0x92, (((imm12_math) << 12) + ((lreg_src_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))
#define TT_OP_SFPNOP\
  TT_OP(0x8f, 0)
#define TT_OP_SFPSHFT(imm12_math, lreg_c, lreg_dest, instr_mod1) \
  TT_OP(0x7a, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))
#define TT_OP_SFPOR(imm12_math, lreg_c, lreg_dest, instr_mod1) \
  TT_OP(0x7f, (((imm12_math) << 12) + ((lreg_c) << 8) + ((lreg_dest) << 4) + ((instr_mod1) << 0)))
#define TT_OP_STALLWAIT(stall_res, wait_res) \
  TT_OP(0xa2, (((stall_res) << 15) + ((wait_res) << 0)))
#define TT_OP_SEMPOST(sem_sel) \
  TT_OP(0xa4, (((sem_sel) << 2)))



const int sfpload = TRISC_OP_SWIZZLE(TT_OP_SFPLOAD(1, 0, 12, 3));
const int sfploadi = TRISC_OP_SWIZZLE(TT_OP_SFPLOADI(0, 10, 2));
const int sfpand = TRISC_OP_SWIZZLE(TT_OP_SFPAND(0, 0, 1, 0));
const int sfpstore = TRISC_OP_SWIZZLE(TT_OP_SFPSTORE(0, 1, 12, 3));
const int incrwc = TRISC_OP_SWIZZLE(TT_OP_INCRWC(0, 2, 0, 0));
const int setrwc = TRISC_OP_SWIZZLE(TT_OP_SETRWC(0, 0, 0, 0, 0, 4));
const int setc16 = TRISC_OP_SWIZZLE(TT_OP_SETC16(2, 0));
const int sfpconfig = TRISC_OP_SWIZZLE(TT_OP_SFPCONFIG(15, 0, 0));
const int sfpswap = TRISC_OP_SWIZZLE(TT_OP_SFPSWAP(0, 0, 2, 0));
const int sfpnop = TRISC_OP_SWIZZLE(TT_OP_SFPNOP);
const int sfpshft = TRISC_OP_SWIZZLE(TT_OP_SFPSHFT(0, 0, 0x10, 1));
const int sfpor = TRISC_OP_SWIZZLE(TT_OP_SFPOR(0, 0, 1, 0));

// do I need this?
const int stallwait = TRISC_OP_SWIZZLE(TT_OP_STALLWAIT(128, 16512));
const int sempost = TRISC_OP_SWIZZLE(TT_OP_SEMPOST(2));
