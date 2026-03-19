# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tt_umd
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.hardware.risc_debug import RiscLocation


# ---------------------------------------------------------------------------
# Root exceptions
# ---------------------------------------------------------------------------


class TTException(Exception):
    pass


class TTFatalException(Exception):
    pass


class HardwareError(BaseException):
    """Hardware I/O failures.

    Intentionally does NOT inherit from Exception so that broad
    'except Exception' blocks do not swallow hardware failures.
    Use 'except HardwareError' to handle the whole category, or
    catch a specific subclass (e.g. TimeoutDeviceRegisterError).
    """

    pass


# ---------------------------------------------------------------------------
# Mid-tier bases
# ---------------------------------------------------------------------------


class MemoryAccessException(TTException):
    """Memory access policy violations (out-of-bounds, read-only writes)."""

    pass


class DebugSymbolError(TTException):
    """ELF/DWARF symbol resolution failures. May be recoverable."""

    pass


class CoordinateError(TTException):
    """Coordinate system conversion failures."""

    pass


# ---------------------------------------------------------------------------
# Hardware errors
# ---------------------------------------------------------------------------


class TimeoutDeviceRegisterError(HardwareError):
    def __init__(self, chip_id: int, coord: tt_umd.CoreCoord, address: int, size: int, is_read: bool, duration: float):
        self.chip_id = chip_id
        self.coord = coord
        self.address = address
        self.size = size
        self.is_read = is_read
        self.duration = duration

    def __str__(self):
        operation = "read" if self.is_read else "write"
        return (
            f"TimeoutDeviceRegisterError: Timeout during {operation} operation on device {self.chip_id}, "
            f"coord ({self.coord.x}, {self.coord.y}, {self.coord.core_type}), address {hex(self.address)}, "
            f"size {self.size} bytes after {self.duration:.4f} seconds."
        )


class RiscHaltError(HardwareError):
    """Raised when we failed to halt RISC core."""

    def __init__(self, risc_name: str, location: OnChipCoordinate):
        super().__init__(f"Failed to halt {risc_name} core at {location.to_user_str()} on device {location.device_id}")


# ---------------------------------------------------------------------------
# Memory access exceptions
# ---------------------------------------------------------------------------


class RestrictedMemoryAccessError(MemoryAccessException):
    """
    Raised when attempting to access memory outside of allowed regions
    (e.g., outside L1 or data private memory when restricted_access for them is enabled).
    """

    def __init__(self, access_start: int, access_end: int, location: OnChipCoordinate | RiscLocation):
        from ttexalens.coordinate import OnChipCoordinate as _OnChipCoordinate

        self.access_start = access_start
        self.access_end = access_end
        if isinstance(location, _OnChipCoordinate):
            self.risc_name = None
            self.neo_id = None
            self.location = location
        else:
            self.risc_name = location.risc_name
            self.neo_id = location.neo_id
            self.location = location.location

    def __str__(self) -> str:
        msg = f"Restricted access: Address range [0x{self.access_start:08x}, 0x{self.access_end:08x}] is outside allowed memory regions."
        if self.risc_name:
            if self.neo_id is not None:
                return f"RISC '{self.risc_name}' (Neo ID {self.neo_id}) at {self.location.to_user_str()}, {msg}"
            else:
                return f"RISC '{self.risc_name}' at {self.location.to_user_str()}, {msg}"
        return f"{self.location.to_user_str()}, {msg}"


class ReadOnlyMemoryError(MemoryAccessException):
    """Raised when a write is attempted on a read-only memory accessor (e.g. FixedMemoryAccess)."""

    def __init__(self, address: int, byte_count: int):
        super().__init__(f"Cannot write {byte_count} bytes to read-only memory at address 0x{address:08x}")
        self.address = address
        self.byte_count = byte_count


class UnsafeAccessException(MemoryAccessException):
    """Exception raised when an unsafe memory access violation is detected."""

    def __init__(
        self,
        location: OnChipCoordinate,
        original_addr: int,
        num_bytes: int,
        violating_addr: int,
        is_write: bool = False,
        reason: str | None = None,
    ):
        self.location = location
        self.original_addr = original_addr
        self.num_bytes = num_bytes
        self.violating_addr = violating_addr
        self.is_write = is_write
        self.reason = reason

    def __str__(self) -> str:
        msg = f"Attempted to {'write to' if self.is_write else 'read from'} address range [0x{self.original_addr:08x}, 0x{self.original_addr + self.num_bytes - 1:08x}]."
        if self.reason:
            msg += f" Reason: {self.reason}"
        return f"{self.location.to_user_str()}, unsafe access at address 0x{self.violating_addr:08x}. {msg}"


# ---------------------------------------------------------------------------
# Coordinate exceptions
# ---------------------------------------------------------------------------


class CoordinateTranslationError(CoordinateError):
    """Raised when a coordinate translation fails."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"CoordinateTranslationError: {self.message}"


class UnknownCoordinateSystemError(CoordinateError):
    """Raised when an unrecognized coordinate system name is used."""

    def __init__(self, coord_system: str, coordinate: OnChipCoordinate | None = None):
        msg = f"Unknown coordinate system: {coord_system!r}"
        if coordinate is not None:
            msg += f" for coordinate {coordinate}"
        super().__init__(msg)
        self.coord_system = coord_system
        self.coordinate = coordinate


# ---------------------------------------------------------------------------
# ELF / DWARF exceptions
# ---------------------------------------------------------------------------


class SymbolNotFoundError(DebugSymbolError):
    """A struct member, global symbol, or enum value was not found in DWARF.

    This is a static layout mismatch — the field does not exist in this
    firmware version's debug info. It is not a hardware failure.
    """

    def __init__(self, member_path: str):
        super().__init__(f"Cannot find member: {member_path}")
        self.member_path = member_path


class TypeMismatchError(DebugSymbolError):
    """The ELF type does not support the requested operation.

    Examples: indexing a non-array type, dereferencing a non-pointer,
    calling read_value() on a composite type.
    """

    def __init__(self, operation: str, actual_type: str | None):
        super().__init__(f"Cannot perform '{operation}' on type '{actual_type or '<unknown>'}'")
        self.operation = operation
        self.actual_type = actual_type or "<unknown>"


class InvalidArrayAccessError(DebugSymbolError):
    """Array index out of bounds or array length cannot be determined."""

    def __init__(self, index: int, length: int | None):
        super().__init__(f"Array index {index} out of bounds (length={length})")
        self.index = index
        self.length = length


class DataLossError(DebugSymbolError):
    """Writing this value would cause data loss (truncation or precision loss)."""

    def __init__(self, value: object, type_name: str | None):
        super().__init__(f"Data loss writing {value!r} to {type_name or '<unknown>'}")
        self.value = value
        self.type_name = type_name or "<unknown>"


class MemoryLayoutError(DebugSymbolError):
    """ELF/DWARF memory layout is invalid or incomplete.

    Raised when an L1 memory block cannot be found or has no NOC address.
    This is a firmware build artifact, not a hardware failure.
    """

    def __init__(self, message: str, location: OnChipCoordinate):
        super().__init__(message)
        self.location = location
