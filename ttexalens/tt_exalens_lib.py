# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from contextlib import suppress
from dataclasses import dataclass
import datetime
from enum import Enum, auto
from functools import partial
import os
import struct
from typing import Callable

from ttexalens import util
from ttexalens._lib_helpers import (
    check_context,
    check_noc_id,
    convert_coordinate,
    trace_api,
    validate_addr,
    validate_device_id,
)
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context, NocId
from ttexalens.elf import read_elf, CallstackEntry, ElfFile, ElfVariable, get_callstack, get_frame_callstack
from ttexalens.exceptions import RiscHaltError, TTException
from ttexalens.hardware.baby_risc_debug import RISCV_REGISTER_NAMES_BY_INDEX
from ttexalens.hardware.blackhole.tensix_register_description import BlackholeTensixRegisterDescription
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.hardware.rocket_core_debug import RocketCoreDebug
from ttexalens.hardware.wormhole.tensix_register_description import WormholeTensixRegisterDescription
from ttexalens.memory_access import create_memory_access
from ttexalens.memory_map import MemoryMapBlockInfo
from ttexalens.register_store import ConfigurationRegisterDescription


@trace_api
def read_word_from_device(
    location: str | OnChipCoordinate,
    addr: int,
    device_id: int = 0,
    context: Context | None = None,
    noc_id: NocId | int | None = None,
    safe_mode: bool | None = None,
    register_access: bool | None = None,
) -> int:
    """
    Reads one four-byte word of data, from address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to read from.
        device_id (int, default 0):	ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        noc_id (NocId, int, optional): NOC ID to use. If None, it will be set based on context initialization.
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.
        register_access (bool, optional): Whether to access the address as a register, 4 bytes at a time and without DMA. If False, bulk access is used. If None, it is decided based on memory map: everything outside of L1 and DRAM is accessed as a register.

    Returns:
        int: Data read from the device.
    """

    coordinate = convert_coordinate(location, device_id, context)
    validate_addr(addr)
    noc_id = check_noc_id(noc_id, coordinate.context)

    return coordinate.noc_read32(addr, noc_id, safe_mode=safe_mode, register_access=register_access)


@trace_api
def read_words_from_device(
    location: str | OnChipCoordinate,
    addr: int,
    device_id: int = 0,
    word_count: int = 1,
    context: Context | None = None,
    noc_id: NocId | int | None = None,
    safe_mode: bool | None = None,
    register_access: bool | None = None,
) -> list[int]:
    """
    Reads word_count four-byte words of data, starting from address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to read from.
        device_id (int, default 0):	ID number of device to read from.
        word_count (int, default 1): Number of 4-byte words to read.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        noc_id (NocId, int, optional): NOC ID to use. If None, it will be set based on context initialization.
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.
        register_access (bool, optional): Whether to access the address as a register, 4 bytes at a time and without DMA. If False, bulk access is used. If None, it is decided based on memory map: everything outside of L1 and DRAM is accessed as a register.

    Returns:
        list[int]: Data read from the device.
    """

    coordinate = convert_coordinate(location, device_id, context)
    validate_addr(addr)
    noc_id = check_noc_id(noc_id, coordinate.context)
    if word_count <= 0:
        raise TTException("word_count must be greater than 0.")

    buffer = bytearray(4 * word_count)
    coordinate.noc_read(addr, buffer, noc_id, safe_mode=safe_mode, register_access=register_access)
    data = list(struct.unpack(f"<{word_count}I", buffer))
    return data


@trace_api
def read_from_device(
    location: str | OnChipCoordinate,
    addr: int,
    device_id: int = 0,
    num_bytes: int = 4,
    context: Context | None = None,
    noc_id: NocId | int | None = None,
    safe_mode: bool | None = None,
    register_access: bool | None = None,
) -> bytes:
    """
    Reads num_bytes of data starting from address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to read from.
        device_id (int, default 0): ID number of device to read from.
        num_bytes (int, default 4): Number of bytes to read.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        noc_id (NocId, int, optional): NOC ID to use. If None, it will be set based on context initialization.
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.
        register_access (bool, optional): Whether to access the address as a register, 4 bytes at a time and without DMA. If False, bulk access is used. If None, it is decided based on memory map: everything outside of L1 and DRAM is accessed as a register.

    Returns:
        bytes: Data read from the device.
    """

    coordinate = convert_coordinate(location, device_id, context)
    validate_addr(addr)
    noc_id = check_noc_id(noc_id, coordinate.context)
    if num_bytes <= 0:
        raise TTException("num_bytes must be greater than 0.")

    buffer = bytearray(num_bytes)
    coordinate.noc_read(addr, buffer, noc_id, safe_mode=safe_mode, register_access=register_access)
    return bytes(buffer)


