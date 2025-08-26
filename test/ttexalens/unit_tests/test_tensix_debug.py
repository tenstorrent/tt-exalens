# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class, parameterized
from ttexalens import tt_exalens_init
from ttexalens import tt_exalens_lib as lib

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_tensix import TensixDebug, TILE_SIZE, TensixDataFormat, REGFILE
from ttexalens.util import TTException


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
        if self.context.devices[0]._arch == "wormhole_b0":
            self.skipTest("Direct read/write is not supported on Wormhole.")

        step = 0.01
        error_threshold = 1e-4
        num_of_elements = num_tiles * TILE_SIZE
        data = [step * i - step * num_of_elements / 2 for i in range(num_of_elements)]
        original_df = self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tdbg.write_regfile_data(data, TensixDataFormat.Float32)
        ret = self.tdbg.read_regfile_data(REGFILE.DSTACC, TensixDataFormat.Float32, num_tiles)
        assert len(ret) == len(data)
        assert all(abs(a - b) < error_threshold for a, b in zip(ret, data))
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
        if self.context.devices[0]._arch == "wormhole_b0":
            self.skipTest("Direct read/write is not supported on Wormhole.")

        num_of_elements = num_tiles * TILE_SIZE
        data = [i - num_of_elements // 2 for i in range(num_of_elements)]
        original_df = self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tdbg.write_regfile_data(data, TensixDataFormat.Int32)
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
        if self.context.devices[0]._arch == "wormhole_b0":
            self.skipTest("Direct read/write is not supported on Wormhole.")

        num_of_elements = num_tiles * TILE_SIZE
        data = [(i % 2**8) - 2**7 for i in range(num_of_elements)]
        original_df = self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tdbg.write_regfile_data(data, TensixDataFormat.Int8)
        assert self.tdbg.read_regfile_data(REGFILE.DSTACC, TensixDataFormat.Int8, num_tiles) == data
        self.tdbg.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tdbg.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df

    @parameterized.expand(
        [
            (TensixDataFormat.UInt16,),
            (TensixDataFormat.Float16,),
            (TensixDataFormat.Float16_b,),
            (TensixDataFormat.Bfp8,),
            (TensixDataFormat.Int32, 2**31),  # Value out of range for Int32
            (TensixDataFormat.Int32, -(2**31 + 1)),  # Value out of range for Int32
            (TensixDataFormat.Int8, 2**7),  # Value out of range for Int8
            (TensixDataFormat.Int8, -(2**7 + 1)),  # Value out of range for Int8
        ]
    )
    def test_invalid_write_regfile_data(self, df: TensixDataFormat, value: int | float = 1):
        if self.context.devices[0]._arch == "wormhole_b0":
            self.skipTest("Direct read/write is not supported on Wormhole.")

        with self.assertRaises(TTException):
            self.tdbg.write_regfile_data([value], df)
