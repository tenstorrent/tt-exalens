# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import re
import struct

from typing import Union, List

from ttlens import tt_lens_init

from ttlens.tt_coordinate import OnChipCoordinate
from ttlens.tt_lens_context import Context
from ttlens.tt_util import TTException


def read_word_from_device(
    core_loc: Union[str, OnChipCoordinate], addr: int, device_id: int = 0, context: Context = None
) -> "int":
    """Reads one word of data, from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0):	ID number of device to read from.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
            int: Data read from the device.
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])
    if context.devices[device_id]._has_jtag:
        word = context.server_ifc.jtag_read32(device_id, *core_loc.to("noc0"), addr)
    else:
        word = context.server_ifc.pci_read32(device_id, *core_loc.to("nocVirt"), addr)
    return word


def read_words_from_device(
    core_loc: Union[str, OnChipCoordinate], addr: int, device_id: int = 0, word_count: int = 1, context: Context = None
) -> "List[int]":
    """Reads word_count four-byte words of data, starting from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0):	ID number of device to read from.
            word_count (int, default 1): Number of 4-byte words to read.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
            List[int]: Data read from the device.
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)
    if word_count <= 0:
        raise TTException("word_count must be greater than 0.")

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])
    data = []
    for i in range(word_count):
        if context.devices[device_id]._has_jtag:
            word = context.server_ifc.jtag_read32(device_id, *core_loc.to("noc0"), addr + 4 * i)
        else:
            word = context.server_ifc.pci_read32(device_id, *core_loc.to("nocVirt"), addr + 4 * i)
        data.append(word)
    return data


def read_from_device(
    core_loc: Union[str, OnChipCoordinate], addr: int, device_id: int = 0, num_bytes: int = 4, context: Context = None
) -> bytes:
    """Reads num_bytes of data starting from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0): ID number of device to read from.
            num_bytes (int, default 4): Number of bytes to read.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
            bytes: Data read from the device.
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)
    if num_bytes <= 0:
        raise TTException("num_bytes must be greater than 0.")

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])

    if context.devices[device_id]._has_jtag:
        int_array = read_words_from_device(core_loc, addr, device_id, num_bytes // 4 + (num_bytes % 4 > 0), context)
        return struct.pack(f"{len(int_array)}I", *int_array)[:num_bytes]

    return context.server_ifc.pci_read(device_id, *core_loc.to("nocVirt"), addr, num_bytes)


def write_words_to_device(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    data: Union[int, List[int]],
    device_id: int = 0,
    context: Context = None,
) -> int:
    """Writes data word to address 'addr' at noc0 location x-y of the current chip.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to write to. If multiple words are to be written, the address is the starting address.
            data (int | List[int]): 4-byte integer word to be written, or a list of them.
            device_id (int, default 0): ID number of device to write to.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
            int: If the execution is successful, return value should be 4 (number of bytes written).
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])

    if isinstance(data, int):
        data = [data]

    bytes_written = 0
    for i, word in enumerate(data):
        if context.devices[device_id]._has_jtag:
            bytes_written += context.server_ifc.jtag_write32(device_id, *core_loc.to("noc0"), addr + i * 4, word)
        else:
            bytes_written += context.server_ifc.pci_write32(device_id, *core_loc.to("nocVirt"), addr + i * 4, word)
    return bytes_written


