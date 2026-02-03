#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0

from docopt import DocoptExit


class TTException(Exception):
    """Base exception for TTExaLens errors."""


class CoordinateError(TTException):
    """Raised for coordinate parsing or translation errors."""


class ElfError(TTException):
    """Raised for ELF/DWARF parsing and symbol errors."""


class ElfLookupError(ElfError):
    """Raised when ELF symbols or members cannot be found."""


class ElfTypeError(ElfError):
    """Raised for invalid ELF/DWARF type operations."""


class ElfDataLossError(ElfError):
    """Raised when a write would cause data loss."""


class GdbError(TTException):
    """Raised for GDB server/client errors."""


class ServerError(TTException):
    """Raised for TTExaLens server startup/connection failures."""


class DocumentationError(TTException):
    """Raised for documentation generation errors."""


class CommandParsingException(TTException):
    """Custom exception to wrap DocoptExit and SystemExit."""

    def __init__(self, original_exception):
        self.original_exception = original_exception
        super().__init__(str(original_exception))

    def is_parsing_error(self):
        """If exception is DocoptExit, some parsing error occured"""
        return isinstance(self.original_exception, DocoptExit)

    def is_help_message(self):
        """If exception is SystemExit, h or help command is parsed. It is docopt behavior"""
        return isinstance(self.original_exception, SystemExit)


class CoordinateTranslationError(CoordinateError):
    """
    This exception is thrown when a coordinate translation fails.
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"CoordinateTranslationError: {self.message}"


class MemoryAccessError(TTException):
    """Raised for invalid or restricted memory access operations."""


class MemoryConfigurationError(MemoryAccessError):
    """Raised when required memory blocks or mappings are missing."""


class RestrictedMemoryAccessError(MemoryAccessError):
    """
    Raised when attempting to access memory outside of allowed regions
    (e.g., outside L1 or data private memory when restricted_access for them is is enabled).
    """

    def __init__(self, access_start: int, access_end: int, location: "OnChipCoordinate | RiscLocation"):
        """
        Args:
            access_start: Starting address of the attempted access
            access_end: Ending address of the attempted access (inclusive)
            location: Location of the RISC or on-chip memory where the access was attempted
        """

        from ttexalens.coordinate import OnChipCoordinate

        self.access_start = access_start
        self.access_end = access_end
        if isinstance(location, OnChipCoordinate):
            self.risc_name = None
            self.neo_id = None
            self.location = location
        else:
            self.risc_name = location.risc_name
            self.neo_id = location.neo_id
            self.location = location.location

    def __str__(self) -> str:
        """Generate error message lazily when the exception is converted to string."""

        msg = f"Restricted access: Address range [0x{self.access_start:08x}, 0x{self.access_end:08x}] is outside allowed memory regions."
        if self.risc_name:
            if self.neo_id is not None:
                return f"RISC '{self.risc_name}' (Neo ID {self.neo_id}) at {self.location.to_user_str()}, {msg}"
            else:
                return f"RISC '{self.risc_name}' at {self.location.to_user_str()}, {msg}"

        return f"{self.location.to_user_str()}, {msg}"


class UnsafeAccessException(TTException):
    """Exception raised when an unsafe memory access violation is detected."""

    def __init__(
        self,
        location: "OnChipCoordinate",
        original_addr: int,
        num_bytes: int,
        violating_addr: int,
        is_write: bool = False,
    ):
        self.location = location
        self.original_addr = original_addr
        self.num_bytes = num_bytes
        self.violating_addr = violating_addr
        self.is_write = is_write

    def __str__(self) -> str:
        """Generate error message lazily when the exception is converted to string."""

        msg = f"Attempted to {'write to' if self.is_write else 'read from'} address range [0x{self.original_addr:08x}, 0x{self.original_addr + self.num_bytes - 1:08x}]."
        return f"{self.location.to_user_str()}, unsafe access at address 0x{self.violating_addr:08x}. {msg}"


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tt_umd
    from ttexalens.coordinate import OnChipCoordinate
    from ttexalens.hardware.risc_debug import RiscLocation


class TimeoutDeviceRegisterError(TTException):
    def __init__(
        self,
        chip_id: int,
        coord: "tt_umd.CoreCoord",
        address: int,
        size: int,
        is_read: bool,
        duration: float,
    ):
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


class RiscHaltError(TTException):
    """
    Raised when we failed to halt RISC core.
    """

    def __init__(self, risc_name: str, location: "OnChipCoordinate"):
        self.risc_name = risc_name
        self.location = location

    def __str__(self):
        return f"RiscHaltError: Failed to halt RISC core {self.risc_name} at {self.location.to_user_str()}."


# We create a fatal exception that must terminate the program
# All other exceptions might get caught and the program might continue
class TTFatalException(TTException):
    pass
