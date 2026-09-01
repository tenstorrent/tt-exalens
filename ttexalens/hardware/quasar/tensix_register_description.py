# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import re
from dataclasses import dataclass, field

from ttexalens.hardware.quasar.functional_neo_registers import register_map
from ttexalens.hardware.tensix_registers_description import TensixRegisterDescription

# Hardware dimensions of a single NEO.
NUM_UNPACKERS = 3
NUM_PACKERS = 2
NUM_BUFFER_DESCRIPTORS = 32

# Configuration sections (the SEC<n> suffix in the register names) are the per-context copies of a
# configuration register. Address modifiers have 32 of them, everything else has 4.
NUM_CONFIG_SECTIONS = 4
NUM_ADDR_MOD_SECTIONS = 32


@dataclass
class QuasarTensixRegisterDescription(TensixRegisterDescription):
    """Quasar configuration register groups."""

    buffer_descriptor_table: list[dict[str, str]] = field(default_factory=list)
    addr_mod: list[dict[str, str]] = field(default_factory=list)
    dest_config: list[dict[str, str]] = field(default_factory=list)
    src_config: list[dict[str, str]] = field(default_factory=list)
    sfpu_config: list[dict[str, str]] = field(default_factory=list)
    dest_dvalid_ctrl: list[dict[str, str]] = field(default_factory=list)
    perf_counter_config: list[dict[str, str]] = field(default_factory=list)
    watchpoints: list[dict[str, str]] = field(default_factory=list)
    global_config: list[dict[str, str]] = field(default_factory=list)


def _group(pattern: str, instances: int) -> list[dict[str, str]]:
    """Collects the registers matching `pattern` into one {field name: register name} map per instance."""
    regex = re.compile(pattern)
    groups: list[dict[str, str]] = [{} for _ in range(instances)]
    for register_name in register_map:
        match = regex.fullmatch(register_name)
        if match is None:
            continue
        captured = match.groupdict()
        field_name = captured["field"]
        block = captured.get("block")
        if block is not None:
            field_name = f"{block}_{field_name}"
        instance = captured.get("instance")
        instance = int(instance) if instance is not None else 0
        groups[instance][field_name] = register_name
    return groups


def _build() -> QuasarTensixRegisterDescription:
    return QuasarTensixRegisterDescription(
        alu_config=_group(r"ALU_(?P<field>.+)", 1),
        unpack_config=_group(r"THCON_UNPACKER(?P<instance>\d)_(?P<field>REG\d_.+)", NUM_UNPACKERS),
        pack_config=_group(
            r"THCON_PACKER(?P<instance>\d)_(?P<field>REG\d_(?!EDGE_MASK|PACK_STRIDE|RELU_).+)", NUM_PACKERS
        ),
        pack_edge_offset=_group(r"THCON_PACKER(?P<instance>\d)_(?P<field>REG\d_EDGE_MASK.+)", NUM_PACKERS),
        pack_strides=_group(r"THCON_PACKER(?P<instance>\d)_(?P<field>REG\d_PACK_STRIDE_.+)", NUM_PACKERS),
        relu_config=_group(r"THCON_PACKER(?P<instance>\d)_(?P<field>REG\d_RELU_.+)", NUM_PACKERS),
        buffer_descriptor_table=_group(
            r"BUFFER_DESCRIPTOR_TABLE_REG(?P<instance>\d+)_(?P<field>.+)", NUM_BUFFER_DESCRIPTORS
        ),
        addr_mod=_group(
            r"(?P<block>ADDR_MOD_(?:AB2|AB|DST))_SEC(?P<instance>\d+)_(?P<field>.+)", NUM_ADDR_MOD_SECTIONS
        ),
        dest_config=_group(
            r"(?P<block>RISC_DEST_ACCESS_CTRL|DEST_TARGET_REG_CFG_MATH|ENABLE_ACC_STATS|FP16A_FORCE)"
            r"_SEC(?P<instance>\d)_(?P<field>.+)",
            NUM_CONFIG_SECTIONS,
        ),
        src_config=_group(
            r"(?P<block>CLR_DVALID|FIDELITY_BASE|DISABLE_IMPLIED_SRCA_FMT|DISABLE_IMPLIED_SRCB_FMT)"
            r"_SEC(?P<instance>\d)_(?P<field>.+)",
            NUM_CONFIG_SECTIONS,
        ),
        sfpu_config=_group(
            r"(?P<block>SFPU_DEST_FMT|SFPU_STACK)_SEC(?P<instance>\d)_(?P<field>.+)", NUM_CONFIG_SECTIONS
        ),
    )


tensix_registers_descriptions = _build()