def write_to_device(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    data: "Union[List[int], bytes]",
    device_id: int = 0,
    context: Context = None,
) -> int:
    """Writes data to address 'addr' at noc0 location x-y of the current chip.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int):	Memory address to write to.
            data (List[int] | bytes): Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
            device_id (int, default 0):	ID number of device to write to.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
            int: If the execution is successful, return value should be number of bytes written.
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)

    if isinstance(data, list):
        data = bytes(data)

    if len(data) == 0:
        raise TTException("Data to write must not be empty.")

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])

    if context.devices[device_id]._has_jtag:
        assert (
            len(data) % 4 == 0
        ), "Data length must be a multiple of 4 bytes as JTAG currently does not support unaligned access."
        for i in range(0, len(data), 4):
            write_words_to_device(core_loc, addr + i, struct.unpack("<I", data[i : i + 4])[0], device_id, context)
        return len(data)

    return context.server_ifc.pci_write(device_id, *core_loc.to("nocVirt"), addr, data)


def run_elf(
    elf_file: os.PathLike,
    core_loc: Union[str, OnChipCoordinate, List[Union[str, OnChipCoordinate]]],
    risc_id: int = 0,
    device_id: int = 0,
    context: Context = None,
) -> None:
    """Loads the given ELF file into the specified RISC core and executes it.

    Args:
            elf_file (os.PathLike): Path to the ELF file to run.
            core_loc (str | OnChipCoordinate | List[str | OnChipCoordinate]): One of the following:
                    1. "all" to run the ELF on all cores;
                    2. an X-Y (nocTr) or R,C (netlist) location of a core in string format;
                    3. a list of X-Y (nocTr), R,C (netlist) or OnChipCoordinate locations of cores, possibly mixed;
                    4. an OnChipCoordinate object.
            risc_id (int, default 0): RiscV ID (0: brisc, 1-3 triscs).
            device_id (int, default 0):	ID number of device to run ELF on.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    from ttlens.tt_debug_risc import RiscLoader, RiscDebug, RiscLoc

    context = check_context(context)

    validate_device_id(device_id, context)
    if (risc_id < 0) or (risc_id > 4):
        raise TTException("Invalid RiscV ID. Must be between 0 and 4.")

    device = context.devices[device_id]

    locs = []
    if isinstance(core_loc, OnChipCoordinate):
        locs = [core_loc]
    elif isinstance(core_loc, list):
        for loc in core_loc:
            if isinstance(loc, OnChipCoordinate):
                locs.append(loc)
            else:
                locs.append(OnChipCoordinate.create(loc, device))
    elif core_loc == "all":
        for loc in device.get_block_locations(block_type="functional_workers"):
            locs.append(loc)
    else:
        locs = [OnChipCoordinate.create(core_loc, device)]

    if not os.path.exists(elf_file):
        raise TTException(f"ELF file {elf_file} does not exist.")

    assert locs, "No valid core locations provided."
    for loc in locs:
        rdbg = RiscDebug(RiscLoc(loc, 0, risc_id), context, False)
        rloader = RiscLoader(rdbg, context, False)
        rloader.run_elf(elf_file)


def check_context(context: Context = None) -> Context:
    """Function to initialize context if not provided. By default, it starts a local
    TTLens session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
    that the context can be reused in calls to other functions.
    """
    if context is not None:
        return context

    if not tt_lens_init.GLOBAL_CONTEXT:
        tt_lens_init.GLOBAL_CONTEXT = tt_lens_init.init_ttlens()
    return tt_lens_init.GLOBAL_CONTEXT


def validate_addr(addr: int) -> None:
    if addr < 0:
        raise TTException("addr must be greater than or equal to 0.")


def validate_device_id(device_id: int, context: Context) -> None:
    if device_id not in context.device_ids:
        raise TTException(f"Invalid device_id {device_id}.")


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


def arc_msg(
    device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int, context: Context = None
) -> "List[int]":
    """Sends an ARC message to the device.

    Args:
            device_id (int): ID number of device to send message to.
            msg_code (int): Message code to send.
            wait_for_done (bool): If True, waits for the message to be processed.
            arg0 (int): First argument to the message.
            arg1 (int): Second argument to the message.
            timeout (int): Timeout in milliseconds.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
            List[int]: return code, reply0, reply1.
    """
    context = check_context(context)

    validate_device_id(device_id, context)
    if timeout < 0:
        raise TTException("Timeout must be greater than or equal to 0.")

    return context.server_ifc.arc_msg(device_id, msg_code, wait_for_done, arg0, arg1, timeout)