@trace_api
def write_words_to_device(
    location: str | OnChipCoordinate,
    addr: int,
    data: int | list[int],
    device_id: int = 0,
    context: Context | None = None,
    noc_id: NocId | int | None = None,
    safe_mode: bool | None = None,
    register_access: bool | None = None,
):
    """
    Writes data word to address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int): Memory address to write to. If multiple words are to be written, the address is the starting address.
        data (int | list[int]): 4-byte integer word to be written, or a list of them.
        device_id (int, default 0): ID number of device to write to.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        noc_id (NocId, int, optional): NOC ID to use. If None, it will be set based on context initialization.
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.
        register_access (bool, optional): Whether to access the address as a register, 4 bytes at a time and without DMA. If False, bulk access is used. If None, it is decided based on memory map: everything outside of L1 and DRAM is accessed as a register.
    """

    coordinate = convert_coordinate(location, device_id, context)
    validate_addr(addr)
    noc_id = check_noc_id(noc_id, coordinate.context)

    if isinstance(data, int):
        coordinate.noc_write32(addr, data, noc_id, safe_mode=safe_mode, register_access=register_access)
    else:
        byte_data = b"".join(x.to_bytes(4, "little") for x in data)
        coordinate.noc_write(addr, byte_data, noc_id, safe_mode=safe_mode, register_access=register_access)


@trace_api
def write_to_device(
    location: str | OnChipCoordinate,
    addr: int,
    data: list[int] | bytes,
    device_id: int = 0,
    context: Context | None = None,
    noc_id: NocId | int | None = None,
    safe_mode: bool | None = None,
    register_access: bool | None = None,
):
    """
    Writes data to address 'addr' at specified location using specified noc.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        addr (int):	Memory address to write to.
        data (list[int] | bytes): Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
        device_id (int, default 0):	ID number of device to write to.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        noc_id (NocId, int, optional): NOC ID to use. If None, it will be set based on context initialization.
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.
        register_access (bool, optional): Whether to access the address as a register, 4 bytes at a time and without DMA. If False, bulk access is used. If None, it is decided based on memory map: everything outside of L1 and DRAM is accessed as a register.
    """

    coordinate = convert_coordinate(location, device_id, context)
    validate_addr(addr)
    noc_id = check_noc_id(noc_id, coordinate.context)

    if isinstance(data, list):
        data = bytes(data)

    if len(data) == 0:
        raise TTException("Data to write must not be empty.")

    coordinate.noc_write(addr, data, noc_id, safe_mode=safe_mode, register_access=register_access)


@trace_api
def load_elf(
    elf_file: str | ElfFile,
    location: str | OnChipCoordinate | list[str | OnChipCoordinate],
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
    return_start_address: bool = False,
    verify_write: bool = True,
) -> None | int | list[int]:
    """
    Loads the given ELF file into the specified RISC core. RISC core must be in reset before loading the ELF.

    Args:
        elf_file (str | ElfFile): ELF file to be loaded.
        location (str | OnChipCoordinate | list[str | OnChipCoordinate]): One of the following:
            1. "all" to run the ELF on all cores;
            2. an X-Y (noc0/translated) or X,Y (logical) location of a core in string format;
            3. a list of X-Y (noc0/translated), X,Y (logical) or OnChipCoordinate locations of cores, possibly mixed;
            4. an OnChipCoordinate object.
        risc_name (str): RiscV name (e.g. "brisc", "trisc0", "trisc1", "trisc2", "ncrisc").
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        device_id (int, default 0):	ID number of device to run ELF on.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        return_start_address (bool, default False): If True, returns the start address of the loaded ELF.
        verify_write (bool, default True): If True, verifies that the ELF was written correctly to the device.
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
        device = validate_device_id(device_id, context)
        for block_loc in device.get_block_locations(block_type="functional_workers"):
            locations.append(block_loc)
    else:
        locations = [convert_coordinate(location, device_id, context)]

    if isinstance(elf_file, str):
        if not os.path.exists(elf_file):
            raise TTException(f"ELF file {elf_file} does not exist.")
        context = check_context(context)
        elf_file = read_elf(context.file_api, elf_file, require_debug_symbols=False)

    assert locations, "No valid core locations provided."
    returns = []
    for loc in locations:
        risc_debug = loc.noc_block.get_risc_debug(risc_name, neo_id)
        elf_loader = ElfLoader(risc_debug)
        start_address = elf_loader.load_elf(
            elf_file, return_start_address=return_start_address, verify_write=verify_write
        )
        if return_start_address:
            assert start_address is not None
            returns.append(start_address)
    if return_start_address:
        return returns if len(returns) > 1 else returns[0]
    else:
        return None


@trace_api
def run_elf(
    elf_file: str | ElfFile,
    location: str | OnChipCoordinate | list[str | OnChipCoordinate],
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
    verify_write: bool = True,
) -> None:
    """
    Loads the given ELF file into the specified RISC core and executes it. Similar to load_elf, but RISC core is taken out of reset after load.

    Args:
        elf_file (str | ElfFile): ELF file to be run.
        location (str | OnChipCoordinate | list[str | OnChipCoordinate]): One of the following:
            1. "all" to run the ELF on all cores;
            2. an X-Y (noc0/translated) or X,Y (logical) location of a core in string format;
            3. a list of X-Y (noc0/translated), X,Y (logical) or OnChipCoordinate locations of cores, possibly mixed;
            4. an OnChipCoordinate object.
        risc_name (str): RiscV name (e.g. "brisc", "trisc0", "trisc1", "trisc2", "ncrisc").
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        device_id (int, default 0):	ID number of device to run ELF on.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        verify_write (bool, default True): If True, verifies that the ELF was written correctly to the device.
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
        device = validate_device_id(device_id, context)
        for block_loc in device.get_block_locations(block_type="functional_workers"):
            locations.append(block_loc)
    else:
        locations = [convert_coordinate(location, device_id, context)]

    if isinstance(elf_file, str):
        if not os.path.exists(elf_file):
            raise TTException(f"ELF file {elf_file} does not exist.")
        context = check_context(context)
        elf_file = read_elf(context.file_api, elf_file, require_debug_symbols=False)

    assert locations, "No valid core locations provided."
    for loc in locations:
        risc_debug = loc.noc_block.get_risc_debug(risc_name, neo_id)
        elf_loader = ElfLoader(risc_debug)
        elf_loader.run_elf(elf_file, verify_write=verify_write)


