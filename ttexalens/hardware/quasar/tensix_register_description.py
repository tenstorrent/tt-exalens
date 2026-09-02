# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field

from ttexalens.hardware.tensix_registers_description import TensixRegisterDescription


@dataclass
class QuasarTensixRegisterDescription(TensixRegisterDescription):
    """Tensix configuration register groups of a Quasar NEO block."""

    # ALU
    alu_config: list[dict[str, str]] = field(default_factory=list)

    # UNPACKER
    unpack_config: list[dict[str, str]] = field(default_factory=list)

    # PACKER
    pack_config: list[dict[str, str]] = field(default_factory=list)
    relu_config: list[dict[str, str]] = field(default_factory=list)
    pack_edge_offset: list[dict[str, str]] = field(default_factory=list)
    pack_strides: list[dict[str, str]] = field(default_factory=list)

    # BUFFER DESCRIPTOR
    buffer_descriptor_table: list[dict[str, str]] = field(default_factory=list)

    # ADDRESS MODIFIERS
    addr_mod: list[dict[str, str]] = field(default_factory=list)

    # REGISTERS
    dest_config: list[dict[str, str]] = field(default_factory=list)
    src_config: list[dict[str, str]] = field(default_factory=list)
    sfpu_config: list[dict[str, str]] = field(default_factory=list)
    dest_dvalid_ctrl: list[dict[str, str]] = field(default_factory=list)

    # PERF COUNTERS CONFIG
    perf_counter_config: list[dict[str, str]] = field(default_factory=list)

    # DEBUG
    watchpoints: list[dict[str, str]] = field(default_factory=list)

    # GLOBAL CONFIG
    global_config: list[dict[str, str]] = field(default_factory=list)
