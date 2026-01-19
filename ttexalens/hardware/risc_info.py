# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.memory_map import MemoryMap


class RiscInfo:
    def __init__(
        self,
        risc_name: str,
        risc_id: int,
        noc_block: NocBlock,
        neo_id: int | None,
        l1: MemoryBlock,
        memory_map: MemoryMap | None = None,
    ):
        self.risc_name = risc_name
        self.risc_id = risc_id
        self.noc_block = noc_block
        self.neo_id = neo_id
        self.l1 = l1
        self.memory_map = memory_map if memory_map is not None else MemoryMap()
