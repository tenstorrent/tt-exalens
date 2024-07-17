<a id="tt_debuda_lib"></a>

# tt\_debuda\_lib

<a id="tt_debuda_lib.read_words_from_device"></a>

#### read\_words\_from\_device

```python
def read_words_from_device(core_loc: Union[str, OnChipCoordinate],
                           addr: int,
                           device_id: int = 0,
                           word_count: int = 1,
                           context: Context = None) -> "list[int]"
```

Reads word_count four-byte words of data, starting from address 'addr' at core <x-y>.

**Arguments**:

- `core_loc` _str | OnChipCoordinate_ - Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
- `addr` _int_ - Memory address to read from.
- `device_id` _int, default 0_ - ID number of device to read from.
- `word_count` _int, default 1_ - Number of 4-byte words to read.
- `context` _Context, optional_ - Debuda context object used for interaction with device. If None, global context is used and potentailly initialized.
  

**Returns**:

- `list[int]` - Data read from the device.

<a id="tt_debuda_lib.read_from_device"></a>

#### read\_from\_device

```python
def read_from_device(core_loc: Union[str, OnChipCoordinate],
                     addr: int,
                     device_id: int = 0,
                     num_bytes: int = 4,
                     context: Context = None) -> bytes
```

Reads num_bytes of data starting from address 'addr' at core <x-y>.

**Arguments**:

- `core_loc` _str | OnChipCoordinate_ - Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
- `addr` _int_ - Memory address to read from.
- `device_id` _int, default 0_ - ID number of device to read from.
- `num_bytes` _int, default 4_ - Number of bytes to read.
- `context` _Context, optional_ - Debuda context object used for interaction with device. If None, global context is used and potentially initialized.
  

**Returns**:

- `bytes` - Data read from the device.

<a id="tt_debuda_lib.write_words_to_device"></a>

#### write\_words\_to\_device

```python
def write_words_to_device(core_loc: Union[str, OnChipCoordinate],
                          addr: int,
                          data: Union[int, list[int]],
                          device_id: int = 0,
                          context: Context = None) -> int
```

Writes data word to address 'addr' at noc0 location x-y of the current chip.

**Arguments**:

- `core_loc` _str | OnChipCoordinate_ - Either X-Y (nocTr) or R,C (netlist) location of a core in string format, dram channel (e.g. ch3), or OnChipCoordinate object.
- `addr` _int_ - Memory address to write to. If multiple words are to be written, the address is the starting address.
- `data` _int | list[int]_ - 4-byte integer word to be written, or a list of them.
- `device_id` _int, default 0_ - ID number of device to write to.
- `context` _Context, optional_ - Debuda context object used for interaction with device. If None, global context is used and potentailly initialized.
  

**Returns**:

- `int` - If the execution is successful, return value should be 4 (number of bytes written).

<a id="tt_debuda_lib.write_to_device"></a>

#### write\_to\_device

```python
def write_to_device(core_loc: Union[str, OnChipCoordinate],
                    addr: int,
                    data: Union[list[int], bytes],
                    device_id: int = 0,
                    context: Context = None) -> int
```

Writes data to address 'addr' at noc0 location x-y of the current chip.

**Arguments**:

  
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

<a id="tt_debuda_lib.run_elf"></a>

#### run\_elf

```python
def run_elf(elf_file: os.PathLike,
            core_loc: Union[str, OnChipCoordinate,
                            list[str | OnChipCoordinate]],
            risc_id: int = 0,
            device_id: int = 0,
            context: Context = None) -> None
```

Loads the given ELF file into the specified RISC core and executes it.

**Arguments**:

- `elf_file` _os.PathLike_ - Path to the ELF file to run.
- `core_loc` _str | OnChipCoordinate | list[str | OnChipCoordinate]_ - One of the following:
  1. "all" to run the ELF on all cores;
  2. an X-Y (nocTr) or R,C (netlist) location of a core in string format;
  3. a list of X-Y (nocTr), R,C (netlist) or OnChipCoordinate locations of cores, possibly mixed;
  4. an OnChipCoordinate object.
