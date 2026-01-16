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
    def __init__(self, pc: int, fde: FDE, risc_debug: RiscDebug, dwarf_info=None):
        self.pc = pc
        self.fde = fde
        self.risc_debug = risc_debug
        self.dwarf_info = dwarf_info
        self.mem_access = MemoryAccess.create(risc_debug)
        self.current_fde_entry = None

        # Go through fde and try to find one that fits the pc
        decoded = self.fde.get_decoded()
        for entry in decoded.table:
            if entry["pc"] > self.pc:
                break
            self.current_fde_entry = entry

    def try_read_register(
        self, register_index: int, cfa: int | None, previous_frame: FrameInspection | None = None
    ) -> int | None:
        if self.current_fde_entry is not None and register_index in self.current_fde_entry:
            register_rule = self.current_fde_entry[register_index]

            if register_rule.type == "UNDEFINED":
                return None

            # Handle SAME_VALUE rule - register value is unchanged from previous frame
            elif register_rule.type == "SAME_VALUE":
                if previous_frame is not None:
                    value = previous_frame.read_register(register_index)
                    return value
                # This shouldn't happen in normal unwinding - if it does, something is wrong
                return None

            # Handle OFFSET rule - register value is stored at address CFA + offset
            elif register_rule.type == "OFFSET":
                if cfa is None:
                    return None
                address = cfa + register_rule.arg
                try:
                    value = self.mem_access.read_word(address)
                    return value
                except RestrictedMemoryAccessError:
                    # If access was restricted (outside L1/data_private_memory), return None
                    return None

            # Handle REGISTER rule - register value is in another register from previous frame
            elif register_rule.type == "REGISTER":
                other_register_index = register_rule.arg
                if previous_frame is not None:
                    value = previous_frame.read_register(other_register_index)
                    return value
                # This shouldn't happen in normal unwinding - if it does, something is wrong
                return None

            # Handle VAL_OFFSET rule - register value is CFA + offset (not at that address)
            elif register_rule.type == "VAL_OFFSET":
                if cfa is None:
                    return None
                value = int(cfa + register_rule.arg)
                return value

            # Handle EXPRESSION rule - evaluate expression to get memory address, then read value
            elif register_rule.type == "EXPRESSION":
                if self.dwarf_info is None or previous_frame is None:
                    # Need DWARF info for expression parser and previous frame for context
                    return None

                from ttexalens.elf.expression_evaluator import evaluate_dwarf_expression

                # Parse the expression bytes
                expression_bytes = register_rule.arg
                try:
                    expr_parser = self.dwarf_info.location_parser
                    # The arg should be a bytes-like expression
                    if isinstance(expression_bytes, (list, bytes)):
                        # Parse expression using DWARF expression parser
                        parsed = self.dwarf_info.expression_parser.parse_expr(expression_bytes)

                        # Evaluate to get address
                        is_address, address = evaluate_dwarf_expression(parsed, previous_frame, cfa, cu=None)

                        if address is None:
                            return None

                        if not is_address:
                            # EXPRESSION should yield an address, not a value
                            return None

                        # Read value from the computed address
                        try:
                            value = self.mem_access.read_word(address)
                            return value
                        except RestrictedMemoryAccessError:
                            return None
                    else:
                        return None
                except Exception:
                    # Expression evaluation failed
                    return None

            # Handle VAL_EXPRESSION rule - evaluate expression to get value directly
            elif register_rule.type == "VAL_EXPRESSION":
                if self.dwarf_info is None or previous_frame is None:
                    # Need DWARF info for expression parser and previous frame for context
                    return None

                from ttexalens.elf.expression_evaluator import evaluate_dwarf_expression

                # Parse the expression bytes
                expression_bytes = register_rule.arg
                try:
                    # The arg should be a bytes-like expression
                    if isinstance(expression_bytes, (list, bytes)):
                        # Parse expression using DWARF expression parser
                        parsed = self.dwarf_info.expression_parser.parse_expr(expression_bytes)

                        # Evaluate to get value directly
                        is_address, value = evaluate_dwarf_expression(parsed, previous_frame, cfa, cu=None)

                        if value is None:
                            return None

                        # VAL_EXPRESSION gives value directly (not an address to read from)
                        return value if isinstance(value, int) else None
                    else:
                        return None
                except Exception:
                    # Expression evaluation failed
                    return None

        return None

    def read_register(self, register_index: int, cfa: int, previous_frame: FrameInspection | None = None) -> int | None:
        # Try to read using frame rules first
        value = self.try_read_register(register_index, cfa, previous_frame)
        if value is not None:
            return value
        # Fall back to reading current register value
        return self.risc_debug.read_gpr(register_index)

    def read_previous_cfa(
        self, current_cfa: int | None = None, previous_frame: FrameInspection | None = None
    ) -> int | None:
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
                return self.read_register(register_index, current_cfa, previous_frame)

        # We don't know how to calculate CFA, return 0 which will stop callstack evaluation
        return None


class FrameInspection:
    def __init__(
        self,
        risc_debug: RiscDebug,
        loaded_offset: int,
        frame_description: FrameDescription | None = None,
        cfa: int | None = None,
        previous_frame: "FrameInspection | None" = None,
    ):
        self.risc_debug = risc_debug
        self.loaded_offset = loaded_offset
        self.frame_description = frame_description
        self.cfa = cfa
        self.previous_frame = previous_frame
        self.mem_access = MemoryAccess.create(risc_debug)
        self._register_cache: dict[int, int | None] = {}

    @cached_property
    def pc(self) -> int:
        value = self.read_register(register_index=32)
        assert value is not None
        return value

    def read_register(self, register_index: int) -> int | None:
        if register_index in self._register_cache:
            return self._register_cache[register_index]

        value: int | None
        if self.frame_description is None:
            # Top frame - read all registers from RiscDebug (current hardware state)
            value = self.risc_debug.read_gpr(register_index)
        else:
            # Non-top frame - read registers from frame description using DWARF rules
            value = self.frame_description.try_read_register(register_index, self.cfa, self.previous_frame)

        self._register_cache[register_index] = value
        return value


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
                return FrameDescription(pc, fde, risc_debug, self.dwarf_info)
        return None


class FrameInfoProviderWithOffset(FrameInfoProvider):
    def __init__(self, frame_info: FrameInfoProvider, loaded_offset: int):
        self.dwarf_info = frame_info.dwarf_info
        self.fdes = frame_info.fdes
        self._frame_info = frame_info
        self.loaded_offset = loaded_offset

    def get_frame_description(self, pc, risc_debug) -> FrameDescription | None:
        adjusted_pc = pc + self.loaded_offset
        return self._frame_info.get_frame_description(adjusted_pc, risc_debug)
