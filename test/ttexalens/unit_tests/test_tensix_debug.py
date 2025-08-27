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
        {"location_str": "0,0"},
        {"location_str": "1,1"},
        {"location_str": "2,2"},
    ]
)
class TestTensixDebug(unittest.TestCase):
    context: Context
    location: OnChipCoordinate
    tensix_debug: TensixDebug

    @classmethod
    def setUpClass(cls):
        cls.context = tt_exalens_init.init_ttexalens()

    def setUp(self):
        self.location = OnChipCoordinate.create(self.location_str, device=self.context.devices[0])
        self.tensix_debug = TensixDebug(self.location, 0, self.context)

    def test_read_write_cfg_register(self):
        cfg_reg_name = "ALU_FORMAT_SPEC_REG2_Dstacc"
        self.tensix_debug.write_tensix_register(cfg_reg_name, 10)
        assert self.tensix_debug.read_tensix_register(cfg_reg_name) == 10
        self.tensix_debug.write_tensix_register(cfg_reg_name, 0)
        assert self.tensix_debug.read_tensix_register(cfg_reg_name) == 0
        self.tensix_debug.write_tensix_register(cfg_reg_name, 5)
        assert self.tensix_debug.read_tensix_register(cfg_reg_name) == 5

    def test_read_write_dbg_register(self):
        dbg_reg_name = "RISCV_DEBUG_REG_CFGREG_RD_CNTL"
        self.tensix_debug.write_tensix_register(dbg_reg_name, 10)
        assert self.tensix_debug.read_tensix_register(dbg_reg_name) == 10
        self.tensix_debug.write_tensix_register(dbg_reg_name, 0)
        assert self.tensix_debug.read_tensix_register(dbg_reg_name) == 0
        self.tensix_debug.write_tensix_register(dbg_reg_name, 5)
        assert self.tensix_debug.read_tensix_register(dbg_reg_name) == 5

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

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        step = 0.01
        error_threshold = 1e-4
        num_of_elements = num_tiles * TILE_SIZE
        data = [step * i - step * num_of_elements / 2 for i in range(num_of_elements)]
        original_df = self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tensix_debug.write_regfile_data(regfile, data, TensixDataFormat.Float32)
        ret = self.tensix_debug.read_regfile(regfile, num_tiles)
        assert len(ret) == len(data)
        assert all(abs(a - b) < error_threshold for a, b in zip(ret, data))
        self.tensix_debug.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df

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

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        num_of_elements = num_tiles * TILE_SIZE
        data = [i - num_of_elements // 2 for i in range(num_of_elements)]
        original_df = self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tensix_debug.write_regfile_data(regfile, data, TensixDataFormat.Int32)
        assert self.tensix_debug.read_regfile(regfile, num_tiles) == data
        self.tensix_debug.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df

    @parameterized.expand(
        [
            (1,),
            (2,),
            (4,),
            (8,),
        ]
    )
    def test_read_write_regfile_data_uint32(self, num_tiles: int):
        if self.context.devices[0]._arch == "wormhole_b0":
            self.skipTest("Direct read/write is not supported on Wormhole.")

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        num_of_elements = num_tiles * TILE_SIZE
        data = [2**32 - 1 for i in range(num_of_elements)]
        original_df = self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tensix_debug.write_regfile_data(regfile, data, TensixDataFormat.UInt32)
        assert self.tensix_debug.read_regfile(regfile, num_tiles, signed=False) == data
        self.tensix_debug.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df

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

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        num_of_elements = num_tiles * TILE_SIZE
        data = [(i % 2**8) - 2**7 for i in range(num_of_elements)]
        original_df = self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tensix_debug.write_regfile_data(regfile, data, TensixDataFormat.Int8)
        assert self.tensix_debug.read_regfile(regfile, num_tiles) == data
        self.tensix_debug.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df

    @parameterized.expand(
        [
            (1,),
            (2,),
            (4,),
            (8,),
        ]
    )
    def test_read_write_regfile_data_uint8(self, num_tiles: int):
        if self.context.devices[0]._arch == "wormhole_b0":
            self.skipTest("Direct read/write is not supported on Wormhole.")

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        num_of_elements = num_tiles * TILE_SIZE
        data = [(i % 2**8) for i in range(num_of_elements)]
        original_df = self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        self.tensix_debug.write_regfile_data(regfile, data, TensixDataFormat.UInt8)
        assert self.tensix_debug.read_regfile(regfile, num_tiles, signed=False) == data
        self.tensix_debug.write_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc", original_df)
        assert self.tensix_debug.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc") == original_df

    @parameterized.expand(
        [
            (TensixDataFormat.UInt16,),  # Unsupported data format
            (TensixDataFormat.Float16,),  # Unsupported data format
            (TensixDataFormat.Float16_b,),  # Unsupported data format
            (TensixDataFormat.Bfp8,),  # Unsupported data format
            (TensixDataFormat.Int32, REGFILE.DSTACC, 2**31),  # Value out of range for Int32
            (TensixDataFormat.Int32, REGFILE.DSTACC, -(2**31 + 1)),  # Value out of range for Int32
            (TensixDataFormat.Int8, REGFILE.DSTACC, 2**7),  # Value out of range for Int8
            (TensixDataFormat.Int8, REGFILE.DSTACC, -(2**7 + 1)),  # Value out of range for Int8
            (TensixDataFormat.Float32, REGFILE.SRCA),  # srcA not supported
            (TensixDataFormat.Float32, REGFILE.SRCB),  # srcB not supported
        ]
    )
    def test_invalid_write_regfile_data(
        self, df: TensixDataFormat, regfile: int | str | REGFILE = REGFILE.DSTACC, value: int | float = 1
    ):
        if self.context.devices[0]._arch == "wormhole_b0":
            self.skipTest("Direct read/write is not supported on Wormhole.")

        with self.assertRaises(TTException):
            self.tensix_debug.write_regfile_data(regfile, [value], df)