@trace_api
def arc_msg(
    device_id: int,
    msg_code: int,
    wait_for_done: bool,
    args: list[int],
    timeout: datetime.timedelta,
    context: Context | None = None,
    noc_id: NocId | int | None = None,
) -> list[int]:
    """
    Sends an ARC message to the device.

    Args:
        device_id (int): ID number of device to send message to.
        msg_code (int): Message code to send.
        wait_for_done (bool): If True, waits for the message to be processed.
        args (list[int]): Arguments to the message.
        timeout (datetime.timedelta): Timeout.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        noc_id (NocId, int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
        list[int]: return code, reply0, reply1.
    """
    context = check_context(context)
    device = validate_device_id(device_id, context)
    noc_id = check_noc_id(noc_id, context)
    if timeout < datetime.timedelta(0):
        raise TTException("Timeout must be greater than or equal to 0.")

    return list(device.arc_msg(noc_id, msg_code, wait_for_done=wait_for_done, args=args, timeout=timeout))


@trace_api
def read_firmware_telemetry_entry(
    device_id: int, telemetry_tag: int | str, context: Context | None = None, noc_id: NocId | int | None = None
) -> int:
    """
    Reads a firmware telemetry entry from the device.

    Args:
        device_id (int): ID number of device to read telemetry from.
        telemetry_tag (int | str): Name or ID of the tag to read.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        noc_id (NocId, int, optional): NOC ID to use. If None, it will be set based on context initialization.

    Returns:
        int: Value of the telemetry entry.
    """
    context = check_context(context)
    device = validate_device_id(device_id, context)
    noc_id = check_noc_id(noc_id, context)

    return device.firmware_telemetry.read_entry(telemetry_tag, noc_id)


@trace_api
def read_register(
    location: str | OnChipCoordinate,
    register,
    noc_id: NocId | int | None = None,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
    safe_mode: bool | None = None,
) -> int:
    """
    Reads the value of a register from the noc location.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, or OnChipCoordinate object.
        register (str | RegisterDescription): Configuration or debug register to read from (name or instance of ConfigurationRegisterDescription or DebugRegisterDescription).
                                              ConfigurationRegisterDescription(id, mask, shift), DebugRegisterDescription(addr).
        noc_id (NocId, int, optional): NOC ID to use. If None, the architecture default is used (NOC1 on Wormhole/Blackhole, NOC0 on Quasar).
        neo_id (int | None, optional): NEO ID of the register store.
        device_id (int, default 0):	ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.

    Returns:
        int: Value of the configuration or debug register specified.
    """
    from ttexalens.register_store import RegisterDescription

    coordinate = convert_coordinate(location, device_id, context)
    noc_id = check_noc_id(noc_id, coordinate.context)

    if not isinstance(register, RegisterDescription) and not isinstance(register, str):
        raise TTException(
            f"Invalid register type. Must be an str or instance of RegisterDescription or its subclasses, but got {type(register)}"
        )
    register_store = coordinate.noc_block.get_register_store(noc_id, neo_id)
    return register_store.read_register(register, safe_mode=safe_mode)


@trace_api
def write_register(
    location: str | OnChipCoordinate,
    register,
    value: int,
    noc_id: NocId | int | None = None,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
    safe_mode: bool | None = None,
) -> None:
    """
    Writes value to a register on the noc location.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, or OnChipCoordinate object.
        register (str | TensixRegisterDescription): Configuration or debug register to read from (name or instance of ConfigurationRegisterDescription or DebugRegisterDescription).
                                                    ConfigurationRegisterDescription(id, mask, shift), DebugRegisterDescription(addr).
        value (int): Value to write to the register.
        noc_id (NocId, int, optional): NOC ID to use. If None, the architecture default is used (NOC1 on Wormhole/Blackhole, NOC0 on Quasar).
        neo_id (int | None, optional): NEO ID of the register store.
        device_id (int, default 0):	ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.
    """

    from ttexalens.register_store import RegisterDescription

    coordinate = convert_coordinate(location, device_id, context)
    noc_id = check_noc_id(noc_id, coordinate.context)

    if not isinstance(register, RegisterDescription) and not isinstance(register, str):
        raise TTException(
            f"Invalid register type. Must be an str or instance of RegisterDescription or its subclasses, but got {type(register)}"
        )

    register_store = coordinate.noc_block.get_register_store(noc_id, neo_id)
    register_store.write_register(register, value, safe_mode=safe_mode)


