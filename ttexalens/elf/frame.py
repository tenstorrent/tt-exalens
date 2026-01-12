# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from functools import cached_property
from elftools.dwarf.callframe import FDE
from typing import TYPE_CHECKING

from ttexalens.memory_access import MemoryAccess, RestrictedMemoryAccessError

if TYPE_CHECKING:
    from ttexalens.hardware.risc_debug import RiscDebug


class FrameDescription:
    def __init__(self, pc: int, fde: FDE, risc_debug: RiscDebug):
        self.pc = pc
        self.fde = fde
        self.risc_debug = risc_debug
        self.mem_access = MemoryAccess.create(risc_debug)

        # Go through fde and try to find one that fits the pc
        decoded = self.fde.get_decoded()
        for entry in decoded.table:
            if entry["pc"] > self.pc:
                break
            self.current_fde_entry = entry

    def try_read_register(self, register_index: int, cfa: int | None) -> int | None:
        """Try to read a register value based on DWARF frame information rules.

        This method attempts to read a saved register value from the stack or another
        register using DWARF call frame information rules. Unlike `read_register`, this
        method does NOT fall back to reading the current register value if no rule is found.

        Args:
            register_index: The register index to read
            cfa: The Canonical Frame Address (can be None for top frame)

        Returns:
            The register value if it can be determined from frame rules, None otherwise
        """
        if self.current_fde_entry is not None and register_index in self.current_fde_entry:
            register_rule = self.current_fde_entry[register_index]

            # Handle UNDEFINED rule - register value is undefined
            if register_rule.type == "UNDEFINED":
                return None

            # Handle SAME_VALUE rule - register value is unchanged from previous frame
            elif register_rule.type == "SAME_VALUE":
                return self.risc_debug.read_gpr(register_index)

            # Handle OFFSET rule - register value is stored at address CFA + offset
            elif register_rule.type == "OFFSET":
                if cfa is None:
                    return None
                address = cfa + register_rule.arg
                try:
                    return self.mem_access.read_word(address)
                except RestrictedMemoryAccessError:
                    # If access was restricted (outside L1/data_private_memory), return None
                    return None

            # Handle REGISTER rule - register value is in another register
            elif register_rule.type == "REGISTER":
                other_register_index = register_rule.arg
                return self.risc_debug.read_gpr(other_register_index)

            # Handle VAL_OFFSET rule - register value is CFA + offset (not at that address)
            elif register_rule.type == "VAL_OFFSET":
                if cfa is None:
                    return None
                return cfa + register_rule.arg

            # Handle EXPRESSION and VAL_EXPRESSION rules - not yet implemented
            # These would require evaluating DWARF expressions, which is complex
            # and may not be needed for the current use case
            elif register_rule.type in ("EXPRESSION", "VAL_EXPRESSION"):
                return None

        # If no rule found or rule type not handled, return None
        return None

    def read_register(self, register_index: int, cfa: int) -> int | None:
        """Read a register value, with fallback to current register state.

        This method attempts to read a saved register value using DWARF frame rules,
        and falls back to reading the current register value from risc_debug if no
        rule is available or the rule evaluation returns None.
        This is useful for scenarios where you want to guarantee a register value.

        Args:
            register_index: The register index to read
            cfa: The Canonical Frame Address

        Returns:
            The register value
        """
        # Try to read using frame rules first
        value = self.try_read_register(register_index, cfa)
        if value is not None:
            return value
        # Fall back to reading current register value
        return self.risc_debug.read_gpr(register_index)

    def read_previous_cfa(self, current_cfa: int | None = None) -> int | None:
        if self.current_fde_entry is not None and self.fde.cie is not None:
            cfa_location = self.current_fde_entry["cfa"]
            register_index = cfa_location.reg
            offset: int = cfa_location.offset

            # Check if it is first CFA
            if current_cfa is None:
                # We have rule on how to calculate CFA (register_value + offset)
                return self.risc_debug.read_gpr(register_index) + offset
            else:
                # If register is not stored in the current frame, we can calculate it from the previous CFA
                if not register_index in self.current_fde_entry:
                    return current_cfa + offset

                # Just read stored value of the register in current frame
                return self.read_register(register_index, current_cfa)

        # We don't know how to calculate CFA, return 0 which will stop callstack evaluation
        return None


class FrameInspection:
    def __init__(
        self,
        risc_debug: RiscDebug,
        loaded_offset: int,
        frame_description: FrameDescription | None = None,
        cfa: int | None = None,
    ):
        self.risc_debug = risc_debug
        self.loaded_offset = loaded_offset
        self.frame_description = frame_description
        self.cfa = cfa
        self.mem_access = MemoryAccess.create(risc_debug)

    @cached_property
    def pc(self) -> int:
        value = self.read_register(register_index=32)
        assert value is not None
        return value

    def read_register(self, register_index: int) -> int | None:
        # If it is top frame, we can read all registers from RiscDebug
        if self.frame_description is None:
            return self.risc_debug.read_gpr(register_index)

        # If it is not top frame, we need to read registers from frame description
        return self.frame_description.try_read_register(register_index, self.cfa)


class FrameInfoProvider:
    def __init__(self, dwarf_info):
        self.dwarf_info = dwarf_info
        self.fdes = []

        # Check if we have dwarf_frame CFI section
        if dwarf_info.has_CFI():
            for entry in dwarf_info.CFI_entries():
                if not isinstance(entry, FDE):
                    continue
                start_address = entry.header["initial_location"]
                end_address = start_address + entry.header["address_range"]
                self.fdes.append((start_address, end_address, entry))

    def get_frame_description(self, pc, risc_debug) -> FrameDescription | None:
        for start_address, end_address, fde in self.fdes:
            if start_address <= pc < end_address:
                return FrameDescription(pc, fde, risc_debug)
        return None


class FrameInfoProviderWithOffset(FrameInfoProvider):
    def __init__(self, frame_info: FrameInfoProvider, loaded_offset: int):
        self.dwarf_info = frame_info.dwarf_info
        self.fdes = frame_info.fdes
        self._frame_info = frame_info
        self.loaded_offset = loaded_offset

    def get_frame_description(self, pc, risc_debug) -> FrameDescription | None:
        pc = pc + self.loaded_offset
        return self._frame_info.get_frame_description(pc, risc_debug)
