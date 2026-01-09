# tt_exalens_init

## init_ttexalens

```
init_ttexalens(init_jtag: bool = False, use_noc1: bool = False, use_4B_mode: bool = True, simulation_directory: str | None = None) -> Context
```


### Description

Initializes TTExaLens internals by creating the device interface and TTExaLens context.
Interfacing device is local, through pybind.


### Args

- `init_jtag` *(bool)*: Whether to initialize JTAG interface. Default is False.
- `use_noc1` *(bool)*: Whether to initialize with NOC1 and use NOC1 for communication with the device. Default is False.
- `use_4B_mode` *(bool)*: Whether to use 4B mode for communication with the device. Default is True.
- `simulation_directory` *(str, optional)*: If specified, starts the simulator from the given build output directory.


### Returns

 *(Context)*: TTExaLens context object.



## init_ttexalens_remote

```
init_ttexalens_remote(ip_address: str = localhost, port: int = 5555, use_4B_mode: bool = True) -> Context
```


### Description

Initializes TTExaLens internals by creating the device interface and TTExaLens context.
Interfacing device is done remotely through TTExaLens client.


### Args

- `ip_address` *(str)*: IP address of the TTExaLens server. Default is 'localhost'.
- `port` *(int)*: Port number of the TTExaLens server interface. Default is 5555.
- `use_4B_mode` *(bool)*: Whether to use 4B mode for communication with the device. Default is True.


### Returns

 *(Context)*: TTExaLens context object.



## set_active_context

```
set_active_context(context: Context | None) -> None
```


### Description

Set the active TTExaLens context object.


### Args

- `context` *(Context)*: TTExaLens context object.


### Notes

- Every new context initialization will overwrite the currently active context.






# tt_exalens_lib

## check_context

```
check_context(context: Context | None = None) -> Context
```


### Description

Function to initialize context if not provided. By default, it starts a local
TTExaLens session with no output folder and caching disabled and sets GLOBAL_CONTEXT variable so
that the context can be reused in calls to other functions.




## convert_coordinate

```
convert_coordinate(location: str | OnChipCoordinate, device_id: int = 0, context: Context | None = None) -> OnChipCoordinate
```


### Description

Converts a string location to an OnChipCoordinate object.
If location is already OnChipCoordinate, it is returned as-is.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `device_id` *(int, default 0)*: ID number of device to convert to.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.


### Returns

 *(OnChipCoordinate)*: Converted coordinate.



## read_word_from_device

```
read_word_from_device(location: str | OnChipCoordinate, addr: int, device_id: int = 0, context: Context | None = None, noc_id: int | None = None) -> int
```


### Description

Reads one four-byte word of data, from address 'addr' at specified location using specified noc.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to read from.
- `device_id` *(int, default 0)*: ID number of device to read from.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
- `noc_id` *(int, optional)*: NOC ID to use. If None, it will be set based on context initialization.
- `use_4B_mode` *(bool, optional)*: Whether to use 4B mode for communication with the device. If None, it will be set based on context initialization.


### Returns

 *(int)*: Data read from the device.



## read_words_from_device

```
read_words_from_device(location: str | OnChipCoordinate, addr: int, device_id: int = 0, word_count: int = 1, context: Context | None = None, noc_id: int | None = None, use_4B_mode: bool | None = None) -> list[int]
```


### Description

Reads word_count four-byte words of data, starting from address 'addr' at specified location using specified noc.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to read from.
- `device_id` *(int, default 0)*: ID number of device to read from.
- `word_count` *(int, default 1)*: Number of 4-byte words to read.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
- `noc_id` *(int, optional)*: NOC ID to use. If None, it will be set based on context initialization.
- `use_4B_mode` *(bool, optional)*: Whether to use 4B mode for communication with the device. If None, it will be set based on context initialization.


### Returns

 *(list[int])*: Data read from the device.



## read_from_device

```
read_from_device(location: str | OnChipCoordinate, addr: int, device_id: int = 0, num_bytes: int = 4, context: Context | None = None, noc_id: int | None = None, use_4B_mode: bool | None = None) -> bytes
```


### Description

Reads num_bytes of data starting from address 'addr' at specified location using specified noc.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to read from.
- `device_id` *(int, default 0)*: ID number of device to read from.
- `num_bytes` *(int, default 4)*: Number of bytes to read.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
- `noc_id` *(int, optional)*: NOC ID to use. If None, it will be set based on context initialization.


### Returns

 *(bytes)*: Data read from the device.



