# tt_exalens_init

## GLOBAL_CONTEXT

`GLOBAL_CONTEXT` = **None** *(Context | None)*

### Description

GLOBAL_CONTEXT is a convenience variable to store fallback TTExaLens context object.
If a library function needs context parameter but it isn't provided, it will use
whatever is in GLOBAL_CONTEXT variable. This does not mean that TTExaLens context is
a singleton, as it can be explicitly provided to library functions.




## init_ttexalens

```
init_ttexalens(wanted_devices=None, init_jtag=False, use_noc1=False) -> Context
```


### Description

Initializes TTExaLens internals by creating the device interface and TTExaLens context.
Interfacing device is local, through pybind.


### Args

- `wanted_devices` *(list, optional)*: List of device IDs we want to connect to. If None, connect to all available devices.
- `caching_path` *(str, optional)*: Path to the cache file to write. If None, caching is disabled.


### Returns

 *(Context)*: TTExaLens context object.



## init_ttexalens_remote

```
init_ttexalens_remote(ip_address=localhost, port=5555) -> Context
```


### Description

Initializes TTExaLens internals by creating the device interface and TTExaLens context.
Interfacing device is done remotely through TTExaLens client.


### Args

- `ip_address` *(str)*: IP address of the TTExaLens server. Default is 'localhost'.
- `port` *(int)*: Port number of the TTExaLens server interface. Default is 5555.
- `cache_path` *(str, optional)*: Path to the cache file to write. If None, caching is disabled.


### Returns

 *(Context)*: TTExaLens context object.



## get_cluster_desc_yaml

```
get_cluster_desc_yaml(lens_ifc) -> util.YamlFile
```


### Description

Get the runtime data and cluster description yamls through the TTExaLens interface.




## load_context

```
load_context(server_ifc, use_noc1=False) -> Context
```


### Description

Load the TTExaLens context object with specified parameters.




## set_active_context

```
set_active_context(context) -> None
```


### Description

Set the active TTExaLens context object.


### Args

- `context` *(Context)*: TTExaLens context object.


### Notes

- Every new context initialization will overwrite the currently active context.




## locate_most_recent_build_output_dir

```
locate_most_recent_build_output_dir() -> str | None
```


### Description

Try to find a default output directory.






# tt_exalens_lib

## check_context

```
check_context(context=None) -> Context
```


### Description

Function to initialize context if not provided. By default, it starts a local
TTExaLens session with no output folder and caching disabled and sets GLOBAL_CONTEXT variable so
that the context can be reused in calls to other functions.




## convert_coordinate

```
convert_coordinate(location, device_id=0, context=None) -> OnChipCoordinate
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
read_word_from_device(location, addr, device_id=0, context=None, noc_id=None) -> int
```


### Description

Reads one four-byte word of data, from address 'addr' at specified location using specified noc.


### Args

- `location` *(str | OnChipCoordinate)*: Either X-Y (noc0/translated) or X,Y (logical) location on chip in string format, dram channel (e.g. ch3, d0,0), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to read from.
- `device_id` *(int, default 0)*: ID number of device to read from.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentailly initialized.
- `noc_id` *(int, optional)*: NOC ID to use. If None, it will be set based on context initialization.


### Returns

 *(int)*: Data read from the device.



## read_words_from_device

```
read_words_from_device(location, addr, device_id=0, word_count=1, context=None, noc_id=None) -> int
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


### Returns

 *(list[int])*: Data read from the device.



## read_from_device

```
read_from_device(location, addr, device_id=0, num_bytes=4, context=None, noc_id=None) -> bytes
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
write_words_to_device(location, addr, data, device_id=0, context=None, noc_id=None) -> int
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


### Returns

 *(int)*: If the execution is successful, return value should be 4 (number of bytes written).



## write_to_device

```
write_to_device(location, addr, data, device_id=0, context=None, noc_id=None) -> int
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


### Returns

 *(int)*: If the execution is successful, return value should be number of bytes written.



## load_elf

```
load_elf(elf_file, location, risc_name, neo_id=None, device_id=0, context=None) -> None
```


### Description

Loads the given ELF file into the specified RISC core. RISC core must be in reset before loading the ELF.


### Args

- `elf_file` *(str)*: Path to the ELF file to run.
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
run_elf(elf_file, location, risc_name, neo_id=None, device_id=0, context=None) -> None
```


### Description

Loads the given ELF file into the specified RISC core and executes it. Similar to load_elf, but RISC core is taken out of reset after load.


### Args

