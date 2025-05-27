# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import re
import struct

from typing import Union, List

from ttexalens import tt_exalens_init

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.parse_elf import ParsedElfFile, read_elf
from ttexalens.util import TTException


def convert_coordinate(
    core_loc: Union[str, OnChipCoordinate], device_id: int = 0, context: Context = None
) -> OnChipCoordinate:
    """Converts a string coordinate to an OnChipCoordinate object.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            device_id (int, default 0): ID number of device to convert to.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
            OnChipCoordinate: Converted coordinate.
    """
    context = check_context(context)

    if not isinstance(core_loc, OnChipCoordinate):
        return OnChipCoordinate.create(core_loc, device=context.devices[device_id])
    return core_loc


def read_word_from_device(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    device_id: int = 0,
    context: Context = None,
    noc_id: int | None = None,
) -> "int":
    """Reads one word of data, from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0):	ID number of device to read from.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
            noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
            int: Data read from the device.
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)
    noc_id = check_noc_id(noc_id, context)

    coordinate = convert_coordinate(core_loc, device_id, context)
    if context.devices[device_id]._has_jtag:
        word = context.server_ifc.jtag_read32(noc_id, device_id, *context.convert_loc_to_jtag(coordinate), addr)
    else:
        word = context.server_ifc.pci_read32(noc_id, device_id, *context.convert_loc_to_umd(coordinate), addr)
    return word


def read_words_from_device(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    device_id: int = 0,
    word_count: int = 1,
    context: Context = None,
    noc_id: int | None = None,
) -> "List[int]":
    """Reads word_count four-byte words of data, starting from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0):	ID number of device to read from.
            word_count (int, default 1): Number of 4-byte words to read.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
            noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
            List[int]: Data read from the device.
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)
    noc_id = check_noc_id(noc_id, context)
    if word_count <= 0:
        raise TTException("word_count must be greater than 0.")

    coordinate = convert_coordinate(core_loc, device_id, context)
    data = []
    for i in range(word_count):
        if context.devices[device_id]._has_jtag:
            word = context.server_ifc.jtag_read32(
                noc_id, device_id, *context.convert_loc_to_jtag(coordinate), addr + 4 * i
            )
        else:
            word = context.server_ifc.pci_read32(
                noc_id, device_id, *context.convert_loc_to_umd(coordinate), addr + 4 * i
            )
        data.append(word)
    return data


def read_from_device(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    device_id: int = 0,
    num_bytes: int = 4,
    context: Context = None,
    noc_id: int | None = None,
) -> bytes:
    """Reads num_bytes of data starting from address 'addr' at core <x-y>.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            device_id (int, default 0): ID number of device to read from.
            num_bytes (int, default 4): Number of bytes to read.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
            noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
            bytes: Data read from the device.
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)
    noc_id = check_noc_id(noc_id, context)
    if num_bytes <= 0:
        raise TTException("num_bytes must be greater than 0.")

    coordinate = convert_coordinate(core_loc, device_id, context)

    if context.devices[device_id]._has_jtag:
        int_array = read_words_from_device(
            coordinate, addr, device_id, num_bytes // 4 + (num_bytes % 4 > 0), context, noc_id
        )
        return struct.pack(f"{len(int_array)}I", *int_array)[:num_bytes]

    return context.server_ifc.pci_read(noc_id, device_id, *context.convert_loc_to_umd(coordinate), addr, num_bytes)


def write_words_to_device(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    data: Union[int, List[int]],
    device_id: int = 0,
    context: Context = None,
    noc_id: int | None = None,
) -> int:
    """Writes data word to address 'addr' at noc0 location x-y of the current chip.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to write to. If multiple words are to be written, the address is the starting address.
            data (int | List[int]): 4-byte integer word to be written, or a list of them.
            device_id (int, default 0): ID number of device to write to.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
            noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
            int: If the execution is successful, return value should be 4 (number of bytes written).
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)
    noc_id = check_noc_id(noc_id, context)

    coordinate = convert_coordinate(core_loc, device_id, context)

    if isinstance(data, int):
        data = [data]

    bytes_written = 0
    for i, word in enumerate(data):
        if context.devices[device_id]._has_jtag:
            bytes_written += context.server_ifc.jtag_write32(
                noc_id, device_id, *context.convert_loc_to_jtag(coordinate), addr + i * 4, word
            )
        else:
            bytes_written += context.server_ifc.pci_write32(
                noc_id, device_id, *context.convert_loc_to_umd(coordinate), addr + i * 4, word
            )
    return bytes_written


