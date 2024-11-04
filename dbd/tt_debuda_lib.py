# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import re
import struct

from typing import Union, List

from dbd import tt_debuda_init

from dbd.tt_coordinate import OnChipCoordinate
from dbd.tt_debuda_context import Context
from dbd.tt_debug_risc import RiscLoader, RiscDebug, RiscLoc
from dbd.tt_util import TTException

import time

def read_words_from_device(
		core_loc: Union[str, OnChipCoordinate], 
		addr: int, 
		device_id: int = 0,
		word_count: int = 1,
		context: Context = None
) -> "List[int]":
	""" Reads word_count four-byte words of data, starting from address 'addr' at core <x-y>.
	
	Args:
		core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
		addr (int): Memory address to read from.
		device_id (int, default 0):	ID number of device to read from.
		word_count (int, default 1): Number of 4-byte words to read.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentailly initialized.
	
	Returns:
		List[int]: Data read from the device.
	"""
	context = check_context(context)
	
	validate_addr(addr)
	validate_device_id(device_id, context)
	if word_count <= 0: raise TTException("word_count must be greater than 0.")


	if not isinstance(core_loc, OnChipCoordinate):
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
		core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])
	return context.server_ifc.pci_read(
		device_id, *core_loc.to("nocVirt"), addr, num_bytes
	)


def write_words_to_device(
		core_loc: Union[str, OnChipCoordinate],
		addr: int,
		data: Union[int, List[int]],
		device_id: int = 0,
		context: Context = None
) -> int:
	"""Writes data word to address 'addr' at noc0 location x-y of the current chip.
	
	Args:
		core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
		addr (int): Memory address to write to. If multiple words are to be written, the address is the starting address.
		data (int | List[int]): 4-byte integer word to be written, or a list of them.
		device_id (int, default 0): ID number of device to write to.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentailly initialized.

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
		bytes_written += context.server_ifc.pci_write32(
			device_id, *core_loc.to("nocVirt"), addr + i*4, word
		)
	return bytes_written


def write_to_device(
		core_loc: Union[str, OnChipCoordinate],
		addr: int,
		data:"Union[List[int], bytes]",
		device_id: int = 0,
		context: Context = None
) -> int:
	"""Writes data to address 'addr' at noc0 location x-y of the current chip.
	
	Args:
		core_loc (str | OnChipCoordinate): Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
		addr (int):	Memory address to write to.
		data (List[int] | bytes): Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
		device_id (int, default 0):	ID number of device to write to.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentailly initialized.

	Returns:
		int: If the execution is successful, return value should be number of bytes written.
	"""
	context = check_context(context)

	validate_addr(addr)
	validate_device_id(device_id, context)

	if isinstance(data, list):
		data = bytes(data)
	
	if len(data) == 0: raise TTException("Data to write must not be empty.")

	if not isinstance(core_loc, OnChipCoordinate):
		core_loc = OnChipCoordinate.create(core_loc, device=context.devices[device_id])
	return context.server_ifc.pci_write(
		device_id, *core_loc.to("nocVirt"), addr, data
	)


def run_elf(elf_file: os.PathLike, core_loc: Union[str, OnChipCoordinate, List[Union[str, OnChipCoordinate]]], risc_id: int = 0, device_id: int = 0, context: Context = None) -> None:
	""" Loads the given ELF file into the specified RISC core and executes it.

	Args:
		elf_file (os.PathLike): Path to the ELF file to run.
		core_loc (str | OnChipCoordinate | List[str | OnChipCoordinate]): One of the following:
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

	if not os.path.exists(elf_file): raise TTException(f"ELF file {elf_file} does not exist.")

	assert locs, "No valid core locations provided."
	for loc in locs:
		rdbg = RiscDebug(RiscLoc(loc, 0, risc_id), context.server_ifc, False)
		rloader = RiscLoader(rdbg, context, False)
		rloader.run_elf(elf_file)


def check_context(context: Context = None) -> Context:
	""" Function to initialize context if not provided. By default, it starts a local
	Debuda session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
	that the context can be reused in calls to other functions.
	"""
	if context is not None:
		return context
	
	if not tt_debuda_init.GLOBAL_CONTEXT:
		tt_debuda_init.GLOBAL_CONTEXT = tt_debuda_init.init_debuda()
	return tt_debuda_init.GLOBAL_CONTEXT


