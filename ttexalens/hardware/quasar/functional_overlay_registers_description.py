# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field

# Hardware dimensions of the overlay cluster.
NUM_CORES = 8
NUM_INTERFACES = 4
NUM_TILE_COUNTERS = 16
NUM_PLIC_PENDING_WORDS = 3
NUM_PLIC_PRIORITY_SOURCES = 80


@dataclass
class OverlayRegistersDescription:
    tile_counters: list[list[dict[str, str]]] = field(default_factory=list)

    command_buffers: list[dict[str, str]] = field(default_factory=list)
    command_buffer_descriptors: list[dict[str, str]] = field(default_factory=list)

    bus_error_units: list[dict[str, str]] = field(default_factory=list)

    watchdog_timers: list[dict[str, str]] = field(default_factory=list)

    debug_module: dict[str, str] = field(default_factory=dict)
    debug_module_verbose: dict[str, str] = field(default_factory=dict)

    clint: list[dict[str, str]] = field(default_factory=list)
    clint_mtime: str = ""

    plic_cores: list[dict[str, str]] = field(default_factory=list)
    plic_pending: list[str] = field(default_factory=list)
    plic_priorities: list[str] = field(default_factory=list)


_LLK_IFACE_PREFIX = {
    0: "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_TILE_COUNTERS_",
    1: "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_1_TILE_COUNTERS_",
    2: "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_2_TILE_COUNTERS_",
    3: "TT_OVERLAY_LLK_TILE_COUNTERS_TT_LLK_INTERFACE_3_TILE_COUNTERS_",
}

_TILE_COUNTER_FIELDS = {
    "POSTED": "POSTED",
    "ACKED": "ACKED",
    "CAP": "BUFFER_CAPACITY",
    "ERR": "ERROR_STATUS",
    "R_POST": "READ_POSTED",
    "R_ACK": "READ_ACKED",
    "AVL_TH": "TILES_AVAIL_THRESHOLD",
    "FREE_TH": "TILES_FREE_THRESHOLD",
}

_CMDBUF_FIELDS = {
    "IP": "IP",
    "WR_SENT": "WR_SENT_TR_ID",
    "TR_ACK": "TR_ACK_TR_ID",
    "IP_0": "PER_TR_ID_IP_0",
    "IP_1": "PER_TR_ID_IP_1",
    "IP_2": "PER_TR_ID_IP_2",
}
_CMDBUF_DESCRIPTOR_FIELDS = [
    "SRC_ADDR",
    "SRC_COORD",
    "DEST_ADDR",
    "DEST_COORD",
    "LEN_BYTES",
    "REQ_VC",
    "RESP_VC",
    "TR_ID",
    "MISC",
]

_BUS_ERROR_FIELDS = ["CAUSE", "PHYS_ADDR", "ACCRUED", "ENABLE", "PLIC_ENABLE", "LOCAL_ENABLE"]

_WDT_FIELDS = ["CTRL", "COUNT", "SCALED_COUNT", "CMP"]

_DEBUG_FIELDS = ["DMSTATUS", "DMCONTROL", "HALTSUMMARY0", "HALTSUMMARY1", "ABSTRACTCS", "STATUS2", "SBCS", "HARTINFO"]
_DEBUG_VERBOSE_EXTRA = [
    "DATA0",
    "DATA1",
    "COMMAND",
    "ABSTRACTAUTO",
    "PROGBUF0",
    "PROGBUF1",
    "SBADDR0",
    "SBADDR1",
    "SBDATA0",
    "SBDATA1",
]

_PLIC_FIELDS = {
    "THRESHOLD": "THRESHOLD",
    "CLAIM_COMP": "CLAIM_COMPLETE",
    "IE_0": "IE_0_",
    "IE_1": "IE_1_",
    "IE_2": "IE_2_",
}


def _build() -> OverlayRegistersDescription:
    return OverlayRegistersDescription(
        tile_counters=[
            [
                {
                    field: f"{_LLK_IFACE_PREFIX[iface]}{counter}__{suffix}"
                    for field, suffix in _TILE_COUNTER_FIELDS.items()
                }
                for counter in range(NUM_TILE_COUNTERS)
            ]
            for iface in range(NUM_INTERFACES)
        ],
        command_buffers=[
            {field: f"TT_ROCC_ACCEL_TT_ROCC_CPU{cpu}_CMD_BUF_R_{suffix}" for field, suffix in _CMDBUF_FIELDS.items()}
            for cpu in range(NUM_CORES)
        ],
        command_buffer_descriptors=[
            {field: f"TT_ROCC_ACCEL_TT_ROCC_CPU{cpu}_CMD_BUF_R_{field}" for field in _CMDBUF_DESCRIPTOR_FIELDS}
            for cpu in range(NUM_CORES)
        ],
        bus_error_units=[
            {field: f"BUS_ERROR_UNIT_{unit}_{field}" for field in _BUS_ERROR_FIELDS} for unit in range(NUM_CORES)
        ],
        watchdog_timers=[
            {field: f"TT_CLUSTER_CORE{core}_WDT_{field}" for field in _WDT_FIELDS} for core in range(NUM_CORES)
        ],
        debug_module={field: f"TT_DEBUG_MODULE_APB_{field}" for field in _DEBUG_FIELDS},
        debug_module_verbose={field: f"TT_DEBUG_MODULE_APB_{field}" for field in _DEBUG_FIELDS + _DEBUG_VERBOSE_EXTRA},
        clint=[
            {
                "MSIP": f"TT_CLUSTER_CLINT_MSIP_{core}_",
                "MTIMECMP": f"TT_CLUSTER_CLINT_MTIMECMP_{core}_",
            }
            for core in range(NUM_CORES)
        ],
        clint_mtime="TT_CLUSTER_CLINT_MTIME",
        plic_cores=[
            {field: f"TT_CLUSTER_PLIC_CORE{core}_{suffix}" for field, suffix in _PLIC_FIELDS.items()}
            for core in range(NUM_CORES)
        ],
        plic_pending=[f"TT_CLUSTER_PLIC_PENDING_{word}_" for word in range(NUM_PLIC_PENDING_WORDS)],
        plic_priorities=[f"TT_CLUSTER_PLIC_PRIORITY_{source}_" for source in range(NUM_PLIC_PRIORITY_SOURCES)],
    )


overlay_registers_description = _build()
