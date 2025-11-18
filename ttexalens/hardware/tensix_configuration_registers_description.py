# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field


@dataclass
class TensixConfigurationRegistersDescription:
    # ALU
    alu_config: list[dict[str, str]] = field(default_factory=list)

    # UNPACKER
    unpack_tile_descriptor: list[dict[str, str]] = field(default_factory=list)
    unpack_config: list[dict[str, str]] = field(default_factory=list)

    # PACKER
    pack_config: list[dict[str, str]] = field(default_factory=list)
    relu_config: list[dict[str, str]] = field(default_factory=list)
    pack_dest_rd_ctrl: list[dict[str, str]] = field(default_factory=list)
    pack_edge_offset: list[dict[str, str]] = field(default_factory=list)
    pack_counters: list[dict[str, str]] = field(default_factory=list)
    pack_strides: list[dict[str, str]] = field(default_factory=list)

    # GENERAL PURPOSE REGISTERS
    general_purpose_registers: list[dict[str, str]] = field(default_factory=list)
