# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
from functools import cached_property
from elftools.dwarf.callframe import FDE
from typing import TYPE_CHECKING

from ttexalens.memory_access import MemoryAccess, RestrictedMemoryAccessError

if TYPE_CHECKING:
    from ttexalens.hardware.risc_debug import RiscDebug
    from ttexalens.elf.dwarf import ElfDwarf


# https://github.com/riscv-non-isa/riscv-elf-psabi-doc/blob/master/riscv-cc.adoc
# RISC-V calling convention defines 12 callee-saved integer registers: s0/fp (x8), s1 (x9) and s2-s11 (x18-x27).
# If register wasn't mentioned in the call frame rules, it is preserved unchanged,
# so we can look for it further out or read it live.
RISCV_CALLEE_SAVED_REGISTERS = frozenset({8, 9} | set(range(18, 28)))


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

    def recover_register(self, register_index: int, cfa: int) -> tuple[bool, int | None]:
        """Describe how this frame restores the given register for its caller.

        First element of the returned tuple is boolean status: is value lost?
        Second element is the value if it is saved by this frame, or None if it is preserved unchanged or lost.

        Returns one of:
          (False, value)   - the frame spilled the register to the stack, here is its value;
          (True, None)     - the register is no longer recoverable through this frame;
          (False, None)    - the frame leaves the register unchanged (it is preserved), so the
                             caller's value must be looked for further out (or read live).
        """
        if self.current_fde_entry is None or register_index not in self.current_fde_entry:
            # Not mentioned by this frame's call-frame rules: preserved unchanged.
            return False, None
        rule = self.current_fde_entry[register_index]
        if rule.type == "OFFSET":
            try:
                return False, self.mem_access.read_word(cfa + rule.arg)
            except RestrictedMemoryAccessError:
                return True, None
        if rule.type == "SAME_VALUE":
            return False, None
        # UNDEFINED / REGISTER / EXPRESSION / ... - cannot recover the value safely.
        return True, None

    def read_register(self, register_index: int, cfa: int) -> int | None:
        if self.current_fde_entry is not None and register_index in self.current_fde_entry:
            register_rule = self.current_fde_entry[register_index]
            if register_rule.type == "OFFSET":
                address = cfa + register_rule.arg
            else:
                address = None
            if address is not None:
                try:
                    return self.mem_access.read_word(address)
                except RestrictedMemoryAccessError:
                    # If access was restricted (outside L1/data_private_memory), return None
                    return None
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

                # Read stored value of the register and apply the CFA offset
                saved_value = self.read_register(register_index, current_cfa)
                if saved_value is not None:
                    return saved_value + offset
                return None

        # We don't know how to calculate CFA, return 0 which will stop callstack evaluation
        return None


class FrameInspection:
    def __init__(
        self,
        risc_debug: RiscDebug,
        loaded_offset: int,
        cfa: int | None,
        inner_frames: list[tuple[FrameDescription, int]],
    ):
        self.risc_debug = risc_debug
        self.loaded_offset = loaded_offset
        self.cfa = cfa
        self.inner_frames = inner_frames
        self.mem_access = MemoryAccess.create(risc_debug)

    @cached_property
    def pc(self) -> int:
        value = self.read_register(register_index=32)
        assert value is not None
        return value

    def read_register(self, register_index: int) -> int | None:
        # If there are no inner frames, we are at the top of the call stack
        # and all registers are live in the core, so read directly.
        if not self.inner_frames:
            return self.risc_debug.read_gpr(register_index)

        # Look for the register value in the inner frames.
        for frame_description, cfa in self.inner_frames:
            lost, value = frame_description.recover_register(register_index, cfa)
            if lost:
                # Stop the search, the register is unrecoverable.
                return None
            elif not lost and value is not None:
                # The register is saved by this inner frame, return its value.
                return value
            else:
                # It could be preserved by this inner frame, keep looking further out.
                continue

        # Register wasn't preseved on any inner frame, so it is live in the core. Read it directly.
        if register_index in RISCV_CALLEE_SAVED_REGISTERS:
            return self.risc_debug.read_gpr(register_index)
        return None


class FrameInfoProvider:
    def __init__(self, dwarf: ElfDwarf):
        self.dwarf = dwarf
        self.fdes = []

        for entry in dwarf.cfi_entries:
            if not isinstance(entry, FDE):
                continue
            start_address = entry.header["initial_location"]
            end_address = start_address + entry.header["address_range"]
            self.fdes.append((start_address, end_address, entry))

    def get_frame_description(self, pc, risc_debug) -> FrameDescription | None:
        for start_address, end_address, fde in self.fdes:
            if start_address <= pc < end_address:
                with self.dwarf.parsed_elf._lock:
                    return FrameDescription(pc, fde, risc_debug)
        return None


class FrameInfoProviderWithOffset(FrameInfoProvider):
    def __init__(self, frame_info: FrameInfoProvider, loaded_offset: int):
        self.dwarf = frame_info.dwarf
        self.fdes = frame_info.fdes
        self._frame_info = frame_info
        self.loaded_offset = loaded_offset

    def get_frame_description(self, pc, risc_debug) -> FrameDescription | None:
        pc = pc + self.loaded_offset
        return self._frame_info.get_frame_description(pc, risc_debug)
