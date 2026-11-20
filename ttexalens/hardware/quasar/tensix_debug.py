# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from collections.abc import Generator
from contextlib import contextmanager

from ttexalens.debug_tensix import REGFILE, TensixDebug, convert_regfile
from ttexalens.exceptions import TTException
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug, BabyRiscDebugHardware
from ttexalens.hardware.quasar.tensix_data_formats import QuasarRiscDestFormat
from ttexalens.pack_unpack_regfile import TensixDataFormat


class QuasarTensixDebug(TensixDebug):
    def _direct_dest_format(self, df: TensixDataFormat) -> TensixDataFormat:
        if df == TensixDataFormat.Int8:
            return TensixDataFormat.CompactInt8
        if df == TensixDataFormat.UInt8:
            return TensixDataFormat.CompactUInt8
        return df

    def _direct_dest_datum_size(self, df: TensixDataFormat) -> int:
        # 8-bit integers are stored in 16-bit dest.
        return 2 if self._is_8_bit_int_format(df) else 4

    @contextmanager
    def _dest_int8_view(self, df: TensixDataFormat) -> Generator[tuple[int, BabyRiscDebugHardware], None, None]:
        # The INT8 view maps each datum to its own byte address and returns it in every byte of the word,
        # so each datum takes one debug access at its exact address.
        assert self.dest is not None and self.dest.address.private_address is not None
        assert isinstance(self.risc_debug, BabyRiscDebug) and self.risc_debug.debug_hardware is not None
        prefix = f"RISC_DEST_ACCESS_CTRL_SEC{self.risc_debug.risc_info.risc_id}"
        fields = {
            f"{prefix}_fmt": QuasarRiscDestFormat.INT8.value,
            f"{prefix}_unsigned_int": int(df == TensixDataFormat.UInt8),
            f"{prefix}_no_swizzle": 0,
        }
        with self.risc_debug.ensure_private_memory_access():
            saved = {name: self.register_store.read_register(name) for name in fields}
            changed = [name for name, value in fields.items() if saved[name] != value]
            try:
                for name in changed:
                    self.register_store.write_register(name, fields[name])
                yield self.dest.address.private_address, self.risc_debug.debug_hardware
            finally:
                for name in changed:
                    self.register_store.write_register(name, saved[name])

    def _read_dest(self, df: TensixDataFormat, num_data: int) -> list[int]:
        if not self._is_8_bit_int_format(df):
            return super()._read_dest(df, num_data)
        with self._dest_int8_view(df) as (address, debug_hardware):
            return [debug_hardware.read_memory(address + i) & 0xFF for i in range(num_data)]

    def _write_dest(self, data: list[int], df: TensixDataFormat) -> None:
        if not self._is_8_bit_int_format(df):
            super()._write_dest(data, df)
            return
        with self._dest_int8_view(df) as (address, debug_hardware):
            for i, value in enumerate(data):
                debug_hardware.write_memory(address + i, value)

    def read_regfile_data(
        self, regfile: int | str | REGFILE, df: TensixDataFormat, num_tiles: int | None = None
    ) -> list[int]:
        if not self._direct_dest_access_enabled(df, convert_regfile(regfile)):
            raise TTException("Only DSTACC can be read on Quasar.")
        return super().read_regfile_data(regfile, df, num_tiles)

    def _read_dest_data_format(self) -> TensixDataFormat:
        # Quasar LLK leaves ALU_FORMAT_SPEC_REG2_Dstacc at 0 and selects 32-bit and Int32 dest with these bits.
        if self.register_store.read_register("ALU_ACC_CTRL_Fp32_enabled"):
            if self.register_store.read_register("ALU_ACC_CTRL_INT8_math_enabled"):
                return TensixDataFormat.Int32
            return TensixDataFormat.Float32
        # For 16-bit dest, the SrcA format is the only configuration that says what dest holds.
        df = self._decode_data_format(self.register_store.read_register("ALU_FORMAT_SPEC_REG_SrcA_val"))
        if not self._is_8_bit_int_format(df):
            raise TTException(
                f"Only 32-bit dest and 8-bit integers can be read on Quasar, but dest is 16-bit with SrcA format {df.name}."
            )
        return df

    def _write_dest_data_format(self, df: TensixDataFormat) -> None:
        if self._is_8_bit_int_format(df):
            self.register_store.write_register("ALU_ACC_CTRL_Fp32_enabled", 0)
            self.register_store.write_register("ALU_ACC_CTRL_INT8_math_enabled", 0)
            self.register_store.write_register("ALU_FORMAT_SPEC_REG_SrcA_val", self._encode_data_format(df))
            return
        self.register_store.write_register("ALU_ACC_CTRL_Fp32_enabled", 1)
        self.register_store.write_register(
            "ALU_ACC_CTRL_INT8_math_enabled", int(df in (TensixDataFormat.Int32, TensixDataFormat.UInt32))
        )