@trace_api
def parse_elf(elf_path: str, context: Context | None = None, require_debug_symbols: bool = True) -> ElfFile:
    """
    Reads the ELF file and returns a ElfFile object.
    Args:
        elf_path (str): Path to the ELF file.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized. Default: None
        require_debug_symbols (bool, optional): Whether to require debug symbols in the ELF file. Default: True
    """
    context = check_context(context)
    return read_elf(context.file_api, elf_path, require_debug_symbols=require_debug_symbols)


@trace_api
def parse_elfs(
    elfs: list[str] | str | list[ElfFile] | ElfFile,
    offsets: int | None | list[int | None],
    context: Context,
) -> list[ElfFile]:
    """
    Parses the given ELF file(s) and anchors each to its live load address.
    Args:
        elfs (list[str] | str | list[ElfFile] | ElfFile): ELF file(s) to parse, given as path(s), already-parsed
            ElfFile object(s), or a list mixing the two.
        offsets (int | None | list[int | None]): Load address offset for each ELF. May be None (no offset for any
            ELF), a single int, or a per-ELF list whose length must match the number of ELFs.
        context (Context): TTExaLens context object used for interaction with the device.
    """
    # If given a single path / ElfFile, convert to a list; parse any paths.
    if isinstance(elfs, str):
        elfs = [parse_elf(elfs, context)]
    elif isinstance(elfs, ElfFile):
        elfs = [elfs]
    else:
        elfs = [parse_elf(elf, context) if isinstance(elf, str) else elf for elf in elfs]

    offsets = offsets if offsets is not None else [None for _ in range(len(elfs))]
    if isinstance(offsets, int):
        offsets = [offsets]

    if len(offsets) != len(elfs):
        raise TTException("Number of offsets must match the number of elf files")

    loaded_elfs: list[ElfFile] = []
    for parsed_elf, offset in zip(elfs, offsets):
        offset = None if offset == 0 else offset
        if offset is not None:
            loaded_elfs.append(parsed_elf.with_load_address(offset))
        else:
            loaded_elfs.append(parsed_elf)
    return loaded_elfs


@trace_api
def get_global(
    location: str | OnChipCoordinate,
    elf: str | ElfFile,
    name: str,
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
    safe_mode: bool | None = None,
) -> ElfVariable:
    """
    Resolves a global (or static) variable by name from the given ELF and binds it to
    the specified RISC-V core, returning an ElfVariable that reads/writes the variable
    through its type. This wraps the construction of the underlying memory access so a
    typed read is as simple as a raw read_word_from_device call.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        elf (str | ElfFile): ELF file (path or already-parsed) that defines the variable.
        name (str): Name of the variable to resolve.
        risc_name (str): RISC-V core name (e.g. "brisc", "trisc0", etc.).
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        device_id (int, optional): ID of the device to access. Default 0.
        context (Context | None, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
        safe_mode (bool | None, optional): Whether to use safe mode for memory access. If None, it is decided based on context.

    Returns:
        ElfVariable: The resolved variable, bound to the core's memory for reading/writing.
    """
    coordinate = convert_coordinate(location, device_id, context)
    parsed_elf = parse_elf(elf, coordinate.context) if isinstance(elf, str) else elf
    risc_debug = coordinate.noc_block.get_risc_debug(risc_name, neo_id)
    memory_access = create_memory_access(risc_debug, safe_mode=safe_mode)
    return parsed_elf.get_global(name, memory_access)


@trace_api
def top_callstack(
    pc: int,
    elfs: list[str] | str | list[ElfFile] | ElfFile,
    offsets: int | None | list[int | None] = None,
    context: Context | None = None,
    extract_variables: bool = True,
) -> list[CallstackEntry]:
    """
    Retrieves the top frame of the callstack for the specified PC on the given ELF.
    There is no stack walking, so the function will return the function at the given PC and all inlined functions on the top frame (if there are any).

    Args:
        pc (int): Program counter to be used for the callstack.
        elfs (list[str] | str | list[ElfFile] | ElfFile): ELF files to be used for the callstack.
        offsets (list[int], int, optional): List of offsets for each ELF file. Default: None.
        context (Context): TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None
        extract_variables (bool): If True, collect each frame's arguments, locals and template parameters. Default: True.

    Returns:
        List: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.
    """

    context = check_context(context)
    elfs_loaded = parse_elfs(elfs, offsets, context)
    return get_frame_callstack(elfs_loaded, pc, extract_variables=extract_variables)


