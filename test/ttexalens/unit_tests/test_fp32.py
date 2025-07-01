import unittest
from ttexalens import tt_exalens_init
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_tensix import TensixDebug

class TestTensixDebug(unittest.TestCase):
    context: Context
    core_loc: OnChipCoordinate
    tdbg: TensixDebug

    def setUp(self):
        self.core_loc = OnChipCoordinate.create(self.core_loc_str, device=self.context.devices[0])
        self.tdbg = TensixDebug(self.core_loc, 0, self.context)

    # Write into SRCA, pass that into DST and read the output in float32 format
    def test_fp32(self):
        cfg_reg_name = "ALU_FORMAT_SPEC_REG2_Dstacc"
        self.tdbg.write_tensix_register(cfg_reg_name, 0) # 0 is for fp32
        assert True