def validate_addr(addr: int) -> None:	
	if addr < 0: raise TTException("addr must be greater than or equal to 0.")

def validate_device_id(device_id: int, context: Context) -> None:
	if device_id not in context.device_ids: raise TTException(f"Invalid device_id {device_id}.")

def arc_msg(device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int, context: Context = None) -> "List[int]":
	""" Sends an ARC message to the device.

	Args:
		device_id (int): ID number of device to send message to.
		msg_code (int): Message code to send.
		wait_for_done (bool): If True, waits for the message to be processed.
		arg0 (int): First argument to the message.
		arg1 (int): Second argument to the message.
		timeout (int): Timeout in milliseconds.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.

	Returns:
		List[int]: return code, reply0, reply1.
	"""
	context = check_context(context)

	validate_device_id(device_id, context)
	if timeout < 0: raise TTException("Timeout must be greater than or equal to 0.")

	return context.server_ifc.arc_msg(device_id, msg_code, wait_for_done, arg0, arg1, timeout)

def write_field(reg_addr: int, value: int, core_loc: OnChipCoordinate, bit_range: tuple = (0, 31), device_id: int = 0, context: Context = None) -> None:
	""" Write a value to a field in a register.

	Args:
		reg_addr (int): Register address to write to.
		value (int): Value to write to the field.
		core_loc (OnChipCoordinate): Core location.
		bit_range (tuple, default (0, 31)): Tuple of start and end bits of the field.
		device_id (int, default 0): ID number of device to write to.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	"""

	context = check_context(context)
	validate_device_id(device_id, context)

	start_bit, end_bit = bit_range
	if not (0 <= start_bit <= 31 and 0 <= end_bit <= 31 and start_bit <= end_bit):
		raise TTException("Invalid bit range. Must be between 0 and 31 and start_bit must be less than or equal to end_bit.")

	mask = ((1 << (end_bit - start_bit + 1)) - 1) << start_bit

	value = (value << start_bit) & mask
	
	if context.devices[device_id]._has_mmio:
		context.server_ifc.pci_write32_raw(
			device_id, reg_addr, value
		)
	else:
		context.server_ifc.pci_write32(
			device_id, *core_loc.to("nocVirt"), reg_addr, value
		)

def read_field(reg_addr: int, core_loc: OnChipCoordinate, bit_range: tuple = (0, 31), device_id: int = 0, context: Context = None) -> int:
	""" Read a value from a field in a register.

	Args:
		reg_addr (int): Register address to read from.
		core_loc (OnChipCoordinate): Core location.
		bit_range (tuple, default (0, 31)): Tuple of start and end bits of the field.
		device_id (int, default 0): ID number of device to read from.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	
	Returns:
		int: Value read from the field.
	"""
	context = check_context(context)
	validate_device_id(device_id, context)

	start_bit, end_bit = bit_range
	if not (0 <= start_bit <= 31 and 0 <= end_bit <= 31 and start_bit <= end_bit):
		raise TTException("Invalid bit range. Must be between 0 and 31 and start_bit must be less than or equal to end_bit.")

	mask = ((1 << (end_bit - start_bit + 1)) - 1) << start_bit
	
	if context.devices[device_id]._has_mmio:
		read_val = context.server_ifc.pci_read32_raw(
			device_id, reg_addr
		)
	else:
		read_val = context.server_ifc.pci_read32(
			device_id, *core_loc.to("nocVirt"), reg_addr
		)

	return (read_val & mask) >> start_bit

def run_arc_core(mask: int, device_id: int = 0, context: Context = None):
	""" Runs the arc core specified by the mask.

	Args:
		mask : Mask specifying which ARC core to run.
		device_id (int, default 0) : ID number of device to run ARC core on.
		context (Context, optional) : Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	"""
	device = context.devices[device_id]
	arc_core_loc = device.get_arc_block_location()

	req_arc_core_run_bit_range = (0,3)
	core_run_ack_bit_range = (0,3)

	write_field(device.get_register_addr("ARC_RESET_ARC_MISC_CNTL"), mask, arc_core_loc, req_arc_core_run_bit_range, device_id, context)

	core_run_ack = 0
	# Waiting for run to be acknowledged
	while (core_run_ack & mask != mask):
		core_run_ack = read_field(device.get_register_addr("ARC_RESET_ARC_MISC_STATUS"), arc_core_loc, core_run_ack_bit_range, device_id, context)
	
	write_field(device.get_register_addr("ARC_RESET_ARC_MISC_CNTL"), 0, arc_core_loc, req_arc_core_run_bit_range, device_id, context)

