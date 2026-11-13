# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from enum import Enum

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.exceptions import TTException
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug, BabyRiscDebugHardware
from ttexalens.hardware.quasar.tensix_data_formats import QuasarRiscDestFormat
from ttexalens.util import WARN
from ttexalens.pack_unpack_regfile import (
    unpack_data,
    unpack_data_direct_access,
    pack_data_direct_access,
    TensixDataFormat,
)
from ttexalens.memory_access import create_memory_access


def validate_instruction(instruction: bytearray | bytes) -> None:
    if len(bytearray(instruction)) != 4:
        raise TTException("Instruction must be 4 bytes long.")


class REGFILE(Enum):
    SRCA = 0
    SRCB = 1
    DSTACC = 2


TILE_SIZE = 32 * 32


def convert_regfile(regfile: int | str | REGFILE) -> REGFILE:
    if isinstance(regfile, REGFILE):
        return regfile

    try:
        return REGFILE(int(regfile))
    except ValueError:
        pass

    try:
        if isinstance(regfile, str):
            return REGFILE[regfile.upper()]
    except KeyError:
        pass
    raise TTException(f"Invalid regfile {regfile}.")


class TensixDebug:
    def __init__(
        self,
        location: OnChipCoordinate,
        neo_id: int | None = None,
    ) -> None:
        self.location = location
        self.device = location.device
        self.noc_block = location.noc_block
        self.register_store = self.noc_block.get_register_store(neo_id=neo_id)
        self.thread_count = len(
            [risc for risc in self.noc_block.get_riscs(neo_id) if risc.risc_location.risc_name.startswith("trisc")]
        )

        # Using TRISC debug hardware to read/write memory
        # Use restricted_access=False because the Tensix dest is outside L1/data_private, but we still need to read/write it via TRISC debug hardware.
        # Quasar uses TRISC3 because LLK never programs its dest window
        risc_debug = self.noc_block.get_risc_debug("trisc3" if self.device.is_quasar() else "trisc0", neo_id)
        self.risc_debug = risc_debug
        self.mem_access = create_memory_access(risc_debug, restricted_access=False)
        dest = risc_debug.risc_info.memory_map.find_by_name("dest")
        self.dest = dest.memory_block if dest is not None else None

    def _validate_thread_id(self, thread_id: int) -> None:
        if not 0 <= thread_id < self.thread_count:
            raise TTException(f"Invalid thread_id {thread_id}.")

    def dbg_buff_status(self):
        return self.register_store.read_register("RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS")

    def _start_insn_push(self, thread_id: int) -> None:
        """Take control of thread_id's Tensix FIFO over the
        debug bus to prepare to push instructions into it."""
        # Relevant documentation:
        # https://github.com/tenstorrent/tt-isa-documentation/blob/ac3215a86ffa22a89b49df195a38338b66ab4dbc/WormholeB0/TensixTile/BabyRISCV/PushTensixInstruction.md

        # Wait for buffer ready signal (poll bit 0/1/2, depending on thread, of DBG_INSTRN_BUF_STATUS until it’s 1).
        while (self.register_store.read_register("RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS") & (1 << thread_id)) == 0:
            pass

        # Take control of thread n's FIFO through the debug bus by setting bit n of INSTRN_BUF_CTRL0.
        self.register_store.write_register("RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0", 1 << thread_id)

    def _insn_push(self, insn: bytes | bytearray, thread_id: int) -> None:
        """Push one Tensix instruction through the previously claimed FIFO.
        Each instruction pushed this way is guaranteed to be executed sequentially on the given thread.
        It is not recommended to push more than one instruction during a single FIFO claim."""
        # Check if the buffer is ready. This must be done before every instruction push.
        while (self.register_store.read_register("RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS") & (1 << thread_id)) == 0:
            pass

        # Write the insn to DBG_INSTRN_BUF_CTRL1.
        self.register_store.write_register(
            "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL1", int.from_bytes(insn, byteorder="little")
        )

        # Trigger the insn push: set the push bit in CTRL0 for this thread.
        push = 1 << (4 + thread_id)
        control = 1 << thread_id
        self.register_store.write_register("RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0", push | control)

        # Wait for the instruction to drain.
        while (
            self.register_store.read_register("RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS") & (1 << (4 + thread_id))
        ) == 0:
            pass

    def _end_insn_push(self, thread_id: int) -> None:
        """Relinquish control over thread_id's FIFO."""
        self._validate_thread_id(thread_id)
        self.register_store.write_register("RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0", 0)  # simply clear the register.

    def inject_instruction(
        self,
        instruction: bytes | bytearray | int,
        thread_id: int,
    ) -> None:
        """Inject a single instruction into the given Tensix thread.
        The instruction doesn't go through the baby RISCs, it's passed directly to Tensix.
        Thus, do not attempt to use this API to execute arbitrary RISC-V instructions.

        Args:
                instruction (bytearray): 32-bit instruction to inject.
                thread_id (int): Tensix thread ID (0 to thread_count - 1).
        """
        self._validate_thread_id(thread_id)
        if isinstance(instruction, int):
            instruction_bytes = instruction.to_bytes(4, byteorder="little")
        else:
            instruction_bytes = instruction
        validate_instruction(instruction_bytes)
        self._start_insn_push(thread_id)
        self._insn_push(instruction_bytes, thread_id)
        self._end_insn_push(thread_id)

    def _validate_number_of_tiles(self, num_tiles: int | None, df: TensixDataFormat) -> int:
        max_num_tiles = (
            self.dest.size // TILE_SIZE // self._direct_dest_datum_size(df) if self.dest is not None else None
        )
        if num_tiles is None or (max_num_tiles is not None and num_tiles > max_num_tiles) or num_tiles <= 0:
            WARN(
                f"Number of tiles given {num_tiles} is not valid, defaulting to maximum number of tiles {max_num_tiles}"
            )
            assert max_num_tiles is not None
            return max_num_tiles

        return num_tiles

    @staticmethod
    def _is_32_bit_format(df: TensixDataFormat) -> bool:
        return df in (TensixDataFormat.Float32, TensixDataFormat.Int32, TensixDataFormat.UInt32)

    @staticmethod
    def _is_8_bit_int_format(df: TensixDataFormat) -> bool:
        return df in (TensixDataFormat.Int8, TensixDataFormat.UInt8)

    def _uses_int8_view(self, df: TensixDataFormat) -> bool:
        return self.device.is_quasar() and self._is_8_bit_int_format(df)

    def _direct_dest_datum_size(self, df: TensixDataFormat) -> int:
        # Direct access reads 32-bit words; Quasar's INT8 view reads 8-bit integers stored in 16-bit dest.
        return 2 if self._uses_int8_view(df) else 4

    def _direct_dest_access_enabled(self, df: TensixDataFormat, regfile: REGFILE) -> bool:
        # Blackhole stores 8-bit integers in 32-bit dest, Quasar reads them through the dest window's INT8 view.
        return (
            regfile == REGFILE.DSTACC
            and self.dest is not None
            and (self._is_32_bit_format(df) or self._is_8_bit_int_format(df))
        )

    @contextmanager
    def _dest_int8_view(self, df: TensixDataFormat) -> Generator[tuple[int, BabyRiscDebugHardware], None, None]:
        # The INT8 view maps each datum to its own byte address and returns it in every byte of the word,
        # so each datum takes one debug access at its exact address.
        assert self.dest is not None and self.dest.address.private_address is not None
        assert isinstance(self.risc_debug, BabyRiscDebug) and self.risc_debug.debug_hardware is not None
        fields = {
            "RISC_DEST_ACCESS_CTRL_SEC3_fmt": QuasarRiscDestFormat.INT8.value,
            "RISC_DEST_ACCESS_CTRL_SEC3_unsigned_int": int(df == TensixDataFormat.UInt8),
            "RISC_DEST_ACCESS_CTRL_SEC3_no_swizzle": 0,
        }
        saved = {name: self.register_store.read_register(name) for name in fields}
        changed = [name for name, value in fields.items() if saved[name] != value]
        for name in changed:
            self.register_store.write_register(name, fields[name])
        try:
            with self.risc_debug.ensure_private_memory_access():
                yield self.dest.address.private_address, self.risc_debug.debug_hardware
        finally:
            for name in changed:
                self.register_store.write_register(name, saved[name])

    def direct_dest_read(self, df: TensixDataFormat, num_tiles: int) -> list[int]:
        data: list[int] = []
        if self.dest is None:
            raise TTException("Direct dest reading not supported for this architecture.")

        base_address = self.dest.address.private_address
        dest_size = self.dest.size
        assert base_address is not None
        size_bytes = num_tiles * TILE_SIZE * self._direct_dest_datum_size(df)
        if size_bytes > dest_size:
            raise TTException(f"Size {size_bytes} bytes is out of bounds for destination memory block.")
        if self._uses_int8_view(df):
            with self._dest_int8_view(df) as (int8_base_address, debug_hardware):
                return [debug_hardware.read_memory(int8_base_address + i) & 0xFF for i in range(num_tiles * TILE_SIZE)]

        bytes_data = bytearray(size_bytes)
        self.mem_access.read(base_address, bytes_data)
        data.extend(int.from_bytes(bytes_data[i : i + 4], byteorder="little") for i in range(0, size_bytes, 4))

        return data

    def direct_dest_write(self, data: list[int], df: TensixDataFormat) -> None:
        if self.dest is None:
            raise TTException("Direct dest writing not supported for this architecture.")
        dest_size = self.dest.size
        size_bytes = len(data) * self._direct_dest_datum_size(df)
        if size_bytes > dest_size:
            raise TTException(f"Data is to large to be written in destination memory block.")
        if self._uses_int8_view(df):
            with self._dest_int8_view(df) as (int8_base_address, debug_hardware):
                for i, value in enumerate(data):
                    debug_hardware.write_memory(int8_base_address + i, value)
            return
        base_address = self.dest.address.private_address
        assert base_address is not None
        bytes_data = b"".join(word.to_bytes(4, byteorder="little") for word in data)

        self.mem_access.write(base_address, bytes_data)

    def read_regfile_data(
        self, regfile: int | str | REGFILE, df: TensixDataFormat, num_tiles: int | None = None
    ) -> list[int]:
        """Dumps SRCA/DSTACC register file from the specified core.
            Due to the architecture of SRCA, you can see only see last two faces written.
            SRCB is currently not supported.

        Args:
                regfile (int | str | REGFILE): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).

        Returns:
                list[int]:  Returns num_tiles * TILE_SIZE of data if using direct dest reading or list of int values containing bytes if using non-direct reading.
        """
        thread_id = 2
        regfile = convert_regfile(regfile)

        if regfile == REGFILE.SRCB:
            raise TTException("SRCB is currently not supported.")

        # Directly reading dest does not require complex unpacking so we return it right away
        if self._direct_dest_access_enabled(df, regfile):
            num_tiles = self._validate_number_of_tiles(num_tiles, df)
            return self.direct_dest_read(df, num_tiles)

        if not self.device.is_wormhole() and not self.device.is_blackhole():
            raise TTException("Not supported for this architecture: ")
        ops = self.device.instructions

        data: list[int] = []
        self.register_store.write_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_EN", 1)
        for row in range(64):
            row_addr = row if regfile != REGFILE.SRCA else 0
            regfile_id = 2 if regfile == REGFILE.SRCA else regfile.value

            if regfile == REGFILE.SRCA:
                self.inject_instruction(ops.TT_OP_SFPLOAD(3, 0, 0, 0), thread_id)
                self.inject_instruction(ops.TT_OP_SFPLOAD(3, 0, 0, 2), thread_id)
                self.inject_instruction(ops.TT_OP_STALLWAIT(0x40, 0x4000), thread_id)
                self.inject_instruction(ops.TT_OP_MOVDBGA2D(0, row & 0xF, 0, 0, 0), thread_id)
            # elif regfile == REGFILE.SRCB:
            #     self.inject_instruction(ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF), thread_id)
            #     self.inject_instruction(ops.TT_OP_SETDVALID(0b10), thread_id)
            #     self.inject_instruction(ops.TT_OP_CLEARDVALID(0b10, 0), thread_id)
            #     self.inject_instruction(ops.TT_OP_SETDVALID(0b10), thread_id)
            #     self.inject_instruction(ops.TT_OP_SHIFTXB(7, 0, row_addr), thread_id)
            #     self.inject_instruction(ops.TT_OP_CLEARDVALID(0b10, 0), thread_id)

            base_cmd = row_addr + (regfile_id << 16)
            for i in range(8):
                dbg_array_rd_cmd = base_cmd + (i << 12)
                self.register_store.write_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD", dbg_array_rd_cmd)
                rd_data = self.register_store.read_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA")
                data += list(int.to_bytes(rd_data, 4, byteorder="big"))

            if regfile == REGFILE.SRCA:
                self.inject_instruction(ops.TT_OP_SFPSTORE(3, 0, 0, 0), thread_id)
                self.inject_instruction(ops.TT_OP_SFPSTORE(3, 0, 0, 2), thread_id)
                if row % 16 == 15:
                    self.inject_instruction(ops.TT_OP_SETRWC(3, 0, 0, 0, 0, 0xF), thread_id)

        self.register_store.write_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_EN", 0)
        self.register_store.write_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD", 0)

        return data

    def _decode_data_format(self, value: int) -> TensixDataFormat:
        data_format = self.device.get_data_format_type()(value)
        if data_format.name not in TensixDataFormat.__members__:
            raise TTException(f"Data format {data_format.name} is not supported.")
        return TensixDataFormat[data_format.name]

    def _encode_data_format(self, df: TensixDataFormat) -> int:
        return int(self.device.get_data_format_type()[df.name].value)

    def _read_dest_data_format(self) -> TensixDataFormat:
        if not self.device.is_quasar():
            return self._decode_data_format(self.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc"))
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
        if not self.device.is_quasar():
            # Workaround because we can't write UInt32 or UInt8 data format to alu register
            # Alu register is 4 bit long so it does not support formats which values exceed 15, which both UInt32 and UInt8 do.
            if df == TensixDataFormat.UInt32:
                df = TensixDataFormat.Int32
            elif df == TensixDataFormat.UInt8:
                df = TensixDataFormat.Int8
            self.register_store.write_register("ALU_FORMAT_SPEC_REG2_Dstacc", self._encode_data_format(df))
            return
        if self._is_8_bit_int_format(df):
            self.register_store.write_register("ALU_ACC_CTRL_Fp32_enabled", 0)
            self.register_store.write_register("ALU_ACC_CTRL_INT8_math_enabled", 0)
            self.register_store.write_register("ALU_FORMAT_SPEC_REG_SrcA_val", self._encode_data_format(df))
            return
        self.register_store.write_register("ALU_ACC_CTRL_Fp32_enabled", 1)
        self.register_store.write_register(
            "ALU_ACC_CTRL_INT8_math_enabled", int(df in (TensixDataFormat.Int32, TensixDataFormat.UInt32))
        )

    def read_regfile(
        self, regfile: int | str | REGFILE, num_tiles: int | None = None, signed: bool = True
    ) -> Sequence[int | float | str]:
        """Dumps SRCA/DSTACC register file from the specified core, and parses the data into a list of values.
        Dumping DSTACC on Wormhole as FP32 clobbers the register.
        On Quasar only DSTACC can be read, through TRISC3 of the NEO, which is halted during the read.

        Args:
                regfile (int | str | REGFILE): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).
                num_tiles (int | None): Number of tiles to print. Only available for direct dest read on blackhole and for dest on quasar. Default: None
        Returns:
                list[int | float | str]: 64x(8/16) values in register file (64 rows, 8 or 16 values per row, depending on the format of the data) or num_tiles * TILE_SIZE for direct read.
        """
        regfile = convert_regfile(regfile)
        df = self._read_dest_data_format()

        if not self._direct_dest_access_enabled(df, regfile) and num_tiles is not None:
            WARN("num_tiles argument only has effect for 32 bit formats on blackhole and for dest on quasar.")

        data: list[int] = []
        # Workaround for an architectural quirk of Wormhole: reading DST as INT32 or FP32
        # returns zeros on the lower 16 bits of each datum. This handles the FP32 case.
        if regfile == REGFILE.DSTACC and df == TensixDataFormat.Float32 and self.device.is_wormhole():
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
            data = upper + lower
            WARN("The previous contents of DSTACC have been lost and should not be relied upon.")
        else:
            data = self.read_regfile_data(regfile, df, num_tiles)
        if self._uses_int8_view(df):
            return [byte - 0x100 if signed and df == TensixDataFormat.Int8 and byte & 0x80 else byte for byte in data]
        try:
            return (
                unpack_data_direct_access(data, df, signed=signed)
                if self._direct_dest_access_enabled(df, regfile)
                else unpack_data(data, df, signed=signed)
            )
        except ValueError as e:
            # If the data format is unsupported, return the raw data.
            WARN(e)
            raw_data: list[str] = [hex(datum) for datum in data]
            return raw_data

    def write_regfile_data(self, regfile: REGFILE, data: list[int], df: TensixDataFormat) -> None:

        if not self._direct_dest_access_enabled(df, regfile):
            raise TTException("Direct dest writing not supported for this architecture or data format.")

        if regfile != REGFILE.DSTACC:
            raise TTException("Writing is only supported for dest register, but got {regfile}")

        self._write_dest_data_format(df)
        self.direct_dest_write(data, df)

    def write_regfile(self, regfile: int | str | REGFILE, data: list[int] | list[float], df: TensixDataFormat) -> None:
        """
        Writes data to the register file.
        Writing is only supported for dest register and only for Float32, Int32, UInt32, Int8 and UInt8.

        Args:
                regfile (int | str | REGFILE): Register file to write to (0: SRCA, 1: SRCB, 2: DSTACC).
                data (list[int | float]): Data to write.
                df (TensixDataFormat): Data format.
        """
        regfile = convert_regfile(regfile)
        packed_data = pack_data_direct_access(data, df, int8_view=self._uses_int8_view(df))
        self.write_regfile_data(regfile, packed_data, df)
