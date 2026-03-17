# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.util import DebugSymbolError


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

    def __init__(self, value, type_name: str | None):
        super().__init__(f"Data loss writing {value!r} to {type_name or '<unknown>'}")
        self.value = value
        self.type_name = type_name or "<unknown>"


class MemoryLayoutError(DebugSymbolError):
    """ELF/DWARF memory layout is invalid or incomplete.

    Raised when an L1 memory block cannot be found or has no NOC address.
    This is a firmware build artifact, not a hardware failure.
    """

    pass
