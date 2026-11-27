# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.debug_tensix import REGFILE, TensixDebug
from ttexalens.pack_unpack_regfile import TensixDataFormat
from ttexalens.util import WARN


class WormholeTensixDebug(TensixDebug):
    def _read_math_dst_offset(self, thread_id: int) -> int:
        """Reads DEST_TARGET_REG_CFG_MATH_Offset of the given Tensix thread from the debug bus."""
        debug_bus = self.noc_block.debug_bus
        assert debug_bus is not None, "Debug bus is not initialized."
        # One 36-bit signal, read in parts of 3, 32 and 1 bits, so a concurrent change can mix two values.
        # Inferred layout, not documented for Wormhole: three 12-bit offsets, thread 0 lowest.
        name = "rwc_i_dest_target_reg_cfg_math_offset"
        offsets = (
            debug_bus.read_signal(f"{name}/0")
            | (debug_bus.read_signal(f"{name}/1") << 3)
            | (debug_bus.read_signal(f"{name}/2") << 35)
        )
        return (offsets >> (12 * thread_id)) & 0xFFF

    def _shift_dst_low_halves_up(self) -> None:
        """Moves the lower 16 bits of Dst rows 0-31 into the upper 16 bits, which the debug read returns.
        Overwrites Dst and resets the Dst counters of Tensix thread 1."""
        # SFPLOAD / SFPSTORE address: Imm10 + Dst offset + Dst counter + DEST_REGW_BASE_Base, modulo 1024 rows.
        # The write base is assumed to be 0 and is not compensated.
        ops = self.device.instructions
        math_thread = 1
        lreg = 2
        mod0_int32 = 4  # MOD0_FMT_INT32: unlike FP32, the store does not flush values that look like denormals
        shift_left_16 = ops.TT_OP_SFPSHFT(0x010, lreg, lreg, 1)
        zero_dst_counter = ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0x4)  # Dst only; the address mode moves it after each access
        dst_offset = self._read_math_dst_offset(math_thread)
        # One access covers 4 rows and the 8 columns of one parity (bit 1 of the address).
        for block in range(8):
            for parity in (0, 1):
                addr = (4 * block + 2 * parity - dst_offset) % 1024
                self.inject_instruction(zero_dst_counter, math_thread)
                self.inject_instruction(ops.TT_OP_SFPLOAD(lreg, mod0_int32, 0, addr), math_thread)
                self.inject_instruction(shift_left_16, math_thread)
                self.inject_instruction(zero_dst_counter, math_thread)
                self.inject_instruction(ops.TT_OP_SFPSTORE(lreg, mod0_int32, 0, addr), math_thread)
        self.inject_instruction(zero_dst_counter, math_thread)

    def _read_regfile_raw(self, regfile: REGFILE, df: TensixDataFormat, num_tiles: int | None) -> list[int]:
        if regfile != REGFILE.DSTACC or df != TensixDataFormat.Float32:
            return super()._read_regfile_raw(regfile, df, num_tiles)

        # Workaround for an architectural quirk of Wormhole: reading DST as INT32 or FP32
        # returns zeros on the lower 16 bits of each datum. This handles the FP32 case.
        upper = self.read_regfile_data(regfile, df)
        # First, read the upper 16 bits of each value.
        # Half of the values read are zeros, shave them off.
        upper = upper[0:256] + upper[512:768] + upper[1024:1280] + upper[1536:1792]

        # Expose the lower 16 bits in place of the upper. This clobbers dest.
        self._shift_dst_low_halves_up()

        # Read the lower 16 bits from the upper bits' position.
        # Prune the zeros again, same as previously.
        lower = self.read_regfile_data(regfile, df)
        lower = lower[0:256] + lower[512:768] + lower[1024:1280] + lower[1536:1792]
        WARN("The previous contents of DSTACC have been lost and should not be relied upon.")
        return upper + lower
