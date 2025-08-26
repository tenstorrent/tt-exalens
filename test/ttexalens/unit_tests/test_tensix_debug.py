# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class, parameterized
from ttexalens import tt_exalens_init
from ttexalens import tt_exalens_lib as lib

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_tensix import TensixDebug, TILE_SIZE, TensixDataFormat, REGFILE


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
        cls.context = tt_exalens_init.init_ttexalens()

    def setUp(self):
        self.core_loc = OnChipCoordinate.create(self.core_loc_str, device=self.context.devices[0])
        self.tdbg = TensixDebug(self.core_loc, 0, self.context)

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

    @parameterized.expand(
        [
            (1,),
            (2,),
            (4,),
            (8,),
        ]
    )
    def test_read_write_regfile_data_fp32(self, num_tiles: int):
        data = [0.01 * i - 5 for i in range(num_tiles * TILE_SIZE)]
        original_df = self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tdbg.write_regfile_data(data, TensixDataFormat.Float32, num_tiles)
        ret = self.tdbg.read_regfile_data(REGFILE.DSTACC, TensixDataFormat.Float32, num_tiles)
        assert len(ret) == len(data)
        assert all(abs(a - b) < 1e-4 for a, b in zip(ret, data))
        self.tdbg.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df

    @parameterized.expand(
        [
            (1,),
            (2,),
            (4,),
            (8,),
        ]
    )
    def test_read_write_regfile_data_int32(self, num_tiles: int):
        data = [i - 512 for i in range(num_tiles * TILE_SIZE)]
        original_df = self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tdbg.write_regfile_data(data, TensixDataFormat.Int32, num_tiles)
        assert self.tdbg.read_regfile_data(REGFILE.DSTACC, TensixDataFormat.Int32, num_tiles) == data
        self.tdbg.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df

    @parameterized.expand(
        [
            (1,),
            (2,),
            (4,),
            (8,),
        ]
    )
    def test_read_write_regfile_data_int8(self, num_tiles: int):
        data = [(i % 256) - 128 for i in range(num_tiles * TILE_SIZE)]
        original_df = self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tdbg.write_regfile_data(data, TensixDataFormat.Int8, num_tiles)
        assert self.tdbg.read_regfile_data(REGFILE.DSTACC, TensixDataFormat.Int8, num_tiles) == data
        self.tdbg.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df