- `risc_id` _int, default 0_ - RiscV ID (0: brisc, 1-3 triscs).
- `device_id` _int, default 0_ - ID number of device to run ELF on.
- `context` _Context, optional_ - Debuda context object used for interaction with device. If None, global context is used and potentially initialized.

<a id="tt_debuda_lib.check_context"></a>

#### check\_context

```python
def check_context(context: Context = None) -> Context
```

Function to initialize context if not provided. By default, it starts a local
debuda session with no output folder and caching disabled and sets GLOBAL_CONETXT variable so
that the context can be reused in calls to other functions.

<a id="tt_debuda_init"></a>

# tt\_debuda\_init

<a id="tt_debuda_init.init_debuda"></a>

#### init\_debuda

```python
def init_debuda(output_dir_path: str = None,
                netlist_path: str = None,
                wanted_devices: list = None,
                cache_path: str = None) -> Context
```

Initializes debuda internals by creating the device interface and debuda context.
Interfacing device is local, through pybind.

**Arguments**:

- `output_dir_path` _str, optional_ - Path to the debuda run output directory. If None, debuda will be initialized in limited mode.
- `netlist_path` _str, optional_ - Path to the netlist file.
- `wanted_devices` _list, optional_ - List of device IDs we want to connect to. If None, connect to all available devices.
- `caching_path` _str, optional_ - Path to the cache file to write. If None, caching is disabled.
  

**Returns**:

- `Context` - Debuda context object.

<a id="tt_debuda_init.init_debuda_remote"></a>

#### init\_debuda\_remote

```python
def init_debuda_remote(ip_address: str = 'localhost',
                       port: int = 5555,
                       cache_path: str = None) -> Context
```

Initializes debuda internals by creating the device interface and debuda context.
Interfacing device is done remotely through debuda client.

**Arguments**:

- `ip_address` _str_ - IP address of the debuda server. Default is 'localhost'.
- `port` _int_ - Port number of the debuda server interface. Default is 5555.
- `cache_path` _str, optional_ - Path to the cache file to write. If None, caching is disabled.
  

**Returns**:

- `Context` - Debuda context object.

<a id="tt_debuda_init.init_debuda_cached"></a>

#### init\_debuda\_cached

```python
def init_debuda_cached(cache_path: str, netlist_path: str = None)
```

Initializes debuda internals by reading cached session data. There is no connection to the device.
Only cached commands are available.

**Arguments**:

- `cache_path` _str_ - Path to the cache file.
- `netlist_path` _str, optional_ - Path to the netlist file.
  

**Returns**:

- `Context` - Debuda context object.

<a id="tt_debuda_init.get_yamls"></a>

#### get\_yamls

```python
def get_yamls(
    debuda_ifc: tt_debuda_ifc.DbdCommunicator
) -> "tuple[util.YamlFile, util.YamlFile]"
```

Get the runtime data and cluster description yamls through the debuda interface.

<a id="tt_debuda_init.load_context"></a>

#### load\_context

```python
def load_context(server_ifc: tt_debuda_ifc.DbdCommunicator,
                 netlist_filepath: str, runtime_data_yaml: util.YamlFile,
                 cluster_desc_yaml: util.YamlFile) -> Context
```

Load the debuda context object with specified parameters.

<a id="tt_debuda_init.set_active_context"></a>

#### set\_active\_context

```python
def set_active_context(context: Context) -> None
```

Set the active debuda context object.

**Arguments**:

- `context` _Context_ - Debuda context object.
  

**Notes**:

  - Every new context initialization will overwrite the currently active context.

<a id="tt_debuda_init.find_runtime_data_yaml_filename"></a>

#### find\_runtime\_data\_yaml\_filename

```python
def find_runtime_data_yaml_filename(output_dir: str = None) -> str | None
```

Find the runtime data yaml file in the output directory. If directory is not specified, try to find the most recent buda output directory.

**Arguments**:

  output_dir(str, optional): Path to the output directory.

<a id="tt_debuda_init.locate_most_recent_build_output_dir"></a>

#### locate\_most\_recent\_build\_output\_dir

```python
def locate_most_recent_build_output_dir() -> str | None
```

Try to find a default output directory.

<a id="tt_coordinate"></a>

# tt\_coordinate