def write_to_device(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    data: "Union[List[int], bytes]",
    device_id: int = 0,
    context: Context = None,
    noc_id: int | None = None,
) -> int:
    """Writes data to address 'addr' at noc0 location x-y of the current chip.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int):	Memory address to write to.
            data (List[int] | bytes): Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
            device_id (int, default 0):	ID number of device to write to.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
            noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
            int: If the execution is successful, return value should be number of bytes written.
    """
    context = check_context(context)

    validate_addr(addr)
    validate_device_id(device_id, context)
    noc_id = check_noc_id(noc_id, context)

    if isinstance(data, list):
        data = bytes(data)

    if len(data) == 0:
        raise TTException("Data to write must not be empty.")

    coordinate = convert_coordinate(core_loc, device_id, context)

    if context.devices[device_id]._has_jtag:
        assert (
            len(data) % 4 == 0
        ), "Data length must be a multiple of 4 bytes as JTAG currently does not support unaligned access."
        for i in range(0, len(data), 4):
            write_words_to_device(
                coordinate, addr + i, struct.unpack("<I", data[i : i + 4])[0], device_id, context, noc_id
            )
        return len(data)

    return context.server_ifc.pci_write(noc_id, device_id, *context.convert_loc_to_umd(coordinate), addr, data)


def load_elf(
    elf_file: str,
    core_loc: Union[str, OnChipCoordinate, List[Union[str, OnChipCoordinate]]],
    risc_id: int = 0,
    device_id: int = 0,
    context: Context = None,
) -> None:
    """Loads the given ELF file into the specified RISC core. RISC core must be in reset before loading the ELF.

    Args:
            elf_file (str): Path to the ELF file to run.
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

    locs: List[OnChipCoordinate] = []
    if isinstance(core_loc, OnChipCoordinate):
        locs = [core_loc]
    elif isinstance(core_loc, list):
        for loc in core_loc:
            if isinstance(loc, OnChipCoordinate):
                locs.append(loc)
            else:
                locs.append(OnChipCoordinate.create(loc, device))
    elif core_loc == "all":
        for block_loc in device.get_block_locations(block_type="functional_workers"):
            locs.append(block_loc)
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
    elf_file: str,
    core_loc: Union[str, OnChipCoordinate, List[Union[str, OnChipCoordinate]]],
    risc_id: int = 0,
    device_id: int = 0,
    context: Context = None,
) -> None:
    """Loads the given ELF file into the specified RISC core and executes it. Similar to load_elf, but RISC core is taken out of reset after load.

    Args:
            elf_file (str): Path to the ELF file to run.
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
        for block_loc in device.get_block_locations(block_type="functional_workers"):
            locs.append(block_loc)
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


def check_noc_id(noc_id: int | None, context: Context) -> int:
    if noc_id is None:
        return 1 if context.use_noc1 else 0
    assert noc_id in (0, 1), f"Invalid NOC ID {noc_id}. Expected 0 or 1."
    return noc_id


def validate_addr(addr: int) -> None:
    if addr < 0:
        raise TTException("addr must be greater than or equal to 0.")


def validate_device_id(device_id: int, context: Context) -> None:
    if device_id not in context.device_ids:
        raise TTException(f"Invalid device_id {device_id}.")


