# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import re
import struct

from functools import wraps
from typing import Union

from dbd import tt_debuda_init

from dbd.tt_coordinate import OnChipCoordinate
from dbd.tt_debuda_context import Context
from dbd.tt_debug_risc import RiscLoader
from dbd.tt_util import TTException



def read_words_from_device(
		core_loc: Union[str, OnChipCoordinate], 
		addr: int, 
		device_id: int = 0,
		word_count: int = 1,
		context: Context = None
) -> "list[int]":
	""" Reads word_count four-byte words of data, starting from address 'addr' at core <x-y>.
	
	Args:
		core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
		addr (int): Memory address to read from.
		device_id (int, default 0):	ID number of device to read from.
		word_count (int, default 1): Number of 4-byte words to read.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentailly initialized.
	
	Returns:
		list[int]: Data read from the device.
	"""
	context = check_context(context)
	
	validate_addr(addr)
	validate_device_id(device_id, context)
	if word_count <= 0: raise TTException("word_count must be greater than 0.")


	if not isinstance(core_loc, OnChipCoordinate):
		validate_core_loc(core_loc)
		core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])
	data = []
	for i in range(word_count):
		word = context.server_ifc.pci_read32(
			device_id, *core_loc.to("nocVirt"), addr + 4 * i
		)
		data.append(word)
	return data


def read_from_device(
		core_loc: Union[str, OnChipCoordinate],
		addr: int,
		device_id: int = 0,
		num_bytes: int = 4,
		context: Context = None
) -> bytes:
	""" Reads num_bytes of data starting from address 'addr' at core <x-y>.
	
	Args:
		core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
		addr (int): Memory address to read from.
		device_id (int, default 0): ID number of device to read from.
		num_bytes (int, default 4): Number of bytes to read.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	
	Returns:
		bytes: Data read from the device.
	"""
	context = check_context(context)

	validate_addr(addr)
	validate_device_id(device_id, context)
	if num_bytes <= 0: raise TTException("num_bytes must be greater than 0.")
	
	if not isinstance(core_loc, OnChipCoordinate):
		validate_core_loc(core_loc)
		core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])
	return context.server_ifc.pci_read(
		device_id, *core_loc.to("nocVirt"), addr, num_bytes
	)


def write_words_to_device(
		core_loc: Union[str, OnChipCoordinate],
		addr: int,
		data: Union[int, list[int]],
		device_id: int = 0,
		context: Context = None
) -> int:
	"""Writes data word to address 'addr' at noc0 location x-y of the current chip.
	
	Args:
	core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
	addr (int): Memory address to write to. If multiple words are to be written, the address is the starting address.
	data (int | list[int]): 4-byte integer word to be written, or a list of them.
	device_id (int, default 0): ID number of device to write to.
	context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentailly initialized.

	Returns:
	int: If the execution is successful, return value should be 4 (number of bytes written).
	"""
	context = check_context(context)

	validate_addr(addr)
	validate_device_id(device_id, context)
	
	if not isinstance(core_loc, OnChipCoordinate):
		validate_core_loc(core_loc)
		core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])

	if isinstance(data, int):
		data = [data]
	
	bytes_written = 0
	for i, word in enumerate(data):
		bytes_written += context.server_ifc.pci_write32(
			device_id, *core_loc.to("nocVirt"), addr + i*4, word
		)
	return bytes_written


def write_to_device(
		core_loc: Union[str, OnChipCoordinate],
		addr: int,
		data:"Union[list[int], bytes]",
		device_id: int = 0,
		context: Context = None
) -> int:
	"""Writes data to address 'addr' at noc0 location x-y of the current chip.
	
	Args:
		
	core_loc : str | OnChipCoordinate
		Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
	addr : int
		Memory address to write to.
	data : list[int] | bytes
		Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
	device_id : int, default 0
		ID number of device to write to.
	context : Context, optional
		Debuda context object used for interaction with device. If None, global context is used and
		potentailly initialized.

	Returns
	-------
	int
		If the execution is successful, return value should be number of bytes written.
	"""
	context = check_context(context)

	validate_addr(addr)
	validate_device_id(device_id, context)

	if isinstance(data, list):
		data = bytes(data)
	
	if len(data) == 0: raise TTException("Data to write must not be empty.")

	if not isinstance(core_loc, OnChipCoordinate):
		validate_core_loc(core_loc)
		core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])
	return context.server_ifc.pci_write(
		device_id, *core_loc.to("nocVirt"), addr, data
	)