def inject_instruction(
    instruction: bytearray,
    trisc_id: int,
    core_loc: Union[str, OnChipCoordinate, List[Union[str, OnChipCoordinate]]],
    device_id: int = 0,
    context: Context = None,
) -> None:
    """Injects instruction into Tensix pipe for TRISC specified by trisc_id.

    Args:
            instruction (bytearray): 32-bit instruction to inject.
            trisc_id (int): TRISC ID (0-2).
            core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format or OnChipCoordinate object.
            device_id (int): ID number of device to send message to.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    context = check_context(context)
    validate_instruction(instruction, context)
    validate_trisc_id(trisc_id, context)
    validate_device_id(device_id, context)

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])

    DBG_INSTRN_BUF_CTRL0 = 0xFFB120A0
    DBG_INSTRN_BUF_CTRL1 = 0xFFB120A4
    DBG_INSTRN_BUF_STATUS = 0xFFB120A8

    # 1. Wait for buffer ready signal (poll bit 0 of DBG_INSTRN_BUF_STATUS until it’s 1)
    while (read_word_from_device(core_loc, DBG_INSTRN_BUF_STATUS, device_id, context) & 1) == 0:
        pass

    write_to_device(core_loc, DBG_INSTRN_BUF_CTRL0, [0x07], device_id, context)

    # 2. Assemble 32-bit instruction and write it to DBG_INSTRN_BUF_CTRL1
    write_to_device(core_loc, DBG_INSTRN_BUF_CTRL1, instruction, device_id, context)

    # 3. Set bit 0(trigger) and bit 4 (override en) to 1 in DBG_INSTRN_BUF_CTRL0 to inject instruction.
    write_to_device(core_loc, DBG_INSTRN_BUF_CTRL0, [0x7 | (0x10 << trisc_id)], device_id, context)

    # 4. Clear DBG_INSTRN_BUF_CTRL0 register
    write_to_device(core_loc, DBG_INSTRN_BUF_CTRL0, [0x07], device_id, context)
    write_to_device(core_loc, DBG_INSTRN_BUF_CTRL0, [0x00], device_id, context)

    # 5. Wait for buffer empty signal to make sure instruction completed (poll bit 4 of DBG_INSTRN_BUF_STATUS until it’s 1)
    while (read_word_from_device(core_loc, DBG_INSTRN_BUF_STATUS, device_id, context) & 0x10) == 0:
        pass


def read_regfile(
    regfile_id: int,
    core_loc: Union[str, OnChipCoordinate, List[Union[str, OnChipCoordinate]]],
    device_id: int = 0,
    context: Context = None,
) -> bytearray:
    """Dumps SRCA/SRCB/DSTACC register file from the specified core.

    Args:
            regfile_id (int): Register file to dump (0: SRCA, 1: SRCB, 2: DSTACC).
            core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format or OnChipCoordinate object.
            device_id (int): ID number of device to send message to.
            context (Context, optional): TTLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
            bytearray: 64x32 bytes of register file data (64 rows, 32 bytes per row).
    """
    context = check_context(context)
    validate_regfile_id(regfile_id, context)
    validate_device_id(device_id, context)

    from ttlens.tt_wormhole_ops import TT_OP_MOVDBGA2D, TT_OP_SETRWC

    RISCV_DEBUG_REG_DBG_ARRAY_RD_EN = 0xFFB12060
    RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD = 0xFFB12064
    RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA = 0xFFB1206C

    if regfile_id == REGFILE_SRCB:
        raise "Not implemented"

    write_to_device(core_loc, RISCV_DEBUG_REG_DBG_ARRAY_RD_EN, [0x1], device_id, context)
    data = []
    if regfile_id == REGFILE_SRCA:
        inject_instruction(
            int.to_bytes(TT_OP_SETRWC(3, 0, 0, 0, 0, 0), 4, byteorder="little"), 2, core_loc, device_id, context
        )
    for row in range(64):
        if regfile_id == REGFILE_SRCA:
            inject_instruction(
                int.to_bytes(TT_OP_MOVDBGA2D(0, row & 0x3F, 0, 0, row & 0x3FF), 4, byteorder="little"),
                2,
                core_loc,
                device_id,
                context,
            )
        for i in range(8):
            dbg_array_rd_cmd = row + (i << 12) + (2 << 16)
            write_to_device(
                core_loc,
                RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD,
                dbg_array_rd_cmd.to_bytes(4, byteorder="little"),
                device_id,
                context,
            )
            rd_data = read_word_from_device(core_loc, RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA, device_id, context=context)
            data += list(int.to_bytes(rd_data, 4, byteorder="big"))

    write_to_device(core_loc, RISCV_DEBUG_REG_DBG_ARRAY_RD_EN, [0x0], device_id, context)
    write_to_device(core_loc, RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD, [0x0], device_id, context)
    return data
