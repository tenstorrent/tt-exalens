# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class
from ttlens import tt_lens_init
from ttlens import tt_lens_lib as lib

from ttlens.tt_coordinate import OnChipCoordinate
from ttlens.tt_lens_context import Context
from ttlens.tt_debug_tensix import TensixDebug
from ttlens.tt_lens_lib import write_to_device
from ttlens.pack import pack_fp16, pack_bfp16, pack_bfp8_b
from ttlens.tt_unpack_regfile import tensix_data_format


@parameterized_class(
    [
        {"core_loc_str": "0,0"},
        {"core_loc_str": "1,1"},
        {"core_loc_str": "2,2"},
    ]
)
class TestTensixDebug(unittest.TestCase):
    context: Context
    core_loc: OnChipCoordinate
    tdbg: TensixDebug

    @classmethod
    def setUpClass(cls):
        cls.context = tt_lens_init.init_ttlens()

    def setUp(self):
        self.core_loc = OnChipCoordinate.create(self.core_loc_str, device=self.context.devices[0])
        self.tdbg = TensixDebug(self.core_loc, 0, self.context)

    def unpacker(self, srcA, srcB, DATA_FORMAT: tensix_data_format):
        REGFILE_BASE = 0xFFE00000
        TENSIX_CFG_BASE = 0xFFEF0000

        UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32 = 39
        ALU_FORMAT_SPEC_REG_SrcA_val_SHAMT = 0
        ALU_FORMAT_SPEC_REG_Dstacc_override_SHAMT = 14
        ALU_FORMAT_SPEC_REG0_SrcAUnsigned_MASK = 0x8000
        ALU_FORMAT_SPEC_REG0_SrcBUnsigned_MASK = 0x10000
        ALU_ACC_CTRL_SFPU_Fp32_enabled_MASK = 0x40000000
        ALU_ACC_CTRL_Fp32_enabled_MASK = 0x20000000
        ALU_ROUNDING_MODE_Fpu_srnd_en_MASK = 0x1
        ALU_ROUNDING_MODE_Gasket_srnd_en_MASK = 0x2
        ALU_ROUNDING_MODE_Packer_srnd_en_MASK = 0x4
        UNP0_ADDR_CTRL_ZW_REG_1_Zstride_ADDR32 = 45
        UNP0_ADDR_CTRL_ZW_REG_1_Wstride_SHAMT = 12
        UNP0_ADDR_CTRL_ZW_REG_1_Zstride_SHAMT = 0
        UNP1_ADDR_CTRL_ZW_REG_1_Zstride_ADDR32 = 47
        UNP1_ADDR_CTRL_ZW_REG_1_Wstride_SHAMT = 12
        UNP1_ADDR_CTRL_ZW_REG_1_Zstride_SHAMT = 0
        ALU_FORMAT_SPEC_REG_SrcA_val_ADDR32 = 0
        ALU_FORMAT_SPEC_REG0_SrcA_ADDR32 = 1
        ALU_ACC_CTRL_Zero_Flag_disabled_src_ADDR32 = 2
        ALU_ACC_CTRL_Zero_Flag_disabled_src_SHAMT = 0
        ALU_ACC_CTRL_Zero_Flag_disabled_src_MASK = 0x1
        THCON_SEC0_REG0_TileDescriptor_ADDR32 = 52
        THCON_SEC1_REG0_TileDescriptor_ADDR32 = 92
        THCON_SEC0_REG2_Out_data_format_ADDR32 = 60
        THCON_SEC1_REG2_Out_data_format_ADDR32 = 100
        THCON_SEC0_REG5_Dest_cntx0_address_ADDR32 = 72
        THCON_SEC0_REG5_Tile_x_dim_cntx0_ADDR32 = 74
        UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr_ADDR32 = 41
        UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr_SHAMT = 8
        THCON_SEC0_REG2_Haloize_mode_ADDR32 = 60
        THCON_SEC0_REG2_Haloize_mode_SHAMT = 8
        THCON_SEC0_REG2_Haloize_mode_MASK = 0x100
        THCON_SEC0_REG3_Base_address_ADDR32 = 64
        THCON_SEC1_REG3_Base_address_ADDR32 = 104
        SRCA_SET_Base_ADDR32 = 3

        ops = self.tdbg.device.instructions

        if DATA_FORMAT == tensix_data_format.Float16_b:
            write_to_device(self.core_loc, 0x1B000, pack_bfp16(srcA))
            write_to_device(self.core_loc, 0x1C000, pack_bfp16(srcB))
        elif DATA_FORMAT == tensix_data_format.Float16:
            write_to_device(self.core_loc, 0x1B000, pack_fp16(srcA))
            write_to_device(self.core_loc, 0x1C000, pack_fp16(srcB))
        elif DATA_FORMAT == tensix_data_format.Bfp8_b:
            write_to_device(self.core_loc, 0x1B000, pack_bfp8_b(srcA))
            write_to_device(self.core_loc, 0x1C000, pack_bfp8_b(srcB))

        buffer_A = 0x1B000
        buffer_B = 0x1C000
        unpA_ch1_x_stride = 2 if (DATA_FORMAT.value & 0x3) == 1 else 1
        unpB_ch1_x_stride = 2 if (DATA_FORMAT.value & 0x3) == 1 else 1
        unpA_ch1_z_stride = 16 * 16 * unpA_ch1_x_stride
        unpB_ch1_z_stride = 16 * 16 * unpB_ch1_x_stride
        alu_src_format = 0x0 << ALU_FORMAT_SPEC_REG_SrcA_val_SHAMT
        mask0 = (1 << (ALU_FORMAT_SPEC_REG_Dstacc_override_SHAMT + 1)) - 1
        alu_mask = (
            ALU_FORMAT_SPEC_REG0_SrcAUnsigned_MASK
            | ALU_FORMAT_SPEC_REG0_SrcBUnsigned_MASK
            | ALU_ACC_CTRL_SFPU_Fp32_enabled_MASK
            | ALU_ACC_CTRL_Fp32_enabled_MASK
            | ALU_ROUNDING_MODE_Fpu_srnd_en_MASK
            | ALU_ROUNDING_MODE_Gasket_srnd_en_MASK
            | ALU_ROUNDING_MODE_Packer_srnd_en_MASK
        )
        address_a = buffer_A // 16 - 1
        address_b = buffer_B // 16 - 1
        while self.tdbg.semaphore_read(5) > 0:
            pass
        self.tdbg.inject_instruction(ops.TT_OP_SETADCXY(0b011, 0, 0, 0, 0, 0b1011), 0)
        self.tdbg.inject_instruction(ops.TT_OP_SETADCZW(0b011, 0, 0, 0, 0, 0b1111), 0)
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE + 4 * UNP0_ADDR_CTRL_ZW_REG_1_Zstride_ADDR32,
            (0 << UNP0_ADDR_CTRL_ZW_REG_1_Wstride_SHAMT) | (unpA_ch1_z_stride << UNP0_ADDR_CTRL_ZW_REG_1_Zstride_SHAMT),
        )
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE + 4 * UNP1_ADDR_CTRL_ZW_REG_1_Zstride_ADDR32,
            (0 << UNP1_ADDR_CTRL_ZW_REG_1_Wstride_SHAMT) | (unpB_ch1_z_stride << UNP1_ADDR_CTRL_ZW_REG_1_Zstride_SHAMT),
        )
        self.tdbg.t6_mutex_acquire(0)
        self.tdbg.cfg_reg_rmw_tensix(
            ALU_FORMAT_SPEC_REG_SrcA_val_ADDR32, ALU_FORMAT_SPEC_REG_SrcA_val_SHAMT, mask0, alu_src_format
        )
        self.tdbg.cfg_reg_rmw_tensix(ALU_FORMAT_SPEC_REG0_SrcA_ADDR32, 0, alu_mask, 0)
        self.tdbg.cfg_reg_rmw_tensix(
            ALU_ACC_CTRL_Zero_Flag_disabled_src_ADDR32,
            ALU_ACC_CTRL_Zero_Flag_disabled_src_SHAMT,
            ALU_ACC_CTRL_Zero_Flag_disabled_src_MASK,
            0,
        )
        self.tdbg.t6_mutex_release(0)
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE + 4 * THCON_SEC0_REG0_TileDescriptor_ADDR32, (DATA_FORMAT.value) | (1 << 4)
        )
        self.tdbg.riscv_write(TENSIX_CFG_BASE + 4 * (THCON_SEC0_REG0_TileDescriptor_ADDR32 + 1), 0x40001)
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE + 4 * THCON_SEC1_REG0_TileDescriptor_ADDR32, (DATA_FORMAT.value) | (1 << 4)
        )
        self.tdbg.riscv_write(TENSIX_CFG_BASE + 4 * (THCON_SEC1_REG0_TileDescriptor_ADDR32 + 1), 0x40100)
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE + 4 * (THCON_SEC0_REG2_Out_data_format_ADDR32), (DATA_FORMAT.value) | (2 << 4)
        )
        self.tdbg.riscv_write(TENSIX_CFG_BASE + 4 * (THCON_SEC0_REG2_Out_data_format_ADDR32 + 1), 0xF000F)
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE + 4 * (THCON_SEC1_REG2_Out_data_format_ADDR32), (DATA_FORMAT.value) | (2 << 4)
        )
        self.tdbg.riscv_write(TENSIX_CFG_BASE + 4 * (THCON_SEC1_REG2_Out_data_format_ADDR32 + 1), 0xF000F)
        self.tdbg.inject_instruction(ops.TT_OP_SETADCXX(1, 255, 0x0), 0)
        self.tdbg.inject_instruction(ops.TT_OP_SETADCXX(2, 255, 0x0), 0)
        self.tdbg.riscv_write(TENSIX_CFG_BASE + 4 * THCON_SEC0_REG5_Dest_cntx0_address_ADDR32, 0x400040)
        self.tdbg.riscv_write(TENSIX_CFG_BASE + 4 * THCON_SEC0_REG5_Tile_x_dim_cntx0_ADDR32, 0x1000100)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 40, 0x1000100)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 41, 0x800080)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 42, 0x400040)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 43, 0x200020)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 44, 0x100010)
        self.tdbg.sync_regfile_write(44)
        self.tdbg.inject_instruction(ops.TT_OP_SETC16(SRCA_SET_Base_ADDR32, 0x4), 0)
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE + 4 * UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr_ADDR32,
            0x1 << UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr_SHAMT,
        )
        self.tdbg.inject_instruction(ops.TT_OP_SETC16(UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32, 0x0000), 0)
        self.tdbg.cfg_reg_rmw_tensix(
            THCON_SEC0_REG2_Haloize_mode_ADDR32,
            THCON_SEC0_REG2_Haloize_mode_SHAMT,
            THCON_SEC0_REG2_Haloize_mode_MASK,
            0,
        )
        self.tdbg.inject_instruction(ops.TT_OP_SETADCXX(3, 255, 0x0), 0)
        while self.tdbg.semaphore_read(5) >= 2:
            pass
        self.tdbg.riscv_write(TENSIX_CFG_BASE + 4 * THCON_SEC0_REG3_Base_address_ADDR32, address_a)
        self.tdbg.riscv_write(TENSIX_CFG_BASE + 4 * THCON_SEC1_REG3_Base_address_ADDR32, address_b)
        self.tdbg.semaphore_post(5)
        for _ in range(4):
            self.tdbg.inject_instruction(ops.TT_OP_UNPACR(0, 0b1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1), 0)
            self.tdbg.inject_instruction(ops.TT_OP_UNPACR(1, 0b1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1), 0)
        self.tdbg.t6_semaphore_get(5)
        self.tdbg.inject_instruction(ops.TT_OP_SETC16(UNPACK_MISC_CFG_CfgContextOffset_0_ADDR32, 0x0101), 0)

        self.tdbg.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", DATA_FORMAT.value)

    def test_read_write_cfg_register(self):
        cfg_reg_name = "ALU_FORMAT_SPEC_REG2_Dstacc"
        self.tdbg.write_tensix_register(cfg_reg_name, 10)
        assert self.tdbg.read_tensix_register(cfg_reg_name) == 10
        self.tdbg.write_tensix_register(cfg_reg_name, 0)
        assert self.tdbg.read_tensix_register(cfg_reg_name) == 0
        self.tdbg.write_tensix_register(cfg_reg_name, 5)
        assert self.tdbg.read_tensix_register(cfg_reg_name) == 5

    def test_read_write_dbg_register(self):
        dbg_reg_name = "RISCV_DEBUG_REG_CFGREG_RD_CNTL"
        self.tdbg.write_tensix_register(dbg_reg_name, 10)
        assert self.tdbg.read_tensix_register(dbg_reg_name) == 10
        self.tdbg.write_tensix_register(dbg_reg_name, 0)
        assert self.tdbg.read_tensix_register(dbg_reg_name) == 0
        self.tdbg.write_tensix_register(dbg_reg_name, 5)
        assert self.tdbg.read_tensix_register(dbg_reg_name) == 5

    def test_dump_srca(self):
        srcA = [i * -1 for i in range(1024)]
        srcB = [i * -2 for i in range(1024)]

        self.unpacker(srcA, srcB, tensix_data_format.Float16)
        regfile = self.tdbg.read_regfile("SRCA")

        assert len(regfile) == 1024
        for i in range(256):
            assert regfile[i] == srcA[i]

        srcA = [i * -2 for i in range(1024)]
        srcB = [i * -1 for i in range(1024)]
        self.unpacker(srcA, srcB, tensix_data_format.Float16_b)
        regfile = self.tdbg.read_regfile("SRCA")

        assert len(regfile) == 1024
        for i in range(256):
            assert regfile[i] == srcA[i]