## write_words_to_device

```
write_words_to_device(location: str | OnChipCoordinate, addr: int, data: int | list[int], device_id: int = 0, context: Context | None = None, noc_id: int | None = None, use_4B_mode: bool | None = None)
```


### Description

Writes data word to address 'addr' at specified location using specified noc.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to write to. If multiple words are to be written, the address is the starting address.
- `data` *(int | list[int])*: 4-byte integer word to be written, or a list of them.
- `device_id` *(int, default 0)*: ID number of device to write to.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
- `noc_id` *(int, optional)*: NOC ID to use. If None, it will be set based on context initialization.
- `use_4B_mode` *(bool, optional)*: Whether to use 4B mode for communication with the device. If None, it will be set based on context initialization.




## write_to_device

```
write_to_device(location: str | OnChipCoordinate, addr: int, data: list[int] | bytes, device_id: int = 0, context: Context | None = None, noc_id: int | None = None, use_4B_mode: bool | None = None)
```


### Description

Writes data to address 'addr' at specified location using specified noc.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to write to.
- `data` *(list[int] | bytes)*: Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
- `device_id` *(int, default 0)*: ID number of device to write to.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
- `noc_id` *(int, optional)*: NOC ID to use. If None, it will be set based on context initialization.
- `use_4B_mode` *(bool, optional)*: Whether to use 4B mode for communication with the device. If None, it will be set based on context initialization.




## load_elf

```
load_elf(elf_file: str | ParsedElfFile, location: str | OnChipCoordinate | list[str | OnChipCoordinate], risc_name: str, neo_id: int | None = None, device_id: int = 0, context: Context | None = None, return_start_address: bool = False) -> None | int | list[int]
```


### Description

Loads the given ELF file into the specified RISC core. RISC core must be in reset before loading the ELF.


### Args

- `elf_file` *(str | ParsedElfFile)*: ELF file to be loaded.
- `location` *(str | OnChipCoordinate | list[str | OnChipCoordinate])*: One of the following:
1. "all" to run the ELF on all cores;
2. an X-Y (noc0/translated) or X,Y (logical) location of a core in string format;
3. a list of X-Y (noc0/translated), X,Y (logical) or OnChipCoordinate locations of cores, possibly mixed;
4. an OnChipCoordinate object.
- `risc_name` *(str)*: RiscV name (e.g. "brisc", "trisc0", "trisc1", "trisc2", "ncrisc").
- `neo_id` *(int | None, optional)*: NEO ID of the RISC-V core.
- `device_id` *(int, default 0)*: ID number of device to run ELF on.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.




## run_elf

```
run_elf(elf_file: str | ParsedElfFile, location: str | OnChipCoordinate | list[str | OnChipCoordinate], risc_name: str, neo_id: int | None = None, device_id: int = 0, context: Context | None = None) -> None
```


### Description

Loads the given ELF file into the specified RISC core and executes it. Similar to load_elf, but RISC core is taken out of reset after load.


### Args

- `elf_file` *(str | ParsedElfFile)*: ELF file to be run.
- `location` *(str | OnChipCoordinate | list[str | OnChipCoordinate])*: One of the following:
1. "all" to run the ELF on all cores;
2. an X-Y (noc0/translated) or X,Y (logical) location of a core in string format;
3. a list of X-Y (noc0/translated), X,Y (logical) or OnChipCoordinate locations of cores, possibly mixed;
4. an OnChipCoordinate object.
- `risc_name` *(str)*: RiscV name (e.g. "brisc", "trisc0", "trisc1", "trisc2", "ncrisc").
- `neo_id` *(int | None, optional)*: NEO ID of the RISC-V core.
- `device_id` *(int, default 0)*: ID number of device to run ELF on.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.




## arc_msg

```
arc_msg(device_id: int, msg_code: int, wait_for_done: bool, args: list[int], timeout: datetime.timedelta, context: Context | None = None, noc_id: int | None = None) -> list[int]
```


### Description

Sends an ARC message to the device.


### Args

- `device_id` *(int)*: ID number of device to send message to.
- `msg_code` *(int)*: Message code to send.
- `wait_for_done` *(bool)*: If True, waits for the message to be processed.
- `args` *(list[int])*: Arguments to the message.
- `timeout` *(datetime.timedelta)*: Timeout.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
- `noc_id` *(int, optional)*: NOC ID to use. If None, it will be set based on context initialization.


### Returns

 *(list[int])*: return code, reply0, reply1.



