# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field


@dataclass
class TensixRegisterDescription:
    """Base for the per architecture groupings of Tensix configuration registers.
    Each architecture defines its own groupings of configuration registers."""


@dataclass
class TensixDebugBusDescription:
    # REGISTER WINDOW COUNTERS
    register_window_counter_groups: list[str] = field(default_factory=list)

    # ADDRESS COUNTERS
    address_counter_groups: list[str] = field(default_factory=list)