@trace_api
def callstack(
    location: str | OnChipCoordinate,
    elfs: list[str] | str | list[ElfFile] | ElfFile,
    offsets: int | None | list[int | None] = None,
    risc_name: str = "brisc",
    neo_id: int | None = None,
    max_depth: int = 100,
    stop_on_main: bool = True,
    device_id: int = 0,
    context: Context | None = None,
    extract_variables: bool = True,
    expand_tail_call_inline_frames: bool = False,
) -> list[CallstackEntry]:
    """
    Retrieves the callstack of the specified RISC core for a given ELF.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        elfs (list[str] | str | list[ElfFile] | ElfFile): ELF files to be used for the callstack.
        offsets (list[int], int, optional): List of offsets for each ELF file. Default: None.
        risc_name (str): RISC-V core name (e.g. "brisc", "trisc0", etc.).
        neo_id (int | None, optional): NEO ID of the RISC-V core.
        max_depth (int): Maximum depth of the callstack. Default: 100.
        stop_on_main (bool): If True, stops at the main function. Default: True.
        device_id (int): ID of the device on which the kernel is run. Default: 0.
        context (Context): TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None
        extract_variables (bool): If True, collect each frame's arguments, locals and template parameters. Default: True.
        expand_tail_call_inline_frames (bool): If True, a reconstructed tail-call frame is expanded into its full inlined-function chain (name and source line only) instead of the single innermost frame GDB reports. Default: False.

    Returns:
        List: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.
    """

    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context

    if max_depth <= 0:
        raise ValueError("Max depth must be greater than 0.")

    elfs_loaded = parse_elfs(elfs, offsets, context)

    risc_debug = coordinate.noc_block.get_risc_debug(risc_name, neo_id)
    if risc_debug.is_in_reset():
        raise TTException(f"RiscV core {risc_debug.risc_location} is in reset")

    with risc_debug.ensure_halted():
        # Reading the program counter from risc register
        pc = risc_debug.read_gpr(32)

        # TODO: #1071
        if not isinstance(risc_debug, RocketCoreDebug):
            # If ebreak was hit, pc will point to the instruction after it
            if risc_debug.is_ebreak_hit():
                # Rewind pc to unwind callstack from the ebreak instruction
                pc -= 4

        mem_access = create_memory_access(risc_debug)

        # Walk the frames natively. The live-PC read and ebreak fix-up stay here
        # because they need the RiscDebug instance.
        return get_callstack(
            elfs_loaded,
            pc,
            mem_access,
            max_depth,
            "main" if stop_on_main else "",
            extract_variables=extract_variables,
            expand_tail_call_inline_frames=expand_tail_call_inline_frames,
        )


@trace_api
def coverage(
    location: str | OnChipCoordinate,
    elf: str | ElfFile,
    gcda_path: str,
    gcno_copy_path: str | None = None,
    device_id: int = 0,
    context: Context | None = None,
) -> None:
    """
    Extract coverage data from the device.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        elf (str | ElfFile): ELF file whose coverage should be extracted.
        gcda_path (str): The path where the gcda file will be written.
        gcno_copy_path (str | None, optional): The path where the gcno will be written, if specified.
        device_id (int, optional): ID of the device to read from. Default 0.
        context (Context | None, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
    """

    coordinate = convert_coordinate(location, device_id, context)
    context = coordinate.context
    parsed_elf: ElfFile
    if isinstance(elf, str):
        parsed_elf = parse_elf(elf, context)
    else:
        parsed_elf = elf

    from ttexalens.coverage import dump_coverage

    dump_coverage(parsed_elf, coordinate, gcda_path, gcno_copy_path)