## read_arc_telemetry_entry

```
read_arc_telemetry_entry(device_id: int, telemetry_tag: int | str, context: Context | None = None, noc_id: int | None = None) -> int
```


### Description

Reads an ARC telemetry entry from the device.


### Args

- `device_id` *(int)*: ID number of device to read telemetry from.
- `telemetry_tag` *(int | str)*: Name or ID of the tag to read.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.


### Returns

 *(int)*: Value of the telemetry entry.



## read_register

```
read_register(location: str | OnChipCoordinate, register, noc_id: int = 0, neo_id: int | None = None, device_id: int = 0, context: Context | None = None) -> int
```


### Description

Reads the value of a register from the noc location.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, or OnChipCoordinate object.
- `register` *(str | RegisterDescription)*: Configuration or debug register to read from (name or instance of ConfigurationRegisterDescription or DebugRegisterDescription).
ConfigurationRegisterDescription(id, mask, shift), DebugRegisterDescription(addr).
- `noc_id` *(int, default 0)*: NOC ID to use.
- `neo_id` *(int | None, optional)*: NEO ID of the register store.
- `device_id` *(int, default 0)*: ID number of device to read from.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.


### Returns

 *(int)*: Value of the configuration or debug register specified.



## write_register

```
write_register(location: str | OnChipCoordinate, register, value: int, noc_id: int = 0, neo_id: int | None = None, device_id: int = 0, context: Context | None = None) -> None
```


### Description

Writes value to a register on the noc location.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, or OnChipCoordinate object.
- `register` *(str | TensixRegisterDescription)*: Configuration or debug register to read from (name or instance of ConfigurationRegisterDescription or DebugRegisterDescription).
ConfigurationRegisterDescription(id, mask, shift), DebugRegisterDescription(addr).
- `value` *(int)*: Value to write to the register.
- `noc_id` *(int, default 0)*: NOC ID to use.
- `neo_id` *(int | None, optional)*: NEO ID of the register store.
- `device_id` *(int, default 0)*: ID number of device to read from.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.




## parse_elf

```
parse_elf(elf_path: str, context: Context | None = None) -> ParsedElfFile
```


### Description

Reads the ELF file and returns a ParsedElfFile object.
Args:
elf_path (str): Path to the ELF file.
context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized. Default: None




## top_callstack

```
top_callstack(pc: int, elfs: list[str] | str | list[ParsedElfFile] | ParsedElfFile, offsets: int | None | list[int | None] = None, context: Context | None = None) -> list[CallstackEntry]
```


### Description

Retrieves the top frame of the callstack for the specified PC on the given ELF.
There is no stack walking, so the function will return the function at the given PC and all inlined functions on the top frame (if there are any).


### Args

- `pc` *(int)*: Program counter to be used for the callstack.
- `elfs` *(list[str] | str | list[ParsedElfFile] | ParsedElfFile)*: ELF files to be used for the callstack.
- `offsets` *(list[int], int, optional)*: List of offsets for each ELF file. Default: None.
- `context` *(Context)*: TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None


### Returns

 *(List)*: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.



## callstack

```
callstack(location: str | OnChipCoordinate, elfs: list[str] | str | list[ParsedElfFile] | ParsedElfFile, offsets: int | None | list[int | None] = None, risc_name: str = brisc, neo_id: int | None = None, max_depth: int = 100, stop_on_main: bool = True, device_id: int = 0, context: Context | None = None) -> list[CallstackEntry]
```


### Description

Retrieves the callstack of the specified RISC core for a given ELF.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `elfs` *(list[str] | str | list[ParsedElfFile] | ParsedElfFile)*: ELF files to be used for the callstack.
- `offsets` *(list[int], int, optional)*: List of offsets for each ELF file. Default: None.
- `risc_name` *(str)*: RISC-V core name (e.g. "brisc", "trisc0", etc.).
- `neo_id` *(int | None, optional)*: NEO ID of the RISC-V core.
- `max_depth` *(int)*: Maximum depth of the callstack. Default: 100.
- `stop_on_main` *(bool)*: If True, stops at the main function. Default: True.
- `device_id` *(int)*: ID of the device on which the kernel is run. Default: 0.
- `context` *(Context)*: TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None


### Returns

 *(List)*: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.



## coverage

```
coverage(location: str | OnChipCoordinate, elf: str | ParsedElfFile, gcda_path: str, gcno_copy_path: str | None = None, device_id: int = 0, context: Context | None = None) -> None
```


