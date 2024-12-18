# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from typing import Union

from ttlens.tt_coordinate import OnChipCoordinate
from ttlens.tt_lens_context import Context
from ttlens.tt_lens_lib import check_context, validate_device_id, read_word_from_device, write_words_to_device
from ttlens.tt_util import TTException
from ttlens.tt_device import Device


def validate_trisc_id(trisc_id: int, context: Context) -> None:
    if trisc_id not in [0, 1, 2]:
        raise TTException(f"Invalid trisc_id {trisc_id}.")


def validate_instruction(instruction: bytearray, context: Context) -> None:
    if len(bytearray(instruction)) != 4:
        raise TTException("Instruction must be 4 bytes long.")


REGFILE_SRCA = 0
REGFILE_SRCB = 1
REGFILE_DSTACC = 2


def validate_regfile_id(regfile_id: int, context: Context) -> None:
    if regfile_id not in [REGFILE_SRCA, REGFILE_SRCB, REGFILE_DSTACC]:
        raise TTException(f"Invalid regfile_id {regfile_id}.")


class TensixDebug:
    trisc_id: int
    core_loc: OnChipCoordinate
    device_id: int
    context: Context
    device: Device

    def __init__(
        self,
        core_loc: Union[str, OnChipCoordinate],
        device_id: int,
        context: Context = None,
    ) -> None:
        if not isinstance(core_loc, OnChipCoordinate):
            self.core_loc = OnChipCoordinate.create(core_loc, device=context.devices[self.device_id])
        else:
            self.core_loc = core_loc
        self.context = check_context(context)
        validate_device_id(device_id, self.context)
        self.device_id = device_id
        self.device = self.context.devices[self.device_id]

    def dbg_buff_status(self):
        return read_word_from_device(
            self.core_loc,
            self.device.get_tensix_register_address("RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS"),
            self.device_id,
            self.context,
        )

    def inject_instruction(
        self,
        instruction: Union[bytearray, int],
        trisc_id: int,
    ) -> None:
        """Injects instruction into Tensix pipe for TRISC specified by trisc_id.

        Args:
                instruction (bytearray): 32-bit instruction to inject.
                trisc_id (int): TRISC ID (0-2).
                core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format or OnChipCoordinate object.
                device_id (int): ID number of device to send message to.
                context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.
        """
        validate_trisc_id(trisc_id, self.context)

        if isinstance(instruction, int):
            instruction = instruction.to_bytes(4, byteorder="little")
        validate_instruction(instruction, self.context)

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
            int.from_bytes(instruction, byteorder="little"),
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

    def read_cfg_reg(self, name):
        device = self.context.devices[self.device_id]
        register = device.get_tensix_register_description(name)

        write_words_to_device(
            self.core_loc,
            device.get_tensix_register_address("RISCV_DEBUG_REG_CFGREG_RD_CNTL"),
            (register.address - device.get_tensix_configuration_register_base()) // 4,
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

    def read_regfile(
        self,
        regfile_id: int,
    ) -> bytearray:
        """Dumps SRCA/DSTACC register file from the specified core.
            Due to the architecture of SRCA, you can see only see last two faces written.
            SRCB is currently not supported.

        Args:
                regfile_id (int): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).
                core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format or OnChipCoordinate object.
                device_id (int): ID number of device to send message to.
                context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.

        Returns:
                bytearray: 64x32 bytes of register file data (64 rows, 32 bytes per row).
        """
        trisc_id = 2
        validate_regfile_id(regfile_id, self.context)
        if regfile_id == REGFILE_SRCB:
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
            row_addr = row if regfile_id != REGFILE_SRCA else 0
            regfile = 2 if regfile_id == REGFILE_SRCA else regfile_id

            if regfile_id == REGFILE_SRCA:
                # self.inject_instruction(ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0xf), trisc_id)
                self.inject_instruction(ops.TT_OP_SFPLOAD(3, 0, 0, 0), trisc_id)
                self.inject_instruction(ops.TT_OP_SFPLOAD(3, 0, 0, 2), trisc_id)

                self.inject_instruction(ops.TT_OP_STALLWAIT(0x40, 0x4000), trisc_id)

                # self.inject_instruction(ops.TT_OP_CLEARDVALID(0b01, 0), trisc_id)
                self.inject_instruction(ops.TT_OP_MOVDBGA2D(0, row & 0xF, 0, 0, 0), trisc_id)
            elif regfile_id == REGFILE_SRCB:
                self.inject_instruction(ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF), trisc_id)

                self.inject_instruction(ops.TT_OP_SETDVALID(0b10), trisc_id)
                self.inject_instruction(ops.TT_OP_CLEARDVALID(0b10, 0), trisc_id)

                self.inject_instruction(ops.TT_OP_SETDVALID(0b10), trisc_id)
                self.inject_instruction(ops.TT_OP_SHIFTXB(7, 0, row_addr), trisc_id)
                self.inject_instruction(ops.TT_OP_CLEARDVALID(0b10, 0), trisc_id)

            for i in range(8):
                dbg_array_rd_cmd = (row_addr) + (i << 12) + (regfile << 16)
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

            if regfile_id == REGFILE_SRCA:
                self.inject_instruction(ops.TT_OP_SFPSTORE(3, 0, 0, 0), trisc_id)
                self.inject_instruction(ops.TT_OP_SFPSTORE(3, 0, 0, 2), trisc_id)
                # self.inject_instruction(ops.TT_OP_CLEARDVALID(0b01, 0), trisc_id)
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
