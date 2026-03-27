# Exception Hierarchy

All tt-exalens exceptions are defined in `ttexalens/exceptions.py`.

## Hierarchy Overview

```
BaseException
├── HardwareError
│   └── TimeoutDeviceRegisterError
└── Exception
    ├── TTException
    │   ├── MemoryAccessException
    │   │   ├── RestrictedMemoryAccessError
    │   │   ├── ReadOnlyMemoryError
    │   │   └── UnsafeAccessException
    │   ├── DebugSymbolError
    │   │   ├── SymbolNotFoundError
    │   │   ├── TypeMismatchError
    │   │   ├── InvalidArrayAccessError
    │   │   ├── DataLossError
    │   │   └── MemoryLayoutError
    │   ├── CoordinateError
    │   │   ├── CoordinateTranslationError
    │   │   └── UnknownCoordinateSystemError
    │   └── RiscHaltError
    └── TTFatalException
```

## Root Exceptions

### `TTException`

Base class for all recoverable tt-exalens errors. Catch this to handle any non-fatal library error.

```python
from ttexalens.exceptions import TTException
```

### `TTFatalException`

Signals an unrecoverable error that should terminate the program. Not a subclass of `TTException` — catching `TTException` will not catch this.

```python
from ttexalens.exceptions import TTFatalException
```

### `HardwareError`

Base class for hardware I/O failures. Intentionally inherits from `BaseException`, not `Exception`, so that broad `except Exception` blocks do not accidentally swallow hardware failures.

```python
from ttexalens.exceptions import HardwareError

try:
    ...
except HardwareError as e:
    # handle any hardware-level failure
```

---

## Hardware Errors

### `TimeoutDeviceRegisterError(HardwareError)`

Raised when a device read or write does not complete within the expected time.

**Attributes:** `chip_id`, `coord`, `address`, `size`, `is_read`, `duration`

```python
from ttexalens.exceptions import TimeoutDeviceRegisterError
```

---

## Memory Access Exceptions

All inherit from `MemoryAccessException(TTException)`.

### `RestrictedMemoryAccessError`

Raised when an access falls outside allowed memory regions (e.g., outside L1 or data private memory when `safe_mode` is enabled).

**Attributes:** `access_start`, `access_end`, `location`, `risc_name`, `neo_id`

### `ReadOnlyMemoryError`

Raised when a write is attempted on a read-only memory accessor (e.g., `FixedMemoryAccess`).

**Attributes:** `address`, `byte_count`

### `UnsafeAccessException`

Raised when a memory access violates safety constraints checked by the device layer.

**Attributes:** `location`, `original_addr`, `num_bytes`, `violating_addr`, `is_write`, `reason`

```python
from ttexalens.exceptions import MemoryAccessException  # catch all three
from ttexalens.exceptions import RestrictedMemoryAccessError, ReadOnlyMemoryError, UnsafeAccessException
```

---

## Debug Symbol Errors

All inherit from `DebugSymbolError(TTException)`. These are static firmware metadata mismatches — not hardware failures.

### `SymbolNotFoundError`

A struct member, global symbol, or enum constant was not found in DWARF debug info.

**Attributes:** `member_path`

### `TypeMismatchError`

The ELF type does not support the requested operation (e.g., indexing a non-array, dereferencing a non-pointer).

**Attributes:** `operation`, `actual_type`

### `InvalidArrayAccessError`

Array index is out of bounds or the array length cannot be determined.

**Attributes:** `index`, `length`

### `DataLossError`

Writing the given value to the ELF type would cause truncation or precision loss.

**Attributes:** `value`, `type_name`

### `MemoryLayoutError`

ELF/DWARF memory layout is invalid or incomplete — e.g., an L1 block cannot be found or has no NOC address.

**Attributes:** `location`

```python
from ttexalens.exceptions import DebugSymbolError  # catch all five
from ttexalens.exceptions import (
    SymbolNotFoundError,
    TypeMismatchError,
    InvalidArrayAccessError,
    DataLossError,
    MemoryLayoutError,
)
```

---

## Coordinate Errors

All inherit from `CoordinateError(TTException)`.

### `CoordinateTranslationError`

Raised when a coordinate cannot be converted between systems (e.g., a harvested row is referenced).

**Attributes:** `message`

### `UnknownCoordinateSystemError`

Raised when an unrecognized coordinate system name is used.

**Attributes:** `coord_system`, `coordinate`

```python
from ttexalens.exceptions import CoordinateError  # catch both
from ttexalens.exceptions import CoordinateTranslationError, UnknownCoordinateSystemError
```

---

## Other Exceptions

### `RiscHaltError(TTException)`

Raised when tt-exalens fails to halt a RISC-V core at the specified location.

**Attributes:** `risc_name`, `location` (via constructor args)

```python
from ttexalens.exceptions import RiscHaltError
```

---

## Catching Strategies

| Goal | Catch |
|------|-------|
| Any recoverable tt-exalens error | `TTException` |
| Any memory policy violation | `MemoryAccessException` |
| Any DWARF/ELF metadata error | `DebugSymbolError` |
| Any coordinate conversion error | `CoordinateError` |
| Any hardware I/O failure | `HardwareError` |
| Fatal errors only | `TTFatalException` |
