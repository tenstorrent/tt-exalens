# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import re
import struct

from typing import Union, List

from ttexalens import tt_exalens_init

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.util import TTException


def read_word_from_device(
    core_loc: Union[str, OnChipCoordinate], addr: int, device_id: int = 0, context: Context = None
) -> "int":
    """Reads one word of data, from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0):	ID number of device to read from.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

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
        word = context.server_ifc.pci_read32(device_id, *context.convert_loc_to_umd(core_loc), addr)
    return word


def read_words_from_device(
    core_loc: Union[str, OnChipCoordinate], addr: int, device_id: int = 0, word_count: int = 1, context: Context = None
) -> "List[int]":
    """Reads word_count four-byte words of data, starting from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0):	ID number of device to read from.
            word_count (int, default 1): Number of 4-byte words to read.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

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
            word = context.server_ifc.pci_read32(device_id, *context.convert_loc_to_umd(core_loc), addr + 4 * i)
        data.append(word)
    return data


def read_from_device(
    core_loc: Union[str, OnChipCoordinate], addr: int, device_id: int = 0, num_bytes: int = 4, context: Context = None
) -> bytes:
    """Reads num_bytes of data starting from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0): ID number of device to read from.
            num_bytes (int, default 4): Number of bytes to read.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.

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

    return context.server_ifc.pci_read(device_id, *context.convert_loc_to_umd(core_loc), addr, num_bytes)


def write_words_to_device(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    data: Union[int, List[int]],
    device_id: int = 0,
    context: Context = None,
) -> int:
    """Writes data word to address 'addr' at noc0 location x-y of the current chip.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to write to. If multiple words are to be written, the address is the starting address.
            data (int | List[int]): 4-byte integer word to be written, or a list of them.
            device_id (int, default 0): ID number of device to write to.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

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
            bytes_written += context.server_ifc.pci_write32(
                device_id, *context.convert_loc_to_umd(core_loc), addr + i * 4, word
            )
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
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int):	Memory address to write to.
            data (List[int] | bytes): Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
            device_id (int, default 0):	ID number of device to write to.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

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

    return context.server_ifc.pci_write(device_id, *context.convert_loc_to_umd(core_loc), addr, data)


def load_elf(
    elf_file: os.PathLike,
    core_loc: Union[str, OnChipCoordinate, List[Union[str, OnChipCoordinate]]],
    risc_id: int = 0,
    device_id: int = 0,
    context: Context = None,
) -> None:
    """Loads the given ELF file into the specified RISC core. RISC core must be in reset before loading the ELF.

    Args:
            elf_file (os.PathLike): Path to the ELF file to run.
            core_loc (str | OnChipCoordinate | List[str | OnChipCoordinate]): One of the following:
                    1. "all" to run the ELF on all cores;
                    2. an X-Y (noc0/translated) or X,Y (logical) location of a core in string format;
                    3. a list of X-Y (noc0/translated), X,Y (logical) or OnChipCoordinate locations of cores, possibly mixed;
                    4. an OnChipCoordinate object.
            risc_id (int, default 0): RiscV ID (0: brisc, 1-3 triscs).
            device_id (int, default 0):	ID number of device to run ELF on.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    from ttexalens.debug_risc import RiscLoader, RiscDebug, RiscLoc

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
        rloader.load_elf(elf_file)


def run_elf(
    elf_file: os.PathLike,
    core_loc: Union[str, OnChipCoordinate, List[Union[str, OnChipCoordinate]]],
    risc_id: int = 0,
    device_id: int = 0,
    context: Context = None,
) -> None:
    """Loads the given ELF file into the specified RISC core and executes it. Similar to load_elf, but RISC core is taken out of reset after load.

    Args:
            elf_file (os.PathLike): Path to the ELF file to run.
            core_loc (str | OnChipCoordinate | List[str | OnChipCoordinate]): One of the following:
                    1. "all" to run the ELF on all cores;
                    2. an X-Y (noc0/translated) or X,Y (logical) location of a core in string format;
                    3. a list of X-Y (noc0/translated), X,Y (logical) or OnChipCoordinate locations of cores, possibly mixed;
                    4. an OnChipCoordinate object.
            risc_id (int, default 0): RiscV ID (0: brisc, 1-3 triscs).
            device_id (int, default 0):	ID number of device to run ELF on.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    from ttexalens.debug_risc import RiscLoader, RiscDebug, RiscLoc

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
    TTExaLens session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
    that the context can be reused in calls to other functions.
    """
    if context is not None:
        return context

    if not tt_exalens_init.GLOBAL_CONTEXT:
        tt_exalens_init.GLOBAL_CONTEXT = tt_exalens_init.init_ttexalens()
    return tt_exalens_init.GLOBAL_CONTEXT


def validate_addr(addr: int) -> None:
    if addr < 0:
        raise TTException("addr must be greater than or equal to 0.")


def validate_device_id(device_id: int, context: Context) -> None:
    if device_id not in context.device_ids:
        raise TTException(f"Invalid device_id {device_id}.")


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
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
            List[int]: return code, reply0, reply1.
    """
    context = check_context(context)

    validate_device_id(device_id, context)
    if timeout < 0:
        raise TTException("Timeout must be greater than or equal to 0.")

    return context.server_ifc.arc_msg(device_id, msg_code, wait_for_done, arg0, arg1, timeout)


