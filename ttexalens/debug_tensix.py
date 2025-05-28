# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from typing import List
from enum import Enum

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.tt_exalens_lib import check_context, validate_device_id, read_word_from_device, write_words_to_device
from ttexalens.util import TTException
from ttexalens.device import Device, ConfigurationRegisterDescription, TensixRegisterDescription
from ttexalens.unpack_regfile import unpack_data
from ttexalens.debug_risc import RiscDebug, RiscLoc, RiscLoader


def validate_trisc_id(trisc_id: int, context: Context) -> None:
    if trisc_id not in [0, 1, 2]:
        raise TTException(f"Invalid trisc_id {trisc_id}.")


def validate_instruction(instruction: bytearray | bytes, context: Context) -> None:
    if len(bytearray(instruction)) != 4:
        raise TTException("Instruction must be 4 bytes long.")


class REGFILE(Enum):
    SRCA = 0
    SRCB = 1
    DSTACC = 2


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
        if not isinstance(core_loc, OnChipCoordinate):
            self.core_loc = OnChipCoordinate.create(core_loc, device=self.device)
        else:
            self.core_loc = core_loc

    def dbg_buff_status(self):
        return read_word_from_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS"),
            self.device_id,
            self.context,
        )

    def inject_instruction(
        self,
        instruction: bytes | bytearray | int,
        trisc_id: int,
    ) -> None:
        """Injects instruction into Tensix pipe for TRISC specified by trisc_id.

        Args:
                instruction (bytearray): 32-bit instruction to inject.
                trisc_id (int): TRISC ID (0-2).
        """
        validate_trisc_id(trisc_id, self.context)

        if isinstance(instruction, int):
            instruction_bytes = instruction.to_bytes(4, byteorder="little")
        else:
            instruction_bytes = instruction
        validate_instruction(instruction_bytes, self.context)

        # 1. Wait for buffer ready signal (poll bit 0 of DBG_INSTRN_BUF_STATUS until it’s 1)
        while (self.dbg_buff_status() & 1) == 0:
            pass

        write_words_to_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0"),
            0x07,
            self.device_id,
            self.context,
        )

        # 2. Assemble 32-bit instruction and write it to DBG_INSTRN_BUF_CTRL1
        write_words_to_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL1"),
            int.from_bytes(instruction_bytes, byteorder="little"),
            self.device_id,
            self.context,
        )

        # 3. Set bit 0(trigger) and bit 4 (override en) to 1 in DBG_INSTRN_BUF_CTRL0 to inject instruction.
        write_words_to_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0"),
            0x7 | (0x10 << trisc_id),
            self.device_id,
            self.context,
        )

        # 4. Clear DBG_INSTRN_BUF_CTRL0 register
        write_words_to_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0"),
            0x07,
            self.device_id,
            self.context,
        )
        write_words_to_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0"),
            0x00,
            self.device_id,
            self.context,
        )

        # 5. Wait for buffer empty signal to make sure instruction completed (poll bit 4 of DBG_INSTRN_BUF_STATUS until it’s 1)
        while (self.dbg_buff_status() & 0x10) == 0:
            pass

    def read_tensix_register(self, register: str | TensixRegisterDescription) -> int:
        """Reads the value of a configuration or debug register from the tensix core.

        Args:
                register (str | TensixRegisterDescription): Name of the configuration or debug register or instance of ConfigurationRegisterDescription or DebugRegisterDescription.

        Returns:
                int: Value of the configuration or debug register specified.
        """
        device = self.context.devices[self.device_id]

        if isinstance(register, str):
            register = device.get_tensix_register_description(register)

        if isinstance(register, ConfigurationRegisterDescription):
            max_index = int(
                (
                    device._get_tensix_register_end_address(register)
                    - device._get_tensix_register_base_address(register)
                    + 1
                )
                / 4
                - 1
            )
            if register.index < 0 or register.index > max_index:
                raise ValueError(
                    f"Register index must be positive and less than or equal to {max_index}, but got {register.index}"
                )
        assert isinstance(register, TensixRegisterDescription)
        if register.mask < 0 or register.mask > 0xFFFFFFFF:
            raise ValueError(f"Invalid mask value {register.mask}. Mask must be between 0 and 0xFFFFFFFF.")

        if register.shift < 0 or register.shift > 31:
            raise ValueError(f"Invalid shift value {register.shift}. Shift must be between 0 and 31.")

        if isinstance(register, ConfigurationRegisterDescription):
            write_words_to_device(
                self.core_loc,
                device.get_tensix_register_address("RISCV_DEBUG_REG_CFGREG_RD_CNTL"),
                register.index,
                self.device_id,
                self.context,
            )
            a = read_word_from_device(
                self.core_loc,
                device.get_tensix_register_address("RISCV_DEBUG_REG_CFGREG_RDDATA"),
                self.device_id,
                self.context,
            )
            return (a & register.mask) >> register.shift
        else:
            a = read_word_from_device(
                self.core_loc,
                register.address,
                self.device_id,
                self.context,
            )
            return (a & register.mask) >> register.shift

    def write_tensix_register(self, register: str | TensixRegisterDescription, value: int) -> None:
        """Writes value to the configuration or debug register on the tensix core.

        Args:
                register (str | TensixRegisterDescription): Name of the configuration or debug register or instance of ConfigurationRegisterDescription or DebugRegisterDescription.
                val (int): Value to write
        """
        device = self.context.devices[self.device_id]

        if isinstance(register, str):
            register = device.get_tensix_register_description(register)
        elif isinstance(register, ConfigurationRegisterDescription):
            base_address = device._get_tensix_register_base_address(register)
            if base_address != None:
                register = register.clone(base_address)
            else:
                raise ValueError(f"Unknown tensix register base address for given register")

        assert isinstance(register, TensixRegisterDescription)
        if value < 0 or value > 2 ** register.mask.bit_count() - 1:
            raise ValueError(f"Value must be between 0 and {2 ** register.mask.bit_count() - 1}, but got {value}")

        if isinstance(register, ConfigurationRegisterDescription):
            max_index = int(
                (
                    device._get_tensix_register_end_address(register)
                    - device._get_tensix_register_base_address(register)
                    + 1
                )
                / 4
                - 1
            )
            if register.index < 0 or register.index > max_index:
                raise ValueError(
                    f"Register index must be positive and less than or equal to {max_index}, but got {register.index}"
                )

        if register.mask < 0 or register.mask > 0xFFFFFFFF:
            raise ValueError(f"Invalid mask value {register.mask}. Mask must be between 0 and 0xFFFFFFFF.")

        if register.shift < 0 or register.shift > 31:
            raise ValueError(f"Invalid shift value {register.shift}. Shift must be between 0 and 31.")

        if isinstance(register, ConfigurationRegisterDescription):
            rdbg = RiscDebug(RiscLoc(self.core_loc), self.context)
            rldr = RiscLoader(rdbg, self.context)
            with rldr.ensure_reading_configuration_register() as rdbg:
                rdbg.write_configuration_register(register, value)
        else:
            write_words_to_device(
                self.core_loc,
                register.address,
                value,
                self.device_id,
                self.context,
            )

    def read_regfile_data(
        self,
        regfile: int | str | REGFILE,
    ) -> list[int]:
        """Dumps SRCA/DSTACC register file from the specified core.
            Due to the architecture of SRCA, you can see only see last two faces written.
            SRCB is currently not supported.

        Args:
                regfile (int | str | REGFILE): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).

        Returns:
                bytearray: 64x32 bytes of register file data (64 rows, 32 bytes per row).
        """
        trisc_id = 2
        regfile = convert_regfile(regfile)

        if regfile == REGFILE.SRCB:
            raise TTException("SRCB is currently not supported.")

        ops = self.device.instructions
        if self.device._arch != "wormhole_b0" and self.device._arch != "blackhole":
            raise TTException("Not supported for this architecture: ")

        write_words_to_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_ARRAY_RD_EN"),
            0x1,
            self.device_id,
            self.context,
        )
        data = []

        for row in range(64):
            row_addr = row if regfile != REGFILE.SRCA else 0
            regfile_id = 2 if regfile == REGFILE.SRCA else regfile.value

            if regfile == REGFILE.SRCA:
                self.inject_instruction(ops.TT_OP_SFPLOAD(3, 0, 0, 0), trisc_id)
                self.inject_instruction(ops.TT_OP_SFPLOAD(3, 0, 0, 2), trisc_id)

                self.inject_instruction(ops.TT_OP_STALLWAIT(0x40, 0x4000), trisc_id)

                self.inject_instruction(ops.TT_OP_MOVDBGA2D(0, row & 0xF, 0, 0, 0), trisc_id)
            elif regfile == REGFILE.SRCB:
                self.inject_instruction(ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF), trisc_id)

                self.inject_instruction(ops.TT_OP_SETDVALID(0b10), trisc_id)
                self.inject_instruction(ops.TT_OP_CLEARDVALID(0b10, 0), trisc_id)

                self.inject_instruction(ops.TT_OP_SETDVALID(0b10), trisc_id)
                self.inject_instruction(ops.TT_OP_SHIFTXB(7, 0, row_addr), trisc_id)
                self.inject_instruction(ops.TT_OP_CLEARDVALID(0b10, 0), trisc_id)

            for i in range(8):
                dbg_array_rd_cmd = (row_addr) + (i << 12) + (regfile_id << 16)
                write_words_to_device(
                    self.core_loc,
                    self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD"),
                    dbg_array_rd_cmd,
                    self.device_id,
                    self.context,
                )
                rd_data = read_word_from_device(
                    self.core_loc,
                    self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA"),
                    self.device_id,
                    self.context,
                )
                data += list(int.to_bytes(rd_data, 4, byteorder="big"))

            if regfile == REGFILE.SRCA:
                self.inject_instruction(ops.TT_OP_SFPSTORE(3, 0, 0, 0), trisc_id)
                self.inject_instruction(ops.TT_OP_SFPSTORE(3, 0, 0, 2), trisc_id)
                if row % 16 == 15:
                    self.inject_instruction(ops.TT_OP_SETRWC(3, 0, 0, 0, 0, 0xF), trisc_id)

        write_words_to_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_ARRAY_RD_EN"),
            0x0,
            self.device_id,
            self.context,
        )
        write_words_to_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD"),
            0x0,
            self.device_id,
            self.context,
        )
        return data

    def read_regfile(self, regfile: int | str | REGFILE) -> List[float | int]:
        """Dumps SRCA/DSTACC register file from the specified core, and parses the data into a list of values.

        Args:
                regfile (int | str | REGFILE): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).

        Returns:
                List[float | int]: 64x(8/16) values in register file (64 rows, 8 or 16 values per row, depending on the format of the data).
        """
        regfile = convert_regfile(regfile)
        data = self.read_regfile_data(regfile)
        df = self.read_tensix_register("ALU_FORMAT_SPEC_REG2_Dstacc")
        unpacked_data = unpack_data(data, df)
        return unpacked_data
