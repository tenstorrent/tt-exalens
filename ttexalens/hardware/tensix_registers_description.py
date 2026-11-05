# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class TensixState:
    """Tensix state groups common to all architectures. Each architecture extends it with its own groups."""

    alu_config: list[dict[str, int]]
    unpack_config: list[dict[str, int]]
    pack_config: list[dict[str, int]]
    relu_config: list[dict[str, int]]
    pack_edge_offset: list[dict[str, int]]
    pack_strides: list[dict[str, int]]
    general_purpose_registers: list[dict[str, int]]
    register_window_counters: dict[str, int]
    address_counters: dict[str, int]


@dataclass
class TensixRegisterDescription:
    """Base for the per architecture groupings of Tensix configuration registers.
    Each architecture defines its own groupings of configuration registers."""

    state_type: ClassVar[type[TensixState]]


@dataclass
class TensixDebugBusDescription:
    # REGISTER WINDOW COUNTERS
    register_window_counter_groups: list[str] = field(default_factory=list)

    # ADDRESS COUNTERS
    address_counter_groups: list[str] = field(default_factory=list)