def run_elf(elf_file: os.PathLike, core_loc: Union[str, OnChipCoordinate, list[Union[str, OnChipCoordinate]]], risc_id: int = 0, device_id: int = 0, context: Context = None) -> None:
	""" Loads the given ELF file into the specified RISC core and executes it.

	Args:
	elf_file (os.PathLike): Path to the ELF file to run.
	core_loc (str | OnChipCoordinate | list[str | OnChipCoordinate]): One of the following:
		1. "all" to run the ELF on all cores;
		2. an X-Y (nocTr) or R,C (netlist) location of a core in string format;
		3. a list of X-Y (nocTr), R,C (netlist) or OnChipCoordinate locations of cores, possibly mixed;
		4. an OnChipCoordinate object.
	risc_id (int, default 0): RiscV ID (0: brisc, 1-3 triscs).
	device_id (int, default 0):	ID number of device to run ELF on.
	context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	"""
	context = check_context(context)

	validate_device_id(device_id, context)
	if (risc_id < 0) or (risc_id > 3):
		raise TTException("Invalid RiscV ID. Must be between 0 and 3.")
	

	device = context.devices[device_id]
	device.all_riscs_assert_soft_reset()

	locs = []
	if isinstance(core_loc, OnChipCoordinate):
		locs = [core_loc]
	elif isinstance(core_loc, list):
		for loc in core_loc:
			if isinstance(loc, OnChipCoordinate):
				locs.append(loc)
			else:
				validate_core_loc(loc)
				locs.append(OnChipCoordinate.create(loc, device))
	elif core_loc == "all":
		for loc in device.get_block_locations(block_type="functional_workers"):
			locs.append(loc)
	else:
		validate_core_loc(core_loc)
		locs = [OnChipCoordinate.create(core_loc, device)]

	if not os.path.exists(elf_file): raise TTException(f"ELF file {elf_file} does not exist.")

	assert locs, "No valid core locations provided."
	for loc in locs:
		rloader = RiscLoader(loc, risc_id, context, context.server_ifc, False)
		rdbg = rloader.risc_debug

		risc_start_address = rloader.get_risc_start_address()
		rloader.start_risc_in_infinite_loop(risc_start_address)
		assert not rdbg.is_in_reset(), f"RISC at location {loc} is in reset."

		rdbg.enable_debug()
		if not rdbg.is_halted():
			rdbg.halt()

		init_section_address = rloader.load_elf(elf_file) # Load the elf file
		assert init_section_address is not None, "No .init section found in the ELF file"

		jump_to_start_of_init_section_instruction = rloader.get_jump_to_offset_instruction(init_section_address - risc_start_address)
		context.server_ifc.pci_write32(loc._device.id(), *loc.to("nocVirt"), risc_start_address, jump_to_start_of_init_section_instruction)

		# Invalidating instruction cache so that the jump instruction is actually loaded.
		rdbg.invalidate_instruction_cache()
		rdbg.cont()


def check_context(context: Context = None) -> Context:
	""" Function to initialize context if not provided. By default, it starts a local
	debuda session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
	that the context can be reused in calls to other functions.
	"""
	if context is not None:
		return context
	
	if not tt_debuda_init.GLOBAL_CONTEXT:
		tt_debuda_init.GLOBAL_CONTEXT = tt_debuda_init.init_debuda()
	return tt_debuda_init.GLOBAL_CONTEXT


def validate_core_loc(core_loc: str) -> None:
	if not re.match("^\d+,\d+$", core_loc) and not re.match("^\d+-\d+$", core_loc):
		raise TTException(f"Invalid core location: {core_loc}. Must be in the format 'X-Y' or 'R,C'.")

def validate_addr(addr: int) -> None:	
	if addr < 0: raise TTException("addr must be greater than or equal to 0.")

def validate_device_id(device_id: int, context: Context) -> None:
	if device_id not in context.device_ids: raise TTException(f"Invalid device_id {device_id}.")
