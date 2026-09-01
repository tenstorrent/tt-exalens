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
NUM_WATCHPOINTS = 4

# Configuration sections (the SEC<n> suffix in the register names) are the per-context copies of a
# configuration register. Address modifiers have 32 of them, everything else has 4.
NUM_CONFIG_SECTIONS = 4
NUM_ADDR_MOD_SECTIONS = 32

# Clients of the DEST register bank, each with its own DVALID control register.
DEST_DVALID_CLIENTS = ["UNPACK_TO", "MATH", "SFPU", "PACK"]


@dataclass
class QuasarTensixRegisterDescription(TensixRegisterDescription):
    """Quasar configuration register groups."""

    # BUFFER DESCRIPTORS
    buffer_descriptor_table: list[dict[str, str]] = field(default_factory=list)

    # ADDRESS MODIFIERS
    addr_mod: list[dict[str, str]] = field(default_factory=list)

    # DEST AND SRC REGISTER BANKS
    dest_config: list[dict[str, str]] = field(default_factory=list)
    src_config: list[dict[str, str]] = field(default_factory=list)
    sfpu_config: list[dict[str, str]] = field(default_factory=list)
    dest_dvalid_ctrl: list[dict[str, str]] = field(default_factory=list)

    # PERFORMANCE COUNTERS
    perf_counter_config: list[dict[str, str]] = field(default_factory=list)

    # DEBUG
    watchpoints: list[dict[str, str]] = field(default_factory=list)

    # GLOBAL
    global_config: list[dict[str, str]] = field(default_factory=list)


def _group(pattern: str, instances: int) -> list[dict[str, str]]:
    """Collects the registers matching `pattern` into one {field name: register name} map per instance.

    The pattern names the parts of a register name it needs: `instance` picks the map a register goes
    into (no such group means everything lands in a single map), `field` becomes the key inside that
    map, and an optional `block` is prepended to the key to keep fields of sibling registers apart.
    Instances do not have to be uniform - a register that only some of them have is simply missing
    from the maps of the ones that do not.
    """
    regex = re.compile(pattern)
    groups: list[dict[str, str]] = [{} for _ in range(instances)]
    for register_name in register_map:
        match = regex.fullmatch(register_name)
        if match is None:
            continue
        captured = match.groupdict()
        field_name = captured["field"]
        if captured.get("block") is not None:
            field_name = f"{captured['block']}_{field_name}"
        instance = int(captured["instance"]) if captured.get("instance") is not None else 0
        groups[instance][field_name] = register_name
    return groups


_DEST_DVALID_FIELDS = ["wait_mask", "wait_polarity", "toggle_mask", "disable_auto_bank_id_toggle"]

# Registers that exist once per NEO instead of once per section, packer or unpacker.
_GLOBAL_REGISTERS = "|".join(
    [
        r"STATE_RESET_EN",
        r"UNUSED\d+",
        r"DEST_REGW_BASE_Base",
        r"DEST_SP_BASE_Base",
        r"DEST_ACCESS_CFG_.+",
        r"SRC_ACCESS_CFG_.+",
        r"DISABLE_IMPLIED_SRCS_FORMAT",
        r"SFPU_SRCS_BANK\d_FORMAT",
        r"PRNG_SEED.*",
        r"INT_DESCALE_VALUES_SEC\d+_Value",
        r"SCRATCH_SEC\d+_val",
        r"FMT_CTRL_.+",
    ]
)


def _build() -> QuasarTensixRegisterDescription:
    return QuasarTensixRegisterDescription(
        # ALU
        alu_config=_group(r"ALU_(?P<field>.+)", 1),
        # UNPACKERS
        unpack_config=_group(r"THCON_UNPACKER(?P<instance>\d)_(?P<field>REG\d_.+)", NUM_UNPACKERS),
        # PACKERS
        pack_config=_group(
            r"THCON_PACKER(?P<instance>\d)_(?P<field>REG\d_(?!EDGE_MASK|PACK_STRIDE|RELU_).+)", NUM_PACKERS
        ),
        pack_edge_offset=_group(r"THCON_PACKER(?P<instance>\d)_(?P<field>REG\d_EDGE_MASK.+)", NUM_PACKERS),
        pack_strides=_group(r"THCON_PACKER(?P<instance>\d)_(?P<field>REG\d_PACK_STRIDE_.+)", NUM_PACKERS),
        relu_config=_group(r"THCON_PACKER(?P<instance>\d)_(?P<field>REG\d_RELU_.+)", NUM_PACKERS),
        # BUFFER DESCRIPTORS
        buffer_descriptor_table=_group(
            r"BUFFER_DESCRIPTOR_TABLE_REG(?P<instance>\d+)_(?P<field>.+)", NUM_BUFFER_DESCRIPTORS
        ),
        # ADDRESS MODIFIERS
        addr_mod=_group(
            r"(?P<block>ADDR_MOD_(?:AB2|AB|DST))_SEC(?P<instance>\d+)_(?P<field>.+)", NUM_ADDR_MOD_SECTIONS
        ),
        # DEST AND SRC REGISTER BANKS
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
        dest_dvalid_ctrl=[
            {field_name: f"{client}_DEST_DVALID_CTRL_{field_name}" for field_name in _DEST_DVALID_FIELDS}
            for client in DEST_DVALID_CLIENTS
        ],
        # PERFORMANCE COUNTERS
        perf_counter_config=_group(r"PERF_CNT_CMD_SEC(?P<instance>\d)_(?P<field>.+)", NUM_CONFIG_SECTIONS),
        # DEBUG
        watchpoints=_group(r"CFG_WATCHPOINTS_(?P<instance>\d)_(?P<field>.+)", NUM_WATCHPOINTS),
        # GLOBAL
        global_config=_group(rf"(?P<field>{_GLOBAL_REGISTERS})", 1),
    )


tensix_registers_descriptions = _build()
