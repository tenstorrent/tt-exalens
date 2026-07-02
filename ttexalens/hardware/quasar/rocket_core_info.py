# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from ttexalens.hardware.memory_block import MemoryBlock
from ttexalens.hardware.risc_info import RiscInfo

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ttexalens.hardware.quasar.functional_overlay_block import QuasarFunctionalOverlayBlock


class QuasarRocketCoreInfo(RiscInfo):
    """
    Describes a single Rocket RISC-V core inside the Quasar overlay cluster.

    Each Quasar functional worker tile contains one overlay cluster with 8
    in-order 64-bit Rocket cores. These are the data-movement (DMRISC) cores
    that replace the NOC stream hardware of earlier architectures (Wormhole /
    Blackhole).

    Hardware reference: Quasar HAS / Overlay Specification (Tenstorrent).
    Cluster ctrl base: 0x03000000
    Debug Module APB base: 0x0300A000
    """

    NUM_CORES = 8

    def __init__(self, risc_id: int, overlay_block: "QuasarFunctionalOverlayBlock", l1: MemoryBlock):
        assert 0 <= risc_id < self.NUM_CORES, f"rocket core ID must be 0-{self.NUM_CORES - 1}, got {risc_id}"
        super().__init__(
            risc_name=f"rocket{risc_id}",
            risc_id=risc_id,
            noc_block=overlay_block,
            neo_id=None,
            l1=l1,
        )
        # Register name for setting / reading the reset (boot) vector of this core.
        self.reset_vector_register = f"TT_CLUSTER_CTRL_RESET_VECTOR_{risc_id}"
        # Register name for reading the write-back PC snapshot (non-invasive PC read).
        self.wb_pc_register = f"TT_CLUSTER_CTRL_WB_PC_REG_C{risc_id}"
        # Default code start address (reset vector default for bare-metal firmware).
        self.default_code_start_address: int = 0x0
