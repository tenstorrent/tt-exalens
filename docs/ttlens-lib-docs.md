# tt_lens_init

## GLOBAL_CONTEXT

`GLOBAL_CONTEXT` = **None** *(Context)*

### Description

GLOBAL_CONTEXT is a convenience variable to store fallback TTLens context object.
If a library function needs context parameter but it isn't provided, it will use
whatever is in GLOBAL_CONTEXT variable. This does not mean that TTLens context is
a singleton, as it can be explicitly provided to library functions.




## init_debuda

```
init_debuda(output_dir_path=None, netlist_path=None, wanted_devices=None, cache_path=None) -> Context
```


### Description

Initializes TTLens internals by creating the device interface and TTLens context.
Interfacing device is local, through pybind.


### Args

- `output_dir_path` *(str, optional)*: Path to the Buda run output directory. If None, TTLens will be initialized in limited mode.
- `netlist_path` *(str, optional)*: Path to the Buda netlist file.
- `wanted_devices` *(list, optional)*: List of device IDs we want to connect to. If None, connect to all available devices.
- `caching_path` *(str, optional)*: Path to the cache file to write. If None, caching is disabled.


### Returns

 *(Context)*: TTLens context object.



## init_debuda_remote

```
init_debuda_remote(ip_address=localhost, port=5555, cache_path=None) -> Context
```


### Description

Initializes TTLens internals by creating the device interface and TTLens context.
Interfacing device is done remotely through TTLens client.


### Args

- `ip_address` *(str)*: IP address of the TTLens server. Default is 'localhost'.
- `port` *(int)*: Port number of the TTLens server interface. Default is 5555.
- `cache_path` *(str, optional)*: Path to the cache file to write. If None, caching is disabled.


### Returns

 *(Context)*: TTLens context object.



## init_debuda_cached

```
init_debuda_cached(cache_path, netlist_path=None) -> None
```


### Description

Initializes TTLens internals by reading cached session data. There is no connection to the device.
Only cached commands are available.


### Args

- `cache_path` *(str)*: Path to the cache file.
- `netlist_path` *(str, optional)*: Path to the netlist file.


### Returns

 *(Context)*: TTLens context object.



## get_yamls

```
get_yamls(debuda_ifc) -> tuple[util.YamlFile, util.YamlFile]
```


### Description

Get the runtime data and cluster description yamls through the TTLens interface.




## load_context

```
load_context(server_ifc, netlist_filepath, runtime_data_yaml, cluster_desc_yaml) -> Context
```


### Description

Load the TTLens context object with specified parameters.




## set_active_context

```
set_active_context(context) -> None
```


### Description

Set the active TTLens context object.


### Args

- `context` *(Context)*: TTLens context object.


### Notes

- Every new context initialization will overwrite the currently active context.




## find_runtime_data_yaml_filename

```
find_runtime_data_yaml_filename(output_dir=None) -> str | None
```


### Description

Find the runtime data yaml file in the output directory. If directory is not specified, try to find the most recent Buda output directory.


### Args

- `output_dir` *(str, optional)*: Path to the output directory.




## locate_most_recent_build_output_dir

```
locate_most_recent_build_output_dir() -> str | None
```


### Description

Try to find a default output directory.






# tt_lens_lib

## read_words_from_device

```
read_words_from_device(core_loc, addr, device_id=0, word_count=1, context=None) -> List[int]
```


### Description

Reads word_count four-byte words of data, starting from address 'addr' at core <x-y>.


### Args

- `core_loc` *(str | OnChipCoordinate)*: Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to read from.
- `device_id` *(int, default 0)*: ID number of device to read from.
- `word_count` *(int, default 1)*: Number of 4-byte words to read.
- `context` *(Context, optional)*: TTLens context object used for interaction with device. If None, global context is used and potentailly initialized.


### Returns

 *(List[int])*: Data read from the device.



## read_from_device

```
read_from_device(core_loc, addr, device_id=0, num_bytes=4, context=None) -> bytes
```


### Description

Reads num_bytes of data starting from address 'addr' at core <x-y>.


### Args

- `core_loc` *(str | OnChipCoordinate)*: Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to read from.
- `device_id` *(int, default 0)*: ID number of device to read from.
- `num_bytes` *(int, default 4)*: Number of bytes to read.
- `context` *(Context, optional)*: TTLens context object used for interaction with device. If None, global context is used and potentially initialized.


### Returns

 *(bytes)*: Data read from the device.



## write_words_to_device

```
write_words_to_device(core_loc, addr, data, device_id=0, context=None) -> int
```


### Description

Writes data word to address 'addr' at noc0 location x-y of the current chip.


### Args

- `core_loc` *(str | OnChipCoordinate)*: Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to write to. If multiple words are to be written, the address is the starting address.
- `data` *(int | List[int])*: 4-byte integer word to be written, or a list of them.
- `device_id` *(int, default 0)*: ID number of device to write to.
- `context` *(Context, optional)*: TTLens context object used for interaction with device. If None, global context is used and potentailly initialized.


### Returns

 *(int)*: If the execution is successful, return value should be 4 (number of bytes written).



## write_to_device

```
write_to_device(core_loc, addr, data, device_id=0, context=None) -> int
```


### Description

Writes data to address 'addr' at noc0 location x-y of the current chip.


### Args

- `core_loc` *(str | OnChipCoordinate)*: Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
- `addr` *(int)*: Memory address to write to.
- `data` *(List[int] | bytes)*: Data to be written. Lists are converted to bytes before writing, each element a byte. Elements must be between 0 and 255.
- `device_id` *(int, default 0)*: ID number of device to write to.
- `context` *(Context, optional)*: TTLens context object used for interaction with device. If None, global context is used and potentailly initialized.


### Returns

 *(int)*: If the execution is successful, return value should be number of bytes written.



## run_elf

```
run_elf(elf_file, core_loc, risc_id=0, device_id=0, context=None) -> None
```


### Description

Loads the given ELF file into the specified RISC core and executes it.


### Args

- `elf_file` *(os.PathLike)*: Path to the ELF file to run.
- `core_loc` *(str | OnChipCoordinate | List[str | OnChipCoordinate])*: One of the following:
1. "all" to run the ELF on all cores;
2. an X-Y (nocTr) or R,C (netlist) location of a core in string format;
3. a list of X-Y (nocTr), R,C (netlist) or OnChipCoordinate locations of cores, possibly mixed;
4. an OnChipCoordinate object.
- `risc_id` *(int, default 0)*: RiscV ID (0: brisc, 1-3 triscs).
- `device_id` *(int, default 0)*: ID number of device to run ELF on.
- `context` *(Context, optional)*: TTLens context object used for interaction with device. If None, global context is used and potentially initialized.




## check_context

```
check_context(context=None) -> Context
```


### Description

Function to initialize context if not provided. By default, it starts a local
TTLens session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
that the context can be reused in calls to other functions.






# tt_coordinate