def arc_msg(
    device_id: int,
    msg_code: int,
    wait_for_done: bool,
    arg0: int,
    arg1: int,
    timeout: int,
    context: Context = None,
    noc_id: int | None = None,
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
            noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
            List[int]: return code, reply0, reply1.
    """
    context = check_context(context)
    noc_id = check_noc_id(noc_id, context)

    validate_device_id(device_id, context)
    if timeout < 0:
        raise TTException("Timeout must be greater than or equal to 0.")

    return context.server_ifc.arc_msg(noc_id, device_id, msg_code, wait_for_done, arg0, arg1, timeout)


def read_arc_telemetry_entry(device_id: int, telemetry_tag: int, context: Context = None) -> int:
    """Reads an ARC telemetry entry from the device.

    Args:
            device_id (int): ID number of device to read telemetry from.
            telemetry_tag (int): Tag for telemetry entry to read.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
            int: Value of the telemetry entry.
    """
    context = check_context(context)
    validate_device_id(device_id, context)

    return context.server_ifc.read_arc_telemetry_entry(device_id, telemetry_tag)


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

    coordinate = convert_coordinate(core_loc, device_id, context)

    if not isinstance(register, TensixRegisterDescription) and not isinstance(register, str):
        raise TTException(
            f"Invalid register type. Must be an str or instance of TensixRegisterDescription or its subclasses, but got {type(register)}"
        )

    return TensixDebug(coordinate, device_id, context).read_tensix_register(register)


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
    coordinate = convert_coordinate(core_loc, device_id, context)

    if not isinstance(register, TensixRegisterDescription) and not isinstance(register, str):
        raise TTException(
            f"Invalid register type. Must be an str or instance of TensixRegisterDescription or its subclasses, but got {type(register)}"
        )

    TensixDebug(coordinate, device_id, context).write_tensix_register(register, value)


def parse_elf(elf_path: str, context: Context | None = None) -> ParsedElfFile:
    """Reads the ELF file and returns a ParsedElfFile object.
    Args:
            elf_path (str): Path to the ELF file.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized. Default: None
    """
    context = check_context(context)
    return read_elf(context.server_ifc, elf_path)


def top_callstack(
    pc: int,
    elfs: Union[List[str], str, List[ParsedElfFile], ParsedElfFile],
    offsets: int | List[int | None] = None,
    context: Context = None,
) -> List:

    """Retrieves the top frame of the callstack for the specified PC on the given ELF.
    There is no stack walking, so the function will return the function at the given PC and all inlined functions on the top frame (if there are any).
    Args:
            pc (int): Program counter to be used for the callstack.
            elfs (List[str] | str | List[ParsedElfFile] | ParsedElfFile): ELF files to be used for the callstack.
            offsets (List[int], int, optional): List of offsets for each ELF file. Default: None.
            context (Context): TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None
    Returns:
            List: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.
    """

    from ttexalens.debug_risc import RiscLoader

    context = check_context(context)

    # If given a single string, convert to list
    if isinstance(elfs, str):
        elfs = [parse_elf(elfs, context)]
    elif isinstance(elfs, ParsedElfFile):
        elfs = [elfs]
    elif isinstance(elfs, list):
        elfs = [parse_elf(elf, context) if isinstance(elf, str) else elf for elf in elfs]

    offsets = offsets if offsets is not None else [None for _ in range(len(elfs))]
    if isinstance(offsets, int):
        offsets = [offsets]

    if len(offsets) != len(elfs):
        raise TTException("Number of offsets must match the number of elf files")

    elfs = RiscLoader._read_elfs(elfs, offsets)
    elf, frame_description = RiscLoader._find_elf_and_frame_description(elfs, pc, None)
    if frame_description is None or elf is None:
        return []
    return RiscLoader.get_frame_callstack(elf, pc)[0]


def callstack(
    core_loc: Union[str, OnChipCoordinate],
    elfs: Union[List[str], str, List[ParsedElfFile], ParsedElfFile],
    offsets: int | List[int | None] = None,
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
            elfs (List[str] | str | List[ParsedElfFile] | ParsedElfFile): ELF files to be used for the callstack.
            offsets (List[int], int, optional): List of offsets for each ELF file. Default: None.
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
    coordinate = convert_coordinate(core_loc, device_id, context)

    # If given a single string, convert to list
    if isinstance(elfs, str):
        elfs = [parse_elf(elfs, context)]
    elif isinstance(elfs, ParsedElfFile):
        elfs = [elfs]
    elif isinstance(elfs, list):
        elfs = [parse_elf(elf, context) if isinstance(elf, str) else elf for elf in elfs]

    offsets = offsets if offsets is not None else [None for _ in range(len(elfs))]
    if isinstance(offsets, int):
        offsets = [offsets]

    if len(offsets) != len(elfs):
        raise TTException("Number of offsets must match the number of elf files")

    if risc_id < 0 or risc_id > 3:
        raise ValueError("Invalid RiscV ID. Must be between 0 and 3.")

    if max_depth <= 0:
        raise ValueError("Max depth must be greater than 0.")

    noc_id = 0
    risc_debug = RiscDebug(RiscLoc(coordinate, noc_id, risc_id), context, verbose=verbose)
    if risc_debug.is_in_reset():
        raise TTException(f"RiscV core {get_risc_name(risc_id)} on location {coordinate.to_user_str()} is in reset")
    loader = RiscLoader(risc_debug, context, verbose)

    return loader.get_callstack(elfs, offsets, max_depth, stop_on_main)


def read_riscv_memory(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    noc_id: int = 0,
    risc_id: int = 0,
    device_id: int = 0,
    context: Context = None,
    verbose: bool = False,
) -> int:

    """Reads a 32-bit word from the specified RISC-V core's private memory.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            noc_id (int): What noc to use. Options [0,1]. Default 0.
            risc_id (int): RiscV ID (0: brisc, 1-3 triscs). Default 0.
            device_id (int): ID number of device to read from. Default 0.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
            verbose (bool): If True, enables verbose output. Default False.

    Returns:
            int: Data read from the device.
    """

    from ttexalens.debug_risc import RiscDebug, RiscLoc, RiscLoader, get_risc_name

    context = check_context(context)
    validate_device_id(device_id, context)
    device = context.devices[device_id]
    coordinate = convert_coordinate(core_loc, device_id, context)

    if noc_id not in (0, 1):
        raise ValueError("Invalid value for noc_id. Expected 0 or 1.")

    if risc_id < 0 or risc_id > 3:
        raise ValueError("Invalid value for risc_id. Expected value between 0 and 3.")

    base_address = device._get_riscv_local_memory_base_address()
    size = device._get_riscv_local_memory_size(risc_id)

    if addr < base_address or addr >= base_address + size:
        raise ValueError(
            f"Invalid address {hex(addr)}. Address must be between {hex(base_address)} and {hex(base_address + size - 1)}."
        )

    location = RiscLoc(loc=coordinate, noc_id=noc_id, risc_id=risc_id)
    debug_risc = RiscDebug(location=location, context=context, verbose=verbose)

    if debug_risc.is_in_reset():
        raise TTException(f"{get_risc_name(risc_id)} core is in reset.")

    with debug_risc.ensure_halted():
        ret = debug_risc.read_memory(addr)

    return ret


def write_riscv_memory(
    core_loc: Union[str, OnChipCoordinate],
    addr: int,
    value: int,
    noc_id: int = 0,
    risc_id: int = 0,
    device_id: int = 0,
    context: Context = None,
    verbose: bool = False,
) -> None:

    """Writes a 32-bit word to the specified RISC-V core's private memory.

    Args:
            core_loc (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
            addr (int): Memory address to read from.
            value (int): Value to write.
            noc_id (int): What noc to use. Options [0,1]. Default 0.
            risc_id (int): RiscV ID (0: brisc, 1-3 triscs). Default 0.
            device_id (int): ID number of device to read from. Default 0.
            context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
            verbose (bool): If True, enables verbose output. Default False.
    """

    from ttexalens.debug_risc import RiscDebug, RiscLoc, RiscLoader, get_risc_name

    context = check_context(context)
    validate_device_id(device_id, context)
    device = context.devices[device_id]
    coordinate = convert_coordinate(core_loc, device_id, context)

    if value < 0 or value > 0xFFFFFFFF:
        raise ValueError(f"Invalid value {value}. Value must be a 32-bit unsigned integer.")

    if noc_id not in (0, 1):
        raise ValueError(f"Invalid value for noc_id {noc_id}. Expected 0 or 1.")

    if risc_id < 0 or risc_id > 3:
        raise ValueError(f"Invalid value for risc_id {risc_id}. Expected value between 0 and 3.")

    base_address = device._get_riscv_local_memory_base_address()
    size = device._get_riscv_local_memory_size(risc_id)

    if addr < base_address or addr >= base_address + size:
        raise ValueError(
            f"Invalid address {hex(addr)}. Address must be between {hex(base_address)} and {hex(base_address + size - 1)}."
        )

    location = RiscLoc(loc=coordinate, noc_id=noc_id, risc_id=risc_id)
    debug_risc = RiscDebug(location=location, context=context, verbose=verbose)

    if debug_risc.is_in_reset():
        raise TTException(f"{get_risc_name(risc_id)} core is in reset.")

    with debug_risc.ensure_halted():
        debug_risc.write_memory(addr, value)
