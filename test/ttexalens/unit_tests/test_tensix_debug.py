# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
from parameterized import parameterized_class
from ttexalens import tt_exalens_init
from ttexalens import tt_exalens_lib as lib

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_tensix import TensixDebug


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
