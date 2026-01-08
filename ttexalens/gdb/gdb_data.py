# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from dataclasses import dataclass
from functools import cached_property
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.memory_access import MemoryAccess


@dataclass
class GdbThreadId:
    process_id: int
    thread_id: int

    def to_gdb_string(self):
        return f"p{self.process_id:X}.{self.thread_id:X}"


@dataclass
class GdbProcess:
    process_id: int
    elf_path: str | None
    risc_debug: RiscDebug
    virtual_core_id: int
    core_type: str
    mem_access: MemoryAccess

    def __init__(
        self, process_id: int, elf_path: str | None, risc_debug: RiscDebug, virtual_core_id: int, core_type: str
    ):
        self.process_id = process_id
        self.elf_path = elf_path
        self.risc_debug = risc_debug
        self.virtual_core_id = virtual_core_id
        self.core_type = core_type
        self.mem_access = MemoryAccess.create(risc_debug)

    @cached_property
    def thread_id(self):
        return GdbThreadId(self.process_id, self.virtual_core_id)

    def __eq__(self, other):
        if not isinstance(other, GdbProcess):
            return NotImplemented
        return (self.process_id, self.elf_path) == (other.process_id, other.elf_path)

    def __hash__(self):
        return hash((self.process_id, self.elf_path))
