# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import datetime
import os
import re
import struct

from ttexalens import tt_exalens_init
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.elf import read_elf, ParsedElfFile
from ttexalens.util import TTException


def check_context(context: Context | None = None) -> Context:
    """Function to initialize context if not provided. By default, it starts a local
    TTExaLens session with no output folder and caching disabled and sets GLOBAL_CONTEXT variable so
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


def convert_coordinate(
    location: str | OnChipCoordinate, device_id: int = 0, context: Context | None = None
) -> OnChipCoordinate:
    """
    Converts a string location to an OnChipCoordinate object.
    If location is already OnChipCoordinate, it is returned as-is.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        device_id (int, default 0): ID number of device to convert to.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
        OnChipCoordinate: Converted coordinate.
    """
    if not isinstance(location, OnChipCoordinate):
        context = check_context(context)
        validate_device_id(device_id, context)
        return OnChipCoordinate.create(location, device=context.devices[device_id])
    return location


def read_word_from_device(
    location: str | OnChipCoordinate,
    addr: int,
    device_id: int = 0,
    context: Context | None = None,
    noc_id: int | None = None,
) -> int:
    """
    Reads one four-byte word of data, from address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to read from.
        device_id (int, default 0):	ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
        int: Data read from the device.
    """
    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context
    validate_addr(addr)
    noc_id = check_noc_id(noc_id, context)

    noc_loc = context.convert_loc_to_umd(coordinate)
    word = context.server_ifc.read32(noc_id, coordinate.device_id, noc_loc[0], noc_loc[1], addr)
    return word


def read_words_from_device(
    location: str | OnChipCoordinate,
    addr: int,
    device_id: int = 0,
    word_count: int = 1,
    context: Context | None = None,
    noc_id: int | None = None,
) -> list[int]:
    """
    Reads word_count four-byte words of data, starting from address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to read from.
        device_id (int, default 0):	ID number of device to read from.
        word_count (int, default 1): Number of 4-byte words to read.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
        list[int]: Data read from the device.
    """
    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context

    validate_addr(addr)
    noc_id = check_noc_id(noc_id, context)
    if word_count <= 0:
        raise TTException("word_count must be greater than 0.")

    noc_loc = context.convert_loc_to_umd(coordinate)
    bytes_data = context.server_ifc.read(noc_id, coordinate.device_id, noc_loc[0], noc_loc[1], addr, 4 * word_count)
    data = list(struct.unpack(f"<{word_count}I", bytes_data))
    return data


def read_from_device(
    location: str | OnChipCoordinate,
    addr: int,
    device_id: int = 0,
    num_bytes: int = 4,
    context: Context | None = None,
    noc_id: int | None = None,
) -> bytes:
    """
    Reads num_bytes of data starting from address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to read from.
        device_id (int, default 0): ID number of device to read from.
        num_bytes (int, default 4): Number of bytes to read.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
        bytes: Data read from the device.
    """
    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context

    validate_addr(addr)
    noc_id = check_noc_id(noc_id, context)
    if num_bytes <= 0:
        raise TTException("num_bytes must be greater than 0.")

    noc_loc = context.convert_loc_to_umd(coordinate)
    return context.server_ifc.read(noc_id, coordinate.device_id, noc_loc[0], noc_loc[1], addr, num_bytes)


def write_words_to_device(
    location: str | OnChipCoordinate,
    addr: int,
    data: int | list[int],
    device_id: int = 0,
    context: Context | None = None,
    noc_id: int | None = None,
) -> int:
    """
    Writes data word to address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to write to. If multiple words are to be written, the address is the starting address.
        data (int | list[int]): 4-byte integer word to be written, or a list of them.
        device_id (int, default 0): ID number of device to write to.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
        int: If the execution is successful, return value should be 4 (number of bytes written).
    """
    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context

    validate_addr(addr)
    noc_id = check_noc_id(noc_id, context)

    noc_loc = context.convert_loc_to_umd(coordinate)
    if isinstance(data, int):
        return context.server_ifc.write32(noc_id, coordinate.device_id, noc_loc[0], noc_loc[1], addr, data)

    byte_data = b"".join(x.to_bytes(4, "little") for x in data)
    return context.server_ifc.write(noc_id, coordinate.device_id, noc_loc[0], noc_loc[1], addr, byte_data)


def write_to_device(
    location: str | OnChipCoordinate,
    addr: int,
    data: list[int] | bytes,
    device_id: int = 0,
    context: Context | None = None,
    noc_id: int | None = None,
) -> int:
    """
    Writes data to address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int):	Memory address to write to.
        data (list[int] | bytes): Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
        device_id (int, default 0):	ID number of device to write to.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
        int: If the execution is successful, return value should be number of bytes written.
    """
    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context

    validate_addr(addr)
    noc_id = check_noc_id(noc_id, context)

    if isinstance(data, list):
        data = bytes(data)

    if len(data) == 0:
        raise TTException("Data to write must not be empty.")

    noc_loc = context.convert_loc_to_umd(coordinate)
    return context.server_ifc.write(noc_id, coordinate.device_id, noc_loc[0], noc_loc[1], addr, data)


def load_elf(
    elf_file: str,
    location: str | OnChipCoordinate | list[str | OnChipCoordinate],
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
    return_start_address: bool = False,
) -> None | int | list[int]:
    """
    Loads the given ELF file into the specified RISC core. RISC core must be in reset before loading the ELF.

    Args:
        elf_file (str): Path to the ELF file to run.
        location (str | OnChipCoordinate | list[str | OnChipCoordinate]): One of the following:
            1. "all" to run the ELF on all cores;
            2. an X-Y (noc0/translated) or X,Y (logical) location of a core in string format;
            3. a list of X-Y (noc0/translated), X,Y (logical) or OnChipCoordinate locations of cores, possibly mixed;
            4. an OnChipCoordinate object.
        risc_name (str): RiscV name (e.g. "brisc", "trisc0", "trisc1", "trisc2", "ncrisc").
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        device_id (int, default 0):	ID number of device to run ELF on.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """

    from ttexalens.elf_loader import ElfLoader

    locations: list[OnChipCoordinate] = []
    if isinstance(location, OnChipCoordinate):
        locations = [location]
    elif isinstance(location, list):
        for loc in location:
            if isinstance(loc, OnChipCoordinate):
                locations.append(loc)
            else:
                locations.append(convert_coordinate(loc, device_id, context))
    elif location == "all":
        context = check_context(context)
        validate_device_id(device_id, context)
        device = context.devices[device_id]
        for block_loc in device.get_block_locations(block_type="functional_workers"):
            locations.append(block_loc)
    else:
        locations = [convert_coordinate(location, device_id, context)]

    if not os.path.exists(elf_file):
        raise TTException(f"ELF file {elf_file} does not exist.")

    assert locations, "No valid core locations provided."
    returns = []
    for loc in locations:
        risc_debug = loc.noc_block.get_risc_debug(risc_name, neo_id)
        elf_loader = ElfLoader(risc_debug)
        start_address = elf_loader.load_elf(elf_file, return_start_address=return_start_address)
        if return_start_address:
            assert start_address is not None
            returns.append(start_address)
    if return_start_address:
        return returns if len(returns) > 1 else returns[0]
    else:
        return None


def run_elf(
    elf_file: str,
    location: str | OnChipCoordinate | list[str | OnChipCoordinate],
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
) -> None:
    """
    Loads the given ELF file into the specified RISC core and executes it. Similar to load_elf, but RISC core is taken out of reset after load.

    Args:
        elf_file (str): Path to the ELF file to run.
        location (str | OnChipCoordinate | list[str | OnChipCoordinate]): One of the following:
            1. "all" to run the ELF on all cores;
            2. an X-Y (noc0/translated) or X,Y (logical) location of a core in string format;
            3. a list of X-Y (noc0/translated), X,Y (logical) or OnChipCoordinate locations of cores, possibly mixed;
            4. an OnChipCoordinate object.
        risc_name (str): RiscV name (e.g. "brisc", "trisc0", "trisc1", "trisc2", "ncrisc").
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        device_id (int, default 0):	ID number of device to run ELF on.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """
    from ttexalens.elf_loader import ElfLoader

    locations: list[OnChipCoordinate] = []
    if isinstance(location, OnChipCoordinate):
        locations = [location]
    elif isinstance(location, list):
        for loc in location:
            if isinstance(loc, OnChipCoordinate):
                locations.append(loc)
            else:
                locations.append(convert_coordinate(loc, device_id, context))
    elif location == "all":
        context = check_context(context)
        validate_device_id(device_id, context)
        device = context.devices[device_id]
        for block_loc in device.get_block_locations(block_type="functional_workers"):
            locations.append(block_loc)
    else:
        locations = [convert_coordinate(location, device_id, context)]

    if not os.path.exists(elf_file):
        raise TTException(f"ELF file {elf_file} does not exist.")

    assert locations, "No valid core locations provided."
    for loc in locations:
        risc_debug = loc.noc_block.get_risc_debug(risc_name, neo_id)
        elf_loader = ElfLoader(risc_debug)
        elf_loader.run_elf(elf_file)


def arc_msg(
    device_id: int,
    msg_code: int,
    wait_for_done: bool,
    arg0: int,
    arg1: int,
    timeout: datetime.timedelta,
    context: Context | None = None,
    noc_id: int | None = None,
) -> list[int]:
    """
    Sends an ARC message to the device.

    Args:
        device_id (int): ID number of device to send message to.
        msg_code (int): Message code to send.
        wait_for_done (bool): If True, waits for the message to be processed.
        arg0 (int): First argument to the message.
        arg1 (int): Second argument to the message.
        timeout (datetime.timedelta): Timeout.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        noc_id (int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
        list[int]: return code, reply0, reply1.
    """
    context = check_context(context)
    noc_id = check_noc_id(noc_id, context)

    validate_device_id(device_id, context)
    if timeout < datetime.timedelta(0):
        raise TTException("Timeout must be greater than or equal to 0.")

    return list(context.server_ifc.arc_msg(noc_id, device_id, msg_code, wait_for_done, arg0, arg1, timeout))


def read_arc_telemetry_entry(device_id: int, telemetry_tag: int | str, context: Context | None = None) -> int:
    """
    Reads an ARC telemetry entry from the device.

    Args:
        device_id (int): ID number of device to read telemetry from.
        telemetry_tag (int | str): Name or ID of the tag to read.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
        int: Value of the telemetry entry.
    """
    from ttexalens.hardware.arc_block import CUTOFF_FIRMWARE_VERSION

    context = check_context(context)
    validate_device_id(device_id, context)
    device = context.devices[device_id]
    arc = device.arc_block

    if device._firmware_version < CUTOFF_FIRMWARE_VERSION:
        raise TTException(
            f"We no longer support ARC telemetry for firmware versions 18.3 and lower. This device is running firmware version {device._firmware_version}"
        )

    if isinstance(telemetry_tag, str):
        telemetry_tag_id = arc.get_telemetry_tag_id(telemetry_tag)
        if telemetry_tag_id is None:
            raise TTException(f"Telemetry tag {telemetry_tag} does not exist.")
    elif isinstance(telemetry_tag, int):
        if not arc.has_telemetry_tag_id(telemetry_tag):
            raise TTException(f"Telemetry tag ID {telemetry_tag} does not exist.")
        telemetry_tag_id = telemetry_tag
    else:
        raise TTException(f"Invalid telemetry_tag type. Must be an int or str, but got {type(telemetry_tag)}")

    return context.server_ifc.read_arc_telemetry_entry(device_id, telemetry_tag_id)


def read_register(
    location: str | OnChipCoordinate,
    register,
    noc_id: int = 0,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
) -> int:
    """
    Reads the value of a register from the core.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, or OnChipCoordinate object.
        register (str | RegisterDescription): Configuration or debug register to read from (name or instance of ConfigurationRegisterDescription or DebugRegisterDescription).
                                              ConfigurationRegisterDescription(id, mask, shift), DebugRegisterDescription(addr).
        noc_id (int, default 0): NOC ID to use.
        neo_id (int | None, optional): NEO ID of the register store.
        device_id (int, default 0):	ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.

    Returns:
        int: Value of the configuration or debug register specified.
    """
    from ttexalens.register_store import RegisterDescription

    coordinate = convert_coordinate(location, device_id, context)

    if not isinstance(register, RegisterDescription) and not isinstance(register, str):
        raise TTException(
            f"Invalid register type. Must be an str or instance of RegisterDescription or its subclasses, but got {type(register)}"
        )
    register_store = coordinate.noc_block.get_register_store(noc_id, neo_id)
    return register_store.read_register(register)


def write_register(
    location: str | OnChipCoordinate,
    register,
    value: int,
    noc_id: int = 0,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
) -> None:
    """
    Writes value to a register on the core.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, or OnChipCoordinate object.
        register (str | TensixRegisterDescription): Configuration or debug register to read from (name or instance of ConfigurationRegisterDescription or DebugRegisterDescription).
                                                    ConfigurationRegisterDescription(id, mask, shift), DebugRegisterDescription(addr).
        value (int): Value to write to the register.
        noc_id (int, default 0): NOC ID to use.
        neo_id (int | None, optional): NEO ID of the register store.
        device_id (int, default 0):	ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
    """

    from ttexalens.register_store import RegisterDescription

    coordinate = convert_coordinate(location, device_id, context)

    if not isinstance(register, RegisterDescription) and not isinstance(register, str):
        raise TTException(
            f"Invalid register type. Must be an str or instance of RegisterDescription or its subclasses, but got {type(register)}"
        )

    register_store = coordinate.noc_block.get_register_store(noc_id, neo_id)
    register_store.write_register(register, value)


def parse_elf(elf_path: str, context: Context | None = None) -> ParsedElfFile:
    """
    Reads the ELF file and returns a ParsedElfFile object.
    Args:
        elf_path (str): Path to the ELF file.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized. Default: None
    """
    context = check_context(context)
    return read_elf(context.server_ifc, elf_path)


def top_callstack(
    pc: int,
    elfs: list[str] | str | list[ParsedElfFile] | ParsedElfFile,
    offsets: int | None | list[int | None] = None,
    context: Context | None = None,
) -> list:

    """
    Retrieves the top frame of the callstack for the specified PC on the given ELF.
    There is no stack walking, so the function will return the function at the given PC and all inlined functions on the top frame (if there are any).

    Args:
        pc (int): Program counter to be used for the callstack.
        elfs (list[str] | str | list[ParsedElfFile] | ParsedElfFile): ELF files to be used for the callstack.
        offsets (list[int], int, optional): List of offsets for each ELF file. Default: None.
        context (Context): TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None
    Returns:
        List: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.
    """

    from ttexalens.hardware.risc_debug import RiscDebug

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

    elfs = RiscDebug._read_elfs(elfs, offsets)
    elf, frame_description = RiscDebug._find_elf_and_frame_description(elfs, pc, None)
    if frame_description is None or elf is None:
        return []
    return RiscDebug.get_frame_callstack(elf, pc)[0]


def callstack(
    location: str | OnChipCoordinate,
    elfs: list[str] | str | list[ParsedElfFile] | ParsedElfFile,
    offsets: int | None | list[int | None] = None,
    risc_name: str = "brisc",
    neo_id: int | None = None,
    max_depth: int = 100,
    stop_on_main: bool = True,
    device_id: int = 0,
    context: Context | None = None,
) -> list:
    """
    Retrieves the callstack of the specified RISC core for a given ELF.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        elfs (list[str] | str | list[ParsedElfFile] | ParsedElfFile): ELF files to be used for the callstack.
        offsets (list[int], int, optional): List of offsets for each ELF file. Default: None.
        risc_name (str): RISC-V core name (e.g. "brisc", "trisc0", etc.).
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        max_depth (int): Maximum depth of the callstack. Default: 100.
        stop_on_main (bool): If True, stops at the main function. Default: True.
        device_id (int): ID of the device on which the kernel is run. Default: 0.
        context (Context): TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None
    Returns:
        List: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.
    """

    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context

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

    if max_depth <= 0:
        raise ValueError("Max depth must be greater than 0.")

    risc_debug = coordinate.noc_block.get_risc_debug(risc_name, neo_id)
    if risc_debug.is_in_reset():
        raise TTException(f"RiscV core {risc_debug.risc_location} is in reset")
    return risc_debug.get_callstack(elfs, offsets, max_depth, stop_on_main)


def coverage(
    location: str | OnChipCoordinate,
    elf: str | ParsedElfFile,
    gcda_path: str,
    gcno_copy_path: str | None = None,
    device_id: int = 0,
    context: Context | None = None,
) -> None:
    """
    Extract coverage data from the device.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        elf (str | ParsedElfFile): ELF file whose coverage should be extracted.
        gcda_path (str): The path where the gcda file will be written.
        gcno_copy_path (str | None, optional): The path where the gcno will be written, if specified.
        device_id (int, optional): ID of the device to read from. Default 0.
        context (Context | None, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """

    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context
    if isinstance(elf, str):
        elf = parse_elf(elf, context)

    from ttexalens.coverage import dump_coverage

    dump_coverage(elf, coordinate, gcda_path, gcno_copy_path)


def read_riscv_memory(
    location: str | OnChipCoordinate,
    addr: int,
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
) -> int:

    """
    Reads a 32-bit word from the specified RISC-V core's private memory.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to read from.
        risc_name (str): RISC-V core name (e.g. "brisc", "trisc0", etc.).
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        device_id (int): ID number of device to read from. Default 0.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
        int: Data read from the device.
    """

    coordinate = convert_coordinate(location, device_id, context)

    risc_debug = coordinate.noc_block.get_risc_debug(risc_name, neo_id)
    private_memory = risc_debug.get_data_private_memory()
    if private_memory is None:
        raise TTException(f"RISC-V core {risc_debug.risc_location} does not have private memory.")
    if private_memory.address.private_address is None:
        raise TTException(f"RISC-V core {risc_debug.risc_location} does not have private memory address.")

    base_address = private_memory.address.private_address
    size = private_memory.size

    if addr < base_address or addr >= base_address + size:
        raise ValueError(
            f"Invalid address {hex(addr)}. Address must be between {hex(base_address)} and {hex(base_address + size - 1)}."
        )

    with risc_debug.ensure_private_memory_access():
        return risc_debug.read_memory(addr)


def write_riscv_memory(
    location: str | OnChipCoordinate,
    addr: int,
    value: int,
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
) -> None:
    """
    Writes a 32-bit word to the specified RISC-V core's private memory.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to read from.
        value (int): Value to write.
        risc_name (str): RISC-V core name (e.g. "brisc", "trisc0", etc.).
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        device_id (int): ID number of device to read from. Default 0.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """

    coordinate = convert_coordinate(location, device_id, context)

    risc_debug = coordinate.noc_block.get_risc_debug(risc_name, neo_id)
    private_memory = risc_debug.get_data_private_memory()

    if value < 0 or value > 0xFFFFFFFF:
        raise ValueError(f"Invalid value {value}. Value must be a 32-bit unsigned integer.")
    if private_memory is None:
        raise TTException(f"RISC-V core {risc_debug.risc_location} does not have private memory.")
    if private_memory.address.private_address is None:
        raise TTException(f"RISC-V core {risc_debug.risc_location} does not have private memory address.")

    base_address = private_memory.address.private_address
    size = private_memory.size

    if addr < base_address or addr >= base_address + size:
        raise ValueError(
            f"Invalid address {hex(addr)}. Address must be between {hex(base_address)} and {hex(base_address + size - 1)}."
        )

    with risc_debug.ensure_private_memory_access():
        risc_debug.write_memory(addr, value)