def read_tensix_register(
    core_loc: Union[str, OnChipCoordinate],
    register,
    device_id: int = 0,
    context: Context = None,
) -> int:
    """Reads the value of a register from the tensix core.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            register (str | TensixRegisterDescription): Configuration or debug register to read from (name or instance of ConfigurationRegisterDescription or DebugRegisterDescription).
                                                        ConfigurationRegisterDescription(id, mask, shift), DebugRegisterDescription(addr).
            device_id (int, default 0):	ID number of device to read from.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
            int: Value of the configuration or debug register specified.
    """
    from ttexalens.device import TensixRegisterDescription
    from ttexalens.debug_tensix import TensixDebug

    context = check_context(context)
    validate_device_id(device_id, context)

    device = context.devices[device_id]

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=device)

    if not isinstance(register, TensixRegisterDescription) and not isinstance(register, str):
        raise TTException(
            f"Invalid register type. Must be an str or instance of TensixRegisterDescription or its subclasses, but got {type(register)}"
        )

    return TensixDebug(core_loc, device_id, context).read_tensix_register(register)


def write_tensix_register(
    core_loc: Union[str, OnChipCoordinate],
    register,
    value: int,
    device_id: int = 0,
    context: Context = None,
) -> None:

    """Writes value to a register on the tensix core.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            register (str | TensixRegisterDescription): Configuration or debug register to read from (name or instance of ConfigurationRegisterDescription or DebugRegisterDescription).
                                                        ConfigurationRegisterDescription(id, mask, shift), DebugRegisterDescription(addr).
            value (int): Value to write to the register.
            device_id (int, default 0):	ID number of device to read from.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
    """

    from ttexalens.device import TensixRegisterDescription
    from ttexalens.debug_tensix import TensixDebug

    context = check_context(context)
    validate_device_id(device_id, context)
    device = context.devices[device_id]

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=device)

    if not isinstance(register, TensixRegisterDescription) and not isinstance(register, str):
        raise TTException(
            f"Invalid register type. Must be an str or instance of TensixRegisterDescription or its subclasses, but got {type(register)}"
        )

    TensixDebug(core_loc, device_id, context).write_tensix_register(register, value)


def callstack(
    core_loc: Union[str, OnChipCoordinate],
    elf_paths: Union[List[str], str],
    offsets: List[int] = None,
    risc_id: int = 0,
    max_depth: int = 100,
    stop_on_main: bool = True,
    verbose: bool = False,
    device_id: int = 0,
    context: Context = None,
) -> List:

    """Retrieves the callstack of the specified RISC core for a given ELF.
    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, DRAM channel (e.g., ch3), or OnChipCoordinate object.
            elf_paths (List[str] | str): Paths to the ELF files to be used for the callstack.
            offsets (List[int], optional): List of offsets for each ELF file. Default: None.
            risc_id (int): RISC-V ID (0: brisc, 1-3 triscs). Default: 0.
            max_depth (int): Maximum depth of the callstack. Default: 100.
            stop_on_main (bool): If True, stops at the main function. Default: True.
            verbose (bool): If True, enables verbose output. Default: False.
            device_id (int): ID of the device on which the kernel is run. Default: 0.
            context (Context): TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None
    Returns:
            List: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.
    """

    from ttexalens.debug_risc import RiscLoader, RiscDebug, RiscLoc, get_risc_name

    context = check_context(context)
    validate_device_id(device_id, context)
    device = context.devices[device_id]

    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=device)

    # If given a single string, convert to list
    if isinstance(elf_paths, str):
        elf_paths = [elf_paths]

    for elf_path in elf_paths:
        if not os.path.exists(elf_path):
            raise TTException(f"File {elf_path} does not exist")

    offsets = offsets if offsets is not None else [None for _ in range(len(elf_paths))]
    if isinstance(offsets, int):
        offsets = [offsets]

    if len(offsets) != len(elf_paths):
        raise TTException("Number of offsets must match the number of elf files")

    if risc_id < 0 or risc_id > 3:
        raise ValueError("Invalid RiscV ID. Must be between 0 and 3.")

    if max_depth <= 0:
        raise ValueError("Max depth must be greater than 0.")

    noc_id = 0
    risc_debug = RiscDebug(RiscLoc(core_loc, noc_id, risc_id), context, verbose=verbose)
    if risc_debug.is_in_reset():
        raise TTException(f"RiscV core {get_risc_name(risc_id)} on location {core_loc.to_user_str()} is in reset")
    loader = RiscLoader(risc_debug, context, verbose)

    return loader.get_callstack(elf_paths, offsets, max_depth, stop_on_main)
