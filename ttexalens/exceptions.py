#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0


class TTException(Exception):
    """Base exception for TTExaLens errors."""


class TTUsageError(TTException):
    """Raised for invalid user input or command usage."""


class TTTimeoutError(TTException):
    """Raised when an expected operation times out."""


class MemoryAccessError(TTException):
    """Raised for invalid or restricted memory access operations."""


class MemoryConfigurationError(MemoryAccessError):
    """Raised when required memory blocks or mappings are missing."""


class ReadOnlyMemoryAccessError(MemoryAccessError):
    """Raised when attempting to write to read-only memory access."""


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


class GdbCommunicationError(GdbError):
    """Raised for GDB transport/connection failures."""


class GdbProtocolError(GdbError):
    """Raised for GDB protocol parsing errors."""


class ServerError(TTException):
    """Raised for TTExaLens server startup/connection failures."""


class DocumentationError(TTException):
    """Raised for documentation generation errors."""


# We create a fatal exception that must terminate the program
# All other exceptions might get caught and the program might continue
class TTFatalException(TTException):
    pass
