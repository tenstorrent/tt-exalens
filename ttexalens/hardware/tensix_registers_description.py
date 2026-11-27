# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field


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

    # Registers stored as two halves named "<name>_lo" and "<name>_hi" that form one value.
    # Maps <name> to the left shift of the "_hi" half: the merged value is (hi << shift) | lo.
    split_registers: dict[str, int] = field(default_factory=dict, kw_only=True)

    def split_register_halves(self, name: str) -> tuple[str, str]:
        return name + "_lo", name + "_hi"

    def merge_split_registers(self, values: dict[str, int]) -> dict[str, int]:
        merged: dict[str, int] = {}
        for name, shift in self.split_registers.items():
            lo, hi = self.split_register_halves(name)
            if lo in values and hi in values:
                merged[name] = (values[hi] << shift) | values[lo]
        return merged


@dataclass
class TensixDebugBusDescription:
    # REGISTER WINDOW COUNTERS
    register_window_counter_groups: list[str] = field(default_factory=list)

    # ADDRESS COUNTERS
    address_counter_groups: list[str] = field(default_factory=list)