@trace_api
def read_riscv_memory(
    location: str | OnChipCoordinate,
    addr: int,
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
    safe_mode: bool | None = None,
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
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.

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

    buffer = bytearray(4)
    create_memory_access(risc_debug, safe_mode=safe_mode).read(addr, buffer)
    return int.from_bytes(buffer, byteorder="little")


@trace_api
def write_riscv_memory(
    location: str | OnChipCoordinate,
    addr: int,
    value: int,
    risc_name: str,
    neo_id: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
    safe_mode: bool | None = None,
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
        safe_mode (bool, optional): Whether to use safe mode for the operation. If True, additional checks are performed to ensure safe access to only known to be safe memory regions. If None, it will be used based on context.
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

    create_memory_access(risc_debug, safe_mode=safe_mode).write(addr, value.to_bytes(4, byteorder="little"))


@dataclass
class TensixState:
    alu_config: list[dict[str, int]]
    unpack_config: list[dict[str, int]]
    unpack_tile_descriptor: list[dict[str, int]]
    pack_config: list[dict[str, int]]
    relu_config: list[dict[str, int]]
    pack_dest_rd_ctrl: list[dict[str, int]]
    pack_edge_offset: list[dict[str, int]]
    pack_counters: list[dict[str, int]]
    pack_strides: list[dict[str, int]]
    gpr: list[dict[str, int]]
    register_window_counters: dict[str, int]
    address_counters: dict[str, int]


@trace_api
def get_tensix_state(
    location: str | OnChipCoordinate,
    l1_address: int | None = None,
    device_id: int = 0,
    context: Context | None = None,
) -> TensixState:
    """
    Gets the tensix state for the given device and location.
    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
        l1_address (int, optional): L1 address to use for reading debug bus signals atomically. If None, debug bus signals are read unsafely.
        device_id (int, default 0):	ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
    Returns:
        TensixState: Tensix state for the given device and location.
    """
    coordinate = convert_coordinate(location, device_id, context)
    device = coordinate.device
    tensix_reg_desc = device.get_tensix_registers_description()
    assert isinstance(tensix_reg_desc, WormholeTensixRegisterDescription | BlackholeTensixRegisterDescription)
    tensix_debug_bus_desc = device.get_tensix_debug_bus_description()
    noc_block = coordinate.noc_block
    if noc_block.block_type != "functional_workers":
        raise ValueError(f"Tensix state can only be retrieved from a tensix block. Got {noc_block.block_type} block.")
    register_store = noc_block.get_register_store()
    debug_bus = noc_block.debug_bus
    assert debug_bus is not None, "Debug bus is not available for the given location."

    def _read_register_group(group: list[dict[str, str]]) -> list[dict[str, int]]:
        return [
            {key: register_store.read_register(register) for key, register in group[i].items()}
            for i in range(len(group))
        ]

    from ttexalens.debug_bus_signal_store import SignalGroupSample

    def _read_signal_groups(groups: list[str], group_reader: Callable[[str], SignalGroupSample]) -> dict[str, int]:
        groups_sample = {signal_group: group_reader(signal_group) for signal_group in groups}
        return {
            signal_name: group_data[signal_name]
            for group_data in groups_sample.values()
            for signal_name in group_data.keys()
        }

    alu = _read_register_group(tensix_reg_desc.alu_config)
    unpack_config = _read_register_group(tensix_reg_desc.unpack_config)
    unpack_tile_descriptor = _read_register_group(tensix_reg_desc.unpack_tile_descriptor)
    pack_config = _read_register_group(tensix_reg_desc.pack_config)
    relu_config = _read_register_group(tensix_reg_desc.relu_config)
    pack_dest_rd_ctrl = _read_register_group(tensix_reg_desc.pack_dest_rd_ctrl)
    pack_edge_offset = _read_register_group(tensix_reg_desc.pack_edge_offset)
    pack_counters = _read_register_group(tensix_reg_desc.pack_counters)
    pack_strides = _read_register_group(tensix_reg_desc.pack_strides)
    gpr = _read_register_group(tensix_reg_desc.general_purpose_registers)
    group_reader = lambda signal_group: (
        debug_bus.read_signal_group(signal_group, l1_address)
        if l1_address is not None
        else debug_bus.read_signal_group_unsafe(signal_group)
    )
    if l1_address is None:
        if util.DEBUG_ENABLED:
            util.DEBUG("No L1 address provided. Disabling atomic group reading ADC and RWC groups.")
    rwc = _read_signal_groups(tensix_debug_bus_desc.register_window_counter_groups, group_reader)
    adc = _read_signal_groups(tensix_debug_bus_desc.address_counter_groups, group_reader)
    return TensixState(
        alu_config=alu,
        unpack_config=unpack_config,
        unpack_tile_descriptor=unpack_tile_descriptor,
        pack_config=pack_config,
        relu_config=relu_config,
        pack_dest_rd_ctrl=pack_dest_rd_ctrl,
        pack_edge_offset=pack_edge_offset,
        pack_counters=pack_counters,
        pack_strides=pack_strides,
        gpr=gpr,
        register_window_counters=rwc,
        address_counters=adc,
    )


class BlockStateEntryKind(Enum):
    """
    What a BlockStateEntry holds. NOC_REGION is a region of the block's NOC memory map, read over the NOC. PRIVATE_REGION is a region of a RISC's memory map read through that RISC at its private address, or the block's configuration registers read through their select register. DEBUG_BUS_GROUP is one debug-bus signal group. GPR is one general purpose register of a RISC, or its PC. DEBUG_HARDWARE_REGISTER is one register of a RISC's debug hardware.
    """

    NOC_REGION = auto()
    PRIVATE_REGION = auto()
    DEBUG_BUS_GROUP = auto()
    GPR = auto()
    DEBUG_HARDWARE_REGISTER = auto()


@dataclass
class BlockStateEntry:
    """
    One piece of a block's state, as read_block_state and halt_and_read_risc_state return it. name is the region, debug-bus group or register name from tt-exalens, or None for an entry about a whole RISC. risc_name is the RISC whose view or register the entry holds, or None for what belongs to the block. address is the NOC address of a NOC region and the private address of a private region, else None. size is in bytes. data holds the raw bytes as the device stores them; when it is None, reason says why.
    """

    kind: BlockStateEntryKind
    name: str | None
    risc_name: str | None
    address: int | None
    size: int
    data: bytes | None
    reason: str | None


def _error_reason(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"


def _unreadable_reason(region: MemoryMapBlockInfo, address: int) -> str | None:
    if not region.is_safe_to_read(address, region.memory_block.size):
        return "unsafe to read"
    if not region.is_accessible:
        return "not accessible"
    return None


def _read_entry(
    kind: BlockStateEntryKind, name: str, address: int | None, size: int, read: Callable[[], bytes]
) -> BlockStateEntry:
    try:
        return BlockStateEntry(kind, name, None, address, size, read(), None)
    except Exception as error:
        return BlockStateEntry(kind, name, None, address, size, None, _error_reason(error))


def _read_region_entry(
    kind: BlockStateEntryKind, region: MemoryMapBlockInfo, address: int, read: Callable[[], bytes]
) -> BlockStateEntry:
    size = region.memory_block.size
    reason = _unreadable_reason(region, address)
    if reason is not None:
        return BlockStateEntry(kind, region.name, None, address, size, None, reason)
    return _read_entry(kind, region.name, address, size, read)


def _read_noc_bytes(coordinate: OnChipCoordinate, address: int, size: int) -> bytes:
    # Names no NOC, so the read fails over to the other NOC if one hangs.
    buffer = bytearray(size)
    coordinate.noc_read(address, buffer)
    return bytes(buffer)


def _configuration_registers(risc: RiscDebug) -> MemoryMapBlockInfo | None:
    # The region RegisterStore reads configuration registers from, found the way RegisterStore finds it.
    return risc.risc_info.memory_map.find_by_name("config_regs")


def _noc_regions(coordinate: OnChipCoordinate) -> list[tuple[MemoryMapBlockInfo, int]]:
    regions: list[tuple[MemoryMapBlockInfo, int]] = []
    for region in coordinate.noc_block.noc_memory_map.blocks:
        noc_address = region.memory_block.address.noc_address
        assert noc_address is not None, "A region of a NOC memory map has a NOC address."
        regions.append((region, noc_address))
    # A NOC read of L1 can set ECC status bits in the debug registers, so registers are stored before L1 is read.
    regions.sort(
        key=lambda item: not coordinate.device.is_register_access(coordinate, item[1], item[0].memory_block.size)
    )
    return regions


@trace_api
def read_block_state(
    location: str | OnChipCoordinate,
    device_id: int = 0,
    context: Context | None = None,
) -> list[BlockStateEntry]:
    """
    Reads the raw state of one Tensix or Ethernet block without halting a core or sending one a command.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, or OnChipCoordinate object.
        device_id (int, default 0): ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
        list[BlockStateEntry]: The entries in read order: every debug-bus group, each region of the block's NOC memory map with register regions first and L1 last, the configuration registers through their select register, then the registers of each RISC's debug hardware. A region or RISC that isn't read has an entry with a reason instead of data, such as "unsafe to read", "not accessible", "no debug hardware", "in reset" or the error its read raised.

    Notes:
        - A region is read only when its memory map calls it accessible and safe to read.
        - A read can change what a later one returns. A NOC read of L1 can set ECC status bits in the debug registers, so the register regions are read before L1.
        - The NIU counters of the NOC the reads go through (NOC1 by default) count this function's own reads, so their returned values are higher than before the call. The returned debug_regs region also holds the debug-bus select value this function wrote last.
        - On Blackhole the NOC memory map marks each RISC's data private memory unsafe to read (tt-exalens#907), so it has a reason here; halt_and_read_risc_state reads it through the RISC.
        - A device timeout (TimeoutDeviceRegisterError) is raised, not returned as a reason.
        - Quasar is not covered.
    """
    coordinate = convert_coordinate(location, device_id, context)
    block = coordinate.noc_block
    entries: list[BlockStateEntry] = []

    debug_bus = block.get_debug_bus()
    if debug_bus is not None:
        sample_size = debug_bus.L1_SAMPLE_SIZE_BYTES
        for group in sorted(debug_bus.group_names):
            entries.append(
                _read_entry(
                    BlockStateEntryKind.DEBUG_BUS_GROUP,
                    group,
                    None,
                    sample_size,
                    lambda: debug_bus.read_signal_group_unsafe(group).raw_data.to_bytes(
                        sample_size, byteorder="little"
                    ),
                )
            )

    for region, noc_address in _noc_regions(coordinate):
        entries.append(
            _read_region_entry(
                BlockStateEntryKind.NOC_REGION,
                region,
                noc_address,
                partial(_read_noc_bytes, coordinate, noc_address, region.memory_block.size),
            )
        )

    config_regs = _configuration_registers(block.get_default_risc_debug())
    if config_regs is not None:
        private_address = config_regs.memory_block.address.private_address
        assert private_address is not None, "Configuration registers have a private address."
        size = config_regs.memory_block.size
        register_store = block.get_register_store()
        registers = ConfigurationRegisterDescription(index=0, size=size)
        entries.append(
            _read_region_entry(
                BlockStateEntryKind.PRIVATE_REGION,
                config_regs,
                private_address,
                lambda: register_store.read_register(registers).to_bytes(size, byteorder="little"),
            )
        )

    for risc in block.all_riscs:
        risc_name = risc.risc_location.risc_name
        debug_registers: dict[str, int] = {}
        reason = "no debug hardware" if not risc.can_debug() else "in reset" if risc.is_in_reset() else None
        if reason is None:
            try:
                debug_registers = risc.read_debug_hardware_registers()
            except Exception as error:
                reason = _error_reason(error)
        for name, value in debug_registers.items():
            data = value.to_bytes(4, byteorder="little")
            entries.append(
                BlockStateEntry(BlockStateEntryKind.DEBUG_HARDWARE_REGISTER, name, risc_name, None, 4, data, None)
            )
        if reason is not None:
            entries.append(
                BlockStateEntry(BlockStateEntryKind.DEBUG_HARDWARE_REGISTER, None, risc_name, None, 0, None, reason)
            )
    return entries


def _private_regions(block: NocBlock, risc: RiscDebug) -> list[MemoryMapBlockInfo]:
    """The regions of a RISC's memory map that read_block_state doesn't cover."""
    config_regs = _configuration_registers(risc)
    regions: list[MemoryMapBlockInfo] = []
    for region in risc.risc_info.memory_map.blocks:
        address = region.memory_block.address
        if address.private_address is None:
            continue
        if address.noc_address is not None:
            noc_region = block.noc_memory_map.find_by_noc_address(address.noc_address)
            if noc_region is not None:
                noc_region_address = noc_region.memory_block.address.noc_address
                assert noc_region_address is not None, "A region of a NOC memory map has a NOC address."
                if _unreadable_reason(noc_region, noc_region_address) is None:
                    continue
        if config_regs is not None and region.name == config_regs.name:
            continue
        regions.append(region)
    return regions


def _read_private_bytes(risc: RiscDebug, address: int, size: int) -> bytes:
    buffer = bytearray(size)
    view = memoryview(buffer)
    # One word per call, so the RISC's own address check sees every word.
    for offset in range(0, size, 4):
        risc.read_memory_bytes(address + offset, view[offset : offset + 4])
    return bytes(buffer)


def _read_private_region(risc: RiscDebug, region: MemoryMapBlockInfo, risc_reason: str | None) -> BlockStateEntry:
    address = region.memory_block.address.private_address
    assert address is not None, "A region read through a RISC has a private address."
    size = region.memory_block.size
    data = None
    reason = _unreadable_reason(region, address) or risc_reason
    if reason is None and not risc.is_halted():
        reason = "didn't stay halted"
    if reason is None:
        try:
            data = _read_private_bytes(risc, address, size)
        except Exception as error:
            reason = _error_reason(error)
        if data is not None and not risc.is_halted():
            data, reason = None, "didn't stay halted"
    return BlockStateEntry(
        BlockStateEntryKind.PRIVATE_REGION, region.name, risc.risc_location.risc_name, address, size, data, reason
    )


@trace_api
def halt_and_read_risc_state(
    location: str | OnChipCoordinate,
    device_id: int = 0,
    context: Context | None = None,
) -> list[BlockStateEntry]:
    """
    Halts every RISC of one Tensix or Ethernet block that can be halted, then reads what only a halted core gives. The cores stay halted.

    Args:
        location (str | OnChipCoordinate): Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, or OnChipCoordinate object.
        device_id (int, default 0): ID number of device to read from.
        context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.

    Returns:
        list[BlockStateEntry]: For each RISC, its GPR entries (named as in RISCV_REGISTER_NAMES_BY_INDEX, with pc from get_pc), then an entry for each region of its memory map that read_block_state doesn't read, read through that RISC at its private address. A RISC that isn't read has one entry without a name that says why, and a region that isn't read has a reason instead of data.

    Notes:
        - Every RISC of the block is halted before the first read. Each one is checked to still report halted after the halt, after its GPRs and after each region, because on Blackhole a halted core can stop reporting halted; data read while that happened is not returned.
        - The cores are not continued: a halt can corrupt the instruction a core was executing, so continuing it can break the core (tt-exalens#908).
        - A remote chip's link cores get no command, because they are the chip's only path to the host and halting one cuts the chip off. Halting a local chip's link cores cuts off the chips reached through them, so call this for the blocks of those chips first.
        - A region that several RISCs list, such as dest, is read through each of them.
        - Regions are read 4 bytes at a time, so a RISC's own address check sees every word. On Blackhole, tt-exalens refuses reads through trisc2 at addresses where address % 16 is above 4, because its reads of private memory there return wrong data (tt-exalens#528). A region read through trisc2 therefore comes back with a reason, not data.
        - A device timeout (TimeoutDeviceRegisterError) is raised, not returned as a reason.
        - Quasar is not covered.
    """
    coordinate = convert_coordinate(location, device_id, context)
    block = coordinate.noc_block
    device = coordinate.device
    if not device.is_local and coordinate in device.active_eth_block_locations:
        return [
            BlockStateEntry(
                BlockStateEntryKind.GPR, None, risc.risc_location.risc_name, None, 0, None, "remote chip's link core"
            )
            for risc in block.all_riscs
        ]

    halt_reasons: list[str | None] = []
    for risc in block.all_riscs:
        if not risc.can_debug():
            halt_reasons.append("no debug hardware")
        elif risc.is_in_reset():
            halt_reasons.append("in reset")
        else:
            if not risc.is_halted():
                with suppress(RiscHaltError):
                    risc.halt()
            halt_reasons.append(None if risc.is_halted() else "didn't halt")

    entries: list[BlockStateEntry] = []
    for risc, reason in zip(block.all_riscs, halt_reasons):
        risc_name = risc.risc_location.risc_name
        if reason is None and not risc.is_halted():
            reason = "didn't stay halted"
        if reason is None:
            values = {
                name: risc.get_pc() if name == "pc" else risc.read_gpr(index)
                for index, name in RISCV_REGISTER_NAMES_BY_INDEX.items()
            }
            gprs_reason = None if risc.is_halted() else "didn't stay halted"
            for name, value in values.items():
                data = value.to_bytes(4, byteorder="little") if gprs_reason is None else None
                entries.append(BlockStateEntry(BlockStateEntryKind.GPR, name, risc_name, None, 4, data, gprs_reason))
        else:
            entries.append(BlockStateEntry(BlockStateEntryKind.GPR, None, risc_name, None, 0, None, reason))
        for region in _private_regions(block, risc):
            entries.append(_read_private_region(risc, region, reason))
    return entries