### Description

Extract coverage data from the device.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `elf` *(str | ParsedElfFile)*: ELF file whose coverage should be extracted.
- `gcda_path` *(str)*: The path where the gcda file will be written.
- `gcno_copy_path` *(str | None, optional)*: The path where the gcno will be written, if specified.
- `device_id` *(int, optional)*: ID of the device to read from. Default 0.
- `context` *(Context | None, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.




## read_riscv_memory

```
read_riscv_memory(location: str | OnChipCoordinate, addr: int, risc_name: str, neo_id: int | None = None, device_id: int = 0, context: Context | None = None) -> int
```


### Description

Reads a 32-bit word from the specified RISC-V core's private memory.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to read from.
- `risc_name` *(str)*: RISC-V core name (e.g. "brisc", "trisc0", etc.).
- `neo_id` *(int | None, optional)*: NEO ID of the RISC-V core.
- `device_id` *(int)*: ID number of device to read from. Default 0.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.


### Returns

 *(int)*: Data read from the device.



## write_riscv_memory

```
write_riscv_memory(location: str | OnChipCoordinate, addr: int, value: int, risc_name: str, neo_id: int | None = None, device_id: int = 0, context: Context | None = None) -> None
```


### Description

Writes a 32-bit word to the specified RISC-V core's private memory.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to read from.
- `value` *(int)*: Value to write.
- `risc_name` *(str)*: RISC-V core name (e.g. "brisc", "trisc0", etc.).
- `neo_id` *(int | None, optional)*: NEO ID of the RISC-V core.
- `device_id` *(int)*: ID number of device to read from. Default 0.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.






# coordinate

## CoordinateTranslationError



This exception is thrown when a coordinate translation fails.
## OnChipCoordinate



This class represents a coordinate on the chip. It can be used to convert between the various
coordinate systems we use.
### to



```
to(self, output_type)
```
Returns a tuple with the coordinates in the specified coordinate system.
- `output_type` *(str)*: The desired output coordinate system.
 *(tuple)*: The coordinates in the specified coordinate system.### to_str



```
to_str(self, output_type = noc0) -> str
```
Returns a tuple with the coordinates in the specified coordinate system.
### to_user_str



```
to_user_str(self) -> str
```
Returns a string representation of the coordinate that is suitable for the user.
### change_device



```
change_device(self, device)
```
Returns coordinates for the specified device.
- `device` *(Device)*: The device object representing the chip.
 *(OnChipCoordinate)*: The new coordinate object for the specified device.### create



```
create(coord_str, device, coord_type = None) -> OnChipCoordinate
```
Creates a coordinate object from a string. The string can be in any of the supported coordinate systems.
- `coord_str` *(str)*: The string representation of the coordinate.
- `device` *(Device)*: The device object representing the chip.
- `coord_type` *(str, optional)*: The type of coordinate system used in the string.
If not specified, it will be determined based on the separators used in the string.
 *(OnChipCoordinate)*: The created coordinate object.- If the coordinate format is X-Y or R,C, the coordinates will be converted to integers.
- If the coordinate format is DRAM channel, the corresponding NOC0 coordinates will be used.


# context

## Context





# device

## Device



### get_block



```
get_block(self, location: OnChipCoordinate) -> NocBlock
```
Returns the NOC block at the given location
### get_blocks



```
get_blocks(self, block_type: str = functional_workers) -> list[NocBlock]
```
Returns all blocks of a given type
### get_block_locations



```
get_block_locations(self, block_type = functional_workers) -> list[OnChipCoordinate]
```
Returns locations of all blocks of a given type
### get_block_type



```
get_block_type(self, loc: OnChipCoordinate) -> str
```
Returns the type of block at the given location


# util

## Verbosity



### set



```
set(verbosity: int | Verbosity) -> None
```
Set the verbosity level of messages shown.
- `verbosity` *(int)*: Verbosity level.
- `1`: ERROR
- `2`: WARN
- `3`: INFO
- `4`: VERBOSE
- `5`: DEBUG
- `6`: TRACE
### get



```
get() -> Verbosity
```
Get the verbosity level of messages shown.
 *(int)*: Verbosity level.
1: ERROR
2: WARN
3: INFO
4: VERBOSE
5: DEBUG
6: TRACE### supports



```
supports(verbosity: Verbosity) -> bool
```
Check if the verbosity level is supported and should be printed.
 *(bool)*: True if supported, False otherwise.## TTException



## TTFatalException