def halt_arc_core(mask: int, device_id: int = 0, context: Context = None):
	""" Halts the ARC core specified by the mask.

	Args:
		mask : Mask specifying which ARC core to halt.
		device_id (int, default 0) : ID number of device to halt ARC core on.
		context (Context, optional) : Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	"""
	device = context.devices[device_id]
	arc_core_loc = device.get_arc_block_location()

	req_arc_core_halt_bit_range = (4,7)
	core_halt_ack_bit_range = (4,7)

	write_field(device.get_register_addr("ARC_RESET_ARC_MISC_CNTL"), mask, arc_core_loc, req_arc_core_halt_bit_range, device_id, context)

	core_halt_ack = 0
	# Waiting for halt to be acknowledged
	while (core_halt_ack != mask):
		core_halt_ack = read_field(device.get_register_addr("ARC_RESET_ARC_MISC_STATUS"), arc_core_loc, core_halt_ack_bit_range, device_id, context)
	
	write_field(device.get_register_addr("ARC_RESET_ARC_MISC_CNTL"), 0, arc_core_loc, req_arc_core_halt_bit_range, device_id, context)

def set_udmiaxi_region(mem_type: str, device_id: int = 0, context:Context=None):
	""" Sets the UDMIAXI region to the specified memory type.

	Args:
		mem_type (str): Memory type to set the UDMIAXI region to. Can be 'iccm', 'iccm0', 'iccm1', 'iccm2', 'iccm3', or 'csm'.
		device_id (int, default 0): ID number of device to set UDMIAXI region on.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	"""
	device = context.devices[device_id]
	arc_core_loc = device.get_arc_block_location()

	iccm_id = re.findall('\d',mem_type)
	if len(iccm_id) == 0:
		iccm_id = 0
		assert mem_type=='iccm' or mem_type=='csm'
	else:
		iccm_id = int(iccm_id[0])
		assert iccm_id>=0 and iccm_id<=3

	base_addr = ((0x10000000 >> 24) & 0xff) if mem_type == 'csm' else (iccm_id*0x3)

	write_field(device.get_register_addr("ARC_RESET_ARC_UDMIAXI_REGION"), base_addr, arc_core_loc, (0,31), device_id, context)


