# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Blackhole Tensix perf-counter block descriptions.

The Blackhole layout (register names, offsets, counter ids) is identical to
Wormhole's — see tensix.h headers for both archs in tt-metal. Re-export the
Wormhole module so there is one source of truth.
"""

from ttexalens.hardware.wormhole.perf_counters import (
    ALL_BLOCKS,
    FPU,
    INSTRN_THREAD,
    TDMA_PACK,
    TDMA_UNPACK,
    initialization,
)

__all__ = [
    "ALL_BLOCKS",
    "FPU",
    "INSTRN_THREAD",
    "TDMA_PACK",
    "TDMA_UNPACK",
    "initialization",
]