This file contains the class for the coordinate object. As we use a number of coordinate systems, this class
is used to uniquely represent one grid location on a chip. Note that not all coordinate systems have a 1:1
mapping to the physical location on the chip. For example, not all noc0 coordinates have a valid netlist
coordinate. This is due to the fact that some locations contain non-Tensix tiles, and also since some Tensix
rows may be disabled due to harvesting.

The following coordinate systems are available to represent a grid location on the chip:

  - die:            represents a location on the die grid. This is a "geographic" coordinate and is
                    not really used in software. It is often shown in martketing materials, and shows the
                    layout in as in <arch>-Noc-Coordinates.xls spreadsheet, and on some T-shirts.
  - noc0:           NOC routing coordinate for NOC 0. Notation: X-Y
                    Represents the chip location on the NOC grid. A difference of 1 in NOC coordinate
                    represents a distance of 1 hop on the NOC. In other words, it takes one clock cycle
                    for the data to cross 1 hop on the NOC. Furthermore, the NOC 'wraps around' so that
                    the distance between 0 and NOC_DIM_SIZE-1 is also 1 hop. As we have 2 NOCs, we have
                    2 NOC coordinate systems: noc0 and noc1.
  - noc1:           NOC routing coordinate for NOC 1. Notation: X-Y
                    Same as noc0, but using the second NOC (which goes in the opposite direction).
  - tensix:         represents a full grid of Tensix cores (including the disabled rows due to harvesting).
                    A distance of 1 in this coordinate system shows the 4 closest cores in terms of the
                    NOC routing. Note that, due to presence of non-Tensix blocks, a distance of 1 in the
                    tensix grid does not necessarily equal to one hop on the NOC. Tensix location 0,0 is
                    anchored to noc0 coordinate of 1-1. Location 1,0 is noc0 1-2 (note that X in noc0
                    corresponds to C in tensix, and Y corresponds to R). Notation: R,C

  The above three do not depend on harvesting. They only depend on the chip architecture. Also, they share
  the extents in both X (column) and Y (row). The following coordinates depend on the harvesting mask on WH
  (i.e. when harvest_mast!=0) and harvested_workers on GS. Note, see HARVESTING_NOC_LOCATIONS for more
  details on how harvest_mask is used. Difference is that UMD returns noc0 coordinates for GS, while for WH
  if uses noc0Virt coordinates.

  - netlist:        Netlist grid coordinate. Notation: R,C
                    is similar to the 'tensix', but it does not include the disabled rows due to
                    harvesting. For a chip that does not have any harvested rows, it is exactly the same as tensix.
                    A distance of 1 in this coordinate system also shows the 4 closest cores in terms
                    of the NOC routing, but it connects only functioning cores. Thus, distance of one may incur even
                    more hops on the NOC as we need to route around the disabled rows. Again, if harvesting mask is 0,
                    meaning that all rows are functional, this coordinate will be the same as tensix coordinate.
                    This coordinate system is used inside the netlist (grid_loc, grid_size). Notation: R,C
  - noc0Virt:       Virtual NOC coordinate. Similar to noc0, but with the harvested rows removed, and the locations of
                    functioning rows shifted down to fill in the gap. This coordinate system is used to communicate with
                    the driver. Notation: X-Y
  - nocTr:          Translated NOC coordinate. Similar to noc0Virt, but offset by 16. Notation: X-Y
                    This system is used by the NOC hardware to account for harvesting. It is similar to the netlist
                    grid (distance one is next functioning core), but it is offset to not use the same range of
                    coordinates as the netlist grid, as that would cause confusion. The coordinates will start at 16, 16.
                    It is also constructed such that starting with (18, 18) it maps exactly to the netlist grid. It is
                    used by the NOC hardware and shows up in blob.yaml. These are also used in device_descs/n.yaml files.
                    Notation: X-Y

<a id="tt_coordinate.CoordinateTranslationError"></a>

## CoordinateTranslationError Objects

```python
class CoordinateTranslationError(Exception)
```

This exception is thrown when a coordinate translation fails.

<a id="tt_coordinate.OnChipCoordinate"></a>

## OnChipCoordinate Objects

```python
class OnChipCoordinate()
```

