# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.risc_info import RiscInfo


class BabyRiscInfo(RiscInfo):
    def __init__(
        self,
        risc_name: str,
        risc_id: int,
        noc_block: NocBlock,
        l1: MemoryBlock,
        data_private_memory: MemoryBlock | None = None,
        code_private_memory: MemoryBlock | None = None,
        debug_hardware_present: bool = False,
    ):
        super().__init__(risc_name, risc_id, noc_block, l1)
        self.data_private_memory = data_private_memory
        self.code_private_memory = code_private_memory
        self.debug_hardware_present = debug_hardware_present
