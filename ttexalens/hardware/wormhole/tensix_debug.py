# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.debug_tensix import REGFILE, TensixDebug
from ttexalens.pack_unpack_regfile import TensixDataFormat
from ttexalens.util import WARN


class WormholeTensixDebug(TensixDebug):
    def _read_regfile_raw(self, regfile: REGFILE, df: TensixDataFormat, num_tiles: int | None) -> list[int]:
        if regfile != REGFILE.DSTACC or df != TensixDataFormat.Float32:
            return super()._read_regfile_raw(regfile, df, num_tiles)

        # Workaround for an architectural quirk of Wormhole: reading DST as INT32 or FP32
        # returns zeros on the lower 16 bits of each datum. This handles the FP32 case.
        ops = self.device.instructions
        upper = self.read_regfile_data(regfile, df)
        # First, read the upper 16 bits of each value.
        # Half of the values read are zeros, shave them off.
        upper = upper[0:256] + upper[512:768] + upper[1024:1280] + upper[1536:1792]

        # Pass a simple kernel directly to Tensix that exposes the lower 16 bits
        # in place of the upper. This unfortunately clobbers dest.
        for _ in range(0, 64):
            self.inject_instruction(ops.TT_OP_SFPLOAD(2, 3, 0, 0), 1)
            self.inject_instruction(ops.TT_OP_SFPSHFT(0x010, 2, 2, 1), 1)
            self.inject_instruction(ops.TT_OP_SFPSTORE(2, 3, 0, 0), 1)
            self.inject_instruction(ops.TT_OP_INCRWC(0, 16, 0, 0), 1)

        # Read the lower 16 bits from the upper bits' position.
        # Prune the zeros again, same as previously.
        lower = self.read_regfile_data(regfile, df)
        lower = lower[0:256] + lower[512:768] + lower[1024:1280] + lower[1536:1792]
        WARN("The previous contents of DSTACC have been lost and should not be relied upon.")
        return upper + lower