This class represents a coordinate on the chip. It can be used to convert between the various
coordinate systems we use.

<a id="tt_coordinate.OnChipCoordinate.__init__"></a>

#### \_\_init\_\_

```python
def __init__(x: int, y: int, input_type: str, device)
```

Constructor for the Coordinate class.

**Arguments**:

- `x` _int_ - The x-coordinate value.
- `y` _int_ - The y-coordinate value.
- `input_type` _str_ - The input coordinate system type. One of the following:
  - noc0: NOC routing coordinate for NOC 0. (X-Y)
  - nocVirt: Virtual NOC coordinate. Similar to noc0, but with the harvested rows removed, and the locations of functioning rows shifted down to fill in the gap. (X-Y)
  - noc1: NOC routing coordinate for NOC 1. (X-Y)
  - die: Die coordinate, a location on the die grid. (X,Y)
  - tensix: Tensix coordinate, represents a full grid of Tensix cores (including the disabled rows due to harvesting). (R,C)
  - netlist: Netlist coordinate, is similar to the 'tensix', but does not include the disabled rows due to harvesting. (R,C)
  - nocTr: Translated NOC coordinate. Similar to noc0Virt, but offset by 16. (X-Y)
- `device` - The device object used for coordinate conversion.
  

**Raises**:

- `Exception` - If the input coordinate system is unknown.
  

**Notes**:

  - If the device is not specified, coordinate conversion to other systems will not be possible.

<a id="tt_coordinate.OnChipCoordinate.from_stream_designator"></a>

#### from\_stream\_designator

```python
@staticmethod
def from_stream_designator(stream_designator: str)
```

This function takes a stream designator and returns the corresponding coordinate.

**Arguments**:

- `stream_designator` _str_ - The stream designator to convert into a coordinate.
  

**Returns**:

- `OnChipCoordinate` - The corresponding coordinate.
  

**Notes**:

  Stream designators are the key names in the blob yaml and have the form: chip_<chip_id>__y_<core_y>__x_<core_x>__stream_<stream_id>.
  

**Examples**:

  >>> from_stream_designator("chip_1__y_2__x_3__stream_4")
  OnChipCoordinate(core_x=3, core_y=2, nocTr='nocTr', chip_id=1)

<a id="tt_coordinate.OnChipCoordinate.to"></a>

#### to

```python
def to(output_type)
```

Returns a tuple with the coordinates in the specified coordinate system.

**Arguments**:

- `output_type` _str_ - The desired output coordinate system.
  

**Returns**:

- `tuple` - The coordinates in the specified coordinate system.
  

**Raises**:

- `Exception` - If the output coordinate system is unknown.

<a id="tt_coordinate.OnChipCoordinate.to_str"></a>

#### to\_str

```python
def to_str(output_type="nocTr")
```

Returns a tuple with the coordinates in the specified coordinate system.

<a id="tt_coordinate.OnChipCoordinate.to_user_str"></a>

#### to\_user\_str

```python
def to_user_str()
```

Returns a string representation of the coordinate that is suitable for the user.

<a id="tt_coordinate.OnChipCoordinate.create"></a>

#### create

```python
def create(coord_str, device, coord_type=None)
```

Creates a coordinate object from a string. The string can be in any of the supported coordinate systems.

**Arguments**:

- `coord_str` _str_ - The string representation of the coordinate.
- `device` _Device_ - The device object representing the chip.
- `coord_type` _str, optional_ - The type of coordinate system used in the string.
  If not specified, it will be determined based on the separators used in the string.
  

**Returns**:

- `OnChipCoordinate` - The created coordinate object.
  

**Raises**:

- `Exception` - If the coordinate format is unknown or invalid.
  
  Supported coordinate formats:
  - X-Y format: The coordinates are separated by a hyphen ("-"). Example: "10-20"
  - R,C format: The coordinates are separated by a comma (","). Example: "10,20"
  - DRAM channel format: The coordinate starts with "CH" followed by the channel number.
- `Example` - "CH1"
  

**Notes**:

  - If the coordinate format is X-Y or R,C, the coordinates will be converted to integers.
  - If the coordinate format is DRAM channel, the corresponding NOC0 coordinates will be used.

