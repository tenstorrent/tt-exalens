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
        REGFILE_BASE = self.tdbg.device.get_tensix_regfile_base()
        TENSIX_CFG_BASE = self.tdbg.device.get_tensix_configuration_register_base()

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
        mask0 = (
            1
            << (
                self.tdbg.device.get_configuration_register_description("ALU_FORMAT_SPEC_REG_Dstacc_override").shift + 1
            )
        ) - 1
        alu_mask = (
            self.tdbg.device.get_configuration_register_description("ALU_FORMAT_SPEC_REG0_SrcA").mask
            | self.tdbg.device.get_configuration_register_description("ALU_FORMAT_SPEC_REG0_SrcBUnsigned").mask
            | self.tdbg.device.get_configuration_register_description("ALU_ACC_CTRL_SFPU_Fp32_enabled").mask
            | self.tdbg.device.get_configuration_register_description("ALU_ACC_CTRL_Fp32_enabled").mask
            | self.tdbg.device.get_configuration_register_description("ALU_ROUNDING_MODE_Fpu_srnd_en").mask
            | self.tdbg.device.get_configuration_register_description("ALU_ROUNDING_MODE_Gasket_srnd_en").mask
            | self.tdbg.device.get_configuration_register_description("ALU_ROUNDING_MODE_Packer_srnd_en").mask
        )
        address_a = buffer_A // 16 - 1
        address_b = buffer_B // 16 - 1
        while self.tdbg.semaphore_read(5) > 0:
            pass
        self.tdbg.inject_instruction(ops.TT_OP_SETADCXY(0b011, 0, 0, 0, 0, 0b1011), 0)
        self.tdbg.inject_instruction(ops.TT_OP_SETADCZW(0b011, 0, 0, 0, 0, 0b1111), 0)
        self.tdbg.write_tensix_register(
            "UNP0_ADDR_CTRL_ZW_REG_1_Zstride",
            (
                unpA_ch1_z_stride
                << self.tdbg.device.get_configuration_register_description("UNP0_ADDR_CTRL_ZW_REG_1_Zstride").shift
            ),
        )
        self.tdbg.write_tensix_register(
            "UNP1_ADDR_CTRL_ZW_REG_1_Zstride",
            (
                unpB_ch1_z_stride
                << self.tdbg.device.get_configuration_register_description("UNP1_ADDR_CTRL_ZW_REG_1_Zstride").shift
            ),
        )
        self.tdbg.t6_mutex_acquire(0)
        self.tdbg.cfg_reg_rmw_tensix(
            self.tdbg.device.get_configuration_register_description("ALU_FORMAT_SPEC_REG_SrcA_val").index,
            self.tdbg.device.get_configuration_register_description("ALU_FORMAT_SPEC_REG_SrcA_val").shift,
            mask0,
            0,
        )
        self.tdbg.cfg_reg_rmw_tensix(
            self.tdbg.device.get_configuration_register_description("ALU_FORMAT_SPEC_REG0_SrcA").index, 0, alu_mask, 0
        )
        self.tdbg.cfg_reg_rmw_tensix(
            self.tdbg.device.get_configuration_register_description("ALU_ACC_CTRL_Zero_Flag_disabled_src").index,
            self.tdbg.device.get_configuration_register_description("ALU_ACC_CTRL_Zero_Flag_disabled_src").shift,
            self.tdbg.device.get_configuration_register_description("ALU_ACC_CTRL_Zero_Flag_disabled_src").mask,
            0,
        )
        self.tdbg.t6_mutex_release(0)
        self.tdbg.write_tensix_register("THCON_SEC0_REG0_TileDescriptor", (DATA_FORMAT.value) | (1 << 4))
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE
            + 4 * (self.tdbg.device.get_configuration_register_description("THCON_SEC0_REG0_TileDescriptor").index + 1),
            0x40001,
        )
        self.tdbg.write_tensix_register("THCON_SEC1_REG0_TileDescriptor", (DATA_FORMAT.value) | (1 << 4))
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE
            + 4 * (self.tdbg.device.get_configuration_register_description("THCON_SEC1_REG0_TileDescriptor").index + 1),
            0x40100,
        )

        self.tdbg.write_tensix_register("THCON_SEC0_REG2_Out_data_format", (DATA_FORMAT.value) | (2 << 4))
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE
            + 4
            * (self.tdbg.device.get_configuration_register_description("THCON_SEC0_REG2_Out_data_format").index + 1),
            0xF000F,
        )
        self.tdbg.write_tensix_register("THCON_SEC1_REG2_Out_data_format", (DATA_FORMAT.value) | (2 << 4))
        self.tdbg.riscv_write(
            TENSIX_CFG_BASE
            + 4
            * (self.tdbg.device.get_configuration_register_description("THCON_SEC1_REG2_Out_data_format").index + 1),
            0xF000F,
        )
        self.tdbg.inject_instruction(ops.TT_OP_SETADCXX(1, 255, 0x0), 0)
        self.tdbg.inject_instruction(ops.TT_OP_SETADCXX(2, 255, 0x0), 0)
        self.tdbg.write_tensix_register("THCON_SEC0_REG5_Dest_cntx0_address", 0x400040)
        self.tdbg.write_tensix_register("THCON_SEC0_REG5_Tile_x_dim_cntx0", 0x1000100)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 40, 0x1000100)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 41, 0x800080)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 42, 0x400040)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 43, 0x200020)
        self.tdbg.riscv_write(REGFILE_BASE + 4 * 44, 0x100010)
        self.tdbg.sync_regfile_write(44)
        self.tdbg.inject_instruction(
            ops.TT_OP_SETC16(self.tdbg.device.get_configuration_register_description("SRCA_SET_Base").index, 0x4), 0
        )
        self.tdbg.write_tensix_register(
            "UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr",
            0x1
            << self.tdbg.device.get_configuration_register_description(
                "UNP0_ADD_DEST_ADDR_CNTR_add_dest_addr_cntr"
            ).shift,
        )
        self.tdbg.inject_instruction(
            ops.TT_OP_SETC16(
                self.tdbg.device.get_configuration_register_description("UNPACK_MISC_CFG_CfgContextOffset_0").index,
                0x0000,
            ),
            0,
        )
        self.tdbg.cfg_reg_rmw_tensix(
            self.tdbg.device.get_configuration_register_description("THCON_SEC0_REG2_Haloize_mode").index,
            self.tdbg.device.get_configuration_register_description("THCON_SEC0_REG2_Haloize_mode").shift,
            self.tdbg.device.get_configuration_register_description("THCON_SEC0_REG2_Haloize_mode").mask,
            0,
        )
        self.tdbg.inject_instruction(ops.TT_OP_SETADCXX(3, 255, 0x0), 0)
        while self.tdbg.semaphore_read(5) >= 2:
            pass
        self.tdbg.write_tensix_register("THCON_SEC0_REG3_Base_address", address_a)
        self.tdbg.write_tensix_register("THCON_SEC1_REG3_Base_address", address_b)
        self.tdbg.semaphore_post(5)
        for _ in range(4):
            self.tdbg.inject_instruction(ops.TT_OP_UNPACR(0, 0b1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1), 0)
            self.tdbg.inject_instruction(ops.TT_OP_UNPACR(1, 0b1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1), 0)
        self.tdbg.t6_semaphore_get(5)
        self.tdbg.inject_instruction(
            ops.TT_OP_SETC16(
                self.tdbg.device.get_configuration_register_description("UNPACK_MISC_CFG_CfgContextOffset_0").index,
                0x0101,
            ),
            0,
        )

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
        if self.tdbg.device._arch != "wormhole_b0":
            self.skipTest("Test is only for wormhole")

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
