# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from enum import Enum

from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.exceptions import TTException
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

# SFPLOAD/SFPSTORE instr_mod0 values that move Dst data without value conversion.
SFP_MOD0_FMT_INT32 = 4
SFP_MOD0_FMT_UINT16 = 6


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
    def __init__(self, risc_debug: RiscDebug) -> None:
        self.location = risc_debug.risc_location.location
        self.device = self.location.device
        self.noc_block = self.location.noc_block
        self.register_store = self.noc_block.get_register_store(neo_id=risc_debug.risc_location.neo_id)
        self.thread_count = self.noc_block.tensix_thread_count

        # Using TRISC debug hardware to read/write memory
        # Use restricted_access=False because the Tensix dest is outside L1/data_private, but we still need to read/write it via TRISC debug hardware.
        self.risc_debug = risc_debug
        self.mem_access = create_memory_access(self.risc_debug, restricted_access=False)
        dest = self.risc_debug.risc_info.memory_map.find_by_name("dest")
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

    def _direct_dest_format(self, df: TensixDataFormat) -> TensixDataFormat:
        return df

    def _direct_dest_datum_size(self, df: TensixDataFormat) -> int:
        return 4

    @property
    def has_direct_dest_access(self) -> bool:
        return self.dest is not None

    def _direct_dest_access_enabled(self, df: TensixDataFormat, regfile: REGFILE) -> bool:
        return (
            regfile == REGFILE.DSTACC
            and self.has_direct_dest_access
            and (self._is_32_bit_format(df) or self._is_8_bit_int_format(df))
        )

    def direct_dest_read(self, df: TensixDataFormat, num_tiles: int) -> list[int]:
        if self.dest is None:
            raise TTException("Direct dest reading not supported for this architecture.")
        size_bytes = num_tiles * TILE_SIZE * self._direct_dest_datum_size(df)
        if size_bytes > self.dest.size:
            raise TTException(f"Size {size_bytes} bytes is out of bounds for destination memory block.")
        return self._read_dest(df, num_tiles * TILE_SIZE)

    def _read_dest(self, df: TensixDataFormat, num_data: int) -> list[int]:
        assert self.dest is not None and self.dest.address.private_address is not None
        bytes_data = bytearray(num_data * 4)
        self.mem_access.read(self.dest.address.private_address, bytes_data)
        return [int.from_bytes(bytes_data[i : i + 4], byteorder="little") for i in range(0, len(bytes_data), 4)]

    def direct_dest_write(self, data: list[int], df: TensixDataFormat) -> None:
        if self.dest is None:
            raise TTException("Direct dest writing not supported for this architecture.")
        size_bytes = len(data) * self._direct_dest_datum_size(df)
        if size_bytes > self.dest.size:
            raise TTException(f"Data is to large to be written in destination memory block.")
        self._write_dest(data, df)

    def _write_dest(self, data: list[int], df: TensixDataFormat) -> None:
        assert self.dest is not None and self.dest.address.private_address is not None
        bytes_data = b"".join(word.to_bytes(4, byteorder="little") for word in data)
        self.mem_access.write(self.dest.address.private_address, bytes_data)

    def read_regfile_data(
        self, regfile: int | str | REGFILE, df: TensixDataFormat, num_tiles: int | None = None
    ) -> list[int]:
        """Dumps SRCA/DSTACC register file from the specified core.
            Due to the architecture of SRCA, you can see only see last two faces written.
            SRCB is currently not supported.
            Dumping SRCA borrows DSTACC rows and SFPU LReg 3 and LReg 4; read_regfile lists what it changes.

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

        ops = self.device.instructions
        # SFPLOAD/SFPSTORE instr_mod0 = 0 converts the data and flushes denormals,
        # so save and restore Dst in a mode that copies the bits.
        sfp_mod0 = SFP_MOD0_FMT_UINT16
        if regfile == REGFILE.SRCA and self.register_store.read_register("ALU_ACC_CTRL_SFPU_Fp32_enabled"):
            sfp_mod0 = SFP_MOD0_FMT_INT32

        data: list[int] = []
        self.register_store.write_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_EN", 1)
        for row in range(64):
            row_addr = row if regfile != REGFILE.SRCA else 0
            regfile_id = 2 if regfile == REGFILE.SRCA else regfile.value

            if regfile == REGFILE.SRCA:
                # Dst rows 0-3 are saved in two LRegs: even columns in LReg 3, odd columns in LReg 4.
                self.inject_instruction(ops.TT_OP_SFPLOAD(3, sfp_mod0, 0, 0), thread_id)
                self.inject_instruction(ops.TT_OP_SFPLOAD(4, sfp_mod0, 0, 2), thread_id)
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
                self.inject_instruction(ops.TT_OP_SFPSTORE(3, sfp_mod0, 0, 0), thread_id)
                self.inject_instruction(ops.TT_OP_SFPSTORE(4, sfp_mod0, 0, 2), thread_id)
                if row % 16 == 15:
                    self.inject_instruction(ops.TT_OP_SETRWC(3, 0, 0, 0, 0, 0xF), thread_id)

        self.register_store.write_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_EN", 0)
        self.register_store.write_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD", 0)

        return data

    def _decode_data_format(self, value: int) -> TensixDataFormat:
        for df, encoding in self.device.get_tensix_data_formats().items():
            if encoding == value:
                return df
        raise TTException(f"Data format {value} is not supported.")

    def _encode_data_format(self, df: TensixDataFormat) -> int:
        data_formats = self.device.get_tensix_data_formats()
        if df not in data_formats:
            raise TTException(f"Data format {df.name} is not supported.")
        return data_formats[df]

    def _read_dest_data_format(self) -> TensixDataFormat:
        return self._decode_data_format(self.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc"))

    def _write_dest_data_format(self, df: TensixDataFormat) -> None:
        # Workaround because we can't write UInt32 or UInt8 data format to alu register
        # Alu register is 4 bit long so it does not support formats which values exceed 15, which both UInt32 and UInt8 do.
        if df == TensixDataFormat.UInt32:
            df = TensixDataFormat.Int32
        elif df == TensixDataFormat.UInt8:
            df = TensixDataFormat.Int8
        self.register_store.write_register("ALU_FORMAT_SPEC_REG2_Dstacc", self._encode_data_format(df))

    def _read_regfile_raw(self, regfile: REGFILE, df: TensixDataFormat, num_tiles: int | None) -> list[int]:
        return self.read_regfile_data(regfile, df, num_tiles)

    def read_regfile(
        self, regfile: int | str | REGFILE, num_tiles: int | None = None, signed: bool = True
    ) -> Sequence[int | float | str]:
        """Dumps SRCA/DSTACC register file from the specified core, and parses the data into a list of values.
        Dumping DSTACC on Wormhole as FP32 clobbers the register.
        On Quasar only DSTACC can be read, through TRISC3 of the NEO, which is halted during the read.
        Dumping SRCA uses SFPU LReg 3 and LReg 4 as scratch, resets the register window counters of Tensix thread 2
        and clears the SrcA and SrcB valid flags.
        It restores the DSTACC rows it borrows only when the Dst counters, base and address modes of that thread
        are at their defaults, all SFPU lanes are enabled, and the FPU and SFPU Dst widths are equal.
        If the data cannot be decoded in the Dst data format, a warning is printed and the raw data is returned
        as hex strings.

        Args:
                regfile (int | str | REGFILE): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).
                num_tiles (int | None): Number of tiles to print. Only available for direct dest read on blackhole and for dest on quasar. Default: None
        Returns:
                list[int | float | str]: 64x(8/16) values in register file (64 rows, 8 or 16 values per row, depending on the format of the data) or num_tiles * TILE_SIZE for direct read.
        """
        regfile = convert_regfile(regfile)
        unsupported: str | None = None
        try:
            df = self._read_dest_data_format()
        except TTException:
            # The Dst format field holds a value that is not a data format. Read the data anyway.
            df = TensixDataFormat.Invalid
            df_value = self.register_store.read_register("ALU_FORMAT_SPEC_REG2_Dstacc")
            unsupported = f"Unsupported data format {df_value} for unpacking."
        if regfile == REGFILE.SRCA and df == TensixDataFormat.Float32:
            unsupported = f"Unsupported data format {df.name} for unpacking {regfile.name}."

        if not self._direct_dest_access_enabled(df, regfile) and num_tiles is not None:
            WARN("num_tiles argument only has effect for 32 bit formats on blackhole and for dest on quasar.")

        data = self._read_regfile_raw(regfile, df, num_tiles)
        if unsupported is None:
            try:
                return (
                    unpack_data_direct_access(data, self._direct_dest_format(df), signed=signed)
                    if self._direct_dest_access_enabled(df, regfile)
                    else unpack_data(data, df, signed=signed)
                )
            except ValueError as e:
                unsupported = str(e)
        # If the data format is unsupported, return the raw data.
        WARN(unsupported)
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
        packed_data = pack_data_direct_access(data, self._direct_dest_format(df))
        self.write_regfile_data(regfile, packed_data, df)
