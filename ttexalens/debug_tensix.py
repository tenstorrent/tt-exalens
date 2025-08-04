# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from enum import Enum
import struct

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.hardware.blackhole.functional_worker_block import BlackholeFunctionalWorkerBlock
from ttexalens.hw.tensix.wormhole.wormhole import WormholeDevice
from ttexalens.hw.tensix.blackhole.blackhole import BlackholeDevice
from ttexalens.register_store import RegisterDescription
from ttexalens.tt_exalens_lib import check_context, validate_device_id
from ttexalens.util import WARN, TTException
from ttexalens.device import Device
from ttexalens.unpack_regfile import unpack_data, TensixDataFormat


def validate_thread_id(thread_id: int) -> None:
    if thread_id not in [0, 1, 2]:
        raise TTException(f"Invalid thread_id {thread_id}.")


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
    except:
        pass
    raise TTException(f"Invalid regfile {regfile}.")


class TensixDebug:
    trisc_id: int
    core_loc: OnChipCoordinate
    device_id: int
    context: Context
    device: Device

    def __init__(
        self,
        core_loc: str | OnChipCoordinate,
        device_id: int,
        context: Context = None,
    ) -> None:
        self.context = check_context(context)
        validate_device_id(device_id, self.context)
        self.device_id = device_id
        self.device = self.context.devices[self.device_id]
        self.noc_block = self.device.get_block(core_loc)
        self.register_store = self.noc_block.get_register_store()
        if not isinstance(core_loc, OnChipCoordinate):
            self.core_loc = OnChipCoordinate.create(core_loc, device=self.device)
        else:
            self.core_loc = core_loc

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
        validate_thread_id(thread_id)
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
                thread_id (int): Tensix thread ID (0-2).
        """
        validate_thread_id(thread_id)
        if isinstance(instruction, int):
            instruction_bytes = instruction.to_bytes(4, byteorder="little")
        else:
            instruction_bytes = instruction
        validate_instruction(instruction_bytes)
        self._start_insn_push(thread_id)
        self._insn_push(instruction_bytes, thread_id)
        self._end_insn_push(thread_id)

    def read_tensix_register(self, register: str | RegisterDescription) -> int:
        """Reads the value of a configuration or debug register from the tensix core.

        Args:
                register (str | TensixRegisterDescription): Name of the configuration or debug register or instance of ConfigurationRegisterDescription or DebugRegisterDescription.

        Returns:
                int: Value of the configuration or debug register specified.
        """
        return self.register_store.read_register(register)

    def write_tensix_register(self, register: str | RegisterDescription, value: int) -> None:
        """Writes value to the configuration or debug register on the tensix core.

        Args:
                register (str | RegisterDescription): Name of the configuration or debug register or instance of ConfigurationRegisterDescription or DebugRegisterDescription.
                val (int): Value to write
        """
        self.register_store.write_register(register, value)

    @staticmethod
    def _validate_number_of_tiles(num_tiles: int | None) -> int:
        max_num_tiles = 8  # maximum number of tiles in dest for 32 bit formats
        if num_tiles is None or num_tiles > max_num_tiles or num_tiles <= 0:
            WARN(
                f"Number of tiles given {num_tiles} is not valid, defaulting to maximum number of tiles {max_num_tiles}"
            )
            return max_num_tiles

        return num_tiles

    @staticmethod
    def _is_32_bit_format(df: TensixDataFormat) -> bool:
        return df in (TensixDataFormat.Float32, TensixDataFormat.Int32)

    def _direct_dest_read_enabled(self, df: TensixDataFormat) -> bool:
        return type(self.device) == BlackholeDevice and self._is_32_bit_format(df)

    def direct_dest_read(self, df: TensixDataFormat, num_tiles: int) -> list[int] | list[float]:
        if not self._direct_dest_read_enabled(df):
            raise TTException("Direct dest reading not supported for this architecture or data format.")

        data: list[int] | list[float] = []
        # Using TRISC0 debug hardware to read memory
        risc_debug = self.noc_block.get_risc_debug(risc_name="trisc0")
        for i in range(num_tiles * TILE_SIZE):
            if isinstance(self.noc_block, BlackholeFunctionalWorkerBlock):
                address = self.noc_block.dest_start_address.private_address + 4 * i
            with risc_debug.ensure_halted():
                rd_data = risc_debug.read_memory(address)
            # Interpreting data as float32
            if df == TensixDataFormat.Float32:
                rd_data = struct.unpack(">f", rd_data.to_bytes(4, "big"))[0]

            data.append(rd_data)

        return data

    def read_regfile_data(
        self, regfile: int | str | REGFILE, df: TensixDataFormat, num_tiles: int | None = None
    ) -> list[int] | list[float]:
        """Dumps SRCA/DSTACC register file from the specified core.
            Due to the architecture of SRCA, you can see only see last two faces written.
            SRCB is currently not supported.

        Args:
                regfile (int | str | REGFILE): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).

        Returns:
                list[int | float]: 64x32 bytes of register file data (64 rows, 32 bytes per row). Also returns num_tiles * TILE_SIZE of unpacked data if using direct dest reading.
        """
        thread_id = 2
        regfile = convert_regfile(regfile)

        if regfile == REGFILE.SRCB:
            raise TTException("SRCB is currently not supported.")

        ops = self.device.instructions
        if self.device._arch != "wormhole_b0" and self.device._arch != "blackhole":
            raise TTException("Not supported for this architecture: ")

        # Directly reading dest does not require complex unpacking so we return it right away
        if regfile == REGFILE.DSTACC and self._direct_dest_read_enabled(df):
            num_tiles = self._validate_number_of_tiles(num_tiles)
            return self.direct_dest_read(df, num_tiles)
        else:
            self.register_store.write_register("RISCV_DEBUG_REG_DBG_ARRAY_RD_EN", 1)
            data: list[int] = []
            for row in range(64):
                row_addr = row if regfile != REGFILE.SRCA else 0
                regfile_id = 2 if regfile == REGFILE.SRCA else regfile.value

                if regfile == REGFILE.SRCA:
                    self.inject_instruction(ops.TT_OP_SFPLOAD(3, 0, 0, 0), thread_id)
                    self.inject_instruction(ops.TT_OP_SFPLOAD(3, 0, 0, 2), thread_id)
                    self.inject_instruction(ops.TT_OP_STALLWAIT(0x40, 0x4000), thread_id)
                    self.inject_instruction(ops.TT_OP_MOVDBGA2D(0, row & 0xF, 0, 0, 0), thread_id)
                elif regfile == REGFILE.SRCB:
                    self.inject_instruction(ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF), thread_id)
                    self.inject_instruction(ops.TT_OP_SETDVALID(0b10), thread_id)
                    self.inject_instruction(ops.TT_OP_CLEARDVALID(0b10, 0), thread_id)
                    self.inject_instruction(ops.TT_OP_SETDVALID(0b10), thread_id)
                    self.inject_instruction(ops.TT_OP_SHIFTXB(7, 0, row_addr), thread_id)
                    self.inject_instruction(ops.TT_OP_CLEARDVALID(0b10, 0), thread_id)

                for i in range(8):
                    dbg_array_rd_cmd = (row_addr) + (i << 12) + (regfile_id << 16)
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

    def read_regfile(
        self, regfile: int | str | REGFILE, num_tiles: int | None = None
    ) -> list[int] | list[float] | list[str]:
        """Dumps SRCA/DSTACC register file from the specified core, and parses the data into a list of values.
        Dumping DSTACC on Wormhole as FP32 clobbers the register.

        Args:
                regfile (int | str | REGFILE): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).
                num_tiles (int | None): Number of tiles to print. Only available for direct dest read on blackhole. Default: None
        Returns:
                list[int | float | str]: 64x(8/16) values in register file (64 rows, 8 or 16 values per row, depending on the format of the data) or num_tiles * TILE_SIZE for direct read.
        """
        regfile = convert_regfile(regfile)
        df = TensixDataFormat(self.read_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc"))

        if regfile == REGFILE.DSTACC and not self._direct_dest_read_enabled(df) and num_tiles is not None:
            WARN("num_tiles argument only has effect for 32 bit formats on blackhole.")

        # Workaround for an architectural quirk of Wormhole: reading DST as INT32 or FP32
        # returns zeros on the lower 16 bits of each datum. This handles the FP32 case.
        if regfile == REGFILE.DSTACC and df == TensixDataFormat.Float32 and type(self.device) == WormholeDevice:
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
        try:
            if regfile == REGFILE.DSTACC and self._direct_dest_read_enabled(df):
                # If we use dircet read data is already unpacked
                return data
            else:
                return unpack_data(data, df)
        except ValueError as e:
            # If the data format is unsupported, return the raw data.
            WARN(e)
            if isinstance(data, list) and all(isinstance(d, int) for d in data):
                WARN("Printing raw data...")
                return [hex(datum) for datum in data]
            else:
                raise TTException("Stopping execution, unsupported data format encountered.")
