import inspect

from functools import wraps

from tt_debuda_context import Context
from tt_debuda_init import init_debuda
from tt_debuda_init import GLOBAL_CONTEXT
from tt_object import DataArray


def read_from_device(
		x: int, 
		y: int, 
		addr: int, 
		device_id: int = 0,
		word_count: int = 1,
		context: Context = None
) -> "list[int]":
	""" Reads word_count four-byte words of data, starting from address 'addr' at core <x-y>.
	
	Parameters
	----------
	x : int
		X coordinate of the core to read from.
	y : int
		Y coordinate of the core to read from.
	addr : int
		Memory address to read from.
	device_id : int, default 0
		ID number of device to read from.
	word_count : int, default 1
		Number of 4-byte words to read.
	context : Context, optional
		Debuda context object used for interaction with device. If None, global context is used and
		potentailly initialized.
	
	Returns
	-------
	list[int]
		Data read from the device.
	"""
	context = check_context(context)
	
	data = []
	for i in range(word_count):
		word = context.server_ifc.pci_read32(
			device_id, x, y, addr + 4 * i
		)
		data.append(word)
	return data


def write_word_to_device(
		x: int, 
		y: int,
		addr: int,
		data: int,
		device_id: int = 0,
		context: Context = None
) -> int:
	"""Writes data word to address 'addr' at noc0 location x-y of the current chip.
	
	Parameters
	----------
	x : int
		X coordinate of the core to write to.
	y : int
		Y coordinate of the core to write to.
	addr : int
		Memory address to write to.
	data : int
		4-byte data to be written.
	device_id : int, default 0
		ID number of device to write to.
	context : Context, optional
		Debuda context object used for interaction with device. If None, global context is used and
		potentailly initialized.

	Returns
	-------
	int
		If the execution is successful, return value should be 4 (number of bytes written).
	"""
	context = check_context(context)
	
	return context.server_ifc.pci_write32(
		device_id, x, y, addr, data
	)


def write_to_device(
		x: int, 
		y: int,
		addr: int,
		data: list[int] | bytes,
		device_id: int = 0,
		context: Context = None
) -> int:
	"""Writes data to address 'addr' at noc0 location x-y of the current chip.
	
	Parameters
	----------
	x : int
		X coordinate of the core to write to.
	y : int
		Y coordinate of the core to write to.
	addr : int
		Memory address to write to.
	data : list[int] | bytes
		Data to be written. Lists are converted to bytes before writing. Elements must be between 0 and 255.
	device_id : int, default 0
		ID number of device to write to.
	context : Context, optional
		Debuda context object used for interaction with device. If None, global context is used and
		potentailly initialized.

	Returns
	-------
	int
		If the execution is successful, return value should be 4 (number of bytes written).
	"""
	context = check_context(context)
	
	if isinstance(data, list):
		data = bytes(data)

	return context.server_ifc.pci_write(
		device_id, x, y, addr, data
	)


def check_context(context: Context = None) -> Context:
	""" Function to initialize context if not provided. By default, it starts a local
	debuda session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
	that the context can be reused in calls to other functions.
	"""
	if context:
		return context
	
	global GLOBAL_CONTEXT
	if not GLOBAL_CONTEXT:
		GLOBAL_CONTEXT = init_debuda()
	return GLOBAL_CONTEXT


if __name__ == '__main__':
	print(hex(read_from_device(0, 0, 0x0)[0]))
	write_word_to_device(0, 0, 0x0, 0x1234)
	print(hex(read_from_device(0, 0, 0x0)[0]))