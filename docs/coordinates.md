# On-Chip Coordinate Systems

This document explains how we handle different coordinate systems on a chip. The `OnChipCoordinate` class is central to translating between these systems.

## Coordinate Systems

1. **die**
   - Represents a “geographic” location on the die grid. Used mainly for diagrams or marketing visuals.

2. **noc0** (also called “physical”)
   - The main routing coordinate for NOC 0 (X-Y notation). One hop is one clock cycle on the network.

3. **noc1**
   - Similar to `noc0`, but for NOC 1. It routes in the opposite direction.

4. **logical**
   - Abstracts physical details. Often used to reference Tensix cores (e.g., `t0,0`), Ethernet (`e0,0`), DRAM (`d0,0`), etc.

5. **virtual**
   - A “compressed” version of `noc0`, skipping harvested (disabled) rows.

6. **translated**
   - A hardware-usable coordinate system offset by certain values (e.g., `(16,16)` on some chips), automatically accounting for harvesting.

## Class Overview

### `OnChipCoordinate`
- Stores an internal `noc0` coordinate (`_noc0_coord`).
- Converts from the input coordinate (die, noc0, noc1, logical, translated, virtual) to `noc0`.
- Provides a `.to(output_type)` method to translate to the desired system.
- Offers helper string methods (`to_str`, `to_user_str`) for user-friendly representation.

## Example Usage

The `OnChipCoordinate` class unifies different ways of specifying a chip location (e.g., `"X-Y"`, `"X,Y"`, `"chX"`) into one consistent object. Below are simple examples demonstrating how to use `OnChipCoordinate` in various scenarios.

### 1. Converting from a String

```python
from ttexalens.coordinate import OnChipCoordinate

# Suppose we have a device list: context.devices[0]
device = context.devices[0]

# Example coordinate string: could be "3-5" (noc0), "3,5" (logical), or "ch4" (DRAM channel).
core_loc_str = "3-5"

# Convert it into an OnChipCoordinate:
coord = OnChipCoordinate.create(core_loc_str, device=device)

print(coord)                  # Default string representation (logical)
print(coord.to("noc0"))       # Translate to (x_noc0, y_noc0)
print(coord.to("translated")) # If supported, translate to "translated" coords
```

1. **Automatic Parsing**
   `create()` inspects the string format (`"-"`, `","`, or `"ch"`) and determines which coordinate system to use.

2. **Translations**
   Calling `coord.to("<system>")` returns the coordinate in that system.

---

### 2. Working with Existing OnChipCoordinate

```python
# If you already have an OnChipCoordinate:
my_coord = OnChipCoordinate(2, 3, "noc0", device)

# You can convert it to logical coordinates:
logical_coord = my_coord.to("logical")

print("Logical coords:", logical_coord)
```


1. **Direct Instantiation**
   You can manually instantiate `OnChipCoordinate(x, y, input_type, device)` if you know the type (e.g., `"noc0"`).

2. **Switching Types**
   Use `.to("logical")`, `.to("noc0")`, `.to("virtual")`, etc., as needed.

---

### 3. Using OnChipCoordinate for Device Operations

When functions expect a chip location, you can supply either:
- A string like `"2-3"` (which gets converted internally).
- An existing `OnChipCoordinate`.

**Example** (pseudocode, not the full function):
```python
def read_word(core_loc, address, device):
    # Ensure we have an OnChipCoordinate:
    if not isinstance(core_loc, OnChipCoordinate):
        core_loc = OnChipCoordinate.create(core_loc, device=device)

    # Then translate to noc0:
    x, y = core_loc.to("noc0")

    # Perform your read operation here...
    return read_from_hardware_noc0(x, y, address)
```

In this way, **any** user input format (string or coordinate) is unified before performing the hardware call.

---

### 4. Changing Device

Sometimes you want to apply the same coordinate to a different device object:

```python
coord_dev0 = OnChipCoordinate.create("0,0", device=context.devices[0])
coord_dev1 = coord_dev0.change_device(context.devices[1])

print("Device 0 logical:", coord_dev0)
print("Device 1 logical:", coord_dev1)
```

- `change_device()` attempts to convert the existing coordinate to a “logical” representation (or “translated” if needed), then re-instantiate it on the new device.

---

### Tips

- **Convert Early:** If a function accepts a coordinate, convert it to `OnChipCoordinate` first.
- **Use `.to("noc0")`:** Most lower-level hardware calls need noc0 coordinates.
- **Harvesting:** If certain rows/columns are disabled, the device’s translation logic in `OnChipCoordinate` takes care of offsetting them internally.

#### Logical Coordinate Return Format

When calling `.to("logical")` on an `OnChipCoordinate`, the method returns a **two-part tuple**:

1. **The Logical Coordinates** `(x, y)`
2. **The Core Type**, such as `"tensix"`, `"eth"`, or `"dram"`

For example:
```
((2, 5), "tensix")
```
- `(2, 5)` is the logical coordinate.
- `"tensix"` is the core type.

## Device Command

The `device` command shows a summary of each chip’s layout or status (e.g., running RISC-V cores, block types) across various coordinate systems. This helps you see how a single physical location maps to different coordinate representations—such as `noc0`, `logical-tensix`, or `die`.

You can customize:

1. **Axis coordinate** (e.g., `noc0`, `logical-tensix`)
2. **Cell contents** (e.g., `riscv`, `block`)

If no arguments are provided, the command defaults to displaying the RISC-V status in a logical axis.

### Examples

- **Show default RISC-V status for all devices**
  ```
  device
  ```

- **Show RISC-V status in `noc0` coordinates**
  ```
  device noc0
  ```

- **Show block types in `logical-tensix` coordinates**
  ```
  device logical-tensix block
  ```

- **Show `noc0` coordinates on a `logical-dram` axis for device 0**
  ```
  device -d 0 logical-dram noc0
  ```

- **Hide the legend**
  ```
  device noc0 block --no-legend
  ```

Using `device` in different ways lets you explore how the chip’s coordinates relate to each other, whether you’re looking at physical routing (`noc0`) or logical groupings (`logical-tensix`, `logical-dram`)—all from a single command.