def load_arc_fw(file_name: str, device_id: int = 0, context: Context = None) -> None:
	""" Loads the ARC firmware from the file into the device.

	Args:
		file_name (str): Path to the file containing the ARC firmware.
		device_id (int, default 0): ID number of device to load firmware on.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	"""
	context = check_context(context)
	validate_device_id(device_id, context)

	device = context.devices[device_id]
	arc_core_loc = device.get_arc_block_location()

	iccm_id = 2
	mem_type = f'iccm{iccm_id}'

	halt_arc_core(1<<iccm_id, device_id, context)

	set_udmiaxi_region(mem_type, device_id, context)

	base_addr = device.get_register_addr("ARC_CSM_DATA")

	def read_contiguous_hex_chunks(f):
		chunk_start_address = 0
		current_chunk = bytearray()

		for line in f:
			a = line.split ('@')
			if len(a)==2: # Address change
				# address change splits chunk, output current chunk if not empty
				if len(current_chunk) > 0:
					yield (chunk_start_address, current_chunk)
					current_chunk = []

				chunk_start_address = int (a[1], 16) * 4   # Parse hex number, hence 16
			else:         # Data
				data = int(a[0], 16)
				current_chunk += data.to_bytes(4, 'big')

		if len(current_chunk) > 0:
			yield (chunk_start_address, current_chunk)

	with open(file_name) as f:
		first_chunk = True

		for offset, data in read_contiguous_hex_chunks(f):
			if first_chunk: # Load reset vector
				write_field(device.get_register_addr("ARC_ROM_DATA"), int.from_bytes(data[0:4], 'little'), arc_core_loc, (0,31), device_id, context)
				first_chunk = False

			for i in range(len(data) // 4):
				word = int.from_bytes(data[i*4 : i*4+4], 'little')
				write_field(base_addr+i*4, word, arc_core_loc, (0,31), device_id, context)

	set_udmiaxi_region("csm",device_id,context)
	run_arc_core(1<<iccm_id, device_id, context)

def arc_dbg_fw_send_message(message ,arg0: int = 0,arg1: int = 0, device_id: int = 0, context: Context=None) -> None:
	""" Send a message to the ARC debug firmware.
	
	Args:
		message: Message to send. Must be in the lower 8 bits.
		arg0 (int, default 0): First argument to the message.
		arg1 (int, default 0): Second argument to the message.
		device_id (int, default 0): ID number of device to send message to.
		context (Context, optional): Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
	"""
	# // Message format in scratch_2:
	# // +-----------+-----------+-----------+-----------+
	# // | 0xab      | 0xcd      | 0xef      | MSG_CODE  |
	# // +-----------+-----------+-----------+-----------+
	# // Message reply in scratch_2:
	# // +-----------+-----------+-----------+-----------+
	# // |         REPLY         | MSG_CODE  | 0x00      |
	# // +-----------+-----------+-----------+-----------+
	context = check_context(context)
	validate_device_id(device_id, context)

	device = context.devices[device_id]
	arc_core_loc = device.get_arc_block_location()	

	write_field(device.get_register_addr("ARC_RESET_SCRATCH3"), arg0, arc_core_loc, (0,31), device_id, context)
	write_field(device.get_register_addr("ARC_RESET_SCRATCH4"), arg1, arc_core_loc, (0,31), device_id, context)
	assert(message & 0xffffff00 == 0) # "Message must be in the lower 8 bits"
	write_field(device.get_register_addr("ARC_RESET_SCRATCH2"), message | 0xabcdef00 , arc_core_loc, (0,31), device_id, context)

def check_msg_loop_running(device_id: int = 0, context: Context = None):
	"""
	Send PING, receive PONG
	"""
	context = check_context(context)
	validate_device_id(device_id, context)

	device = context.devices[device_id]
	arc_core_loc = device.get_arc_block_location()	

	request = read_field(device.get_register_addr("ARC_RESET_SCRATCH2"), arc_core_loc, (0,31), device_id,context)
	arc_dbg_fw_send_message (0x88,0,0,device_id,context) 
	time.sleep(0.1)
	reply = read_field(device.get_register_addr("ARC_RESET_SCRATCH2"), arc_core_loc, (0,31), device_id,context)
	if (reply >> 16) != 0x99 or (reply & 0xff00) == 0x8800: 
		return False
	return True

def control_arc_logger(command: str,tt_metal_arc_debug_buffer_size: int = 1024, device_id: int = 0, context: Context = None) -> None:
	check_msg_loop_running(device_id,context)

	DRAM_REGION_START_ADDR = get_arc_logger_buffer_start_addr()
	
	DRAM_REGION_SIZE = os.getenv("TT_METAL_ARC_DEBUG_BUFFER_SIZE")
	if DRAM_REGION_SIZE is None:
		DRAM_REGION_SIZE = tt_metal_arc_debug_buffer_size
	else:
		DRAM_REGION_SIZE = int(DRAM_REGION_SIZE)

	DFW_MSG_CLEAR_DRAM         = 0x1  # Calls dfw_clear_dram(start_addr, size)
	DFW_MSG_CHECK_DRAM_CLEARED = 0x2  # Calls dfw_check_dram_cleared(start_addr, size)
	DFW_MSG_SETUP_LOGGING      = 0x3  # Calls dfw_setup_log_buffer(start_addr, size)

	if command == "start":
		arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, DRAM_REGION_START_ADDR, DRAM_REGION_SIZE, device_id, context)
	elif command == "stop":
		arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, 0xffffffff, 0xffffffff, device_id, context)
	elif command == "clear":
		arc_dbg_fw_send_message(DFW_MSG_SETUP_LOGGING, DFW_MSG_CLEAR_DRAM, DRAM_REGION_SIZE, device_id, context)

def get_arc_logger_buffer_start_addr():
	return 32

def get_number_of_arc_log_calls(device_id):
	return read_words_from_device("ch0", device_id=device_id, addr=get_arc_logger_buffer_start_addr()+7*4, word_count=1)[0]