- `elf_file` *(str)*: Path to the ELF file to run.
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
arc_msg(device_id, msg_code, wait_for_done, arg0, arg1, timeout, context=None, noc_id=None) -> int
```


### Description

Sends an ARC message to the device.


### Args

- `device_id` *(int)*: ID number of device to send message to.
- `msg_code` *(int)*: Message code to send.
- `wait_for_done` *(bool)*: If True, waits for the message to be processed.
- `arg0` *(int)*: First argument to the message.
- `arg1` *(int)*: Second argument to the message.
- `timeout` *(int)*: Timeout in milliseconds.
- `context` *(Context, optional)*: TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized.
- `noc_id` *(int, optional)*: NOC ID to use. If None, it will be set based on context initialization.


### Returns

 *(list[int])*: return code, reply0, reply1.



## read_arc_telemetry_entry

```
read_arc_telemetry_entry(device_id, telemetry_tag, context=None) -> int
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
read_register(location, register, noc_id=0, neo_id=None, device_id=0, context=None) -> int
```


### Description

Reads the value of a register from the tensix core.


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
write_register(location, register, value, noc_id=0, neo_id=None, device_id=0, context=None) -> None
```


### Description

Writes value to a register on the core.


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
parse_elf(elf_path, context=None) -> ParsedElfFile
```


### Description

Reads the ELF file and returns a ParsedElfFile object.
Args:
elf_path (str): Path to the ELF file.
context (Context, optional): TTExaLens context object used for interaction with device. If None, global context is used and potentially initialized. Default: None




## top_callstack

```
top_callstack(pc, elfs, offsets=None, context=None) -> list
```


### Description

Retrieves the top frame of the callstack for the specified PC on the given ELF.
There is no stack walking, so the function will return the function at the given PC and all inlined functions on the top frame (if there are any).


### Args

- `pc` *(int)*: Program counter to be used for the callstack.
- `elfs` *(list[str] | str | list[ParsedElfFile] | ParsedElfFile)*: ELF files to be used for the callstack.
- `offsets` *(list[int], int, optional)*: List of offsets for each ELF file. Default: None.
- `context` *(Context)*: TTExaLens context object used for interaction with the device. If None, the global context is used and potentially initialized. Default: None
- `Returns`
- `List`: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.




## callstack

```
callstack(location, elfs, offsets=None, risc_name=brisc, neo_id=None, max_depth=100, stop_on_main=True, device_id=0, context=None) -> list
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
- `Returns`
- `List`: Callstack (list of functions and information about them) of the specified RISC core for the given ELF.




## coverage

```
coverage(location, elf, gcda_path, gcno_copy_path=None, device_id=0, context=None) -> None
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
read_riscv_memory(location, addr, risc_name, neo_id=None, device_id=0, context=None) -> int
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
write_riscv_memory(location, addr, value, risc_name, neo_id=None, device_id=0, context=None) -> None
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
### __init__



```
__init__(self, x, y, input_type, device, core_type=any) -> None
```
Constructor for the Coordinate class.
- `x` *(int)*: The x-coordinate value.
- `y` *(int)*: The y-coordinate value.
- `input_type` *(str)*: The input coordinate system type. One of the following:
- `- noc0`: NOC routing coordinate for NOC 0. (X-Y). Also known as "physical" coordinate.
- `- noc1`: NOC routing coordinate for NOC 1. (X-Y)
- `- die`: Die coordinate, a location on the die grid. (X,Y)
- `- logical`: Logical grid coordinate. Notation: qX,Y, where q represents first letter of the core type. If q is not present, it is considered as tensix core.
- `- translated`: Translated NOC coordinate. (X-Y)
- `device`: The device object used for coordinate conversion.
- `core_type` *(str, optional)*: The core_type used for coordinate conversion. Some coordinate systems require core_type as third dimension. Defaults to "any".
- If the device is not specified, coordinate conversion to other systems will not be possible.
### to



```
to(self, output_type) -> None
```
Returns a tuple with the coordinates in the specified coordinate system.
- `output_type` *(str)*: The desired output coordinate system.
 *(tuple)*: The coordinates in the specified coordinate system.### to_str



```
to_str(self, output_type=noc0) -> None
```
Returns a tuple with the coordinates in the specified coordinate system.
### to_user_str



```
to_user_str(self) -> None
```
Returns a string representation of the coordinate that is suitable for the user.
### change_device



```
change_device(self, device) -> None
```
Returns coordinates for the specified device.
- `device` *(Device)*: The device object representing the chip.
 *(OnChipCoordinate)*: The new coordinate object for the specified device.### create



```
create(coord_str, device, coord_type=None) -> None
```
Creates a coordinate object from a string. The string can be in any of the supported coordinate systems.
 *(OnChipCoordinate)*: The created coordinate object.
